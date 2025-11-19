#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Test Health is a table that shows elapsed execution time, pass rate, and
# a history of test statuses, which will help us identify tests that need
# stabilization or optimization, and follow performance trends.

from datetime import datetime, timedelta
from collections import namedtuple
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from database import (
    Database,
    ReportTestRailTestHealth,
)

from api.testrail.client import TestRail
from api.testrail.helpers import testrail_project_ids


_DB = None
_TR = None


def _db() -> Database():
    global _DB
    if _DB is None:
        _DB = Database()
    return _DB


def _tr() -> TestRail():
    global _TR
    if _TR is None:
        _TR = TestRail()
    return _TR


def clip_to_numerals(s: str) -> str:
    i = 0
    try:
        while not s[i].isnumeric():
            i += 1
    except IndexError:
        i = len(s)
    return s[i:]


def dur_to_sec(timestamp: str) -> float:
    accu = 0
    conv = {"d": 86400.0, "h": 3600.0, "m": 60.0, "s": 1.0}
    for unit in conv:
        if unit in timestamp:
            val, remainder = timestamp.split(unit, 1)
            accu += float(val) * conv[unit]
            timestamp = clip_to_numerals(remainder)
    return accu


def update_testrail_test_health_row(payload, update_list):
    db = _db()
    new_row = {
        "testrail_case_id": None,
        "testrail_project_id": None,
        "testrail_case_name": None,
        "testrail_suite_name": None,
        "num_executions": None,
        "avg_runtime": None,
        "pass_rate": None,
        "most_recent_timestamp": None,
        "most_recent_runtime": None,
        "most_recent_status": None,
        "status_history_1": None,
        "status_history_2": None,
        "status_history_3": None,
        "status_history_4": None,
        "created_on": datetime.utcnow(),
    }

    reserved_names = ["metadata", "registry"]
    Update = namedtuple(
        "Update",
        [
            k
            for k in dir(ReportTestRailTestHealth())
            if not k.startswith("_") and k not in reserved_names
        ],
    )

    def increment_average(starting_count, starting_average, new_value) -> float:
        return (
            float(starting_average)
            * (float(starting_count) / float(starting_count + 1))
        ) + (float(new_value) * (1.0 / float(starting_count + 1)))

    new_row["testrail_case_id"] = payload.get("case_id")
    new_row["testrail_project_id"] = payload.get("project_id")
    new_row["testrail_case_name"] = payload.get("case_name")
    new_row["testrail_suite_name"] = payload.get("suite_name")

    try:
        matching_update = [
            u for u in update_list if u["testrail_case_id"] == payload["case_id"]
        ]
        if matching_update:
            row = Update(**matching_update[0])
        else:
            row = db.session.scalars(
                select(ReportTestRailTestHealth).where(
                    ReportTestRailTestHealth.testrail_case_id == payload.get(
                        "case_id")
                )
            ).one()
        starting_count = row.num_executions
        new_row["num_executions"] = starting_count + 1
        new_row["avg_runtime"] = increment_average(
            starting_count, row.avg_runtime, payload.get("elapsed")
        )
        new_row["pass_rate"] = increment_average(
            starting_count, row.pass_rate, payload.get("status")
        )
        new_row["status_history_4"] = row.status_history_3
        new_row["status_history_3"] = row.status_history_2
        new_row["status_history_2"] = row.status_history_1
        if payload.get("created_on") > row.most_recent_timestamp:
            new_row["most_recent_timestamp"] = payload["created_on"]
            new_row["most_recent_runtime"] = payload["elapsed"]
            new_row["status_history_1"] = row.most_recent_status
            new_row["most_recent_status"] = payload["status"]
        else:
            new_row["status_history_1"] = payload["status"]
            new_row["most_recent_timestamp"] = row.most_recent_timestamp
            new_row["most_recent_runtime"] = row.most_recent_runtime
            new_row["most_recent_status"] = row.most_recent_status
    except NoResultFound:
        # new test
        new_row["num_executions"] = 1
        new_row["avg_runtime"] = payload.get("elapsed")
        new_row["pass_rate"] = float(payload.get("status"))
        new_row["most_recent_timestamp"] = payload.get("created_on")
        new_row["most_recent_runtime"] = payload.get("elapsed")
        new_row["most_recent_status"] = payload.get("status")

    return new_row


def testrail_test_health(project, num_days=1):
    tr = _tr()

    # Dictionary of project ids and their respective service acct user id
    AUTOUSERS = {17: 976}
    updates = []
    project_ids_list = testrail_project_ids(project)[0]
    start_date = datetime.now() - timedelta(days=int(num_days))
    for project_id in project_ids_list:
        if project_id not in AUTOUSERS:
            continue
        plans = tr.search_test_plans(
            project_id,
            created_by=AUTOUSERS.get(project_id),
            created_after=int(start_date.timestamp()),
        )

        # Iterate through plans to get result and test info
        for plan in plans.get("plans"):
            plan_details = tr.get_test_plan(plan.get("id"))
            for entry in plan_details.get("entries"):
                for run in entry.get("runs"):
                    for result in tr.test_results_for_run(run.get("id")).get("results"):
                        if not result.get("elapsed"):
                            continue
                        test = tr.get_test(result.get("test_id"))
                        suite_name = tr.test_suite(
                            run.get("suite_id")).get("name")
                        update_payload = {
                            "case_id": test.get("case_id"),
                            "project_id": project_id,
                            "case_name": test.get("title"),
                            "suite_name": suite_name,
                            "created_on": datetime.fromtimestamp(
                                int(result.get("created_on"))
                            ),
                            "elapsed": dur_to_sec(result.get("elapsed")),
                            "status": result.get("status_id"),
                        }
                        new_row = update_testrail_test_health_row(
                            update_payload, updates
                        )
                        matching_row = [
                            u
                            for u in updates
                            if u.get("testrail_case_id") == new_row["testrail_case_id"]
                        ]
                        if matching_row:
                            updates.remove(matching_row[0])
                        updates.append(new_row)

    report_test_health_update(updates)


def report_test_health_update(payload):
    db = _db()
    for row in payload:
        matching_row = db.session.query(ReportTestRailTestHealth).filter(
            ReportTestRailTestHealth.testrail_case_id == row["testrail_case_id"]
        )
        if matching_row:
            matching_row.update(row, synchronize_session="fetch")
        else:
            db.session.add(ReportTestRailTestHealth(**payload))
            db.session.commit()
        db.session.commit()
