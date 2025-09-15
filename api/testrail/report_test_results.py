#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import inspect

from database import (
    Database,
    ReportTestRailTestPlans,
    ReportTestRailTestResults,
    ReportTestRailTestRuns,
)

from api.testrail.client import TestRail
from utils.datetime_utils import DatetimeUtils as dt

_TR = None
_DB = None


def _tr() -> TestRail():
    global _TR
    if _TR is None:
        _TR = TestRail()
    return _TR


def _db() -> Database():
    global _DB
    if _DB is None:
        _DB = Database()
    return _DB


# ===================================================================
# ORCHESTRATOR (BATCH)
# ===================================================================

def testrail_test_results():
    """Gets all the test result duration for the latest test plans
    Precondition: testrail_plans_and_runs have been run prior"""

    print("--------------------------------------")
    print("DIAGNOSTIC")
    print(inspect.currentframe().f_code.co_name)
    print("--------------------------------------")

    db = _db()
    tr = _tr()

    # Get the most recent test plan ids for beta and l10n
    tp_ids = [None, None]
    for tp in db.session.query(ReportTestRailTestPlans).order_by(
            ReportTestRailTestPlans.testrail_plan_id.desc()).all():
        if "Beta" in tp.name:
            if not tp_ids[0] and "L10N" not in tp.name:
                tp_ids[0] = tp.testrail_plan_id
            elif not tp_ids[1] and "L10N" in tp.name:
                tp_ids[1] = tp.testrail_plan_id
            if tp_ids[0] and tp_ids[1]:
                break

    # Insert data for beta and refer back to test run table
    db.clean_table(ReportTestRailTestResults)
    types = ("beta", "l10n")

    for i, type in enumerate(types):

        print("DIAGNOSTIC")
        print(f"type: {type}, i: {i}, tp_ids[i]: {tp_ids[i]}")

        runs = tr.get_test_plan(tp_ids[i])["entries"]

        for run in runs:
            for config in run["runs"]:
                db_run_id = db.session.query(
                    ReportTestRailTestRuns).filter_by(
                        testrail_run_id=config["id"]).first().id
                run_results = (
                    tr.test_results_for_run(config["id"])["results"]
                )

                print(f"Adding all results from run {config['id']}")
                report_testrail_test_result_insert(
                    db_run_id, run_results, type)
        print(f"Added all test results from table {type}")


# ===================================================================
# PREPARE/PAYLOAD
# ===================================================================

def report_test_run_payload(runs):
    """pack testrail data for 1 run in a data array

    NOTE:
    run_name

    Because storing data for 1 run will occupy multipe db rows,
    Storing the run name would require inserting into a reference
    table.  For now, we will just store the testrail run id.

    project_id, suite_id

    We will pass along the proj_name_abbrev to the db.
    For suite_id, we will always default to Full Functional.
    """

    # DIAGNOSTIC
    print("--------------------------------------")
    print("DIAGNOSTIC")
    print(inspect.currentframe().f_code.co_name)
    print("--------------------------------------")

    # create array to store values to insert in database
    payload = []

    for run in runs:
        tmp = {}

        # identifiers
        # tmp.append({'name': run['name']})
        tmp.update({'testrail_run_id': run['id']})

        # epoch dates
        tmp.update({'testrail_created_on': run['created_on']})
        tmp.update({'testrail_completed_on': run['completed_on']})

        # test data
        tmp.update({'passed_count': run['passed_count']})
        tmp.update({'retest_count': run['retest_count']})
        tmp.update({'failed_count': run['failed_count']})
        tmp.update({'blocked_count': run['blocked_count']})
        payload.append(tmp)
    return payload


# ===================================================================
# ORCHESTRATOR (PER-PROJECT)
# ===================================================================

def testrail_run_counts_update(project, num_days):

    db = _db()
    tr = _tr()

    start_date = dt.start_date(num_days)

    # Get reference IDs from DB
    # TODO: testrail_identity_ids was removed in 2022
    #       could be replaced by helper.testrail_project_ids

    (
        projects_id,
        testrail_project_id,
        functional_test_suite_id,
    ) = db.testrail_identity_ids(project)

    # Pull JSON blob from Testrail
    runs = tr.test_runs(testrail_project_id, start_date)

    # Format and store data in a 'totals' array
    totals = db.report_test_run_payload(runs)

    print("-------------------------")
    print("DIAGNOSTIC")
    print(inspect.currentframe().f_code.co_name)
    print("-------------------------")
    print(totals)

    # Insert data in the 'totals' array into DB
    db.report_test_runs_insert(projects_id, totals)


# ===================================================================
# DB INSERT
# ===================================================================

def report_testrail_test_result_insert(db_run_id, payload, type):

    print("--------------------------------------")
    print("DIAGNOSTIC")
    print(inspect.currentframe().f_code.co_name)
    print("--------------------------------------")

    # insert data from payload into report_testrail_test_results table

    db = _db()

    for result in payload:
        # Skip if not automated testing
        if result["created_by"] != 976:
            continue

        created_on = dt.convert_epoch_to_datetime(result['created_on'])

        completed_on = (
            dt.convert_epoch_to_datetime(result['completed_on'])
            if result.get('completed_on') else None
        )

        elapsed = result["elapsed"]
        if elapsed:
            if "min" in elapsed:
                parts = elapsed.split(" ")
                time = int(parts[0][:-3]) * 60 + \
                    (int(parts[1][:-3]) if len(parts) > 1 else 0)
            else:
                time = elapsed[:-3]

        args = {
            'testrail_result_id': result['id'],
            'run_id': db_run_id,
            'test_id': result['test_id'],
            'elapsed': float(time),
            'status_id': result['status_id'],
            'testrail_created_on': created_on,
            'testrail_completed_on': completed_on,
            'type': type
        }

        report = ReportTestRailTestResults(**args)

        db.session.add(report)
        db.session.commit()
        result['id'] = report.id

    return payload
