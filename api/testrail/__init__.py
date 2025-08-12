# Package init for api.testrail
# Temporary monkeypatch: ensure TestRailClient has testrail_coverage_update during migration.

try:
    from .service_client import TestRailClient  # type: ignore
    from .report_testrail_coverage import testrail_coverage_update as _cov_update  # type: ignore

    if not hasattr(TestRailClient, "testrail_coverage_update"):
        def _testrail_coverage_update_shim(self, *args, **kwargs):
            # Forward to the functional report implementation
            return _cov_update(*args, **kwargs)
        setattr(TestRailClient, "testrail_coverage_update", _testrail_coverage_update_shim)
except Exception:
    # Fail silently; this is a best-effort shim during refactor.
    pass
