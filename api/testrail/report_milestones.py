
#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys
from datetime import datetime

import pandas as pd
import numpy as np

from lib.testrail_conn import APIClient

from database import (
    Database,
    Projects,
    TestSuites,
    ReportTestCaseCoverage,
    ReportTestRailMilestones,
    ReportTestRailUsers,
    ReportTestRailTestPlans,
    ReportTestRailTestRuns,
    ReportTestRailTestResults,
)

from api.testrail.client import TestRail
from api.testrail.helpers import testrail_project_ids 
from utils.datetime_utils import DatetimeUtils as dt
from utils.payload_utils import PayloadUtils as pl

import inspect

_TR = None
_DB = None


def _tr() -> TestRail():
    global _TR 
    if _TR is None:
        _TR = TestRail()
    return _TR 


def _db() -> Database():
    global _DB 
    if _DB is None:
        _DB = Database()
    return _DB


def testrail_milestones_delete():
    # DIAGNOSTIC
    print("Running: report_milestones")
    print(inspect.currentframe().f_code.co_name)

    db = _db()

    #self.session.query(ReportTestRailMilestones).delete()
    db.session.query(ReportTestRailMilestones).delete()
    #self.session.commit()
    db.session.commit()


def testrail_milestones(project):

	db = _db()

	#self.db.testrail_milestones_delete()
	db.testrail_milestones_delete()

	#project_ids_list = self.testrail_project_ids(project)
	project_ids_list = testrail_project_ids(project)
	milestones_all = pd.DataFrame()

	for project_ids in project_ids_list:
		projects_id = project_ids[0]
		testrail_project_id = project_ids[1]

		#payload = self.milestones(testrail_project_id)
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

			# Insert into database only if there is data
			if not df_selected.empty:
				#self.db.report_milestones_insert(projects_id, df_selected)
                # TODO: remove db. after putting function here
				db.report_milestones_insert(projects_id, df_selected)
			else:
				print(
					f"No milestones data to insert into database for project "
					f"{testrail_project_id}."
				)



def report_milestones_insert(projects_id, payload):

    # DIAGNOSTIC
    print("--------------------------------------")
    print("Running: report_milestones")
    print(inspect.currentframe().f_code.co_name)
    print("--------------------------------------")

    db = _db()

    for index, row in payload.iterrows():
        # print(row)

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
        #self.session.add(report)
        db.session.add(report)
        #self.session.commit()
        db.session.commit()
