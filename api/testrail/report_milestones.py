#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sys
import pandas as pd
import numpy as np

from database import (
    Database,
    ReportTestRailMilestones,
)

from api.testrail.client import TestRail
from api.testrail.helpers import testrail_project_ids, testrail_milestones_delete
from utils.payload_utils import PayloadUtils as pl

import inspect


_DB = None
_TR = None


def _db() -> Database():
    global _DB
    if _DB is None:
        _DB = Database()
    return _DB


def _tr() -> TestRail():
    global _TR
    if _TR is None:
        _TR = TestRail()
    return _TR


def run(project, milestone_validate_closed: bool = False):

    testrail_milestones_delete()
    project_ids_list = testrail_project_ids(project)

    # TODO: this gets overwritten in conditional below (remove)
    milestones_all = pd.DataFrame()

    for project_ids in project_ids_list:

        # fetch - begin
        payload, df_selected, testrail_project_id = _fetch(project_ids, milestones_all)

        print(f"milestone_validate_closed: {milestone_validate_closed}")

        if milestone_validate_closed:
            print("NO DB INSERT")
            # TODO: initiate follow-on reporting here
        else:
            # Insert into database only if there is data
            if not df_selected.empty:
                print("DB_UPSERT")
                _db_upsert(projects_id, payload, df_selected)
            else:
                print("DB_UPSERT - NO DATA")
                print(
                    f"No milestones data to insert into database for project "
                    f"{testrail_project_id}."
                )

def _fetch(project_ids, milestones_all):

    tr = _tr()
    projects_id = project_ids[0]
    testrail_project_id = project_ids[1]
    payload = tr.milestones(testrail_project_id)

    if not payload:
        print(
            f"No milestones found for project {testrail_project_id}."
            f" Skipping..."
        )

        # Empty DataFrame to avoid errors
        milestones_all = pd.DataFrame()

    else:
        # Convert JSON to DataFrame
        milestones_all = pd.json_normalize(payload)

    # Ensure DataFrame is not empty before processing
    if milestones_all.empty:
        print(
            f"Milestones DataFrame is empty for project {testrail_project_id}."
            f"Skipping..."
        )
        # Continue to next project (if inside a loop)
    else:
        # Define selected columns
        selected_columns = {
            "id": "testrail_milestone_id",
            "name": "name",
            "started_on": "started_on",
            "is_completed": "is_completed",
            "description": "description",
            "completed_on": "completed_on",
            "url": "url"
        }

        # Select specific columns (only if they exist)
        existing_columns = [
            col for col in selected_columns.keys()
            if col in milestones_all.columns
        ]

        df_selected = milestones_all[existing_columns].rename(
            columns={
                k: v
                for k, v in selected_columns.items()
                if k in milestones_all.columns
            }
        )

        # Convert valid timestamps, leave empty ones as NaT
        if 'started_on' in df_selected.columns:
            df_selected['started_on'] = pd.to_datetime(
                df_selected['started_on'], unit='s', errors='coerce'
            )
            df_selected['started_on'] = df_selected['started_on'].replace(
                {np.nan: None}
            )

        if 'completed_on' in df_selected.columns:
            df_selected['completed_on'] = pd.to_datetime(
                df_selected['completed_on'], unit='s', errors='coerce'
            )
            df_selected['completed_on'] = df_selected['completed_on'].replace(
                {np.nan: None}
            )

        # Apply transformations only if description column exists
        if 'description' in df_selected.columns:
            df_selected['testing_status'] = df_selected['description'].apply(
                pl.extract_testing_status
            )

            desc_series = df_selected['description']
            df_selected['testing_recommendation'] = desc_series.apply(
                pl.extract_testing_recommendation
            )

        # Apply transformations only if name column exists
        if 'name' in df_selected.columns:

            df_selected['build_name'] = df_selected['name'].apply(
                pl.extract_build_name
            )

            df_selected['build_version'] = df_selected['build_name'].apply(
                pl.extract_build_version
            )

    return payload, df_selected, testrail_project_id


def _db_upsert(projects_id, payload, df_selected):

    # DIAGNOSTIC
    print("--------------------------------------")
    print("Running: report_milestones")
    print(inspect.currentframe().f_code.co_name)
    print("--------------------------------------")

    db = _db()

    for index, row in payload.iterrows():

        report = ReportTestRailMilestones(
            testrail_milestone_id=row['testrail_milestone_id'],
            projects_id=projects_id,
            name=row['name'],
            started_on=row['started_on'],
            is_completed=row['is_completed'],
            completed_on=row['completed_on'],
            description=row['description'],
            url=row['url'],
            testing_status=row['testing_status'],
            testing_recommendation=row['testing_recommendation'],
            build_name=row['build_name'],
            build_version=row['build_version']
        )
        db.session.add(report)
        db.session.commit()
