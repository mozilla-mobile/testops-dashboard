#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import sys


from api_bugzilla import BugzillaClient
from api_github import GithubClient
from api_jira import JiraClient
from api_testrail import TestRailClient
from api_sentry import SentryClient
import api_confluence

from api_bitrise import BitriseClient

from constants import (
    PROJECTS_MOBILE,
    PROJECTS_ECOSYSTEM,
    PROJECTS_DESKTOP,
    PLATFORMS,
    REPORT_TYPES,
)


def parse_args(cmdln_args):
    parser = argparse.ArgumentParser(
        description="Retrieve and update mobile project test data"
    )

    parser.add_argument(
        "--project",
        help="Indicate project",
        required=False,
    )

    parser.add_argument(
        "--platform",
        help="Select the platform: Mobile, Ecosystem or Desktop",
        required=False,
        choices=PLATFORMS,
        )

    parser.add_argument(
        "--report-type",
        help="Indicate report type",
        required=False,
        choices=REPORT_TYPES
    )

    parser.add_argument(
        "--num-days",
        help="Indicate number of historic days of records to include",
        required=False
    )

    parser.add_argument(
        "--meta-bug-id",
        help="Indicate Bugzilla metabug ID for bugzilla-meta-bugs",
        required=False,
        type=int,
    )

    return parser.parse_args(args=cmdln_args)


# Function to validate the project based on the platform
def validate_project(platform, project, report_type):
    # Conditionally require --platform and --project
    # if --report-type is 'test-case-coverage'
    if report_type in ('test-case-coverage', 'testrail-milestones'):
        if not project:
            print("--project is required for the report selected")
        if not platform:
            print("--platform is required for the report selected")

    if platform == 'mobile' and project not in PROJECTS_MOBILE:
        print(f"Error: Invalid project '{project}' for mobile. Valid options are {PROJECTS_MOBILE}") # noqa 
        sys.exit(1)
    elif platform == 'desktop' and project not in PROJECTS_DESKTOP:
        print(f"Error: Invalid project '{project}' for desktop. Valid options are {PROJECTS_DESKTOP}") # noqa
        sys.exit(1)
    elif platform == 'ecosystem' and project not in PROJECTS_ECOSYSTEM:
        print(f"Error: Invalid project '{project}' for ecosystem. Valid options are {PROJECTS_ECOSYSTEM}") # noqa
        sys.exit(1)


def expand_project_args(platform, projects):
    projects_list = []
    platform = (platform or "").lower()
    projects = (projects or "").lower()

    if isinstance(projects, str):
        if projects == 'all':
            if platform == 'desktop':
                for project in PROJECTS_DESKTOP[:-1]:
                    projects_list.append(project)

            if platform == 'mobile':
                for project in PROJECTS_MOBILE[:-1]:
                    projects_list.append(project)

            if platform == 'ecosystem':
                for project in PROJECTS_ECOSYSTEM[:-1]:
                    projects_list.append(project)
        else:
            projects_list = [projects]
    return projects_list


# === COMMAND HANDLERS ===

def handle_bitrise_builds(args):
    client = BitriseClient()
    client.post_build_data(args.project_list)


def handle_bugzilla_desktop_bugs(args):
    client = BugzillaClient()
    client.post_desktop_bugs()


def handle_bugzilla_meta_bugs(args):
    client = BugzillaClient()
    client.post_meta_bugs(args.meta_bug_id)


def handle_bugzilla_qe_verify(args):
    client = BugzillaClient()
    client.post_qe_verify_bugs()


def handle_confluence_updates(args):
    api_confluence.update_existing_page()


def handle_confluence_new_page(args):
    api_confluence.create_new_page()


def handle_confluence_build_validation(args):
    api_confluence.post_build_validation()


def handle_github_issue_regression(args):
    client = GithubClient()
    client.post_regression_issues()


def handle_jira_qa_needed(args):
    client = JiraClient()
    client.post_qa_needed()


def handle_jira_qa_requests(args):
    client = JiraClient()
    client.post_qa_requests()


def handle_jira_softvision_worklogs(args):
    client = JiraClient()
    client.post_softvision_worklogs()


def handle_sentry_issues(args):
    client = SentryClient()
    client.post_sentry_issues()


def handle_testrail_milestones(args):
    client = TestRailClient()
    client.post_milestone_report(args.project_list, args.platform)


def handle_testrail_users(args):
    client = TestRailClient()
    client.post_user_report(args.project_list, args.platform)


def handle_testrail_test_case_coverage(args):
    client = TestRailClient()
    client.post_test_case_coverage(args.project_list, args.platform)


def handle_testrail_test_run_counts(args):
    client = TestRailClient()
    client.post_test_run_counts(args.project_list, args.platform)


# === DISPATCH MAP ===
COMMAND_MAP = {
    'bitrise-builds': handle_bitrise_builds,
    'bugzilla-desktop-bugs': handle_bugzilla_desktop_bugs,
    'bugzilla-meta-bugs': handle_bugzilla_meta_bugs,
    'bugzilla-qe-verify': handle_bugzilla_qe_verify,
    'confluence-updates': handle_confluence_updates,
    'confluence-new-page': handle_confluence_new_page,
    'confluence-build-validation': handle_confluence_build_validation,
    'github-issue-regression': handle_github_issue_regression,
    'jira-qa-needed': handle_jira_qa_needed,
    'jira-qa-requests': handle_jira_qa_requests,
    'jira-softvision-worklogs': handle_jira_softvision_worklogs,
    'sentry-issues': handle_sentry_issues,
    'testrail-milestones': handle_testrail_milestones,
    'testrail-users': handle_testrail_users,
    'testrail-test-case-coverage': handle_testrail_test_case_coverage,
    'testrail-test-run-counts': handle_testrail_test_run_counts
}


def main():
    args = parse_args(sys.argv[1:])
    report_type = args.report_type

    if report_type not in COMMAND_MAP:
        sys.exit(f"Unknown or unsupported report type: {report_type}")

    validate_project(args.platform, args.project, report_type)
    args.project_list = args_to_list(args.platform, args.project)

    COMMAND_MAP[report_type](args)


if __name__ == "__main__":
    main()
