# report_testrail_runs.py
"""Functional API for the TestRail "runs" report (delegates for now)."""

from .service_client import TestRailClient


def fetch_testrail_runs(*args, **kwargs):
    """Fetch raw runs JSON (delegates to existing class method)."""
    svc = TestRailClient()
    return svc.testrail_runs_update(*args, **kwargs)


def prepare_testrail_runs(raw):
    """Transform raw JSON to a DataFrame payload (placeholder)."""
    return raw


def insert_testrail_runs(df, *args, **kwargs):
    """Insert the payload DataFrame into the database (delegates)."""
    svc = TestRailClient()
    return svc.testrail_runs_update(*args, **kwargs)


def testrail_runs_update(*args, **kwargs):
    """Orchestrator: fetch -> prepare -> insert (delegates)."""
    svc = TestRailClient()
    return svc.testrail_runs_update(*args, **kwargs)
