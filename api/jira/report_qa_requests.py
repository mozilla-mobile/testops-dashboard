import inspect
import pandas as pd

from database import (
    Database,
    ReportJiraQARequests,
    ReportJIraQARequestsNewIssueType,
)

from api.jira.client import Jira
from api.jira.helpers import jira_delete
from utils.datetime_utils import DatetimeUtils as dt


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

def jira_qa_requests():
    jira = _jira()
    payload = jira.filters()

    jira_delete(ReportJiraQARequests)

    # Normalize the JSON data
    df = pd.json_normalize(payload, sep='_')

    # Ensure fields_labels exists
    if 'fields_labels' not in df.columns:
        df['fields_labels'] = [[] for _ in range(len(df))]

    # Check if 'jira_assignee_username' exists
    # if not use 'alternative_assignee_emailAddress'
    if 'fields_assignee_emailAddress' not in df.columns:
        df['fields_assignee_emailAddress'] = df.get('fields_assignee', "None") # noqa
    else:
        df['fields_assignee_emailAddress'] = df['fields_assignee_emailAddress'].fillna("Not Assigned") # noqa

    # Drop the alternative column if it exists
    if 'fields_assignee' in df.columns:
        df.drop(columns=['fields_assignee'], inplace=True)

    # Select specific columns
    selected_columns = {
        'key': 'jira_key',
        'fields_summary': 'jira_summary',
        'fields_created': 'jira_created_at',
        'fields_customfield_10155_value': 'jira_firefox_release_train',
        'fields_customfield_10134_value': 'jira_engineering_team',
        'fields_customfield_10037': 'jira_story_points',
        'fields_status_name': 'jira_status',
        'fields_assignee_emailAddress': 'jira_assignee_username',
        'fields_labels': 'jira_labels'
    }

    # Select specific columns
    df_selected = df[selected_columns.keys()]

    # Rename columns
    df_selected = df_selected.rename(columns=selected_columns)

    df_selected['jira_created_at'] = df_selected['jira_created_at'].apply(dt.convert_to_utc) # noqa

    # Join list of labels into a single string
    df_selected['jira_labels'] = df_selected['jira_labels'].apply(lambda x: ','.join(x) if isinstance(x, list) else x) # noqa

    # Convert NaN values to 0 and ensure the column is of type int
    df_selected['jira_story_points'] = df_selected['jira_story_points'].fillna(0).astype(int) # noqa

    df_selected
    print(df_selected)

    report_jira_qa_requests_insert(df_selected)

def jira_qa_requests_new_issue_types():
    jira = _jira()
    payload = jira.filters_new_issue_type()

    jira_delete(ReportJIraQARequestsNewIssueType)
    df = pd.json_normalize(payload, sep='_')

    # Ensure fields_labels exists
    if 'fields_labels' not in df.columns:
        df['fields_labels'] = [[] for _ in range(len(df))]

    # Check if 'jira_assignee_username' exists
    # if not use 'alternative_assignee_emailAddress'
    if 'fields_assignee_emailAddress' not in df.columns:
        df['fields_assignee_emailAddress'] = df.get('fields_assignee', "None") # noqa
    else:
        df['fields_assignee_emailAddress'] = df['fields_assignee_emailAddress'].fillna("Not Assigned") # noqa

    # Drop the alternative column if it exists
    if 'fields_assignee' in df.columns:
        df.drop(columns=['fields_assignee'], inplace=True)

    # Select specific columns
    selected_columns = {
        'key': 'jira_key',
        'fields_summary': 'jira_summary',
        'fields_created': 'jira_created_at',
        'fields_customfield_10037': 'jira_story_points',
        'fields_status_name': 'jira_status',
        'fields_assignee_emailAddress': 'jira_assignee_username',
        'fields_labels': 'jira_labels',
        'fields_customfield_11930': 'jira_tested_train',
        'fields_issuetype_name': 'jira_issue_type',
        'fields_parent_key': 'jira_parent_link'
    }

    # Select specific columns
    df_selected = df[selected_columns.keys()]
    print(df_selected)

    # Rename columns
    df_selected = df_selected.rename(columns=selected_columns)

    df_selected['jira_created_at'] = df_selected['jira_created_at'].apply(dt.convert_to_utc) # noqa

    # Join list of labels into a single string
    df_selected['jira_labels'] = df_selected['jira_labels'].apply(lambda x: ','.join(x) if isinstance(x, list) else x) # noqa

    # Convert NaN values to 0 and ensure the column is of type int
    df_selected['jira_story_points'] = df_selected['jira_story_points'].fillna(0).astype(int) # noqa

    df_selected = df_selected.where(pd.notnull(df_selected), None)

    
    print(df_selected)    
    report_jira_qa_requests_new_issue_types_insert(df_selected)

# ===================================================================
# DB INSERT
# ===================================================================


def report_jira_qa_requests_insert(payload):
    db = _db()
    print(payload)

    for index, row in payload.iterrows():
        print(row)
        report = ReportJiraQARequests(jira_key=row['jira_key'],
                                      jira_created_at=row['jira_created_at'].date(), # noqa
                                      jira_summary=row['jira_summary'], # noqa
                                      jira_firefox_release_train=row['jira_firefox_release_train'], # noqa
                                      jira_engineering_team=row['jira_engineering_team'], # noqa
                                      jira_story_points=row['jira_story_points'], # noqa
                                      jira_status=row['jira_status'], # noqa
                                      jira_assignee_username=row['jira_assignee_username'], # noqa
                                      jira_labels=row['jira_labels'])
        db.session.add(report)
    db.session.commit()

def report_jira_qa_requests_new_issue_types_insert(payload):
    db = _db()
    print(payload)

    for index, row in payload.iterrows():
        print(row)
        report = ReportJIraQARequestsNewIssueType(jira_key=row['jira_key'],
                                                  jira_created_at=row['jira_created_at'].date(), # noqa
                                                  jira_summary=row['jira_summary'], # noqa
                                                  jira_story_points=row['jira_story_points'], # noqa
                                                  jira_status=row['jira_status'], # noqa
                                                  jira_assignee_username=row['jira_assignee_username'], # noqa
                                                  jira_labels=row['jira_labels'], # noqa
                                                  jira_tested_train=row['jira_tested_train'], # noqa
                                                  jira_issue_type=row['jira_issue_type'], # noqa
                                                  jira_parent_link=row['jira_parent_link']) # noqa
        db.session.add(report)
    db.session.commit()
