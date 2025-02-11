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
    'testrail-milestones'
]

# JQL query All QA Requests since 2022 filter_id: 13856
FILTER_ID_ALL_REQUESTS_2022 = "13856"
MAX_RESULT = "maxResults=100"

# JQL query All QA Needed iOS filter_id: 13789
FILTER_ID_QA_NEEDED_iOS = "13789"

# Bugzilla queries
BUGZILLA_URL = "bugzilla.mozilla.org"
PRODUCTS = ["Fenix", "Focus", "GeckoView"]
FIELDS = ["id", "summary", "flags", "severity",
          "priority", "status", "resolution"]
