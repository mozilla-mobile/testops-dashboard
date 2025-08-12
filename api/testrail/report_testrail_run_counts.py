"""Functional API for the TestRail 'run counts' report.

These functions currently delegate to the existing class method to keep
behavior identical while we migrate. We will inline the logic later.
"""

from .service_client import TestRailClient


def fetch_testrail_run_counts(*args, **kwargs):
    """Fetch raw run counts (delegates to class for now)."""
    svc = TestRailClient()
    return svc.testrail_run_counts_update(*args, **kwargs)


def prepare_testrail_run_counts(raw):
    """Transform the raw data to the DataFrame payload (placeholder)."""
    return raw


def insert_testrail_run_counts(df, *args, **kwargs):
    """Insert the payload into the database (delegates for now)."""
    svc = TestRailClient()
    return svc.testrail_run_counts_update(*args, **kwargs)


def testrail_run_counts_update(*args, **kwargs):
    """Orchestrator: fetch -> prepare -> insert (delegates for now)."""
    svc = TestRailClient()
    return svc.testrail_run_counts_update(*args, **kwargs)
