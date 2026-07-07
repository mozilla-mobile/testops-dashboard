#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import inspect
import logging

from database import (
    Database,
    ReportJiraSoftvisionIssuesQATeams,
)

from api.jira.client import Jira
from constants import (
    FILTER_ID_SOFTVISION_ISSUES_QA_TEAMS,
)
from api.jira.helpers import (
    prepare_jira_df,
    select_and_transform_jira_df,
)
from utils.datetime_utils import DatetimeUtils as dt


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


def _extract_linked_issue_keys(links):
    if not isinstance(links, list) or not links:
        return None
    keys = []
    for link in links:
        outward = link.get('outwardIssue') if isinstance(link, dict) else None
        inward = link.get('inwardIssue') if isinstance(link, dict) else None
        if outward:
            keys.append(outward.get('key'))
        if inward:
            keys.append(inward.get('key'))
    joined = ','.join(k for k in keys if k)
    return joined or None


# ===================================================================
# ORCHESTRATOR (BATCH)
# ===================================================================


def jira_softvision_issues_qa_teams():
    jira = _jira()
    try:
        payload = jira.filters(
            filter_id=FILTER_ID_SOFTVISION_ISSUES_QA_TEAMS,
            extra_fields=[
                "project",
                "reporter",
                "priority",
                "issuelinks",
                "statuscategorychangedate",
            ],
        )
    except Exception as exc:
        logger.exception("Jira filters call failed: %s. No DB changes made.", exc)
        return

    df = prepare_jira_df(payload)

    if df.empty:
        raise ValueError(
            "jira_softvision_issues_qa_teams returned empty payload — "
            "check Jira credentials or filter. Database was not modified."
        )

    selected_columns = {
        'key': 'jira_key',
        'fields_summary': 'jira_summary',
        'fields_project_key': 'jira_project_key',
        'fields_project_name': 'jira_project_name',
        'fields_reporter_displayName': 'jira_reporter_name',
        'fields_reporter_emailAddress': 'jira_reporter_username',
        'fields_status_name': 'jira_status',
        'fields_priority_name': 'jira_priority',
        'fields_labels': 'jira_labels',
        'fields_issuelinks': 'jira_linked_issues',
        'fields_created': 'jira_created_at',
        'fields_statuscategorychangedate': 'jira_status_changed_at',
    }
    missing_inputs = [c for c in selected_columns.keys() if c not in df.columns]
    if missing_inputs:
        logger.info("Input columns are missing from Jira payload: %s", missing_inputs)

    payload = select_and_transform_jira_df(df, selected_columns)

    payload['jira_linked_issues'] = payload['jira_linked_issues'].apply(
        _extract_linked_issue_keys
    )

    # select_and_transform_jira_df only converts jira_created_at / jira_updated_at
    # to UTC. Convert jira_status_changed_at manually so MySQL accepts it.
    payload['jira_status_changed_at'] = payload['jira_status_changed_at'].apply(
        lambda v: dt.convert_to_utc(v) if isinstance(v, str) else v
    )

    # Jira pagination can return the same issue on adjacent pages when its
    # statusCategoryChangedDate is updated mid-scan. Dedupe by jira_key,
    # keeping the last occurrence (most likely the freshest snapshot).
    before = len(payload)
    payload = payload.drop_duplicates(subset=['jira_key'], keep='last')
    dropped = before - len(payload)
    if dropped:
        logger.warning(
            "Dropped %d duplicate jira_key rows from payload", dropped
        )

    report_jira_softvision_issues_qa_teams_insert(payload)


# ===================================================================
# DB UPSERT
# ===================================================================


def report_jira_softvision_issues_qa_teams_insert(payload):
    # DIAGNOSTIC
    print("--------------------------------------")
    print("Running: report_jira_softvision_issues_qa_teams")
    print(inspect.currentframe().f_code.co_name)
    print("--------------------------------------")

    db = _db()
    inserted = 0
    updated = 0
    skipped = 0

    try:
        for index, row in payload.iterrows():
            try:
                jira_key = row['jira_key']

                existing = (
                    db.session.query(ReportJiraSoftvisionIssuesQATeams)
                    .filter_by(jira_key=jira_key)
                    .one_or_none()
                )

                status_changed_remote = dt.to_naive_utc(row['jira_status_changed_at'])

                linked = (
                    row['jira_linked_issues']
                    if isinstance(row['jira_linked_issues'], str) else None
                )

                if existing:
                    status_changed_existing = dt.to_naive_utc(
                        existing.jira_status_changed_at
                    )
                    if (
                        status_changed_remote is not None
                        and (
                            status_changed_existing is None
                            or status_changed_remote > status_changed_existing
                        )
                    ):
                        existing.jira_summary = row['jira_summary']
                        existing.jira_project_key = row['jira_project_key']
                        existing.jira_project_name = row['jira_project_name']
                        existing.jira_reporter_name = row['jira_reporter_name']
                        existing.jira_reporter_username = row['jira_reporter_username']
                        existing.jira_status = row['jira_status']
                        existing.jira_priority = row['jira_priority']
                        existing.jira_labels = row['jira_labels']
                        existing.jira_linked_issues = linked
                        existing.jira_created_at = row['jira_created_at']
                        existing.jira_status_changed_at = row['jira_status_changed_at']
                        updated += 1
                    else:
                        skipped += 1
                else:
                    new_issue = ReportJiraSoftvisionIssuesQATeams(
                        jira_key=jira_key,
                        jira_summary=row['jira_summary'],
                        jira_project_key=row['jira_project_key'],
                        jira_project_name=row['jira_project_name'],
                        jira_reporter_name=row['jira_reporter_name'],
                        jira_reporter_username=row['jira_reporter_username'],
                        jira_status=row['jira_status'],
                        jira_priority=row['jira_priority'],
                        jira_labels=row['jira_labels'],
                        jira_linked_issues=linked,
                        jira_created_at=row['jira_created_at'],
                        jira_status_changed_at=row['jira_status_changed_at'],
                    )
                    db.session.add(new_issue)
                    inserted += 1

            except KeyError as e:
                print(f"Missing key: {e} in row {index}")

        db.session.commit()
        print(f"Summary, inserted: {inserted}, updated: {updated}, skipped: {skipped}")
    except Exception:
        # Roll back so a mid-loop failure doesn't leave pending writes
        # in the session for a later commit to flush.
        db.session.rollback()
        logger.exception(
            "Upsert failed for report_jira_softvision_issues_qa_teams; "
            "rolled back. inserted=%d updated=%d skipped=%d",
            inserted, updated, skipped,
        )
        raise
