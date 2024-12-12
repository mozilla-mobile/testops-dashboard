#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys

from datetime import datetime

import pandas as pd

from lib.jira_conn import JiraAPIClient
from database import (
    Database,
    ReportJiraQARequests,
    ReportJiraQANeeded,
    ReportJiraSoftvisionWorklogs,
    ReportJIraQARequestsNewIssueType
)
from utils.datetime_utils import DatetimeUtils as dt
from constants import FILTER_ID_ALL_REQUESTS_2022, MAX_RESULT
from constants import FILTER_ID_QA_NEEDED_iOS
from constants import QATT_FIELDS, QATT_BOARD, QATT_PARENT_TICKETS_IN_BOARD # noqa
from constants import SEARCH, WORKLOG_URL_TEMPLATE
# JQL query All QA Requests since 2022 filter_id: 13856
# Extra fields needed
STORY_POINTS = "customfield_10037"
FIREFOX_RELEASE_TRAIN = "customfield_10155"
ENGINEERING_TEAM = "customfield_10134"
DEFAULT_COLUMNS = "id,key,status,created,summary,labels,assignee"
DEFAULT_COLUMNS_ISSUE_TYPE = "id,key,status,created,summary,labels,assignee,issuetype,parent"
TESTED_TRAINS = "customfield_11930"

NEW_FILTER_ID = "14266"

JQL_QUERY = 'jql=filter='


class Jira:

    def __init__(self):
        try:
            # Change in github secrets: remove last part
            JIRA_HOST = os.environ['JIRA_HOST']
            self.client = JiraAPIClient(JIRA_HOST)
            self.client.user = os.environ['JIRA_USER']
            self.client.password = os.environ['JIRA_PASSWORD']

        except KeyError:
            print("ERROR: Missing jira env var")
            sys.exit(1)

    # API: Filters
    def filters(self):
        query = SEARCH + '?' + JQL_QUERY + FILTER_ID_ALL_REQUESTS_2022 \
                + '&fields=' \
                + DEFAULT_COLUMNS + ',' + STORY_POINTS + ',' \
                + FIREFOX_RELEASE_TRAIN + ',' \
                + ENGINEERING_TEAM + '&' + MAX_RESULT

        return self.client.get_search(query, data_type='issues')

    def filters_new_issue_type(self):
        query = JQL_QUERY + NEW_FILTER_ID + '&fields=' \
                + DEFAULT_COLUMNS_ISSUE_TYPE + ',' + STORY_POINTS + ',' \
                + FIREFOX_RELEASE_TRAIN + ',' + TESTED_TRAINS + ',' \
                + ENGINEERING_TEAM + '&' + MAX_RESULT

        return self.client.get_search(query)

    def filter_qa_needed(self):
        query = SEARCH + '?' + JQL_QUERY + FILTER_ID_QA_NEEDED_iOS \
                + '&' + MAX_RESULT
        return self.client.get_search(query, data_type='issues')

    def filter_sv_parent_in_board(self):
        query = SEARCH + '?' + JQL_QUERY + QATT_BOARD + '&' + QATT_FIELDS
        return self.client.get_search(query, data_type='issues')

    # API: Issues
    def filter_child_issues(self, parent_key):
        query = SEARCH + '?' + QATT_PARENT_TICKETS_IN_BOARD + parent_key
        return self.client.get_search(query, data_type='issues')

    # API: Worklogs
    def filter_worklogs(self, issue_key):
        query = WORKLOG_URL_TEMPLATE.format(issue_key=issue_key)
        return self.client.get_search(query, data_type='worklogs')


class JiraClient(Jira):
    def __init__(self):
        super().__init__()
        self.db = DatabaseJira()

    def jira_softvision_worklogs(self):
        worklog_data = []
        issues = self.filter_sv_parent_in_board()

        for issue in issues:
            parent_key = issue["key"]
            parent_name = issue["fields"]["summary"]
            children = self.filter_child_issues(parent_key)

            # ---- Get worklogs for the parent itself ----
            parent_worklogs = self.filter_worklogs(parent_key)

            for log in parent_worklogs:
                author = log["author"]["displayName"]
                time_spent = log["timeSpent"]
                time_spent_seconds = log["timeSpentSeconds"]
                started_raw = log["started"]

                comment = log.get("comment", "")
                if not isinstance(comment, str) or comment.strip() == "":
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
                child_worklogs = self.filter_worklogs(child_key)

                for log in child_worklogs:
                    author = log["author"]["displayName"]
                    time_spent = log["timeSpent"]
                    time_spent_seconds = log["timeSpentSeconds"]
                    started_raw = log["started"]

                    comment = log.get("comment", "")
                    if not isinstance(comment, str) or comment.strip() == "":
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
            "parent_key", "child_key", "author", "time_spent", "time_seconds", "started_date", "comment", "parent_name", "child_name" # noqa
        ])

        self.db.jira_worklogs_delete()
        self.db.report_jira_sv_worklogs_insert(df)

    def jira_qa_requests(self):
        payload = self.filters()
        print(payload)

        self.db.qa_requests_delete()

        data_frame = self.db.report_jira_qa_requests_payload(payload)
        print(data_frame)

        self.db.report_jira_qa_requests_insert(data_frame)

    def jira_qa_requests_new_issue_types(self):
        payload = self.filters_new_issue_type()
        print("This is the payload returning from filter")
        print(payload)

        self.db.qa_requests_delete()

        data_frame = self.db.report_jira_qa_requests__new_issue_types_payload(payload)
        print(data_frame)

        self.db.report_jira_qa_requests_insert_new_issue_types(data_frame)

    def jira_qa_needed(self):
        payload = self.filter_qa_needed()
        data_frame = self.db.report_jira_qa_needed(payload)
        print(data_frame)

        self.db.report_jira_qa_needed_insert(data_frame)


