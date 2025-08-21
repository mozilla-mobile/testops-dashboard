#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


from database import (
    Database,
    ReportTestRailTestPlans,
    ReportTestRailTestRuns,
)

from api.testrail.client import TestRail
from api.testrail.helpers import testrail_project_ids
from utils.datetime_utils import DatetimeUtils as dt
from utils.payload_utils import PayloadUtils as pl

import inspect


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


# ===================================================================
# ORCHESTRATOR (BATCH)
# ===================================================================

def testrail_plans_and_runs(project, num_days):
    """
    Given a testrail project, update the test_plans and test_runs tables
    with the latest entries up until the specified number of days.
    Only take the 'Automated testing' plans.

    Args:
        project (str): the name of the testrail project
        num_days (str): number of days to go back from.
    """

    # DIAGNOSTIC
    print("--------------------------------------")
    print("DIAGNOSTIC: testrail_plans_and_runs")
    print(inspect.currentframe().f_code.co_name)
    print("--------------------------------------")
    print(f"project = {project}")
    print(f"num_days: {num_days}")

    db = _db()
    tr = _tr()

    start_date = dt.start_date(num_days)

    # Get reference IDs from DB
    project_ids_list = testrail_project_ids(project)  # noqa

    print("DIAGNOSTIC: project_ids:")
    print(project_ids_list)

    for project_ids in project_ids_list:
        projects_id = project_ids[0]

        testrail_project_id = project_ids[1]
        # get the test plans from the start_date for the test rails project
        result = tr.get_test_plans(testrail_project_id, start_date)  # noqa

        # filter out the Automated testing Plans.
        full_plans = {
            plan['name']: pl.extract_plan_info(plan)
            for plan in result['plans']
            if "Automated testing" in plan['name']
        }

        # delete test plans and runs
        print("DIAGNOSTIC: cleaning tables....")
        db.clean_table(ReportTestRailTestRuns)
        db.clean_table(ReportTestRailTestPlans)

        # Insert data in the formated plan info array into DB
        # get table ids for the plans

        report_test_plans_insert(projects_id, full_plans)

        # add the test runs for the queried test plans
        testrail_runs_update(num_days, full_plans)


# ===================================================================
# ORCHESTRATOR (BATCH)
# ===================================================================

def testrail_runs_update(num_days, project_plans):
    """
        Update the test_runs table with the latest entries up until
        the specified number of days.

        Args:
            num_days (str): number of days to go back from.
            project_plans (dict): the queried and filtered testrail plans.
    """

    # DIAGNOSTIC
    print("--------------------------------------")
    print("DIAGNOSTIC: testrail_runs_update")
    print(inspect.currentframe().f_code.co_name)
    print("--------------------------------------")

    db = _db()
    tr = _tr()

    start_date = dt.start_date(num_days)

    # querying each test plan individually returns the associated runs
    for plan in project_plans.values():
        plan_info = tr.get_test_plan(plan['plan_id'], start_date)
        for entry in plan_info['entries']:
            db.report_test_runs_insert(
                plan['id'], entry['suite_id'], entry['runs'])


# ===================================================================
# DB INSERT
# ===================================================================

def report_test_plans_insert(project_id, payload):
    # insert data from payload into test_plans table

    # DIAGNOSTIC
    print("--------------------------------------")
    print("DIAGNOSTIC: report_test_plans_insert")
    print(inspect.currentframe().f_code.co_name)
    print("--------------------------------------")

    db = _db()

    for total in payload.values():
        created_on = dt.convert_epoch_to_datetime(total['created_on'])
        completed_on = (
            dt.convert_epoch_to_datetime(total['completed_on'])
            if total['completed_on'] else None
        )

        report = ReportTestRailTestPlans(
            projects_id=project_id,
            testrail_plan_id=total['plan_id'],
            name=total['name'],
            test_case_passed_count=total['passed_count'],
            test_case_retest_count=total['retest_count'],
            test_case_failed_count=total['failed_count'],
            test_case_blocked_count=total['blocked_count'],
            test_case_total_count=total['total_count'],
            testrail_created_on=created_on,
            testrail_completed_on=completed_on)

        db.session.add(report)
        db.session.commit()
        total['id'] = report.id
    return payload
