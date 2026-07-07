#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import inspect
import logging

import pandas as pd

from database import (
    Database,
    ReportJiraSoftvisionIssuesOtherTeams,
)

from api.jira.client import Jira
from constants import (
    FILTER_ID_SOFTVISION_ISSUES_OTHER_TEAMS,
)

from api.jira.helpers import (
    categorize_labels,
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


# ===================================================================
# ORCHESTRATOR (BATCH)
# ===================================================================

def jira_softvision_issues_other_teams():
    jira = _jira()

    # NOTE: filter 35755 should restrict to terminal states (closed/done)
    # by appending `AND statusCategory = Done` to its JQL in the Jira UI,
    # so we only fetch issues whose work is finished.
    try:
        payload = jira.filters(
            filter_id=FILTER_ID_SOFTVISION_ISSUES_OTHER_TEAMS,
            extra_fields=[
                "project",
                "reporter",
                "priority",
                "updated",
                "statuscategorychangedate",
            ],
        )

    except Exception as exc:
        logger.exception(
            "Jira filters call failed: %s. No data saved.",
            exc,
        )
        return

    df = prepare_jira_df(payload)

    if df.empty:
        raise ValueError(
            "jira_softvision_issues_other_teams returned empty payload — "
            "check Jira credentials or filter."
        )

    selected_columns = {
        "key": "jira_key",

        "fields_summary": "jira_summary",

        "fields_project_key": "jira_project_key",
        "fields_project_name": "jira_project_name",

        "fields_reporter_displayName": "jira_reporter_name",
        "fields_reporter_emailAddress": "jira_reporter_username",

        "fields_status_name": "jira_status",
        "fields_priority_name": "jira_priority",

        "fields_labels": "jira_labels",

        "fields_created": "jira_created_at",
        "fields_updated": "jira_updated_at",

        "fields_statuscategorychangedate": "jira_status_changed_at",
    }

    missing_inputs = [
        c for c in selected_columns.keys()
        if c not in df.columns
    ]

    if missing_inputs:
        logger.info(
            "Input columns are missing from Jira payload: %s",
            missing_inputs,
        )

    payload = select_and_transform_jira_df(
        df,
        selected_columns,
    )

    payload["jira_status_changed_at"] = payload[
        "jira_status_changed_at"
    ].apply(
        lambda v: dt.convert_to_utc(v)
        if isinstance(v, str)
        else v
    )

    payload["jira_updated_at"] = payload[
        "jira_updated_at"
    ].apply(
        lambda v: dt.convert_to_utc(v)
        if isinstance(v, str)
        else v
    )

    # Jira pagination can return the same issue on adjacent pages when its
    # updated timestamp advances mid-scan. Dedupe by jira_key, keeping the
    # last occurrence (most likely the freshest snapshot).
    before = len(payload)
    payload = payload.drop_duplicates(subset=["jira_key"], keep="last")
    dropped = before - len(payload)
    if dropped:
        logger.warning(
            "Dropped %d duplicate jira_key rows from payload", dropped
        )

    # Derive flag columns (verified / wontfix / duplicate / invalid /
    # qa_not_actionable) from jira_labels. jira_labels itself is kept
    # intact so the full label list is still available for debugging.
    categorized = (
        payload["jira_labels"]
        .apply(categorize_labels)
        .apply(pd.Series)
    )
    payload = payload.join(categorized)

    report_jira_softvision_issues_other_teams_insert(payload)


# ===================================================================
# DB UPSERT
# ===================================================================

def report_jira_softvision_issues_other_teams_insert(payload):
    print("--------------------------------------")
    print("Running: report_jira_softvision_issues_other_teams")
    print(inspect.currentframe().f_code.co_name)
    print("--------------------------------------")

    db = _db()

    inserted = 0
    updated = 0
    skipped = 0

    try:
        for index, row in payload.iterrows():
            try:
                jira_key = row["jira_key"]

                existing = (
                    db.session.query(ReportJiraSoftvisionIssuesOtherTeams)
                    .filter_by(jira_key=jira_key)
                    .one_or_none()
                )

                remote_updated = dt.to_naive_utc(row["jira_updated_at"])

                if existing:
                    existing_updated = dt.to_naive_utc(existing.jira_updated_at)

                    if (
                        remote_updated is not None
                        and (
                            existing_updated is None
                            or remote_updated > existing_updated
                        )
                    ):
                        existing.jira_summary = row["jira_summary"]
                        existing.jira_project_key = row["jira_project_key"]
                        existing.jira_project_name = row["jira_project_name"]
                        existing.jira_reporter_name = row["jira_reporter_name"]
                        existing.jira_reporter_username = row["jira_reporter_username"]  # noqa: E501
                        existing.jira_status = row["jira_status"]
                        existing.jira_priority = row["jira_priority"]
                        existing.jira_labels = row["jira_labels"]
                        existing.jira_label_verified = row["jira_label_verified"]
                        existing.jira_label_wontfix = row["jira_label_wontfix"]
                        existing.jira_label_duplicate = row["jira_label_duplicate"]
                        existing.jira_label_invalid = row["jira_label_invalid"]
                        existing.jira_label_qa_not_actionable = row["jira_label_qa_not_actionable"]  # noqa: E501
                        existing.jira_created_at = row["jira_created_at"]
                        existing.jira_updated_at = row["jira_updated_at"]
                        existing.jira_status_changed_at = row["jira_status_changed_at"]  # noqa: E501

                        updated += 1
                    else:
                        skipped += 1
                else:
                    new_issue = ReportJiraSoftvisionIssuesOtherTeams(
                        jira_key=jira_key,
                        jira_summary=row["jira_summary"],
                        jira_project_key=row["jira_project_key"],
                        jira_project_name=row["jira_project_name"],
                        jira_reporter_name=row["jira_reporter_name"],
                        jira_reporter_username=row["jira_reporter_username"],
                        jira_status=row["jira_status"],
                        jira_priority=row["jira_priority"],
                        jira_labels=row["jira_labels"],
                        jira_label_verified=row["jira_label_verified"],
                        jira_label_wontfix=row["jira_label_wontfix"],
                        jira_label_duplicate=row["jira_label_duplicate"],
                        jira_label_invalid=row["jira_label_invalid"],
                        jira_label_qa_not_actionable=row["jira_label_qa_not_actionable"],  # noqa: E501
                        jira_created_at=row["jira_created_at"],
                        jira_updated_at=row["jira_updated_at"],
                        jira_status_changed_at=row["jira_status_changed_at"],
                    )

                    db.session.add(new_issue)
                    inserted += 1

            except KeyError as e:
                print(f"Missing key: {e} in row {index}")

        db.session.commit()

        print(
            f"Summary, inserted: {inserted}, "
            f"updated: {updated}, skipped: {skipped}"
        )

    except Exception:
        db.session.rollback()

        logger.exception(
            "Upsert failed for report_jira_softvision_issues_other_teams; "
            "rolled back. inserted=%d updated=%d skipped=%d",
            inserted,
            updated,
            skipped,
        )

        raise
