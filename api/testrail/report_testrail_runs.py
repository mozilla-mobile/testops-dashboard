# report_testrail_runs.py
# Thin wrapper that preserves signature by delegating to TestRailClient.testrail_runs_update
from .service_client import TestRailClient


def testrail_runs_update(*args, **kwargs):
    """Delegate to TestRailClient.testrail_runs_update.
    Accepts the same parameters as the original method.
    """
    _svc = TestRailClient()
    return _svc.testrail_runs_update(*args, **kwargs)
