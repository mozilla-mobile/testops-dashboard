import os
import sys

import pandas as pd
import numpy as np

from lib.testrail_conn import APIClient

from database import (
    Database,
    Projects,
    TestSuites,
    ReportTestCaseCoverage,
    ReportTestRailMilestones,
    # ReportTestRunCounts
)

from utils.datetime_utils import DatetimeUtils as dt
from utils.payload_utils import PayloadUtils as pl


class TestRail:

    def __init__(self):
        try:
            TESTRAIL_HOST = os.environ['TESTRAIL_HOST']
            self.client = APIClient(TESTRAIL_HOST)
            self.client.user = os.environ['TESTRAIL_USERNAME']
            self.client.password = os.environ['TESTRAIL_PASSWORD']
        except KeyError:
            print("ERROR: Missing testrail env var")
            sys.exit(1)

    # API: Milestones
    # https://mozilla.testrail.io/index.php?/api/v2/get_milestones/59
    def milestones(self, testrail_project_id):
        return self.client.send_get('get_milestones/{0}'.format(testrail_project_id))

    # API: Projects
    def projects(self):
        return self.client.send_get('get_projects')

    def project(self, testrail_project_id):
        return self.client.send_get(
            'get_project/{0}'.format(testrail_project_id))

    # API: Cases
    def test_cases(self, testrail_project_id, testrail_test_suite_id):
        return self.client.send_get(
            'get_cases/{0}&suite_id={1}'
            .format(testrail_project_id, testrail_test_suite_id))

    def test_case(self, testrail_test_case_id):
        return self.client.send_get(
            'get_case/{0}'.format(testrail_test_case_id))

    # API: Case Fields
    def test_case_fields(self):
        return self.client.send_get(
            'get_case_fields')

    # API: Suites
    def test_suites(self, testrail_project_id):
        return self.client \
                   .send_get('get_suites/{0}'.format(testrail_project_id))

    def test_suite(self, testrail_test_suite_id):
        return self.client \
                   .send_get('get_suite/{0}'.format(testrail_test_suite_id))

    # API: Runs
    def test_runs(self, testrail_project_id, start_date='', end_date=''):
        date_range = ''
        if start_date:
            after = dt.convert_datetime_to_epoch(start_date)
            date_range += '&created_after={0}'.format(after)
        if end_date:
            before = dt.convert_datetime_to_epoch(end_date)
            date_range += '&created_before={0}'.format(before)
        return self.client.send_get('get_runs/{0}{1}'.format(testrail_project_id, date_range)) # noqa

    def test_run(self, run_id):
        return self.client.send_get('get_run/{0}'.format(run_id))

    def test_results_for_run(self, run_id):
        return self.client.send_get('get_results_for_run/{0}'.format(run_id))


