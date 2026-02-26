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
    PROJECTS_SENTRY,
    PLATFORMS,
    REPORT_TYPES,
)

from handlers.bitrise import (
    handle_bitrise_builds,
)

from handlers.bugzilla import (
    handle_bugzilla_desktop_bugs,
    handle_bugzilla_desktop_overall_bugs,
    handle_bugzilla_desktop_release_flags_for_bugs,
    handle_bugzilla_meta_bugs,
    handle_bugzilla_qe_verify,
    handle_bugzilla_query_by_keyword,
)

from handlers.confluence import (
    handle_confluence_build_validation,
    handle_confluence_updates,
)

from handlers.github import (
    handle_github_issue_regression,
    handle_github_new_bugs
)

from handlers.jira import (
    handle_jira_qa_requests,
    handle_jira_qa_needed,
    handle_jira_softvision_worklogs,
    handle_jira_qa_requests_desktop,
)

from handlers.sentry import (
    handle_sentry_issues,
    handle_sentry_rates,
)

from handlers.testrail import (
    handle_testrail_test_plans_and_runs,
    handle_testrail_test_results,
    handle_testrail_milestones,
    handle_testrail_users,
    handle_testrail_test_case_coverage, handle_testrail_test_health,
    # handle_testrail_test_run_counts_update,
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

    parser.add_argument(
        "--bz-keyword",
        help="Indicate Bugzilla keyword for bugzilla-query-by-keyword",
        required=False,
        type=str,
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

    if (report_type in ('sentry-issues', 'sentry-rates')
            and project not in PROJECTS_SENTRY):
        print(
            f"Error: Invalid project '{project}' for Sentry reports. "
            f"Valid options are {PROJECTS_SENTRY}"
        )
        sys.exit(1)

    if (report_type in ('github-new-bugs')
            and project not in PROJECTS_MOBILE):
        print(
            f"Error: Invalid project '{project}' for GitHub new bugs report. "
            f"Valid options are {PROJECTS_MOBILE}"
        )
        sys.exit(1)

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
    'bugzilla-desktop-overall-bugs': handle_bugzilla_desktop_overall_bugs,
    'bugzilla-desktop-release-flags-for-bugs': handle_bugzilla_desktop_release_flags_for_bugs, # noqa
    'bugzilla-meta-bugs': handle_bugzilla_meta_bugs,
    'bugzilla-qe-verify': handle_bugzilla_qe_verify,
    'bugzilla-query-by-keyword': handle_bugzilla_query_by_keyword,
    'confluence-updates': handle_confluence_updates,
    'confluence-build-validation': handle_confluence_build_validation,
    'github-issue-regression': handle_github_issue_regression,
    'github-new-bugs': handle_github_new_bugs,
    'jira-qa-needed': handle_jira_qa_needed,
    'jira-qa-requests': handle_jira_qa_requests,
    'jira-qa-requests-desktop': handle_jira_qa_requests_desktop,
    'jira-softvision-worklogs': handle_jira_softvision_worklogs,
    'sentry-issues': handle_sentry_issues,
    'sentry-rates': handle_sentry_rates,
    'testrail-milestones': handle_testrail_milestones,
    'testrail-users': handle_testrail_users,
    'testrail-test-health': handle_testrail_test_health,
    'testrail-test-case-coverage': handle_testrail_test_case_coverage,
    # 'testrail-test-run-counts': handle_testrail_test_run_counts_update,
    'testrail-test-plans-and-runs': handle_testrail_test_plans_and_runs,
    'testrail-test-results': handle_testrail_test_results,
}


def main():
    args = parse_args(sys.argv[1:])
    args.arg_list = expand_project_args(args.platform, args.project)
    report_type = args.report_type

    # DIAGNOSTIC
    print(f"args: {args}")
    print(f"args.report_type: {args.report_type}")
    print(f"args.arg_list: {args.arg_list}")

    if report_type not in COMMAND_MAP:
        sys.exit(f"Unknown or unsupported report type: {report_type}")

    validate_project(args.platform, args.project, report_type)

    COMMAND_MAP[report_type](args)


if __name__ == "__main__":
    main()
