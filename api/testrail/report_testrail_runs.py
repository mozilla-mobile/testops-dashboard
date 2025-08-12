# report_testrail_runs.py
"""
Functional API for the TestRail "runs" report.

Functions:
- fetch_testrail_runs(...): fetch raw JSON from TestRail (delegates for now)
- prepare_testrail_runs(raw): JSON -> DataFrame payload (placeholder)
- insert_testrail_runs(df, ...): insert into DB (delegates for now)
- testrail_runs_update(...): orchestrator (delegates for now)

Once we have the full class method body, we will inline the real logic into these
functions and deprecate the class method.
"""

from .service_client import TestRailClient


def fetch_testrail_runs(*args, **kwargs):
    """Fetch raw runs JSON (delegates to existing class method for now)."""
    svc = TestRailClient()
    return svc.testrail_runs_update(*args, **kwargs)


def prepare_testrail_runs(raw):
    """Transform raw JSON to a DataFrame payload (placeholder)."""
    # TODO: move the real transform here when we inline
    return raw


def insert_testrail_runs(df, *args, **kwargs):
    """Insert the payload DataFrame into the database (delegates for now)."""
    svc = TestRailClient()
    return svc.testrail_runs_update(*args, **kwargs)


def testrail_runs_update(*args, **kwargs):
    """Orchestrator: fetch -> prepare -> insert (delegates for now)."""
    svc = TestRailClient()
    return svc.testrail_runs_update(*args, **kwargs)