class TestRailClient(TestRail):

    def __init__(self):
        super().__init__()
        self.db = DatabaseTestRail()

    def data_pump(self, project='all', suite='all'):
        # call database for 'all' values
        # convert inputs to a list so we can easily
        # loop thru them
        project_ids_list = self.testrail_project_ids(project)

        # TODO:
        # currently only setup for test_case report
        # fix this for test run data

        # Test suite data is dynamic. Wipe out old test suite data
        # in database before updating.
        self.db.test_suites_delete()

        for project_ids in project_ids_list:
            projects_id = project_ids[0]

            testrail_project_id = project_ids[1]
            suites = self.test_suites(testrail_project_id)
            for suite in suites:
                """
                print("testrail_project_id: {0}".format(testrail_project_id))
                print("suite_id: {0}".format(suite['id']))
                print("suite_name: {0}".format(suite['name']))
                """
                self.db.test_suites_update(testrail_project_id,
                                           suite['id'], suite['name'])
                self.testrail_coverage_update(projects_id,
                                              testrail_project_id, suite['id'])

    def testrail_project_ids(self, project='all'):
        """ Return the ids needed to be able to query the TestRail API for
        a specific test suite from a specific project

        [0]. projects.id = id of project in database table: projects
        [1]. testrail_id = id of project in testrail

        Note:
         - Testrail project ids will never change, so we store them
           in DB for convenience and use them to query test suites
           from each respective project
        """

        q = self.db.session.query(Projects)

        if project == 'all':
            p = q.all()
        else:
            p = []
            proj = q.filter_by(project_name_abbrev=project).first()
            p.append(proj)
        ids = []
        tmp = []

        for item in p:
            if type(item.testrail_project_id == int):
                tmp.append(item.id)
                tmp.append(item.testrail_project_id)
                ids.append(tmp)
            tmp = []
        return ids

    def testrail_coverage_update(self, projects_id,
                                 testrail_project_id, test_suite_id):

        # Pull JSON blob from Testrail
        cases = self.test_cases(testrail_project_id, test_suite_id)

        # Format and store data in a data payload array
        payload = self.db.report_test_coverage_payload(cases)
        print(payload)

        # Insert data in 'totals' array into DB
        self.db.report_test_coverage_insert(projects_id, payload)

    def testrail_run_counts_update(self, project, num_days):
        start_date = dt.start_date(num_days)

        # Get reference IDs from DB
        projects_id, testrail_project_id, functional_test_suite_id = self.db.testrail_identity_ids(project) # noqa 

        # Sample Testrail data from one run:
        # [{'run_id': 44113}, {'project_id': 59}, {'suite_id': 3192},
        # {'name': 'Smoke and sanity automated tests - Beta 90.0.0-beta.2'},
        # {'created_on': 1623151551}, {'completed_on': 1623158050},
        # {'failed_count': 0}, {'passed_count': 35}, {'retest_count': 0},
        # {'blocked_count': 0}, {'untested_count': 0}, {'untested_count': 0}]

        # Pull JSON blob from Testrail
        #runs = self.testrail.test_runs(testrail_project_id, start_date) # noqa
        runs = self.test_runs(testrail_project_id, start_date) # noqa

        # Format and store data in a 'totals' array
        totals = self.db.report_test_run_payload(runs)

        # Insert data in 'totals' array into DB
        self.db.report_test_runs_insert(projects_id, totals)

    def testrail_milestones(self, project='all'):
        self.db.testrail_milestons_delete()

        project_ids_list = self.testrail_project_ids(project)
        milestones_all = pd.DataFrame()

        for project_ids in project_ids_list:
            projects_id = project_ids[0]
            testrail_project_id = project_ids[1]

            payload = self.milestones(testrail_project_id)
            milestones_all = pd.json_normalize(payload)

            selected_columns = {
                "id": "testrail_milestone_id",
                "name": "name",
                "started_on": "started_on",
                "is_completed": "is_completed",
                "description": "description",
                "completed_on": "completed_on",
                "url": "url"
            }

            # Select specific columns
            df_selected = milestones_all[selected_columns.keys()]
            # Rename columns
            df_selected = df_selected.rename(columns=selected_columns)

            # Convert valid timestamps, leave empty ones as NaT
            df_selected['started_on'] = df_selected['started_on'].apply(
                lambda x: pd.to_datetime(x, unit='s', errors='coerce') if pd.notna(x) else pd.NaT # noqa
            )
            df_selected['completed_on'] = df_selected['completed_on'].apply(
                lambda x: pd.to_datetime(x, unit='s', errors='coerce') if pd.notna(x) else pd.NaT # noqa
            )

            # Replace NaT with None
            df_selected['completed_on'] = df_selected['completed_on'].replace({np.nan: None}) # noqa
            df_selected['started_on'] = df_selected['started_on'].replace({np.nan: None}) # noqa

            # Add new columns based on information given
            df_selected['testing_status'] = df_selected['description'].apply(pl.extract_testing_status) # noqa
            df_selected['testing_recommendation'] = df_selected['description'].apply(pl.extract_testing_recommendation) # noqa
            df_selected['build_name'] = df_selected['name'].apply(pl.extract_build_name) # noqa
            df_selected['build_version'] = df_selected['build_name'].apply(pl.extract_build_version) # noqa

            self.db.report_milestones_insert(projects_id, df_selected)

