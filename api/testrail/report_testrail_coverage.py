# report_testrail_coverage.py
"""
Functional facade for the TestRail test-case coverage report (migration-safe).

Strategy (to avoid recursion):
- We route coverage through DatabaseTestRail directly for now.
- TestRailClient may have a shim (added in __init__.py) that also forwards to DB.

These functions will be fully inlined with real fetch/prepare/insert logic in PR3B.
"""
from .service_db import DatabaseTestRail


def fetch_testrail_coverage(*args, **kwargs):
    """Fetch coverage data via DB service (delegation for now)."""
    db = DatabaseTestRail()
    return db.testrail_coverage_update(*args, **kwargs)


def prepare_testrail_coverage(raw):
    """Placeholder for JSON->DataFrame transform (no-op for now)."""
    return raw


def insert_testrail_coverage(df, *args, **kwargs):
    """Insert payload using DB service (delegation for now)."""
    db = DatabaseTestRail()
    return db.testrail_coverage_update(*args, **kwargs)


def testrail_coverage_update(*args, **kwargs):
    """Orchestrator: currently just calls fetch (delegation)."""
    return fetch_testrail_coverage(*args, **kwargs)
