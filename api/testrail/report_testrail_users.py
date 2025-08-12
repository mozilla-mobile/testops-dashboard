# report_testrail_users.py
"""Delegating functional facade for the TestRail *users* report.

This is a no-behavior-change shim: it forwards to the existing class method so
handlers do not need to change yet. We'll inline real logic in PR4.
"""
from .service_client import TestRailClient


def fetch_testrail_users(*args, **kwargs):
    """Fetch raw users JSON (delegates to the existing class method)."""
    svc = TestRailClient()
    return svc.testrail_users_update(*args, **kwargs)


def prepare_testrail_users(raw):
    """Transform raw JSON to a payload (placeholder)."""
    return raw


def insert_testrail_users(df, *args, **kwargs):
    """Insert payload into DB (delegates for now)."""
    svc = TestRailClient()
    return svc.testrail_users_update(*args, **kwargs)


def testrail_users_update(*args, **kwargs):
    """Orchestrator (delegates for now)."""
    svc = TestRailClient()
    return svc.testrail_users_update(*args, **kwargs)
