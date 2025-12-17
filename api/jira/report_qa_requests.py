#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import inspect
import logging

from database import (
    Database,
    ReportJiraQARequests,
    ReportJIraQARequestsNewIssueType,
)

from api.jira.client import Jira
from api.jira.helpers import (
    jira_delete,
    prepare_jira_df,
    select_and_transform_jira_df
)


_DB = None
_JIRA = None
logger = logging.getLogger(__name__)


def _db() -> Database():
    global _DB
    if _DB is None:
        _DB = Database()
    return _DB


def _jira() -> Jira():
    global _JIRA
    if _JIRA is None:
        _JIRA = Jira()
    return _JIRA

# ===================================================================
# ORCHESTRATOR (BATCH)
# ===================================================================


def jira_qa_requests():
    jira = _jira()
    try:
        payload = jira.filters()
    except Exception as exc:
        logger.exception("Jira filters call failed %. No DB changes made.", exc)
        return

    df = prepare_jira_df(payload)

    if df.empty:
        logger.warning("Jira filtersreturned empty payload; no DB delete/insert.")
        return

    jira_delete(ReportJiraQARequests)

    selected_columns = {
        'key': 'jira_key',
        'fields_summary': 'jira_summary',
        'fields_created': 'jira_created_at',
        'fields_customfield_10155_value': 'jira_firefox_release_train',
        'fields_customfield_10134_value': 'jira_engineering_team',
        'fields_customfield_10037': 'jira_story_points',
        'fields_status_name': 'jira_status',
        'fields_assignee_emailAddress': 'jira_assignee_username',
        'fields_labels': 'jira_labels'
    }
    missing_inputs = [c for c in selected_columns.keys() if c not in df.columns]
    if missing_inputs:
        logger.info("Input columns are missing from Jira payload: %s", missing_inputs)

    payload = select_and_transform_jira_df(df, selected_columns)
    report_jira_qa_requests_insert(payload)


def jira_qa_requests_new_issue_types():
    jira = _jira()

    try:
        payload = jira.filters_new_issue_type()
    except Exception as exc:
        logger.exception("Jira filters call failed %. No DB changes made.", exc)
        return

    df = prepare_jira_df(payload)

    if df.empty:
        logger.warning("Empty payload; skipping DB delete/insert.")
        return

    jira_delete(ReportJIraQARequestsNewIssueType)

    selected_columns = {
        'key': 'jira_key',
        'fields_summary': 'jira_summary',
        'fields_created': 'jira_created_at',
        'fields_customfield_10037': 'jira_story_points',
        'fields_status_name': 'jira_status',
        'fields_assignee_emailAddress': 'jira_assignee_username',
        'fields_labels': 'jira_labels',
        'fields_customfield_11930': 'jira_tested_train',
        'fields_issuetype_name': 'jira_issue_type',
        'fields_parent_key': 'jira_parent_link'
    }
    missing_inputs = [c for c in selected_columns.keys() if c not in df.columns]
    if missing_inputs:
        logger.info("Input columns are missing from Jira payload: %s", missing_inputs)

    payload = select_and_transform_jira_df(df, selected_columns)
    print(payload)
    report_jira_qa_requests_new_issue_types_insert(payload)

# ===================================================================
# DB INSERT
# ===================================================================


def report_jira_qa_requests_insert(payload):
    # DIAGNOSTIC
    print("--------------------------------------")
    print("Running: report_jira_qa_requests")
    print(inspect.currentframe().f_code.co_name)
    print("--------------------------------------")

    db = _db()
    print(payload)

    for index, row in payload.iterrows():
        print(row)
        report = ReportJiraQARequests(jira_key=row['jira_key'],
                                      jira_created_at=row['jira_created_at'].date(), # noqa
                                      jira_summary=row['jira_summary'], # noqa
                                      jira_firefox_release_train=row['jira_firefox_release_train'], # noqa
                                      jira_engineering_team=row['jira_engineering_team'], # noqa
                                      jira_story_points=row['jira_story_points'], # noqa
                                      jira_status=row['jira_status'], # noqa
                                      jira_assignee_username=row['jira_assignee_username'], # noqa
                                      jira_labels=row['jira_labels'])
        db.session.add(report)
    db.session.commit()


def report_jira_qa_requests_new_issue_types_insert(payload):
    # DIAGNOSTIC
    print("--------------------------------------")
    print("Running: report_jira_qa_requests_new_issue_types")
    print(inspect.currentframe().f_code.co_name)
    print("--------------------------------------")

    db = _db()
    print(payload)

    for index, row in payload.iterrows():
        print(row)
        report = ReportJIraQARequestsNewIssueType(jira_key=row['jira_key'],
                                                  jira_created_at=row['jira_created_at'].date(), # noqa
                                                  jira_summary=row['jira_summary'], # noqa
                                                  jira_story_points=row['jira_story_points'], # noqa
                                                  jira_status=row['jira_status'], # noqa
                                                  jira_assignee_username=row['jira_assignee_username'], # noqa
                                                  jira_labels=row['jira_labels'], # noqa
                                                  jira_tested_train=row['jira_tested_train'], # noqa
                                                  jira_issue_type=row['jira_issue_type'], # noqa
                                                  jira_parent_link=row['jira_parent_link']) # noqa
        db.session.add(report)
    db.session.commit()
