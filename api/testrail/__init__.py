"""
Package init shim for TestRail coverage during migration.

If TestRailClient.testrail_coverage_update is missing (commented out),
attach a shim that forwards DIRECTLY to DatabaseTestRail.testrail_coverage_update.
This avoids recursion through the functional layer.

Remove this shim in PR4 once handlers are updated.
"""
from .service_client import TestRailClient
from .service_db import DatabaseTestRail


def _testrail_coverage_update_shim(self, *args, **kwargs):
    db = DatabaseTestRail()
    return db.testrail_coverage_update(*args, **kwargs)


if not hasattr(TestRailClient, "testrail_coverage_update"):
    setattr(TestRailClient, "testrail_coverage_update", _testrail_coverage_update_shim)