class DatabaseTestRail(Database):

    def __init__(self):
        super().__init__()
        self.db = Database()

    def test_suites_delete(self):
        """ Wipe out all test suite data.
        NOTE: we'll renew this data from Testrail every session."""
        self.session.query(TestSuites).delete()
        self.session.commit()

    def test_suites_update(self, testrail_project_id,
                           testrail_test_suites_id, test_suite_name):
        suites = TestSuites(testrail_project_id=testrail_project_id,
                            testrail_test_suites_id=testrail_test_suites_id,
                            test_suite_name=test_suite_name)
        self.session.add(suites)
        self.session.commit()

    def testrail_milestons_delete(self):
        self.session.query(ReportTestRailMilestones).delete()
        self.session.commit()

    def report_milestones_insert(self, projects_id, payload):
        for index, row in payload.iterrows():
            print(row)

            report = ReportTestRailMilestones(testrail_milestone_id=row['testrail_milestone_id'],
                                      projects_id=projects_id,
                                      name=row['name'],
                                      started_on=row['started_on'],
                                      is_completed=row['is_completed'],
                                      completed_on=row['completed_on'],
                                      description=row['description'],
                                      url=row['url'],
                                      testing_status=row['testing_status'],
                                      testing_recommendation=row['testing_recommendation'], # noqa
                                      build_name=row['build_name'],
                                      build_version=row['build_version']
                                      )
            self.session.add(report)
            self.session.commit()

    def report_test_coverage_payload(self, cases):
        """given testrail data (cases), calculate test case counts by type"""

        payload = []

        for case in cases:

            row = []
            suit = case['suite_id']
            subs = case.get("custom_sub_test_suites", [7])

            # TODO: diagnostic - delete
            print('suite_id: {0}, case_id: {1}, subs: {2}'.format(suit, case['id'], subs)) # noqa
            stat = case['custom_automation_status']
            cov = case['custom_automation_coverage']

            # iterate through multi-select sub_suite data
            # we need to create a separate row for each
            # test case that belongs to multiple sub suites
            for sub in subs:
                row = [suit, sub, stat, cov, 1]
                payload.append(row)

        df = pd.DataFrame(data=payload,
                          columns=['suit', 'sub', 'status', 'cov', 'tally'])
        return df.groupby(['suit', 'sub', 'status', 'cov'])['tally'].sum().reset_index() # noqa

    def report_test_coverage_insert(self, projects_id, payload):
        # TODO:  Error on insert
        # insert data from totals into report_test_coverage table
        for index, row in payload.iterrows():
            # TODO: diagnostic - delete
            print('ROW - suit: {0}, asid: {1}, acid: {2}, ssid: {3}, tally: {4}' # noqa
                  .format(row['suit'], row['status'], row['cov'], row['sub'], row['tally'])) # noqa

            report = ReportTestCaseCoverage(projects_id=projects_id,
                                            testrail_test_suites_id=row['suit'], # noqa
                                            test_automation_status_id=row['status'], # noqa
                                            test_automation_coverage_id=row['cov'], # noqa
                                            test_sub_suites_id=row['sub'],
                                            test_count=row['tally'])
            self.session.add(report)
            self.session.commit()

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

    def report_test_runs_insert(self, project_id, payload):
        # insert data from payload into report_test_run_counts table

        totals = payload
        for total in totals:
            t = total

            # only count completed testruns
            if t['testrail_completed_on']:
                created_on = dt.convert_epoch_to_datetime(t['testrail_created_on']) # noqa
                completed_on = dt.convert_epoch_to_datetime(t['testrail_completed_on']) # noqa
                '''
                report = ReportTestRunCounts(
                    projects_id=project_id,
                    testrail_run_id=t['testrail_run_id'],
                    test_case_passed_count=t['passed_count'],
                    test_case_retest_count=t['retest_count'],
                    test_case_failed_count=t['failed_count'],
                    test_case_blocked_count=t['blocked_count'],
                    testrail_created_on=created_on,
                    testrail_completed_on=completed_on)
                '''
                # self.session.add(report)
                self.session.commit()
