# report_testrail_runs.py
"""
Functional conversion of the TestRail runs report.

Steps:
- fetch_testrail_runs(num_days, project_plans) -> dict[plan_id, list[entry]]
- prepare_testrail_runs(raw) -> passthrough (no transform needed)
- insert_testrail_runs(data) -> writes entries to DB
- testrail_runs_update(num_days, project_plans) -> orchestrator
"""

from .service_client import TestRailClient
from .service_db import DatabaseTestRail
from utils.datetime_utils import DatetimeUtils as dt


def fetch_testrail_runs(num_days, project_plans):
    """Fetch plan entries for each plan within the date window."""
    start_date = dt.start_date(num_days)
    tr = TestRailClient()
    plan_entries = {}
    for plan in project_plans.values():
        plan_info = tr.get_test_plan(plan['plan_id'], start_date)
        plan_entries[plan['id']] = plan_info.get('entries', [])
    return plan_entries


def prepare_testrail_runs(raw_plan_entries):
    """No additional shaping required for DB insert; passthrough."""
    return raw_plan_entries


def insert_testrail_runs(plan_entries):
    """Insert each run entry into the database."""
    db = DatabaseTestRail()
    for plan_id, entries in plan_entries.items():
        for entry in entries:
            db.report_test_runs_insert(plan_id, entry.get('suite_id'), entry.get('runs'))


def testrail_runs_update(num_days, project_plans):
    """Orchestrate fetch -> prepare -> insert for runs."""
    data = fetch_testrail_runs(num_days, project_plans)
    payload = prepare_testrail_runs(data)
    insert_testrail_runs(payload)
    return True
