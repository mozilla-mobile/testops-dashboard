#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import inspect
import logging
from datetime import datetime, timezone

from database import (
    Database,
    ReportJiraQARequestsDesktop,
)

from api.jira.client import Jira
from constants import (
    ENGINEERING_TEAM,
    FILTER_ID_ALL_REQUESTS_DESKTOP,
    FIREFOX_RELEASE_TRAIN,
    PRODUCT,
    STORY_POINTS,
    TESTED_TRAINS,
    TIMELINE,
)
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


def _parse_adf_node(node):
    """Recursively extract readable text from an ADF node."""
    if not isinstance(node, dict):
        return ''
    node_type = node.get('type', '')
    if node_type == 'text':
        return node.get('text', '').strip()
    if node_type == 'date':
        ts = node.get('attrs', {}).get('timestamp')
        if ts:
            dt = datetime.fromtimestamp(int(ts) / 1000, tz=timezone.utc)
            return dt.strftime('%Y-%m-%d')
        return ''
    if node_type == 'status':
        return node.get('attrs', {}).get('text', '')
    parts = [_parse_adf_node(c) for c in node.get('content', [])]
    parts = [p for p in parts if p]
    if node_type == 'listItem':
        return '• ' + ' '.join(parts)
    return ' '.join(parts)


def extract_adf_text(nodes):
    """Extract readable text from an ADF content list."""
    if not isinstance(nodes, list) or not nodes:
        return None
    results = [_parse_adf_node(n) for n in nodes]
    results = [r for r in results if r]
    return ' | '.join(results)


def _jira() -> Jira():
    global _JIRA
    if _JIRA is None:
        _JIRA = Jira()
    return _JIRA

# ===================================================================
# ORCHESTRATOR (BATCH)
# ===================================================================


def jira_qa_requests_desktop():
    jira = _jira()
    try:
        payload = jira.filters(
            filter_id=FILTER_ID_ALL_REQUESTS_DESKTOP,
            extra_fields=[
                "reporter",
                "priority",
                "updated",
                "issuetype",
                "subtasks",
                STORY_POINTS,
                FIREFOX_RELEASE_TRAIN,
                ENGINEERING_TEAM,
                TESTED_TRAINS,
                PRODUCT,
                TIMELINE,
            ]
        )
    except Exception as exc:
        logger.exception("Jira filters call failed %. No DB changes made.", exc)
        return

    df = prepare_jira_df(payload)

    if df.empty:
        logger.warning("Jira filtersreturned empty payload; no DB delete/insert.")
        return

    jira_delete(ReportJiraQARequestsDesktop)

    selected_columns = {
        'key': 'jira_key',
        'fields_summary': 'jira_summary',
        'fields_created': 'jira_created_at',
        'fields_updated': 'jira_updated_at',
        'fields_status_name': 'jira_status',
        'fields_assignee_emailAddress': 'jira_assignee_username',
        'fields_reporter_emailAddress': 'jira_reporter_username',
        'fields_priority_name': 'jira_priority',
        'fields_issuetype_name': 'jira_issue_type',
        'fields_labels': 'jira_labels',
        'fields_subtasks': 'jira_subtasks',
        'fields_customfield_10037': 'jira_story_points',
        'fields_customfield_10155_value': 'jira_target_release',
        'fields_customfield_10134_value': 'jira_engineering_team',
        'fields_customfield_11930': 'jira_tested_trains',
        'fields_customfield_10147': 'jira_product',
        'fields_customfield_10509_content': 'jira_timeline',
    }
    missing_inputs = [c for c in selected_columns.keys() if c not in df.columns]
    if missing_inputs:
        logger.info("Input columns are missing from Jira payload: %s", missing_inputs)

    payload = select_and_transform_jira_df(df, selected_columns)

    payload['jira_subtasks'] = payload['jira_subtasks'].apply(
        lambda x: ','.join(s['key'] for s in x) if isinstance(x, list) and x else None
    )
    payload['jira_product'] = payload['jira_product'].apply(
        lambda x: x[0]['value'] if isinstance(x, list) and x else None
    )
    payload['jira_timeline'] = payload['jira_timeline'].apply(extract_adf_text)

    # FIX: Convert pd.NA to None for MySQL compatibility
    payload = payload.astype(object).where(payload.notna(), None)

    # DIAGNOSTIC: dump raw df columns and transformed payload to CSV
    df.to_csv("desktop_raw_df.csv", index=False)
    payload.to_csv("desktop_payload.csv", index=False)
    print("DIAGNOSTIC - raw df columns:", list(df.columns))

    report_jira_qa_requests_desktop_insert(payload)


# ===================================================================
# DB INSERT
# ===================================================================


def report_jira_qa_requests_desktop_insert(payload):
    # DIAGNOSTIC
    print("--------------------------------------")
    print("Running: report_jira_qa_requests")
    print(inspect.currentframe().f_code.co_name)
    print("--------------------------------------")

    db = _db()
    print(payload)

    for index, row in payload.iterrows():
        print(row)
        report = ReportJiraQARequestsDesktop(
            jira_key=row['jira_key'],
            jira_summary=row['jira_summary'],
            jira_created_at=row['jira_created_at'],
            jira_updated_at=row['jira_updated_at'],
            jira_status=row['jira_status'],
            jira_assignee_username=row['jira_assignee_username'],
            jira_reporter_username=row['jira_reporter_username'],
            jira_priority=row['jira_priority'],
            jira_issue_type=row['jira_issue_type'],
            jira_labels=row['jira_labels'],
            jira_subtasks=row['jira_subtasks'],
            jira_story_points=row['jira_story_points'],
            jira_target_release=row['jira_target_release'],
            jira_engineering_team=row['jira_engineering_team'],
            jira_tested_trains=row['jira_tested_trains'],
            jira_product=row['jira_product'],
            jira_timeline=row['jira_timeline'])
        db.session.add(report)
    db.session.commit()
