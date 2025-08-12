# report_testrail_coverage.py
"""
Functional conversion of the TestRail coverage report.
"""

from .service_client import TestRailClient
from .service_db import DatabaseTestRail


def fetch_testrail_coverage(testrail_project_id, test_suite_id):
    """Fetch test cases JSON for coverage calculation."""
    tr = TestRailClient()
    return tr.test_cases(testrail_project_id, test_suite_id)


def prepare_testrail_coverage(cases):
    """Build coverage payload using existing DB helper for consistency."""
    db = DatabaseTestRail()
    payload = db.report_test_coverage_payload(cases)
    return payload


def insert_testrail_coverage(projects_id, payload):
    """Insert coverage payload into DB."""
    db = DatabaseTestRail()
    db.report_test_coverage_insert(projects_id, payload)


def testrail_coverage_update(projects_id, testrail_project_id, test_suite_id):
    """Orchestrate fetch -> prepare -> insert for coverage."""
    cases = fetch_testrail_coverage(testrail_project_id, test_suite_id)
    payload = prepare_testrail_coverage(cases)
    insert_testrail_coverage(projects_id, payload)
    return True
