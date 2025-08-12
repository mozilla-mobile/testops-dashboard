# report_testrail_coverage.py
"""
Coverage report functions with a safe fallback that does NOT depend on
TestRailClient having `testrail_coverage_update`. For now we delegate
directly to DatabaseTestRail so AttributeError can't occur.
"""

from .service_db import DatabaseTestRail


def fetch_testrail_coverage(*args, **kwargs):
    """
    TEMP: delegate to the DB service's coverage update, which already
    performs the end-to-end operation in your current codebase.
    """
    db = DatabaseTestRail()
    return db.testrail_coverage_update(*args, **kwargs)


def prepare_testrail_coverage(raw):
    """
    Placeholder for JSON -> DataFrame shaping once we inline logic.
    Currently just passes through.
    """
    return raw


def insert_testrail_coverage(df, *args, **kwargs):
    """
    TEMP: delegate to the DB service's coverage update to perform the
    insert. When we inline, this will take a DataFrame and write rows.
    """
    db = DatabaseTestRail()
    return db.testrail_coverage_update(*args, **kwargs)


def testrail_coverage_update(*args, **kwargs):
    """
    Orchestrator. For now, call the DB service directly so we don't
    depend on TestRailClient having this method defined.
    """
    db = DatabaseTestRail()
    return db.testrail_coverage_update(*args, **kwargs)
