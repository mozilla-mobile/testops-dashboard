# Jira API
This repository contains a collection of Jira API–based data extraction modules. Each module documents a specific Jira query, the data it produces, how that data is transformed and stored, and how it is ultimately consumed by analytics tools such as Looker.  

The README serves as living documentation for existing and future Jira queries, explaining their purpose, build logic, and downstream usage as new reports are added over time.

## Jira Issues - report_qa_needed
Only for iOS, android bugs are tracked via bugzilla not Jira

### Table name & purpose
Table: *ReportJiraQANeeded*

Purpose: provide a small aggregated snapshot of QA-needed issues per project (total QA-needed, how many are marked as verified nightly, how many are not). This table is useful for a quick KPI tile (e.g. “QA-needed: total / verified / not verified”).

### Build & update logic

- Calls`filter_qa_needed()` which runs a JQL search restricted to the QA-needed filter FILTER_ID_QA_NEEDED_iOS, and fetches only labels field.
- Pay load is normalized and inserted in the database

### Looker artifacts
QA-Needed (daily)
See in dashboard: https://mozilla.cloud.looker.com/dashboards/1846

## Jira Worklogs - report_worklogs
Softvision needs to track the time spent in Jira tasks. They use the Workload tab available in issues to fetch the worklogs per item.

### Table name & purpose
Table: *ReportJiraSoftvisionWorklogs*

Purpose: full export of Softvision worklog lines (both parent and child issue worklog entries). This is the base dataset to build time-spent metrics for the QATT project (total time per ticket, per author, per parent, per date, etc.).

### Build & update logic
To consider: There are parent tickets with no child issues but with worklogs. And parent tickets with or without worklogs with children that may or may not have worklgos. It is necessary to iterate over parents and child items.

- `Jira.filter_sv_parent_in_board()` retrieves parent tickets from a QATT board using QATT_BOARD filter.

    The method requests summary,parent,status,labels,issuetype,assignee,reporter,created,updated,worklog fields and expands names.


- For each parent issue:
Fetch child issues via `filter_child_issues(parent_key)` (JQL to retrieve children).

    Fetch parent worklogs via filter_worklogs(parent_key) (endpoint: .../issue/{issue_key}/worklog).

    For each worklog entry (parent or child):

    Extract author.displayName, timeSpent, timeSpentSeconds, started, and comment.

    Comments may be ADF (Atlassian Document Format) objects; code calls adf_to_plain_text() to extract text. If comment is a plain string, strip it. Fall back to "No Comment".

- After processing all issues, delete the table in database and recreate it inserting all rows.
Parent worklog rows store child_key=None. Child worklogs include both parent_key and child_key

