# report_testrail_run_counts.py
# Thin wrapper that preserves signature by delegating to TestRailClient.testrail_run_counts_update
from .service_client import TestRailClient


def testrail_run_counts_update(*args, **kwargs):
    """Delegate to TestRailClient.testrail_run_counts_update.
    Accepts the same parameters as the original method.
    """
    _svc = TestRailClient()
    return _svc.testrail_run_counts_update(*args, **kwargs)
