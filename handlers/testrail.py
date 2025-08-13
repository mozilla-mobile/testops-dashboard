# Minimal TestRail handlers: call report modules directly.

from api.testrail.report_testrail_coverage import testrail_coverage_update
from api.testrail.report_testrail_milestones import testrail_milestones_update
from api.testrail.report_testrail_users import testrail_users_update
from api.testrail.report_testrail_testplans import testrail_test_plans_and_runs
from api.testrail.report_testrail_runs import testrail_runs_update
from api.testrail.report_testrail_run_counts import testrail_run_counts_update
from api.testrail.report_testrail_test_results import testrail_test_results_update


def handle_testrail_test_plans_and_runs(args):
    project = getattr(args, "project", None)
    num_days = getattr(args, "num_days", None) or "30"
    testrail_test_plans_and_runs(project, num_days)


def handle_testrail_test_results(args):
    project = getattr(args, "project", None)
    num_days = getattr(args, "num_days", None) or "30"
    testrail_test_results_update(project, num_days)


def handle_testrail_milestones(args):
    testrail_milestones_update(getattr(args, "arg_list", None))


def handle_testrail_users(args):
    testrail_users_update()


def handle_testrail_test_case_coverage(args):
    testrail_coverage_update(getattr(args, "arg_list", None))


def handle_testrail_run_counts(args):
    project = getattr(args, "project", None)
    num_days = getattr(args, "num_days", None) or ""
    testrail_run_counts_update(project, num_days)
