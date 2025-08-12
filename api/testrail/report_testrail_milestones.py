# report_testrail_milestones.py
"""Delegating functional facade for the TestRail *milestones* report.

No behavior change; forwards to the existing class method.
"""
from .service_client import TestRailClient


def fetch_testrail_milestones(*args, **kwargs):
    svc = TestRailClient()
    return svc.testrail_milestones_update(*args, **kwargs)


def prepare_testrail_milestones(raw):
    return raw


def insert_testrail_milestones(df, *args, **kwargs):
    svc = TestRailClient()
    return svc.testrail_milestones_update(*args, **kwargs)


def testrail_milestones_update(*args, **kwargs):
    svc = TestRailClient()
    return svc.testrail_milestones_update(*args, **kwargs)
