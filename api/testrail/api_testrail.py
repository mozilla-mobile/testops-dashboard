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
    ReportTestRailTestPlans,
    ReportTestRailTestRuns,
    ReportTestRailTestResults,
)

from utils.datetime_utils import DatetimeUtils as dt
from utils.payload_utils import PayloadUtils as pl
from api.testrail.client import Testrail


_TR = None
_DB = None


def _tr() -> TestRail():
    global _TR 
    if _TR is None:
        _TR = TestRail()
    return _TR 

def _db() -> DatabaseTestRail():
    global _DB 
    if _DB is None:
        _DB = DatabaseTestRail()
    return _DB 


class TestRailClient(TestRail):

    def __init__(self):
        super().__init__()
        self.db = DatabaseTestRail()

    def data_pump_report_test_case_coverage(self, project='all', suite='all'):
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
            q = (
                self.db.session.query(Projects)
                .filter(Projects.project_name_abbrev.in_(project))
            )
        else:
            q = (
                self.db.session.query(Projects)
                .filter(Projects.project_name_abbrev == project)
            )

        # Fetch results
        results = q.all()
        project_ids_list = [
            [project.id, project.testrail_project_id] for project in results
        ]

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
        (
            projects_id,
            testrail_project_id,
            functional_test_suite_id,
        ) = self.db.testrail_identity_ids(project)

        # Pull JSON blob from Testrail
        runs = self.test_runs(testrail_project_id, start_date)

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
                print(
                    f"No milestones found for project {testrail_project_id}."
                    f" Skipping..."
                )

                # Empty DataFrame to avoid errors
                milestones_all = pd.DataFrame()

            else:
                # Convert JSON to DataFrame
                milestones_all = pd.json_normalize(payload)

            # Ensure DataFrame is not empty before processing
            if milestones_all.empty:
                print(
                    f"Milestones DataFrame is empty for project {testrail_project_id}."
                    f"Skipping..."
                )
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
                existing_columns = [
                    col for col in selected_columns.keys()
                    if col in milestones_all.columns
                ]

                df_selected = milestones_all[existing_columns].rename(
                    columns={
                        k: v
                        for k, v in selected_columns.items()
                        if k in milestones_all.columns
                    }
                )

                # Convert valid timestamps, leave empty ones as NaT
                if 'started_on' in df_selected.columns:
                    df_selected['started_on'] = pd.to_datetime(
                        df_selected['started_on'], unit='s', errors='coerce'
                    )
                    df_selected['started_on'] = df_selected['started_on'].replace(
                        {np.nan: None}
                    )

                if 'completed_on' in df_selected.columns:
                    df_selected['completed_on'] = pd.to_datetime(
                        df_selected['completed_on'], unit='s', errors='coerce'
                    )
                    df_selected['completed_on'] = df_selected['completed_on'].replace(
                        {np.nan: None}
                    )

                # Apply transformations only if description column exists
                if 'description' in df_selected.columns:
                    df_selected['testing_status'] = df_selected['description'].apply(
                        pl.extract_testing_status
                    )

                    desc_series = df_selected['description']
                    df_selected['testing_recommendation'] = desc_series.apply(
                        pl.extract_testing_recommendation
                    )

                # Apply transformations only if name column exists
                if 'name' in df_selected.columns:

                    df_selected['build_name'] = df_selected['name'].apply(
                        pl.extract_build_name
                    )

                    df_selected['build_version'] = df_selected['build_name'].apply(
                        pl.extract_build_version
                    )

                # Insert into database only if there is data
                if not df_selected.empty:
                    self.db.report_milestones_insert(projects_id, df_selected)
                else:
                    print(
                        f"No milestones data to insert into database for project "
                        f"{testrail_project_id}."
                    )

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

                unique_emails = {u.get("email") for u in users if u.get("email")}
                project_user_counts[project_name] = len(unique_emails)

                """
                print(
                    f"{project_name} (ID: {project_id}): "
                    f"{len(unique_emails)} unique users (by email)"
                )
                """

            except Exception as e:
                print(f"Error fetching users {project_id} ({project_name}): {e}")

        # Get unique users by email
        unique_by_email = {}
        for user in all_users:
            email = user.get("email")
            if email:
                unique_by_email[email] = user

        """
        # Diagnostic

        print(
            "\nTotal unique users across all accessible projects (by email): "
            f"{len(unique_by_email)}"
        )

        print("\nSample of unique users:")
        for email, user in list(unique_by_email.items()):
            status = "active" if user.get("is_active") else "inactive"
            print(
                f"- {user.get('name')} | {email} | {status} | role: {user.get('role')}"
            )
        """

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

        # print(f"beta: {tp_ids[0]}, l10n: {tp_ids[1]}")

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
                    run_results = (
                        self.test_results_for_run(config["id"])["results"]
                    )
                    print(f"Adding all results from run {config['id']}")
                    self.db.report_testrail_test_result_insert(
                        db_run_id, run_results, type)
            print(f"Added all test results from table {type}")
