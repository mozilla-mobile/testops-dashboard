
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
from api.testrail.db_testrail import DatabaseTestRail
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


def _db() -> DatabaseTestRail():
    global _DB 
    if _DB is None:
        _DB = DatabaseTestRail()
    return _DB


def testrail_test_results(self):
	"""Gets all the test result duration for the latest test plans
	Precondition: testrail_plans_and_runs have been run prior"""

	db = _db()

	# Get the most recent test plan ids for beta and l10n
	tp_ids = [None, None]
	for tp in db.session.query(ReportTestRailTestPlans).order_by(
			ReportTestRailTestPlans.testrail_plan_id.desc()).all():
		if "Beta" in tp.name:
			if not tp_ids[0] and "L10N" not in tp.name:
				tp_ids[0] = tp.testrail_plan_id
			elif not tp_ids[1] and "L10N" in tp.name:
				tp_ids[1] = tp.testrail_plan_id
			if tp_ids[0] and tp_ids[1]:
				break

	# Insert data for beta and refer back to test run table
	#self.db.clean_table(ReportTestRailTestResults)
	db.clean_table(ReportTestRailTestResults)
	types = ("beta", "l10n")
	for i, type in enumerate(types):
		#runs = self.get_test_plan(tp_ids[i])["entries"]
		runs = tr.get_test_plan(tp_ids[i])["entries"]

		for run in runs:
			for config in run["runs"]:
				db_run_id = db.session.query(
					ReportTestRailTestRuns).filter_by(
						testrail_run_id=config["id"]).first().id
				run_results = (
					#self.test_results_for_run(config["id"])["results"]
					tr.test_results_for_run(config["id"])["results"]
				)
				print(f"Adding all results from run {config['id']}")
				#db.report_testrail_test_result_insert(
				report_testrail_test_result_insert(
					db_run_id, run_results, type)
		print(f"Added all test results from table {type}")


def report_testrail_test_result_insert(db_run_id, payload, type):

	# insert data from payload into report_testrail_test_results table
	for result in payload:
		# Skip if not automated testing
		if result["created_by"] != 976:
			continue

		created_on = dt.convert_epoch_to_datetime(result['created_on'])

		completed_on = (
			dt.convert_epoch_to_datetime(result['completed_on'])
			if result.get('completed_on') else None
		)

		elapsed = result["elapsed"]
		if elapsed:
			if "min" in elapsed:
				parts = elapsed.split(" ")
				time = int(parts[0][:-3]) * 60 + \
					(int(parts[1][:-3]) if len(parts) > 1 else 0)
			else:
				time = elapsed[:-3]

		args = {
			'testrail_result_id': result['id'],
			'run_id': db_run_id,
			'test_id': result['test_id'],
			'elapsed': float(time),
			'status_id': result['status_id'],
			'testrail_created_on': created_on,
			'testrail_completed_on': completed_on,
			'type': type
		}

		report = ReportTestRailTestResults(**args)

		#self.session.add(report)
		db.session.add(report)
		#self.session.commit()
		db.session.commit()
		result['id'] = report.id

	return payload
