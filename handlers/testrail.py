"""handlers/testrail.py — unified + alias-friendly handlers (PR4b fix4)

All imports are local per function to avoid import-time side effects.
We expose both canonical handler names and legacy *_update variants used
by __main__.py or workflows.
"""

# --- Coverage ---
def handle_testrail_test_case_coverage(args):
    from api.testrail.report_testrail_coverage import testrail_coverage_update
    return testrail_coverage_update(args.arg_list)

def handle_testrail_coverage_update(args):  # legacy alias
    return handle_testrail_test_case_coverage(args)


# --- Milestones ---
def handle_testrail_milestones(args):
    from api.testrail.report_testrail_milestones import testrail_milestones_update
    return testrail_milestones_update(args.arg_list)

def handle_testrail_milestones_update(args):  # legacy alias
    return handle_testrail_milestones(args)


# --- Users ---
def handle_testrail_users(args):
    from api.testrail.report_testrail_users import testrail_users_update
    return testrail_users_update()

def handle_testrail_users_update(args):  # legacy alias
    return handle_testrail_users(args)


# --- Test Plans and Runs (combined) ---
def handle_testrail_test_plans_and_runs(args):
    from api.testrail.report_testrail_testplans import testrail_testplans_update
    from api.testrail.report_testrail_runs import testrail_runs_update
    testrail_testplans_update(args.project, getattr(args, "num_days", None) or '30')
    return testrail_runs_update(args.project, getattr(args, "num_days", None) or '30')


# --- Individual reports ---
def handle_testrail_testplans(args):
    from api.testrail.report_testrail_testplans import testrail_testplans_update
    return testrail_testplans_update(args.project, getattr(args, "num_days", None) or '30')

def handle_testrail_testplans_update(args):  # legacy alias
    return handle_testrail_testplans(args)


def handle_testrail_runs(args):
    from api.testrail.report_testrail_runs import testrail_runs_update
    return testrail_runs_update(args.project, getattr(args, "num_days", None) or '30')

def handle_testrail_runs_update(args):  # legacy alias
    return handle_testrail_runs(args)


def handle_testrail_run_counts(args):
    from api.testrail.report_testrail_run_counts import testrail_run_counts_update
    return testrail_run_counts_update(args.project, getattr(args, "num_days", None) or '30')

# This is the name your logs are importing
def handle_testrail_test_run_counts_update(args):  # legacy alias expected by __main__.py
    return handle_testrail_run_counts(args)


# --- Test Results ---
def handle_testrail_test_results(args):
    try:
        from api.testrail.report_testrail_test_results import testrail_test_results_update
    except ModuleNotFoundError:
        from api.testrail.report_testrail_results import testrail_test_results_update
    if hasattr(args, "project") and hasattr(args, "num_days"):
        return testrail_test_results_update(args.project, getattr(args, "num_days", None) or '30')
    return testrail_test_results_update()

def handle_testrail_test_results_update(args):  # legacy alias
    return handle_testrail_test_results(args)
