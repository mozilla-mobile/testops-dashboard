from api.testrail import report_testrail_test_case_coverage as coverage
from api.testrail import report_testrail_milestones as milestones
from api.testrail import report_testrail_users as users
from api.testrail import report_testrail_testplans as plans
from api.testrail import report_testrail_runs as runs

def handle_testrail_test_case_coverage(args):
    coverage.testrail_coverage_update(args.arg_list)

def handle_testrail_milestones(args):
    milestones.testrail_milestones_update(args.arg_list)

def handle_testrail_users(args):
    users.testrail_users_update()

def handle_testrail_test_plans_and_runs(args):
    plans.testrail_testplans_update(args.project, args.num_days or '30')
    runs.testrail_runs_update(args.project, args.num_days or '30')
