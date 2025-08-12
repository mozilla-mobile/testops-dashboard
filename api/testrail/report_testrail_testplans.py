# report_testrail_testplans.py
"""Delegating functional facade for the TestRail *test plans* report.

No behavior change; forwards to the existing class method.
"""
from .service_client import TestRailClient


def fetch_testrail_testplans(*args, **kwargs):
    svc = TestRailClient()
    return svc.testrail_testplans_update(*args, **kwargs)


def prepare_testrail_testplans(raw):
    return raw


def insert_testrail_testplans(df, *args, **kwargs):
    svc = TestRailClient()
    return svc.testrail_testplans_update(*args, **kwargs)


def testrail_testplans_update(*args, **kwargs):
    svc = TestRailClient()
    return svc.testrail_testplans_update(*args, **kwargs)
