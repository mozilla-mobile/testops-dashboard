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


### Looker artifacts
- Mobile Feature Testing Requests:
https://mozilla.cloud.looker.com/dashboards/1854
- iOS Feature Testing Requests:
https://mozilla.cloud.looker.com/dashboards/1846
- Android Feature Testing Requests:
https://mozilla.cloud.looker.com/dashboards/1864
