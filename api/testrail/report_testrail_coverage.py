# report_testrail_coverage.py
"""Functional API for TestRail test case coverage (delegates/fallback)."""

from .service_client import TestRailClient
from .service_db import DatabaseTestRail


def fetch_testrail_coverage(*args, **kwargs):
    """Fetch coverage; prefer client method, fall back to DB method if missing."""
    svc = TestRailClient()
    if hasattr(svc, "testrail_coverage_update"):
        return svc.testrail_coverage_update(*args, **kwargs)
    db = DatabaseTestRail()
    return db.testrail_coverage_update(*args, **kwargs)


def prepare_testrail_coverage(raw):
    """Transform raw JSON to a DataFrame payload (placeholder)."""
    return raw


def insert_testrail_coverage(df, *args, **kwargs):
    """Insert payload; prefer client method, fall back to DB if missing."""
    svc = TestRailClient()
    if hasattr(svc, "testrail_coverage_update"):
        return svc.testrail_coverage_update(*args, **kwargs)
    db = DatabaseTestRail()
    return db.testrail_coverage_update(*args, **kwargs)


def testrail_coverage_update(*args, **kwargs):
    """Orchestrator: fetch -> prepare -> insert (delegates/fallback)."""
    return fetch_testrail_coverage(*args, **kwargs)
