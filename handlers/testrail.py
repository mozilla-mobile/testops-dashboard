from api.testrail.service_client import TestRailClient


def handle_testrail_test_plans_and_runs(args):
    client = TestRailClient()
    client.testrail_plans_and_runs(args.project, args.num_days or '30')


def handle_testrail_test_results(args):
    client = TestRailClient()
    client.testrail_test_results()


def handle_testrail_milestones(args):
    client = TestRailClient()
    client.testrail_milestones(args.arg_list)


def handle_testrail_users(args):
    client = TestRailClient()
    client.testrail_users()


def handle_testrail_test_case_coverage(args):
    client = TestRailClient()
    client.data_pump_report_test_case_coverage(args.arg_list)


def handle_testrail_test_run_counts_update(args):
    client = TestRailClient()
    client.testrail_run_counts_update(args.project, args.num_days or '')
