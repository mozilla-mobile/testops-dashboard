# service_client.py (PR4a hotfix2)
"""Thin adapter methods forwarding to functional report modules.

Adds missing legacy entry points used by handlers:
- data_pump_report_test_case_coverage(...)
- testrail_plans_and_runs(project, num_days)

Once handlers call report modules directly, this file can be removed.
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

    # ---- Runs ----
    def testrail_runs_update(self, *args, **kwargs):
        from .report_testrail_runs import testrail_runs_update as _run
        return _run(*args, **kwargs)

    # ---- Run Counts ----
    def testrail_run_counts_update(self, *args, **kwargs):
        from .report_testrail_run_counts import testrail_run_counts_update as _run
        return _run(*args, **kwargs)

    # ---- Combined: Plans + Runs (legacy handler entry) ----
    def testrail_plans_and_runs(self, project, num_days):
        from .report_testrail_testplans import testrail_testplans_update as _plans
        from .report_testrail_runs import testrail_runs_update as _runs
        _plans(project, num_days)
        _runs(project, num_days)
        return True
