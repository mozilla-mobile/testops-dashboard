"""Functional API for the TestRail 'runs' report.

For now, these functions delegate to the existing class method so behavior
remains unchanged. In a later PR, we will inline the fetch/prepare/insert
logic here and remove the class method.
"""

from .service_client import TestRailClient


def fetch_testrail_runs(*args, **kwargs):
    """Fetch raw runs JSON (delegates to class for now)."""
    svc = TestRailClient()
    return svc.testrail_runs_update(*args, **kwargs)


def prepare_testrail_runs(raw):
    """Transform raw JSON to a DataFrame payload (placeholder for now)."""
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
