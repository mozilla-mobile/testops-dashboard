#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import inspect
import pandas as pd

from database import (
    Database,
)

from utils.datetime_utils import DatetimeUtils as dt
from sqlalchemy.exc import OperationalError
from typing import Dict, Any

_DB = None


def _db() -> Database():
    global _DB
    if _DB is None:
        _DB = Database()
    return _DB


def jira_delete(table):
    # DIAGNOSTIC
    print("--------------------------------------")
    print("DIAGNOSTIC: helpers")
    print("--------------------------------------")
    print(inspect.currentframe().f_code.co_name)

    db = _db()
    # Check if there is at least one row
    has_rows = db.session.query(table).first() is not None
    if not has_rows:
        print("Table is empty, skipping delete()")
        return

    try:
        db.session.query(table).delete()
        db.session.commit()
    except OperationalError as e:
        db.session.rollback()
        print(f"Delete failed with OperationalError: {e}")


def prepare_jira_df(payload: Any) -> pd.DataFrame:
    """
    Normalize Jira payload JSON into a DataFrame
    Ensure expected columns exist.
    """
    df = pd.json_normalize(payload, sep='_')

    # Ensure fields_labels exists
    if 'fields_labels' not in df.columns:
        df['fields_labels'] = [[] for _ in range(len(df))]

    # Ensure assignee email column exists
    if 'fields_assignee_emailAddress' not in df.columns:
        df['fields_assignee_emailAddress'] = pd.Series(
            ["None"] * len(df), index=df.index
        )
    else:
        df['fields_assignee_emailAddress'] = (
            df['fields_assignee_emailAddress'].fillna("Not Assigned")
        )

    # Drop alternative assignee column if present
    if 'fields_assignee' in df.columns:
        df = df.drop(columns=['fields_assignee'])

    return df


def select_and_transform_jira_df(
        df: pd.DataFrame,
        selected_columns: Dict[str, str],
) -> pd.DataFrame:
    """
    Select and rename Jira fields, apply common transformations:
    - convert created_at to UTC
    - join labels
    - normalize story points
    - convert NaN -> None
    """
    df_selected = df.reindex(columns=selected_columns.keys()).copy()
    df_selected = df_selected.rename(columns=selected_columns)

    if 'jira_created_at' in df_selected.columns:
        df_selected['jira_created_at'] = df_selected['jira_created_at'].apply(
            dt.convert_to_utc
        )

    if 'jira_updated_at' in df_selected.columns:
        df_selected['jira_updated_at'] = df_selected['jira_updated_at'].apply(
            dt.convert_to_utc
        )

    if 'jira_labels' in df_selected.columns:
        df_selected['jira_labels'] = df_selected['jira_labels'].apply(
            lambda x: ','.join(x) if isinstance(x, list) else x
        )

    if 'jira_story_points' in df_selected.columns:
        df_selected['jira_story_points'] = (
            df_selected['jira_story_points'].fillna(0).astype(int)
        )

    return df_selected.astype(object).where(pd.notnull(df_selected), None)
