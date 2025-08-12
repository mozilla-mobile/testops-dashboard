"""
Package init: temporary shim to keep legacy handler paths working during refactor.

We attach a coverage method to TestRailClient that forwards to the *functional*
orchestrator function. The functional module itself must *not* call back into
TestRailClient to avoid recursion.

TODO(PR4): remove this file once handlers call report modules directly.
"""
from .service_client import TestRailClient  # local import; class exists here


def _testrail_coverage_update_shim(self, *args, **kwargs):
    # Import inside to avoid import cycles.
    from .report_testrail_coverage import testrail_coverage_update as _run
    return _run(*args, **kwargs)


# Only attach if it's missing (i.e., the method was commented out during migration)
if not hasattr(TestRailClient, "testrail_coverage_update"):
    setattr(TestRailClient, "testrail_coverage_update", _testrail_coverage_update_shim)
