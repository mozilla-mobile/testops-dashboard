"""handlers/_testrail_imports.py
PR5 helper: export *canonical* TestRail handler functions for __main__.py.

- Imports canonical functions from handlers/testrail.py (which already does
  local, safe imports of report modules).
- Provides stable names so __main__.py doesn't need legacy aliases.
- If a canonical function were missing for some reason, we try to fall back
  to the legacy alias present in handlers/testrail.py (defensive only).
"""
from importlib import import_module

_mod = import_module("handlers.testrail")

def _pick(name, fallback):
    return getattr(_mod, name, getattr(_mod, fallback))

# Canonical exports
handle_testrail_test_case_coverage = _pick(
    "handle_testrail_test_case_coverage", "handle_testrail_test_case_coverage_update"
)
handle_testrail_milestones = _pick(
    "handle_testrail_milestones", "handle_testrail_milestones_update"
)
handle_testrail_users = _pick(
    "handle_testrail_users", "handle_testrail_users_update"
)
handle_testrail_test_plans_and_runs = _pick(
    "handle_testrail_test_plans_and_runs", "handle_testrail_testplans_update"
)
handle_testrail_testplans = _pick(
    "handle_testrail_testplans", "handle_testrail_testplans_update"
)
handle_testrail_runs = _pick(
    "handle_testrail_runs", "handle_testrail_runs_update"
)
handle_testrail_run_counts = _pick(
    "handle_testrail_run_counts", "handle_testrail_test_run_counts_update"
)
handle_testrail_test_results = _pick(
    "handle_testrail_test_results", "handle_testrail_test_results_update"
)
