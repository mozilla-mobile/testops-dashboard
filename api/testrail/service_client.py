# service_client.py (PR4a hotfix3)
"""Thin adapter methods forwarding to functional report modules.

Adds legacy alias methods used by handlers (e.g., `testrail_users`).
Once handlers call report modules directly, this file can be deleted.
"""


class TestRailClient:
    """Legacy facade kept temporarily for handler compatibility.

    Each method simply forwards to the corresponding functional orchestrator.
    """

    # ---- Coverage ----
    def testrail_coverage_update(self, *args, **kwargs):
        from .report_testrail_coverage import testrail_coverage_update as _run
        return _run(*args, **kwargs)

    # Legacy handler entry point name
    def data_pump_report_test_case_coverage(self, *args, **kwargs):
        from .report_testrail_coverage import testrail_coverage_update as _run
        return _run(*args, **kwargs)

    # ---- Users ----
    def testrail_users_update(self, *args, **kwargs):
        from .report_testrail_users import testrail_users_update as _run
        return _run(*args, **kwargs)

    # Legacy alias without _update (used by handlers)
    def testrail_users(self, *args, **kwargs):
        from .report_testrail_users import testrail_users_update as _run
        return _run(*args, **kwargs)

    # ---- Milestones ----
    def testrail_milestones_update(self, *args, **kwargs):
        from .report_testrail_milestones import testrail_milestones_update as _run
        return _run(*args, **kwargs)

    # Legacy alias without _update
    def testrail_milestones(self, *args, **kwargs):
        from .report_testrail_milestones import testrail_milestones_update as _run
        return _run(*args, **kwargs)

    # ---- Test Plans ----
    def testrail_testplans_update(self, *args, **kwargs):
        from .report_testrail_testplans import testrail_testplans_update as _run
        return _run(*args, **kwargs)

    # Legacy alias without _update
    def testrail_testplans(self, *args, **kwargs):
        from .report_testrail_testplans import testrail_testplans_update as _run
        return _run(*args, **kwargs)

    # ---- Runs (if used) ----
    def testrail_runs_update(self, *args, **kwargs):
        from .report_testrail_runs import testrail_runs_update as _run
        return _run(*args, **kwargs)

    # Legacy alias without _update
    def testrail_runs(self, *args, **kwargs):
        from .report_testrail_runs import testrail_runs_update as _run
        return _run(*args, **kwargs)

    # ---- Run Counts (if used) ----
    def testrail_run_counts_update(self, *args, **kwargs):
        from .report_testrail_run_counts import testrail_run_counts_update as _run
        return _run(*args, **kwargs)

    # Legacy combined entry point used by handlers
    def testrail_plans_and_runs(self, project, num_days):
        from .report_testrail_testplans import testrail_testplans_update as _plans
        from .report_testrail_runs import testrail_runs_update as _runs
        _plans(project, num_days)
        return _runs(project, num_days)
