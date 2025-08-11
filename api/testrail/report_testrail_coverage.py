# report_testrail_coverage.py
# Thin wrapper that preserves signature by
# delegating to TestRailClient.testrail_coverage_update
from .service_client import TestRailClient


def testrail_coverage_update(*args, **kwargs):
    """Delegate to TestRailClient.testrail_coverage_update.
    Accepts the same parameters as the original method.
    """
    _svc = TestRailClient()
    return _svc.testrail_coverage_update(*args, **kwargs)
