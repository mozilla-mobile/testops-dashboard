# service_client.py (PR4a hotfix)
"""Thin adapter methods forwarding to functional report modules.

Adds the missing `data_pump_report_test_case_coverage(...)` so existing handlers
keep working during cutover. Once handlers point directly to report modules,
this file can be removed.
"""


class TestRailClient:
    """Legacy facade kept temporarily for handler compatibility.

    Each method simply forwards to the corresponding functional orchestrator.
    """

    # ---- Coverage ----
    def testrail_coverage_update(self, *args, **kwargs):
        from .report_testrail_coverage import testrail_coverage_update as _run
        return _run(*args, **kwargs)

    # Handler compatibility (old entry point name)
    def data_pump_report_test_case_coverage(self, *args, **kwargs):
        from .report_testrail_coverage import testrail_coverage_update as _run
        return _run(*args, **kwargs)

    # ---- Users ----
    def testrail_users_update(self, *args, **kwargs):
        from .report_testrail_users import testrail_users_update as _run
        return _run(*args, **kwargs)

    # ---- Milestones ----
    def testrail_milestones_update(self, *args, **kwargs):
        from .report_testrail_milestones import testrail_milestones_update as _run
        return _run(*args, **kwargs)

    # ---- Test Plans ----
    def testrail_testplans_update(self, *args, **kwargs):
        from .report_testrail_testplans import testrail_testplans_update as _run
        return _run(*args, **kwargs)

    # ---- Runs (if used) ----
    def testrail_runs_update(self, *args, **kwargs):
        from .report_testrail_runs import testrail_runs_update as _run
        return _run(*args, **kwargs)

    # ---- Run Counts (if used) ----
    def testrail_run_counts_update(self, *args, **kwargs):
        from .report_testrail_run_counts import testrail_run_counts_update as _run
        return _run(*args, **kwargs)
