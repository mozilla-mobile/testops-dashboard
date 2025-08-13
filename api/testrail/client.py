import os
import sys
from lib.testrail_conn import APIClient
from utils.datetime_utils import DatetimeUtils as dt


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
    def milestones(self, testrail_project_id):
        return self.client.send_get(
            f"get_milestones/{testrail_project_id}",
            data_type='milestones'
        )

    def milestone(self, testrail_milestone_id):
        return self.client.send_get(f"get_milestone/{testrail_milestone_id}")

    # API: Projects
    def projects(self):
        return self.client.send_get("get_projects")

    def project(self, testrail_project_id):
        return self.client.send_get(f"get_project/{testrail_project_id}")

    # API: Cases
    def test_cases(self, testrail_project_id, testrail_test_suite_id):
        return self.client.send_get(
            f"get_cases/{testrail_project_id}&suite_id={testrail_test_suite_id}",
            data_type="cases"
        )

    def test_case(self, testrail_test_case_id):
        return self.client.send_get(f"get_case/{testrail_test_case_id}")

    # API: Case Fields
    def test_case_fields(self):
        return self.client.send_get("get_case_fields")

    # API: Suites
    def test_suites(self, testrail_project_id):
        return self.client.send_get(
            f"get_suites/{testrail_project_id}",
            data_type="suites"
        )

    def test_suite(self, testrail_test_suite_id):
        return self.client.send_get(f"get_suite/{testrail_test_suite_id}")

    # API: Runs
    def test_run(self, run_id):
        return self.client.send_get(f"get_run/{run_id}")

    def test_runs(self, testrail_project_id, start_date='', end_date=''):
        date_range = ''
        if start_date:
            after = dt.convert_datetime_to_epoch(start_date)
            date_range += f"&created_after={after}"
        if end_date:
            before = dt.convert_datetime_to_epoch(end_date)
            date_range += f"&created_before={before}"
        return self.client.send_get(f"get_runs/{testrail_project_id}{date_range}")

    def test_results_for_run(self, run_id):
        return self.client.send_get(f'get_results_for_run/{run_id}')

    # API: Plans
    def get_test_plans(self, testrail_project_id, start_date='', end_date=''):
        """Return all plans related to a project id"""
        date_range = ''
        if start_date:
            after = dt.convert_datetime_to_epoch(start_date)
            date_range += f'&created_after={after}'
        if end_date:
            before = dt.convert_datetime_to_epoch(end_date)
            date_range += f'&created_before={before}'
        return self.client.send_get(
            f"/get_plans/{testrail_project_id}{date_range}"
        )

    def get_test_plan(self, plan_id, start_date='', end_date=''):
        """Return a plan object by plan id"""
        date_range = ''
        if start_date:
            after = dt.convert_datetime_to_epoch(start_date)
            date_range += f'&created_after={after}'
        if end_date:
            before = dt.convert_datetime_to_epoch(end_date)
            date_range += f'&created_before={before}'
        return self.client.send_get(f"/get_plan/{plan_id}{date_range}")

    # API: Users
    def users(self, testrail_project_id):
        return self.client.send_get(
            f'get_users/{testrail_project_id}'
        )
