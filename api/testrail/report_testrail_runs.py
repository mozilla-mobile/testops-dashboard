# report_testrail_runs.py
"""
Functional facade for the TestRail "runs" report.

This provides the 3-step functional API you asked for:
  1) fetch_testrail_runs(...)      -> raw JSON
  2) prepare_testrail_runs(raw)    -> pandas.DataFrame payload
  3) insert_testrail_runs(df, ...) -> inserts into DB

For this first iteration, we delegate to the existing class implementation
so behavior is identical. In the next pass, we can inline the class method
body here and remove the class entirely.
"""

from .service_client import TestRailClient  # existing implementation lives here


def fetch_testrail_runs(*args, **kwargs):
    """Fetch raw TestRail runs JSON (delegates to class for now)."""
    svc = TestRailClient()
    return svc.testrail_runs_update(*args, **kwargs)


def prepare_testrail_runs(raw):
    """Transform raw JSON -> pandas.DataFrame payload (placeholder)."""
    return raw  # TODO: replace when inlining the transform


def insert_testrail_runs(df, *args, **kwargs):
    """Insert DataFrame into the database (delegates for now)."""
    svc = TestRailClient()
    return svc.testrail_runs_update(*args, **kwargs)


def testrail_runs_update(*args, **kwargs):
    """Orchestrator (fetch -> prepare -> insert), delegates for now."""
    svc = TestRailClient()
    return svc.testrail_runs_update(*args, **kwargs)
