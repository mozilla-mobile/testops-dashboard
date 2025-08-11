# report_testrail_runs.py
"""
Functional API for the TestRail "runs" report.

Agreed naming:
  1) fetch_testrail_runs(...)      -> raw JSON
  2) prepare_testrail_runs(raw)    -> pandas.DataFrame payload
  3) insert_testrail_runs(df, ...) -> inserts into DB
  4) testrail_runs_update(...)     -> orchestrator

NOTE: This version *delegates* to the existing class method so behavior is unchanged.
Once you confirm structure, we can inline the real logic here and remove the class method.
"""

from .service_client import TestRailClient


def fetch_testrail_runs(*args, **kwargs):
    """Fetch raw TestRail runs JSON (delegates for now)."""
    svc = TestRailClient()
    # TODO: replace with a direct TestRail client call (self.tr.get_runs or similar)
    return svc.testrail_runs_update(*args, **kwargs)


def prepare_testrail_runs(raw):
    """Transform raw JSON -> pandas.DataFrame payload (placeholder for now)."""
    # TODO: pull the transform logic out of the class method into this function
    return raw


def insert_testrail_runs(df, *args, **kwargs):
    """Insert DataFrame into the database (delegates for now)."""
    svc = TestRailClient()
    # TODO: call into the DB service directly once extracted
    return svc.testrail_runs_update(*args, **kwargs)


def testrail_runs_update(*args, **kwargs):
    """Orchestrator (fetch -> prepare -> insert), delegates for now."""
    svc = TestRailClient()
    return svc.testrail_runs_update(*args, **kwargs)
