#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

PLATFORMS = [
    'desktop',
    'ecosystem',
    'mobile',
]

PROJECTS_ECOSYSTEM = [
    'experimenter',
    'nimbus',
    'ALL',
]

PROJECTS_DESKTOP = [
    'firefox-desktop',
    'ALL',
]

PROJECTS_MOBILE = [
    'fenix',
    'firefox-ios',
    'focus-android',
    'focus-ios',
    'reference-browser',
    'ALL',
]

REPORT_TYPES = [
    'bitrise-builds',
    'bugzilla-desktop-bugs',
    'bugzilla-meta-bugs',
    'bugzilla-qe-verify',
    'confluence-updates',
    'confluence-new-page',
    'confluence-build-validation',
    'github-issue-regression',
    'jira-qa-needed',
    'jira-qa-requests',
    'jira-softvision-worklogs',
    'testrail-milestones',
    'testrail-users',
    'testrail-test-case-coverage',
    'testrail-test-run-counts',
    'sentry-issues',
    'testrail-test-plans-and-runs',
    'sentry-rates'
]

# JQL query options
SEARCH = "search"
ISSUES = "issues"

# JQL query All QA Requests since 2022 filter_id: 13856
FILTER_ID_ALL_REQUESTS_2022 = "13856"
MAX_RESULT = "maxResults=100"

# JQL query All QA Needed iOS filter_id: 13789
FILTER_ID_QA_NEEDED_iOS = "13789"

# JQL Softvision Worklogs
QATT_FIELDS = "key,summary"
QATT_BOARD = "15948"
QATT_PARENT_TICKETS_IN_BOARD = f"filter={QATT_BOARD}&jql=parent="
WORKLOG_URL_TEMPLATE = "issue/{issue_key}/worklog"

# Bugzilla queries
BUGZILLA_URL = "bugzilla.mozilla.org"
PRODUCTS = ["Fenix", "Focus", "GeckoView"]
FIELDS = ["id", "summary", "flags", "severity",
          "priority", "status", "resolution"]

BUGZILLA_QA_WHITEBOARD_FILTER = {
    "cf_qa_whiteboard_type": "substring",
    "cf_qa_whiteboard": "qa-found-in-"
}

BUGZILLA_BUGS_FIELDS = [
    "id", "summary", "product",
    "cf_qa_whiteboard", "severity",
    "priority", "status", "resolution",
    "creation_time", "last_change_time",
    "whiteboard", "keywords", "cf_last_resolved"
]
