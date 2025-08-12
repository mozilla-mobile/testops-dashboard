# report_testrail_run_counts.py
"""
Functional conversion of the TestRail run counts report.
"""

from .service_client import TestRailClient
from .service_db import DatabaseTestRail
from utils.datetime_utils import DatetimeUtils as dt


def fetch_testrail_run_counts(project, num_days):
    """Fetch runs JSON and DB identity IDs."""
    db = DatabaseTestRail()
    projects_id, testrail_project_id, functional_test_suite_id = db.testrail_identity_ids(project)
    start_date = dt.start_date(num_days)
    tr = TestRailClient()
    runs = tr.test_runs(testrail_project_id, start_date)
    return projects_id, runs


def prepare_testrail_run_counts(runs):
    """Build totals payload using existing DB helper for consistency."""
    db = DatabaseTestRail()
    totals = db.report_test_run_payload(runs)
    return totals


def insert_testrail_run_counts(projects_id, totals):
    """Insert totals into DB using existing helper."""
    db = DatabaseTestRail()
    db.report_test_runs_insert(projects_id, totals)


def testrail_run_counts_update(project, num_days):
    """Orchestrate fetch -> prepare -> insert for run counts."""
    projects_id, runs = fetch_testrail_run_counts(project, num_days)
    totals = prepare_testrail_run_counts(runs)
    insert_testrail_run_counts(projects_id, totals)
    return True
