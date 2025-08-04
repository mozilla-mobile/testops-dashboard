#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys
from datetime import datetime

import pandas as pd
import numpy as np

from lib.testrail_conn import APIClient

from database import (
    Database,
    Projects,
    TestSuites,
    ReportTestCaseCoverage,
    ReportTestRailMilestones,
    ReportTestRailUsers,
    ReportTestRailTestPlans, ReportTestRailTestRuns, ReportTestRailTestResults
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
        return self.client.send_get(
            'get_milestones/{0}'.format(testrail_project_id), data_type='milestones')  # noqa

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
            .format(testrail_project_id, testrail_test_suite_id), data_type='cases')  # noqa

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
            .send_get('get_suites/{0}'.format(testrail_project_id), data_type='suites')  # noqa

    def test_suite(self, testrail_test_suite_id):
        return self.client \
            .send_get('get_suite/{0}'.format(testrail_test_suite_id))

    # API: Runs
    def test_run(self, run_id):
        return self.client.send_get('get_run/{0}'.format(run_id))

    def test_runs(self, testrail_project_id, start_date='', end_date=''):
        date_range = ''
        if start_date:
            after = dt.convert_datetime_to_epoch(start_date)
            date_range += '&created_after={0}'.format(after)
        if end_date:
            before = dt.convert_datetime_to_epoch(end_date)
            date_range += '&created_before={0}'.format(before)
        return self.client.send_get('get_runs/{0}{1}'.format(testrail_project_id, date_range))  # noqa

    def test_results_for_run(self, run_id):
        return self.client.send_get(f'get_results_for_run/{run_id}')

    # API: Plans
    def get_test_plans(self, testrail_project_id, start_date='', end_date=''):
        """Return all plans related to a project id"""
        date_range = ''
        if start_date:
            after = dt.convert_datetime_to_epoch(start_date)
            date_range += '&created_after={0}'.format(after)
        if end_date:
            before = dt.convert_datetime_to_epoch(end_date)
            date_range += '&created_before={0}'.format(before)
        return self.client.send_get(
            f"/get_plans/{testrail_project_id}{date_range}")

    def get_test_plan(self, plan_id, start_date='', end_date=''):
        """Return a plan object by plan id"""
        date_range = ''
        if start_date:
            after = dt.convert_datetime_to_epoch(start_date)
            date_range += '&created_after={0}'.format(after)
        if end_date:
            before = dt.convert_datetime_to_epoch(end_date)
            date_range += '&created_before={0}'.format(before)
        return self.client.send_get(f"/get_plan/{plan_id}{date_range}")

    # API: Users
    def users(self, testrail_project_id):
        return self.client.send_get(
            'get_users/{0}'.format(testrail_project_id))


