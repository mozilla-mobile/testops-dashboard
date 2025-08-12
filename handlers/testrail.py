from api.testrail.api_testrail import TestRailClient


def handle_testrail_test_plans_and_runs(args) -> None:
    """Run the combined TestRail test plans + runs flow."""
    client = TestRailClient()
    client.testrail_plans_and_runs(args.project, args.num_days or '30')


def handle_testrail_test_results(args) -> None:
    """Update TestRail test results report."""
    client = TestRailClient()
    client.testrail_test_results()


def handle_testrail_milestones(args) -> None:
    """Update TestRail milestones report."""
    client = TestRailClient()
    client.testrail_milestones(args.arg_list)


def handle_testrail_users(args) -> None:
    """Update TestRail users report."""
    client = TestRailClient()
    client.testrail_users()


def handle_testrail_test_case_coverage(args) -> None:
    """Update the TestRail test case coverage report."""
    client = TestRailClient()
    client.data_pump_report_test_case_coverage(args.arg_list)


def handle_testrail_test_run_counts_update(args) -> None:
    """Legacy name kept for compatibility. Prefer handle_testrail_run_counts."""
    client = TestRailClient()
    client.testrail_run_counts_update(args.project, args.num_days or '')


def handle_testrail_run_counts(args) -> None:
    """Update TestRail test run counts report (canonical handler)."""
    handle_testrail_test_run_counts_update(args)