class DatabaseJira(Database):

    def __init__(self):
        super().__init__()
        self.db = Database()

    def qa_requests_delete(self):
        """ Wipe out all test suite data.
        NOTE: we'll renew this data from Testrail every session."""
        print("Delete entries from db first")
        self.session.query(ReportJiraQARequests).delete()
        self.session.commit()

    def report_jira_qa_requests_payload(self, payload):
        # Normalize the JSON data
        df = pd.json_normalize(payload, sep='_')

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

        return df_selected

    def report_jira_qa_requests__new_issue_types_payload(self, payload):
        # Normalize the JSON data
        df = pd.json_normalize(payload, sep='_')

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
            'fields_labels': 'jira_labels',
            'fields_customfield_11930': 'jira_tested_train',
            'fields_issuetype_name':'jira_issue_type',
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

        return df_selected

    def report_jira_qa_requests_insert(self, payload):
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
            self.session.add(report)
        self.session.commit()

    def report_jira_qa_requests_insert_new_issue_types(self, payload):
        print(payload)

        for index, row in payload.iterrows():
            print(row)
            report = ReportJIraQARequestsNewIssueType(jira_key=row['jira_key'],
                                          jira_created_at=row['jira_created_at'].date(), # noqa
                                          jira_summary=row['jira_summary'], # noqa
                                          jira_firefox_release_train=row['jira_firefox_release_train'], # noqa
                                          jira_engineering_team=row['jira_engineering_team'], # noqa
                                          jira_story_points=row['jira_story_points'], # noqa
                                          jira_status=row['jira_status'], # noqa
                                          jira_assignee_username=row['jira_assignee_username'], # noqa
                                          jira_labels=row['jira_labels'],
                                          jira_tested_train=row['jira_tested_train'],
                                          jira_issue_type=row['jira_issue_type'],
                                          jira_parent_link=row['jira_parent_link']
                                    )
            self.session.add(report)
        self.session.commit()

    def report_jira_qa_needed(self, payload):
        # Normalize the JSON data
        df = pd.json_normalize(payload, sep='_')
        total_rows = len(df)

        # Join list of labels into a single string
        jira_labels = df['fields_labels'] = df['fields_labels'].apply(lambda x: ','.join(x) if isinstance(x, list) else x) # noqa
        # Calculate Nightly Verified label
        verified_nightly_count = jira_labels.str.contains('verified', case=False, na=False).sum() # noqa

        not_verified_count = total_rows - verified_nightly_count

        data = [total_rows, not_verified_count, verified_nightly_count]
        return data

    def report_jira_qa_needed_insert(self, payload):
        report = ReportJiraQANeeded(jira_total_qa_needed=payload[0],
                                    jira_qa_needed_not_verified=payload[1],
                                    jira_qa_needed_verified_nightly=payload[2])

        self.session.add(report)
        self.session.commit()

    def report_jira_sv_worklogs_insert(self, payload):
        for index, row in payload.iterrows():
            report = ReportJiraSoftvisionWorklogs(parent_key=row['parent_key'],
                                                  child_key=row['child_key'],
                                                  author=row['author'],
                                                  time_spent=row['time_spent'],
                                                  time_spent_seconds=row['time_seconds'], # noqa
                                                  started_date=row['started_date'], # noqa
                                                  comment=row['comment'],
                                                  parent_name=row['parent_name'], # noqa
                                                  child_name=row['child_name'],) # noqa
            self.session.add(report)
        self.session.commit()

    def jira_worklogs_delete(self):
        self.session.query(ReportJiraSoftvisionWorklogs).delete()
        self.session.commit()