class TestRailClient(TestRail):

    def __init__(self):
        super().__init__()
        self.db = DatabaseTestRail()

    def data_pump(self, project='all', suite='all'):
        # call database for 'all' values
        # convert inputs to a list so we can easily
        # loop thru them
        project_ids_list = self.testrail_project_ids(project)
        print(project_ids_list)
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

    def testrail_project_ids(self, project):
        """ Return the ids needed to be able to query the TestRail API for
        a specific test suite from a specific project

        [0]. projects.id = id of project in database table: projects
        [1]. testrail_id = id of project in testrail

        Note:
         - Testrail project ids will never change, so we store them
           in DB for convenience and use them to query test suites
           from each respective project
        """
        # Query with filtering
        if isinstance(project, list):
            q = self.db.session.query(Projects).filter(Projects.project_name_abbrev.in_(project))  # noqa
        else:
            q = self.db.session.query(Projects).filter(Projects.project_name_abbrev == project)  # noqa

        # Fetch results
        results = q.all()
        project_ids_list = [[project.id, project.testrail_project_id] for project in results]  # noqa
        print(project_ids_list)
        return project_ids_list

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
        projects_id, testrail_project_id, functional_test_suite_id = self.db.testrail_identity_ids(project)  # noqa

        # Pull JSON blob from Testrail
        runs = self.test_runs(testrail_project_id, start_date)  # noqa

        # Format and store data in a 'totals' array
        totals = self.db.report_test_run_payload(runs)

        # Insert data in the 'totals' array into DB
        self.db.report_test_runs_insert(projects_id, totals)

    def testrail_milestones(self, project):
        self.db.testrail_milestons_delete()

        project_ids_list = self.testrail_project_ids(project)
        milestones_all = pd.DataFrame()

        for project_ids in project_ids_list:
            projects_id = project_ids[0]
            testrail_project_id = project_ids[1]

            payload = self.milestones(testrail_project_id)
            if not payload:
                print(f"No milestones found for project {testrail_project_id}. Skipping...")  # noqa
                milestones_all = pd.DataFrame()  # Empty DataFrame to avoid errors # noqa

            else:
                # Convert JSON to DataFrame
                milestones_all = pd.json_normalize(payload)

            # Ensure DataFrame is not empty before processing
            if milestones_all.empty:
                print(f"Milestones DataFrame is empty for project {testrail_project_id}. Skipping...")  # noqa
                # Continue to next project (if inside a loop)
            else:
                # Define selected columns
                selected_columns = {
                    "id": "testrail_milestone_id",
                    "name": "name",
                    "started_on": "started_on",
                    "is_completed": "is_completed",
                    "description": "description",
                    "completed_on": "completed_on",
                    "url": "url"
                }

                # Select specific columns (only if they exist)
                existing_columns = [col for col in selected_columns.keys() if col in milestones_all.columns]  # noqa
                df_selected = milestones_all[existing_columns].rename(
                    columns={k: v for k, v in selected_columns.items() if k in milestones_all.columns})  # noqa

                # Convert valid timestamps, leave empty ones as NaT
                if 'started_on' in df_selected.columns:
                    df_selected['started_on'] = pd.to_datetime(
                        df_selected['started_on'], unit='s',errors='coerce')  # noqa
                    df_selected['started_on'] = df_selected['started_on'].replace({np.nan: None})  # noqa

                if 'completed_on' in df_selected.columns:
                    df_selected['completed_on'] = pd.to_datetime(
                        df_selected['completed_on'], unit='s', errors='coerce')  # noqa
                    df_selected['completed_on'] = df_selected['completed_on'].replace({np.nan: None})  # noqa

                # Apply transformations only if description column exists
                if 'description' in df_selected.columns:
                    df_selected['testing_status'] = df_selected['description'].apply(pl.extract_testing_status)  # noqa
                    df_selected['testing_recommendation'] = df_selected[
                        'description'].apply(pl.extract_testing_recommendation)  # noqa

                # Apply transformations only if name column exists
                if 'name' in df_selected.columns:
                    df_selected['build_name'] = df_selected['name'].apply(pl.extract_build_name)  # noqa
                    df_selected['build_version'] = df_selected['build_name'].apply(pl.extract_build_version)  # noqa

                # Insert into database only if there is data
                if not df_selected.empty:
                    self.db.report_milestones_insert(projects_id, df_selected)
                else:
                    print(f"No milestones data to insert into database for project {testrail_project_id}.")  # noqa

    def testrail_users(self):
        # Step 1: Get all projects
        projects_response = self.projects()
        all_projects = projects_response.get("projects", [])
        all_users = []  # List of all users across all projects
        seen_project_ids = set()
        project_user_counts = {}

        for project in all_projects:
            project_id = project["id"]
            project_name = project["name"]

            # Skip duplicate project IDs
            if project_id in seen_project_ids:
                continue
            seen_project_ids.add(project_id)

            try:
                user_response = self.users(project_id)
                users = user_response.get("users", [])
                all_users.extend(users)

                unique_emails = {user.get("email") for user in users if user.get("email")}  # noqa
                project_user_counts[project_name] = len(unique_emails)

                print(f"{project_name} (ID: {project_id}): {len(unique_emails)} unique users (by email)")  # noqa

            except Exception as e:
                print(f"Error fetching users {project_id} ({project_name}): {e}")  # noqa

        # Get unique users by email
        unique_by_email = {}
        for user in all_users:
            email = user.get("email")
            if email:
                unique_by_email[email] = user

        print(f"\n Total unique users across all accessible projects (by email): {len(unique_by_email)}")  # noqa

        # Diagnostic
        print("\nSample of unique users:")
        for email, user in list(unique_by_email.items()):
            status = "active" if user.get("is_active") else "inactive"
            print(f"- {user.get('name')} | {email} | {status} | role: {user.get('role')}")  # noqa

        created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        user_data = [
            {
                "name": user.get("name"),
                "email": user.get("email"),
                "status": "active" if user.get("is_active") else "inactive",
                "role": user.get("role"),
                "created_at": created_at
            }
            for user in unique_by_email.values()
        ]

        df = pd.DataFrame(user_data)
        self.db.report_testrail_users_insert(df)

    def testrail_runs_update(self, num_days, project_plans):
        """
            Update the test_runs table with the latest entries up until
            the specified number of days.

            Args:
                num_days (str): number of days to go back from.
                project_plans (dict): the queried and filtered testrail plans.
        """
        start_date = dt.start_date(num_days)
        # querying each test plan individually returns the associated runs
        for plan in project_plans.values():
            plan_info = self.get_test_plan(plan['plan_id'], start_date)
            for entry in plan_info['entries']:
                self.db.report_test_runs_insert(
                    plan['id'], entry['suite_id'], entry['runs'])

    def testrail_plans_and_runs(self, project, num_days):
        """
        Given a testrail project, update the test_plans and test_runs tables
        with the latest entries up until the specified number of days.
        Only take the 'Automated testing' plans.

        Args:
            project (str): the name of the testrail project
            num_days (str): number of days to go back from.
        """
        start_date = dt.start_date(num_days)

        # Get reference IDs from DB
        project_ids_list = self.testrail_project_ids(project)  # noqa

        for project_ids in project_ids_list:
            projects_id = project_ids[0]

            testrail_project_id = project_ids[1]
            # get the test plans from the start_date for the test rails project
            result = self.get_test_plans(testrail_project_id, start_date)  # noqa
            # filter out the Automated testing Plans.
            full_plans = {
                plan['name']: pl.extract_plan_info(plan)
                for plan in result['plans']
                if "Automated testing" in plan['name']
            }

            # delete test plans and runs
            self.db.clean_table(ReportTestRailTestRuns)
            self.db.clean_table(ReportTestRailTestPlans)

            # Insert data in the formated plan info array into DB
            # get table ids for the plans
            self.db.report_test_plans_insert(projects_id, full_plans)
            # add the test runs for the queried test plans
            self.testrail_runs_update(num_days, full_plans)

    def testrail_test_results(self):
        """Gets all the test result duration for the latest test plans
        Precondition: testrail_plans_and_runs have been run prior"""

        # Get the most recent test plan ids for beta and l10n
        tp_ids = [None, None]
        for tp in self.db.session.query(ReportTestRailTestPlans).order_by(
                ReportTestRailTestPlans.testrail_plan_id.desc()).all():
            if "Beta" in tp.name:
                if not tp_ids[0] and "L10N" not in tp.name:
                    tp_ids[0] = tp.testrail_plan_id
                elif not tp_ids[1] and "L10N" in tp.name:
                    tp_ids[1] = tp.testrail_plan_id
                if tp_ids[0] and tp_ids[1]:
                    break
        print(f"beta: {tp_ids[0]}, l10n: {tp_ids[1]}")

        # Insert data for beta and refer back to test run table
        self.db.clean_table(ReportTestRailTestResults)
        types = ("beta", "l10n")
        for i, type in enumerate(types):
            runs = self.get_test_plan(tp_ids[i])["entries"]
            for run in runs:
                for config in run["runs"]:
                    db_run_id = self.db.session.query(
                        ReportTestRailTestRuns).filter_by(
                            testrail_run_id=config["id"]).first().id
                    run_results = self.test_results_for_run(config["id"])["results"]    # noqa
                    self.db.report_testrail_test_result_insert(
                        db_run_id, run_results, type)
            print(f"Added all test results from table {type}")


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

    def report_test_runs_insert(self, db_plan_id, suite_id, runs):
        for run in runs:
            created_on = dt.convert_epoch_to_datetime(run['created_on'])  # noqa
            completed_on = dt.convert_epoch_to_datetime(run['completed_on']) if run['completed_on'] else None  # noqa
            total_count = run['passed_count'] + run['retest_count'] + run['failed_count'] + run['blocked_count']  # noqa

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

    def report_milestones_insert(self, projects_id, payload):
        for index, row in payload.iterrows():
            print(row)

            report = ReportTestRailMilestones(
                testrail_milestone_id=row['testrail_milestone_id'],  # noqa
                projects_id=projects_id,
                name=row['name'],
                started_on=row['started_on'],
                is_completed=row['is_completed'],
                completed_on=row['completed_on'],
                description=row['description'],
                url=row['url'],
                testing_status=row['testing_status'],
                testing_recommendation=row['testing_recommendation'],  # noqa
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
            print('suite_id: {0}, case_id: {1}, subs: {2}'.format(suit, case['id'], subs))  # noqa
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
        return df.groupby(['suit', 'sub', 'status', 'cov'])['tally'].sum().reset_index()  # noqa

    def report_test_coverage_insert(self, projects_id, payload):
        # TODO:  Error on insert
        # insert data from totals into report_test_coverage table
        for index, row in payload.iterrows():
            # TODO: diagnostic - delete
            print('ROW - suit: {0}, asid: {1}, acid: {2}, ssid: {3}, tally: {4}'  # noqa
                  .format(row['suit'], row['status'], row['cov'], row['sub'], row['tally']))  # noqa

            report = ReportTestCaseCoverage(projects_id=projects_id,
                                            testrail_test_suites_id=row['suit'],  # noqa
                                            test_automation_status_id=row['status'],  # noqa
                                            test_automation_coverage_id=row['cov'],  # noqa
                                            test_sub_suites_id=row['sub'],
                                            test_count=row['tally'])
            self.session.add(report)
            self.session.commit()

    def report_testrail_users_insert(self, payload):
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

    def report_test_plans_insert(self, project_id, payload):
        # insert data from payload into test_plans table
        for total in payload.values():
            created_on = dt.convert_epoch_to_datetime(total['created_on'])  # noqa
            completed_on = dt.convert_epoch_to_datetime(total['completed_on']) \
                if total['completed_on'] else None  # noqa

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

    def report_testrail_test_result_insert(self, db_run_id, payload, type):
        # insert data from payload into report_testrail_test_results table
        for result in payload:
            # Skip if not automated testing
            if result["created_by"] != 976:
                continue

            created_on = dt.convert_epoch_to_datetime(result['created_on'])  # noqa
            completed_on = dt.convert_epoch_to_datetime(result['completed_on']) if result.get('completed_on') else None  # noqa

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
