# service_client.py (PR4a dynamic adapter)
"""Temporary compatibility layer for legacy handler calls.

- Keeps explicit adapter methods we've already used.
- Adds a *dynamic* fallback via __getattr__ for legacy names like:
    * testrail_<report>(...)
    * testrail_<report>_update(...)
    * data_pump_report_<report>(...)
  These are routed to the functional orchestrators in:
    api/testrail/report_testrail_<report>.py -> testrail_<report>_update(...)

IMPORTANT: This does **not** rename any functions in your codebase.
It only provides a runtime bridge so CI doesn't fail while we migrate.
It also prints a one-line notice when a dynamic fallback is used so
you can grep logs and tidy the handlers in PR4b.
"""
from importlib import import_module
import sys


_ALLOWED_REPORTS = {
    "coverage",
    "users",
    "milestones",
    "testplans",
    "runs",
    "run_counts",
}


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

    # ---- Runs ----
    def testrail_runs_update(self, *args, **kwargs):
        from .report_testrail_runs import testrail_runs_update as _run
        return _run(*args, **kwargs)

    # Legacy alias without _update
    def testrail_runs(self, *args, **kwargs):
        from .report_testrail_runs import testrail_runs_update as _run
        return _run(*args, **kwargs)

    # ---- Run Counts ----
    def testrail_run_counts_update(self, *args, **kwargs):
        from .report_testrail_run_counts import testrail_run_counts_update as _run
        return _run(*args, **kwargs)

    # Legacy combined entry point used by handlers
    def testrail_plans_and_runs(self, project, num_days):
        from .report_testrail_testplans import testrail_testplans_update as _plans
        from .report_testrail_runs import testrail_runs_update as _runs
        _plans(project, num_days)
        return _runs(project, num_days)

    # -------- Dynamic fallback for any other legacy names --------
    def __getattr__(self, name: str):
        # Only handle specific legacy prefixes to keep behavior predictable.
        prefix_map = (
            ("testrail_", ""),
            ("data_pump_report_", ""),
        )
        for prefix, strip in prefix_map:
            if name.startswith(prefix):
                remainder = name[len(prefix):]
                # Normalize optional trailing '_update'
                if remainder.endswith("_update"):
                    remainder = remainder[:-7]
                report = remainder
                if report in _ALLOWED_REPORTS:
                    def _dynamic_forward(*args, **kwargs):
                        # Log once to stderr so we can find & clean these up in PR4b
                        print(f"[testrail adapter] dynamic fallback: '{name}' -> report '{report}'",
                              file=sys.stderr)
                        mod = import_module(f"{__package__}.report_testrail_{report}")
                        run = getattr(mod, f"testrail_{report}_update")
                        return run(*args, **kwargs)
                    return _dynamic_forward
        # Default behavior: normal AttributeError for unknowns.
        raise AttributeError(f"{self.__class__.__name__!s} object has no attribute {name!r}")
