"""Functional API for the TestRail 'coverage' report.

Delegates to existing implementations for now. To avoid AttributeError when
the class method is commented out during migration, we fall back to the DB
service if the client method is missing.
"""

from .service_client import TestRailClient
from .service_db import DatabaseTestRail


def _call_coverage_on_available(*args, **kwargs):
    """Call coverage update on whichever service exposes it."""
    svc = TestRailClient()
    if hasattr(svc, "testrail_coverage_update"):
        return svc.testrail_coverage_update(*args, **kwargs)
    db = DatabaseTestRail()
    return db.testrail_coverage_update(*args, **kwargs)


def fetch_testrail_coverage(*args, **kwargs):
    """Fetch raw coverage data (delegates; uses fallback)."""
    return _call_coverage_on_available(*args, **kwargs)


def prepare_testrail_coverage(raw):
    """Transform raw coverage JSON to a DataFrame payload (placeholder)."""
    return raw


def insert_testrail_coverage(df, *args, **kwargs):
    """Insert the coverage payload into the database (delegates; fallback)."""
    return _call_coverage_on_available(*args, **kwargs)


def testrail_coverage_update(*args, **kwargs):
    """Orchestrator: fetch -> prepare -> insert (delegates; fallback)."""
    return _call_coverage_on_available(*args, **kwargs)
