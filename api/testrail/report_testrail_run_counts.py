# report_testrail_run_counts.py
"""Functional API for TestRail run counts (delegates for now)."""

from .service_client import TestRailClient


def fetch_testrail_run_counts(*args, **kwargs):
    """Fetch raw run counts (delegates to class method)."""
    svc = TestRailClient()
    return svc.testrail_run_counts_update(*args, **kwargs)


def prepare_testrail_run_counts(raw):
    """Transform raw JSON to a DataFrame payload (placeholder)."""
    return raw


def insert_testrail_run_counts(df, *args, **kwargs):
    """Insert payload into the database (delegates)."""
    svc = TestRailClient()
    return svc.testrail_run_counts_update(*args, **kwargs)


def testrail_run_counts_update(*args, **kwargs):
    """Orchestrator: fetch -> prepare -> insert (delegates)."""
    svc = TestRailClient()
    return svc.testrail_run_counts_update(*args, **kwargs)
