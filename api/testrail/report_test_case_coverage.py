
#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import pandas as pd

from database import (
    Database,
    TestSuites,
    ReportTestCaseCoverage,
)

from api.testrail.client import TestRail
from api.testrail.helpers import testrail_project_ids

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


def test_suites_delete():
    """ Wipe out all test suite data.
    NOTE: we'll renew this data from Testrail every session."""

    db = _db()

    # DIAGNOSTIC
    print("--------------------------------------")
    print("DIAGNOSTIC: report_test_case_coverage ")
    print("--------------------------------------")
    print(inspect.currentframe().f_code.co_name)

    db.session.query(TestSuites).delete()
    db.session.commit()


def testrail_test_case_coverage(project):

    # DIAGNOSTIC
    print("--------------------------------------")
    print("DIAGNOSTIC: ")
    print(inspect.currentframe().f_code.co_name)
    print("--------------------------------------")
    print(f"project {project}")   

    # call database for 'all' values
    # convert inputs to a list so we can easily
    # loop thru them

    project_ids_list = testrail_project_ids(project)

    # TODO:
    # currently only setup for test_case report
    # fix this for test run data

    # Test suite data is dynamic. Wipe out old test suite data
    # in database before updating.
    tr = _tr()

    test_suites_delete()

    for project_ids in project_ids_list:
        projects_id = project_ids[0]

        testrail_project_id = project_ids[1]
        suites = tr.test_suites(testrail_project_id)

        for suite in suites:
            """
            print("DIAGNOSTIC")
            print("testrail_project_id: {0}".format(testrail_project_id))
            print("suite_id: {0}".format(suite['id']))
            print("suite_name: {0}".format(suite['name']))
            """
            test_suites_update(testrail_project_id,
                               suite['id'], suite['name'])
            testrail_coverage_update(projects_id,
                                     testrail_project_id, suite['id'])


def test_suites_update(testrail_project_id,
                       testrail_test_suites_id, test_suite_name):

    db = _db()

    # DIAGNOSTIC
    print("DIAGNOSTIC:report_test_case_coverage ")
    print(inspect.currentframe().f_code.co_name)

    suites = TestSuites(testrail_project_id=testrail_project_id,
                        testrail_test_suites_id=testrail_test_suites_id,
                        test_suite_name=test_suite_name)
    db.session.add(suites)
    db.session.commit()


def testrail_coverage_update(projects_id, testrail_project_id, test_suite_id):

    tr = _tr()

    # Pull JSON blob from Testrail
    cases = tr.test_cases(testrail_project_id, test_suite_id)

    # Format and store data in a data payload array
    payload = report_test_coverage_payload(cases)

    # Insert data in 'totals' array into DB
    report_test_coverage_insert(projects_id, payload)


def report_test_coverage_payload(cases):
    """given testrail data (cases), calculate test case counts by type"""

    # DIAGNOSTIC
    print("DIAGNOSTIC:report_test_case_coverage ")
    print(inspect.currentframe().f_code.co_name)

    payload = []

    for case in cases:

        row = []
        suit = case['suite_id']
        subs = case.get("custom_sub_test_suites", [7])

        # DIAGNOSTIC 
        # print(f'suite_id: {suit}, case_id: {case["id"]}, subs: {subs}')

        stat = case['custom_automation_status']
        cov = case['custom_automation_coverage']

        # iterate through multi-select sub_suite data
        # we need to create a separate row for each
        # test case that belongs to multiple sub suites
        for sub in subs:
            row = [suit, sub, stat, cov, 1]
            payload.append(row)

    df = pd.DataFrame(
        data=payload,
        columns=['suit', 'sub', 'status', 'cov', 'tally']
    )
    return (
        df.groupby(['suit', 'sub', 'status', 'cov'])['tally']
          .sum()
          .reset_index()
    )


def report_test_coverage_insert(projects_id, payload):

    # DIAGNOSTIC
    print("DIAGNOSTIC: report_test_case_coverage")
    print(inspect.currentframe().f_code.co_name)

    # TODO:  Error on insert
    # insert data from totals into report_test_coverage table

    db = _db()

    for index, row in payload.iterrows():
        """
        # DIAGNOSTIC 

        print(
            'ROW - suit: {0}, asid: {1}, acid: {2}, ssid: {3}, tally: {4}'.format(
                row['suit'],
                row['status'],
                row['cov'],
                row['sub'],
                row['tally']

            )
        )
        """

        report = ReportTestCaseCoverage(
            projects_id=projects_id,
            testrail_test_suites_id=row['suit'],
            test_automation_status_id=row['status'],
            test_automation_coverage_id=row['cov'],
            test_sub_suites_id=row['sub'],
            test_count=row['tally']
        )
        db.session.add(report)
        db.session.commit()
