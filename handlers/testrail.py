#from api.testrail.api_testrail import TestRailClient
import api.testrail.report_users as users
import api.testrail.report_milestones as milestones
import api.testrail.report_test_results as test_results
import api.testrail.report_test_case_coverage as test_case_coverage
import api.testrail.report_test_plans_and_runs as test_plans_and_runs 


def handle_testrail_test_plans_and_runs(args):
    #client = TestRailClient()
    #client.testrail_plans_and_runs(args.project, args.num_days or '30')
    test_plans_and_runs.testrail_plans_and_runs(args.project, args.num_days or '30')


def handle_testrail_test_results(args):
    test_results.testrail_test_results()


def handle_testrail_milestones(args):
    milestones.testrail_milestones(args.arg_list)


def handle_testrail_users(args):
    users.testrail_users()


def handle_testrail_test_case_coverage(args):
    test_case_coverage.testrail_test_case_coverage(args.arg_list)


"""
def handle_testrail_test_run_counts_update(args):
    client = TestRailClient()
    client.testrail_run_counts_update(args.project, args.num_days or '')
"""
