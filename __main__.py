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

from constants import PROJECTS_MOBILE, PROJECTS_ECOSYSTEM, PROJECTS_DESKTOP, PLATFORMS, REPORT_TYPES # noqa


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
    elif platform == 'desktop' and project not in PROJECTS_DESKTOP:
        print(f"Error: Invalid project '{project}' for desktop. Valid options are {PROJECTS_DESKTOP}") # noqa
        sys.exit(1)


def args_to_list(platform, projects):
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


def main():
    args = parse_args(sys.argv[1:])
    validate_project(args.platform, args.project, args.report_type)
    arg_list = args_to_list(args.platform, args.project)

    if args.report_type == 'confluence-updates':
        api_confluence.main()
    if args.report_type == 'testrail-test-case-coverage':
        h = TestRailClient()
        h.data_pump(arg_list)
    if args.report_type == 'testrail-test-run-counts':
        h = TestRailClient()
        if args.num_days:
            num_days = args.num_days
        else:
            num_days = ''
        h.testrail_run_counts_update(args.project, num_days)
    if args.report_type == 'testrail-milestones':
        h = TestRailClient()
        h.testrail_milestones(arg_list)
    if args.report_type == 'testrail-users':
        h = TestRailClient()
        h.testrail_users()
    if args.report_type == 'github-issue-regression':
        h = GithubClient()
        h.github_issue_regression(args.project)
        h = GithubClient()
    if args.report_type == 'jira-qa-requests':
        h = JiraClient()
        h.jira_qa_requests()
    if args.report_type == 'jira-qa-needed':
        h = JiraClient()
        h.jira_qa_needed()
    if args.report_type == 'bugzilla-qe-verify':
        h = BugzillaClient()
        h.bugzilla_qe_verify()
    if args.report_type == 'jira-softvision-worklogs':
        h = JiraClient()
        h.jira_softvision_worklogs()
    if args.report_type == 'bitrise-builds':
        h = BitriseClient()
        h.bitrise_builds_detailed_info()
    if args.report_type == 'sentry-issues':
        h = SentryClient()
        h.sentry_issues()
    if args.report_type == 'sentry-crash-free-rates':
        h = SentryClient()
        h.sentry_crash_free_rate()


if __name__ == '__main__':
    main()
