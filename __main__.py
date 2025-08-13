#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import sys


from constants import (
    PROJECTS_MOBILE,
    PROJECTS_ECOSYSTEM,
    PROJECTS_DESKTOP,
    PLATFORMS,
    REPORT_TYPES,
)

from handlers.bitrise import (
    handle_bitrise_builds,
)

from handlers.bugzilla import (
    handle_bugzilla_desktop_bugs,
    handle_bugzilla_meta_bugs,
    handle_bugzilla_qe_verify,
)

from handlers.confluence import (
    handle_confluence_build_validation,
    handle_confluence_updates,
)

from handlers.github import (
    handle_github_issue_regression,
)

from handlers.jira import (
    handle_jira_qa_requests,
    handle_jira_qa_needed,
    handle_jira_softvision_worklogs,
)

from handlers.sentry import (
    handle_sentry_issues,
    handle_sentry_rates,
)

from handlers.testrail import (
    handle_testrail_test_case_coverage,
    handle_testrail_milestones,
    handle_testrail_users,
    handle_testrail_test_plans_and_runs,  # :white_tick: combined handler
    handle_testrail_run_counts,
    handle_testrail_test_results,
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
        print(
            f"Error: Invalid project '{project}' for mobile. "
            f"Valid options are {PROJECTS_MOBILE}"
        )
        sys.exit(1)
    elif platform == 'desktop' and project not in PROJECTS_DESKTOP:
        print(
            f"Error: Invalid project '{project}' for desktop. "
            f"Valid options are {PROJECTS_DESKTOP}"
        )
        sys.exit(1)
    elif platform == 'ecosystem' and project not in PROJECTS_ECOSYSTEM:
        print(
            f"Error: Invalid project '{project}' for ecosystem. "
            f"Valid options are {PROJECTS_ECOSYSTEM}"
        )
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


# === DISPATCH MAP ===
COMMAND_MAP = {
    'bitrise-builds': handle_bitrise_builds,
    'bugzilla-desktop-bugs': handle_bugzilla_desktop_bugs,
    'bugzilla-meta-bugs': handle_bugzilla_meta_bugs,
    'bugzilla-qe-verify': handle_bugzilla_qe_verify,
    'confluence-updates': handle_confluence_updates,
    'confluence-build-validation': handle_confluence_build_validation,
    'github-issue-regression': handle_github_issue_regression,
    'jira-qa-needed': handle_jira_qa_needed,
    'jira-qa-requests': handle_jira_qa_requests,
    'jira-softvision-worklogs': handle_jira_softvision_worklogs,
    'sentry-issues': handle_sentry_issues,
    'sentry-rates': handle_sentry_rates,
    'testrail-milestones': handle_testrail_milestones,
    'testrail-users': handle_testrail_users,
    'testrail-test-case-coverage': handle_testrail_test_case_coverage,
    'testrail-test-run-counts': handle_testrail_run_counts,
    'testrail-test-plans-and-runs': handle_testrail_test_plans_and_runs,
    'testrail-test-results': handle_testrail_test_results,
}


def main():
    args = parse_args(sys.argv[1:])
    args.arg_list = expand_project_args(args.platform, args.project)

    report_type = args.report_type

    if report_type not in COMMAND_MAP:
        sys.exit(f"Unknown or unsupported report type: {report_type}")

    validate_project(args.platform, args.project, report_type)
    # args.project_list = expand_project_args(args.platform, args.project)

    COMMAND_MAP[report_type](args)


if __name__ == "__main__":
    main()
