"""Unified TestRail handlers with local imports.

We import the specific report modules *inside* each handler to avoid
package-level import side effects during __main__ startup.
"""

# --- Coverage ---
def handle_testrail_test_case_coverage(args):
    from api.testrail.report_testrail_coverage import testrail_coverage_update
    return testrail_coverage_update(args.arg_list)

# --- Milestones ---
def handle_testrail_milestones(args):
    from api.testrail.report_testrail_milestones import testrail_milestones_update
    return testrail_milestones_update(args.arg_list)

# --- Users ---
def handle_testrail_users(args):
    from api.testrail.report_testrail_users import testrail_users_update
    return testrail_users_update()

# --- Test Plans and Runs (combined) ---
def handle_testrail_test_plans_and_runs(args):
    from api.testrail.report_testrail_testplans import testrail_testplans_update
    from api.testrail.report_testrail_runs import testrail_runs_update
    testrail_testplans_update(args.project, args.num_days or '30')
    return testrail_runs_update(args.project, args.num_days or '30')

# --- Individual convenience handlers (if invoked separately) ---
def handle_testrail_testplans(args):
    from api.testrail.report_testrail_testplans import testrail_testplans_update
    return testrail_testplans_update(args.project, args.num_days or '30')

def handle_testrail_runs(args):
    from api.testrail.report_testrail_runs import testrail_runs_update
    return testrail_runs_update(args.project, args.num_days or '30')

def handle_testrail_run_counts(args):
    from api.testrail.report_testrail_run_counts import testrail_run_counts_update
    return testrail_run_counts_update(args.project, args.num_days or '30')

# --- Test Results ---
def handle_testrail_test_results(args):
    # Prefer canonical name; keep a fallback for older filename
    try:
        from api.testrail.report_testrail_test_results import testrail_test_results_update
    except ModuleNotFoundError:
        from api.testrail.report_testrail_results import testrail_test_results_update  # fallback
    # Assume args may include project / date range in your CLI; adapt if needed
    if hasattr(args, "project") and hasattr(args, "num_days"):
        return testrail_test_results_update(args.project, args.num_days or '30')
    return testrail_test_results_update()
