PLATFORMS = [
    'mobile',
    'ecosystem',
    'desktop'
]

PROJECTS_ECOSYSTEM = [
    'experimenter',
    'nimbus',
    'ALL'
]

PROJECTS_DESKTOP = [
    'firefox-desktop',
    'ALL'
]

PROJECTS_MOBILE = [
    'fenix',
    'focus-android',
    'reference-browser',
    'firefox-ios',
    'focus-ios',
    'ALL',
]

REPORT_TYPES = [
    'test-case-coverage',
    'test-run-counts',
    'issue-regression',
    'jira-qa-requests',
    'jira-qa-needed',
    'bugzilla-qe-verify',
    'testrail-milestones',
    'confluence-updates',
    'jira-softvision-worklogs'
]

# JQL query options
SEARCH = "search"
ISSUES = "issues"

# JQL query All QA Requests since 2022 filter_id: 13856
FILTER_ID_ALL_REQUESTS_2022 = "13856"
MAX_RESULT = "maxResults=100"

# JQL query Requests, Internal Task, Sub-Task filter_id: 14323
FILTER_ID_NEW_ISSUE_TYPES = "14323"

# JQL query All QA Needed iOS filter_id: 13789
FILTER_ID_QA_NEEDED_iOS = "13789"

# JQL Softvision Worklogs
QATT_FIELDS = "key,summary"
QATT_BOARD = "15948"
QATT_PARENT_TICKETS_IN_BOARD = f"filter={QATT_BOARD}&jql=parent="
WORKLOG_URL_TEMPLATE = "issue/{issue_key}/worklog"

# JQL Extra fields needed
JQL_QUERY = 'jql=filter='

STORY_POINTS = "customfield_10037"
FIREFOX_RELEASE_TRAIN = "customfield_10155"
ENGINEERING_TEAM = "customfield_10134"
DEFAULT_COLUMNS = "id,key,status,created,summary,labels,assignee"
COLUMNS_ISSUE_TYPE = ",issuetype,parent"
TESTED_TRAINS = "customfield_11930"

# Bugzilla queries
BUGZILLA_URL = "bugzilla.mozilla.org"
PRODUCTS = ["Fenix", "Focus", "GeckoView"]
FIELDS = ["id", "summary", "flags", "severity",
          "priority", "status", "resolution"]
