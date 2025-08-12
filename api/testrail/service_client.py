# service_client.py (PR4 cutover adapters)
"""Thin adapter methods forwarding to functional report modules.

This keeps legacy handlers working while making the functional modules the
single source of truth. After handlers are updated to import report modules
directly, this file can be removed.
"""


class TestRailClient:
    """Legacy facade kept temporarily for handler compatibility.

    Each method simply forwards to the corresponding functional orchestrator.

    TODO(PR5): delete this class after handlers are switched.
    """

    # ---- Coverage ----
    def testrail_coverage_update(self, *args, **kwargs):
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
