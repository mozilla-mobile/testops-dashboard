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


def testrail_users():
    # Step 1: Get all projects
    #projects_response = self.projects()

    tr = _tr()

    projects_response = tr.projects()
    all_projects = projects_response.get("projects", [])
    all_users = []  # List of all users across all projects
    seen_project_ids = set()
    project_user_counts = {}

    for project in all_projects:
        project_id = project["id"]
        project_name = project["name"]

        # Skip duplicate project IDs
        if project_id in seen_project_ids:
            continue
        seen_project_ids.add(project_id)

        try:
            #user_response = self.users(project_id)
            user_response = tr.users(project_id)
            users = user_response.get("users", [])
            all_users.extend(users)

            unique_emails = {u.get("email") for u in users if u.get("email")}
            project_user_counts[project_name] = len(unique_emails)

            # DIAGNOSTIC
            print(
                f"{project_name} (ID: {project_id}): "
                f"{len(unique_emails)} unique users (by email)"
            )

        except Exception as e:
            print(f"Error fetching users {project_id} ({project_name}): {e}")

    # Get unique users by email
    unique_by_email = {}
    for user in all_users:
        email = user.get("email")
        if email:
            unique_by_email[email] = user

    # DIAGNOSTIC

    print(
        "\nTotal unique users across all accessible projects (by email): "
        f"{len(unique_by_email)}"
    )

    print("\nSample of unique users:")
    for email, user in list(unique_by_email.items()):
        status = "active" if user.get("is_active") else "inactive"
        print(
            f"- {user.get('name')} | {email} | {status} | role: {user.get('role')}"
        )

    created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    user_data = [
        {
            "name": user.get("name"),
            "email": user.get("email"),
            "status": "active" if user.get("is_active") else "inactive",
            "role": user.get("role"),
            "created_at": created_at
        }
        for user in unique_by_email.values()
    ]

    df = pd.DataFrame(user_data)

    #self.db.report_testrail_users_insert(df)
    report_testrail_users_insert(df)



def report_test_runs_insert(db_plan_id, suite_id, runs):

    # DIAGNOSTIC
    print("Running: DatabaseTestRail")
    print(inspect.currentframe().f_code.co_name)

    for run in runs:
        created_on = dt.convert_epoch_to_datetime(run['created_on'])
        completed_on = (
            dt.convert_epoch_to_datetime(run['completed_on'])
            if run['completed_on'] else None
        )
        total_count = (
            run['passed_count']
            + run['retest_count']
            + run['failed_count']
            + run['blocked_count']
        )

        report_run = ReportTestRailTestRuns(
            testrail_run_id=run['id'],
            plan_id=db_plan_id,
            suite_id=suite_id,
            name=run['name'],
            config=run['config'],
            test_case_passed_count=run['passed_count'],
            test_case_retest_count=run['retest_count'],
            test_case_failed_count=run['failed_count'],
            test_case_blocked_count=run['blocked_count'],
            test_case_total_count=total_count,
            testrail_created_on=created_on,
            testrail_completed_on=completed_on)
        db = _db()
        #self.session.add(report_run)
        db.session.add(report_run)
        #self.session.commit()
        db.session.commit()
