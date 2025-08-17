#! /usr/bin/env python3

# T
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys
from datetime import datetime

import pandas as pd
import numpy as np

from database import (
    Database,
    Projects,
    TestSuites,
    ReportTestCaseCoverage,
    ReportTestRailMilestones,
    ReportTestRailUsers,
    ReportTestRailTestPlans,
    ReportTestRailTestRuns,
    ReportTestRailTestResults,
)

from utils.datetime_utils import DatetimeUtils as dt
from utils.payload_utils import PayloadUtils as pl

import inspect


class DatabaseTestRail(Database):

    def __init__(self):
        super().__init__()
        self.db = Database()

        # DIAGNOSTIC
        print("Initiating: DatabaseTestRail")
        print(inspect.currentframe().f_code.co_name)

    def test_suites_delete(self):
        """ Wipe out all test suite data.
        NOTE: we'll renew this data from Testrail every session."""

        # DIAGNOSTIC
        print("Running: DatabaseTestRail")
        print(inspect.currentframe().f_code.co_name)

        self.session.query(TestSuites).delete()
        self.session.commit()

    def test_suites_update(self, testrail_project_id,
                           testrail_test_suites_id, test_suite_name):

        # DIAGNOSTIC
        print("Running: DatabaseTestRail")
        print(inspect.currentframe().f_code.co_name)

        suites = TestSuites(testrail_project_id=testrail_project_id,
                            testrail_test_suites_id=testrail_test_suites_id,
                            test_suite_name=test_suite_name)
        self.session.add(suites)
        self.session.commit()

    """
    def testrail_milestones_delete(self):
        # DIAGNOSTIC
        print("Running: DatabaseTestRail")
        print(inspect.currentframe().f_code.co_name)


        self.session.query(ReportTestRailMilestones).delete()
        self.session.commit()
    """

    """
    def report_test_runs_insert(self, db_plan_id, suite_id, runs):

        # DIAGNOSTIC
        print("Running: DatabaseTestRail")
        print(inspect.currentframe().f_code.co_name)

        for run in runs:
            created_on = dt.convert_epoch_to_datetime(run['created_on'])
            completed_on = (
                dt.convert_epoch_to_datetime(run['completed_on'])
                if run['completed_on'] else None
            )
            total_count = (
                run['passed_count']
                + run['retest_count']
                + run['failed_count']
                + run['blocked_count']
            )

            report_run = ReportTestRailTestRuns(
                testrail_run_id=run['id'],
                plan_id=db_plan_id,
                suite_id=suite_id,
                name=run['name'],
                config=run['config'],
                test_case_passed_count=run['passed_count'],
                test_case_retest_count=run['retest_count'],
                test_case_failed_count=run['failed_count'],
                test_case_blocked_count=run['blocked_count'],
                test_case_total_count=total_count,
                testrail_created_on=created_on,
                testrail_completed_on=completed_on)
            self.session.add(report_run)
            self.session.commit()
    """

    """
    def report_milestones_insert(self, projects_id, payload):

        # DIAGNOSTIC
        print("Running: DatabaseTestRail")
        print(inspect.currentframe().f_code.co_name)

        for index, row in payload.iterrows():
            # print(row)

            report = ReportTestRailMilestones(
                testrail_milestone_id=row['testrail_milestone_id'],
                projects_id=projects_id,
                name=row['name'],
                started_on=row['started_on'],
                is_completed=row['is_completed'],
                completed_on=row['completed_on'],
                description=row['description'],
                url=row['url'],
                testing_status=row['testing_status'],
                testing_recommendation=row['testing_recommendation'],
                build_name=row['build_name'],
                build_version=row['build_version']
            )
            self.session.add(report)
            self.session.commit()
    """

    def report_test_coverage_payload(self, cases):
        """given testrail data (cases), calculate test case counts by type"""

        # DIAGNOSTIC
        print("Running: DatabaseTestRail")
        print(inspect.currentframe().f_code.co_name)

        payload = []

        for case in cases:

            row = []
            suit = case['suite_id']
            subs = case.get("custom_sub_test_suites", [7])

            # Diagnostic
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

    def report_test_coverage_insert(self, projects_id, payload):

        # DIAGNOSTIC
        print("Running: DatabaseTestRail")
        print(inspect.currentframe().f_code.co_name)

        # TODO:  Error on insert
        # insert data from totals into report_test_coverage table

        for index, row in payload.iterrows():
            """
            # Diagnostic

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
            self.session.add(report)
            self.session.commit()

    """
    def report_testrail_users_insert(self, payload):

        # DIAGNOSTIC
        print("Running: DatabaseTestRail")
        print(inspect.currentframe().f_code.co_name)

        for index, row in payload.iterrows():
            report = ReportTestRailUsers(
                name=row['name'],  # noqa
                email=row['email'],
                status=row['status'],
                role=row['role'],
                created_at=row['created_at']
            )
            self.session.add(report)
            self.session.commit()
    """

    def report_test_run_payload(self, runs):
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
        print("Running: DatabaseTestRail")
        print(inspect.currentframe().f_code.co_name)

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

    def report_test_plans_insert(self, project_id, payload):
        # insert data from payload into test_plans table

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

            self.session.add(report)
            self.session.commit()
            total['id'] = report.id
        return payload

    '''
    def report_testrail_test_result_insert(self, db_run_id, payload, type):

        # insert data from payload into report_testrail_test_results table
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

            self.session.add(report)
            self.session.commit()
            result['id'] = report.id

        return payload
    '''
