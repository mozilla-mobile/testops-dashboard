# handlers/testrail.py (PR4b fix) — import submodules directly to avoid package-level import issues.
from api.testrail.report_testrail_coverage import testrail_coverage_update
from api.testrail.report_testrail_milestones import testrail_milestones_update
from api.testrail.report_testrail_users import testrail_users_update
from api.testrail.report_testrail_testplans import testrail_testplans_update
from api.testrail.report_testrail_runs import testrail_runs_update


def handle_testrail_test_case_coverage(args):
    # preserves legacy signature
    return testrail_coverage_update(args.arg_list)


def handle_testrail_milestones(args):
    return testrail_milestones_update(args.arg_list)


def handle_testrail_users(args):
    # users typically needs no args
    return testrail_users_update()


def handle_testrail_test_plans_and_runs(args):
    # combined flow: testplans first, then runs
    testrail_testplans_update(args.project, args.num_days or '30')
    return testrail_runs_update(args.project, args.num_days or '30')
