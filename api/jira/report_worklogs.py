import pandas as pd

from database import (
    Database,
    ReportJiraSoftvisionWorklogs,
)

from api.jira.client import Jira
from api.jira.helpers import jira_delete
from api.jira.utils import adf_to_plain_text
from datetime import datetime


import inspect


_DB = None
_JIRA = None


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


def jira_worklogs():
    jira = _jira()

    worklog_data = []
    issues = jira.filter_sv_parent_in_board()

    for issue in issues:
        parent_key = (issue.get("fields", {}).get("parent") or {}).get("key", issue.get("key"))  # noqa
        parent_name = issue.get("fields", {}).get("summary", "Unknown")

        parent_name = issue["fields"]["summary"]
        children = jira.filter_child_issues(parent_key)
        print(f"DIAGNOSTIC - children: {children}")

        # ---- Get worklogs for the parent itself ----
        parent_worklogs = jira.filter_worklogs(parent_key)

        for log in parent_worklogs:
            author = log["author"]["displayName"]
            time_spent = log["timeSpent"]
            time_spent_seconds = log["timeSpentSeconds"]
            started_raw = log["started"]

            raw_comment = log.get("comment")
            if isinstance(raw_comment, dict):
                comment = adf_to_plain_text(raw_comment) or "No Comment"
            elif isinstance(raw_comment, str):
                comment = raw_comment.strip() or "No Comment"
            else:
                comment = "No Comment"

            try:
                started_dt = datetime.strptime(started_raw[:19], "%Y-%m-%dT%H:%M:%S") # noqa
                started_str = started_dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception as e:
                print(f"Error parsing date {started_raw}: {e}")
                started_str = started_raw

            worklog_data.append([
                parent_key,  # parent_key
                None,        # child_key is None for parent logs
                author,
                time_spent,
                time_spent_seconds,
                started_str,
                comment,
                parent_name
            ])

        # ---- Get worklogs for each child ----
        for child in children:
            child_key = child.get("key", "Unknown")
            child_name = child.get("fields", {}).get("summary", "Unknown")

            # Skip Unknown keys to avoid 404s like issue/Unknown/worklog
            if child_key in (None, "", "Unknown"):
                print("⚠️ Skipping child without key:", child)
                continue

            child_worklogs = jira.filter_worklogs(child_key)

            for log in child_worklogs:
                author = log["author"]["displayName"]
                time_spent = log["timeSpent"]
                time_spent_seconds = log["timeSpentSeconds"]
                started_raw = log["started"]

                raw_comment = log.get("comment")
                if isinstance(raw_comment, dict):
                    comment = adf_to_plain_text(raw_comment) or "No Comment"
                elif isinstance(raw_comment, str):
                    comment = raw_comment.strip() or "No Comment"
                else:
                    comment = "No Comment"

                try:
                    started_dt = datetime.strptime(started_raw[:19], "%Y-%m-%dT%H:%M:%S") # noqa
                    started_str = started_dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception as e:
                    print(f"Error parsing date {started_raw}: {e}")
                    started_str = started_raw

                worklog_data.append([
                    parent_key,
                    child_key,
                    author,
                    time_spent,
                    time_spent_seconds,
                    started_str,
                    comment,
                    parent_name,
                    child_name
                ])

    df = pd.DataFrame(worklog_data, columns=[
            "parent_key", "child_key", "author",
            "time_spent", "time_seconds", "started_date",
            "comment", "parent_name", "child_name",
            ])

    # FIX: Replace NaN values with None for MySQL compatibility
    df = df.where(pd.notna(df), None)

    jira_delete(ReportJiraSoftvisionWorklogs)
    report_jira_worklogs_insert(df)


# ===================================================================
# DB INSERT
# ===================================================================


def report_jira_worklogs_insert(payload):
    # DIAGNOSTIC
    print("--------------------------------------")
    print("Running: report_jira_worklogs")
    print(inspect.currentframe().f_code.co_name)
    print("--------------------------------------")

    db = _db()

    for index, row in payload.iterrows():
        report = ReportJiraSoftvisionWorklogs(parent_key=row['parent_key'],
                                              child_key=row['child_key'],
                                              author=row['author'],
                                              time_spent=row['time_spent'],
                                              time_spent_seconds=row['time_seconds'], # noqa
                                              started_date=row['started_date'], # noqa
                                              comment=row['comment'],
                                              parent_name=row['parent_name'],
                                              child_name=row['child_name'],)
        db.session.add(report)
    db.session.commit()
