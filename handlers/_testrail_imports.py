"""handlers/_testrail_imports.py
PR5 helper (strict): re-export canonical TestRail handler functions
from handlers.testrail without any legacy fallbacks.

This avoids referencing alias names that may not exist in your repo.
If an attribute is missing, you'll get an ImportError at import time,
which points directly to the missing canonical function.
"""
from importlib import import_module as _imp

_mod = _imp("handlers.testrail")

# Canonical re-exports (no fallbacks)
handle_testrail_test_case_coverage = _mod.handle_testrail_test_case_coverage
handle_testrail_milestones = _mod.handle_testrail_milestones
handle_testrail_users = _mod.handle_testrail_users
handle_testrail_test_plans_and_runs = _mod.handle_testrail_test_plans_and_runs
handle_testrail_testplans = _mod.handle_testrail_testplans
handle_testrail_runs = _mod.handle_testrail_runs
handle_testrail_run_counts = _mod.handle_testrail_run_counts
handle_testrail_test_results = _mod.handle_testrail_test_results