More implementation details in this [doc](https://docs.google.com/document/d/1vXMDQyXDHFkHTJeX130_yQX75rcl9C1cg4X11LROikA/edit?tab=t.0#heading=h.serjcpoaw2v3).

### Looker artifacts
Looker graphs are owned by Softvision, in particular by Paul Oniegas.

## Jira QA Requests - report_requests
The aim of tracking Jira QA Requests is to provide observability into the workload of the Mobile QA team, allowing us to understand testing demand, capacity, and how work is distributed across releases, platforms, and testing cycles.

### Table name & purpose
Tables: *ReportJiraQARequests* and *ReportJIraQARequestsNewIssueType*

Purpose: These tables store Jira QA Request data. QA Requests were represented by a single issue type (`Request`) and contained all workload-related fields (story points, platform labels, target release train).

Starting in 2025, the Jira workflow was updated to support **Internal Tasks** and **Sub-tasks** as child issues of a QA Request. As a result, workload-related data (such as story points and tested trains) now lives on child issues rather than on the parent QA Request.  
To support both historical data and the new Jira structure, we maintain:
- the existing `ReportJiraQARequests` table for legacy and high-level request tracking
- a new `ReportJIraQARequestsNewIssueType` table to capture data from Internal Tasks and Sub-tasks

### Build & update logic
QA Requests are still created by external teams and continue to represent **testing demand**, but the **actual workload** is now tracked in child issues created by the Softvision QA team:

- **Internal Tasks** or **Sub-tasks** are created under each QA Request
- These child issues contain:
  - Story Points (workload is no longer on the parent request)
  - Tested Train (`customfield_11930`, e.g. `b134`, `c134`)
  - Labels (e.g. `android-qa`, `ios-qa`, or both)
  - Issue Type (`Internal Task` or `Sub-task`)
  - Parent reference (link back to the QA Request)

Because of this structural change:
- QA Requests may not have story points or tested trains
- Workload metrics must be computed from child issues
- Parent QA Requests are still useful for volume and platform tracking

## Jira QA Requests Desktop - report_qa_requests_desktop
The aim of tracking Jira QA Requests for Desktop is to provide observability
into the workload of the Desktop QA team, allowing us to understand testing
demand, capacity, and how work is distributed across releases, products, and
engineering teams.

### Table name & purpose
Table: *ReportJiraQARequestsDesktop*

Purpose: full export of Desktop QA Request issues from Jira, including
workload fields (story points, target release, engineering team, tested
trains, product, and timeline). This table is the base dataset to build
workload and demand metrics for the Desktop QA team.

### Build & update logic

- Calls `jira.filters()` using `FILTER_ID_ALL_REQUESTS_DESKTOP` (filter ID
`24973`), fetching the following extra fields: `reporter`, `priority`,
`updated`, `issuetype`, `subtasks`, `story_points`, `firefox_release_train`,
`engineering_team`, `tested_trains`, `product`, and `timeline`.
- Payload is normalized into a DataFrame via `prepare_jira_df()`.
- If the payload is empty, a warning is logged and no database changes are
made.
- The table is cleared (`jira_delete`) and fully repopulated on every run
(delete-and-insert strategy).
- The following field transformations are applied before insertion:
- **`jira_subtasks`** – serialized from a list of objects to a
comma-separated string of issue keys (e.g. `KEY-1,KEY-2`).
- **`jira_product`** – extracted from a list; only the first value is
stored.
- **`jira_timeline`** – extracted from Atlassian Document Format (ADF) to
plain text via `extract_adf_text()`. In this field the information about deferred features is logged as, for example: Moved from Fx123 to Fx124

### Jira custom fields mapped

| Custom field | DB column | Description |
|---|---|---|
| `customfield_10037` | `jira_story_points` | Story points |
| `customfield_10155` | `jira_target_release` | Firefox Release Train / target
release |
| `customfield_10134` | `jira_engineering_team` | Engineering team |
| `customfield_11930` | `jira_tested_trains` | Tested trains |
| `customfield_10147` | `jira_product` | Product |
| `customfield_10509` | `jira_timeline` | Timeline (ADF text) |

### Looker charts & label conventions

The team uses a combination of Jira fields and team-defined labels to power
the following Looker charts. Labels and field values follow agreed naming
conventions so that Looker queries remain consistent across releases.

| Chart | Source field | Logic |
|---|---|---|
| **Total features supported** | `jira_tested_trains` | Count of features
where `Tested train/s` contains any value matching `c#`, `b#`, or `r#`
(nightly/central, beta, release). Features with documentation only use `c#(docs)`. |
| **High-priority features** | `jira_priority` | Count of features with
priority set to `High`, `Highest`, `P1`, or `P2`. |
| **Features that missed the manual QA request milestone** | `jira_labels` |
Count of features with a label matching `late-c#` (late during nightly) or
`late-b#` (late during beta), where `#` is the version number. |
| **Features that missed the tech documentation milestone** | `jira_labels` |
Count of features with a label matching `late-doc#`, where `#` is the version
number. Tracks features submitted on time whose technical documentation was
not. |
| **Features that missed the ready for QA milestone** | `jira_labels` | *(Not
final)* Count of features with a label matching `late-rdns#`, where `#` is the
version number and `rdns` stands for "readiness for QA". |
| **Features that got their target release deferred** | `jira_timeline` /
`jira_target_release` | *(Not final)* Count of features where the `Timeline`
field contains `prev. Fx#`, indicating the feature was originally planned for
a previous version. Alternatively, detect when `Target release` has been
updated from one release to the next (e.g. `FX143 → FX144`). |

> **Label format summary:**
> - `late-c#` – QA request submitted late during nightly phase
> - `late-b#` – QA request submitted late during beta phase
> - `late-doc#` – tech documentation submitted late
> - `late-rdns#` – feature missed the ready-for-QA milestone *(not final)*
> - `c# (docs)` – feature tested for documentation only


### GitHub Action
This report runs daily via the `staging-daily-desktop.yml` and
`production-daily-desktop.yaml` workflows at **04:00 UTC**, using:
--platform desktop --project firefox-desktop --report-type
jira-requests-desktop

### Looker artifacts
- Mobile Feature Testing Requests:
https://mozilla.cloud.looker.com/dashboards/1854
- iOS Feature Testing Requests:
https://mozilla.cloud.looker.com/dashboards/1846
- Android Feature Testing Requests:
https://mozilla.cloud.looker.com/dashboards/1864
- Staging Desktop
https://mozilla.cloud.looker.com/dashboards/1889
