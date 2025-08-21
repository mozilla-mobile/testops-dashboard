#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from datetime import datetime

import pandas as pd

from database import (
    Database,
    ReportTestRailUsers,
)

from api.testrail.client import TestRail

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


# ===================================================================
# ORCHESTRATOR (BATCH) 
# ===================================================================

def testrail_users():
    # Step 1: Get all projects

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
    report_testrail_users_insert(df)


# ===================================================================
# DB INSERT 
# ===================================================================

def report_testrail_users_insert(payload):

    # DIAGNOSTIC
    print("Running: report_testrail_users_insert")
    print(inspect.currentframe().f_code.co_name)

    db = _db()

    for index, row in payload.iterrows():
        report = ReportTestRailUsers(
            name=row['name'],
            email=row['email'],
            status=row['status'],
            role=row['role'],
            created_at=row['created_at']
        )
        db.session.add(report)
        db.session.commit()
