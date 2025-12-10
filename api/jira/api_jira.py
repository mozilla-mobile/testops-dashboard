#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys

import pandas as pd

from lib.jira_conn import JiraAPIClient
from database import (
    Database,
    ReportJiraQARequests,
    ReportJiraQANeeded,
    ReportJIraQARequestsNewIssueType
)
from utils.datetime_utils import DatetimeUtils as dt
from constants import (
    COLUMNS_ISSUE_TYPE,
    JQL_QUERY,
    ENGINEERING_TEAM,
    DEFAULT_COLUMNS,
    FILTER_ID_ALL_REQUESTS_2022,
    FILTER_ID_ALL_REQUEST_ISSUE_TYPE,
    FILTER_ID_QA_NEEDED_iOS,
    FIREFOX_RELEASE_TRAIN,
    HOST_JIRA,
    MAX_RESULT,
    QATT_BOARD,
    QATT_PARENT_TICKETS_IN_BOARD,
    SEARCH,
    STORY_POINTS,
    TESTED_TRAINS,
    WORKLOG_URL_TEMPLATE,
)


class Jira:

    def __init__(self):
        try:

            # _url_host = os.environ['JIRA_HOST']
            _url_host = f"https://{HOST_JIRA}/rest/api/3"
            self.client = JiraAPIClient(_url_host)
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

        # TODO: remove diagnostic print
        # return self.client.get_search(query, data_type='issues')
        tmp = self.client.get_search(query, data_type='issues')
        print("function: filters")
        print(f"DIAGNOSTIC - query: {query}")
        print(f"DIAGNOSTIC - get_search: {tmp}")
        return tmp

    def filters_new_issue_type(self):
        query = SEARCH + '?' + JQL_QUERY + FILTER_ID_ALL_REQUEST_ISSUE_TYPE \
                + '&fields=' + DEFAULT_COLUMNS \
                + COLUMNS_ISSUE_TYPE + ',' + STORY_POINTS + ',' \
                + TESTED_TRAINS + '&' + MAX_RESULT
        print("function: filters_new_issue_type")
        print(f"DIAGNOSTIC - query: {query}")

        return self.client.get_search(query, data_type='issues')

    def filter_qa_needed(self):
        query = SEARCH + '?' + JQL_QUERY + FILTER_ID_QA_NEEDED_iOS \
                + '&fields=labels&' + MAX_RESULT
        # return self.client.get_search(query, data_type='issues')
        resp = self.client.get_search(query, data_type='issues')
        print("function: filter_qa_needed")
        print(f"DIAGNOSTIC - query: {query}")
        print(f"DIAGNOSTIC - get_search: {resp}")
        return resp

    def filter_sv_parent_in_board(self):
        """
        Jira v3 search using your existing JiraAPIClient.
        No self.session usage; returns the list of issues directly.
        """
        query = (
            "search/jql"
            "?jql=filter=" + QATT_BOARD +
            "&fields=summary,parent,status,labels,issuetype,assignee,reporter,created,updated,worklog"  # noqa
            "&maxResults=100&expand=names"
        )

        print("function: filter_sv_parent_in_board")
        print(f"DIAGNOSTIC - query: {query}")

        issues = self.client.get_search(query, data_type='issues')
        print(f"✅ Total issues retrieved: {len(issues)}")
        return issues

    # API: Issues
    def filter_child_issues(self, parent_key: str):
        query = SEARCH + '?' + QATT_PARENT_TICKETS_IN_BOARD + parent_key
        print("function: filter_child_issues")
        print(f"DIAGNOSTIC - query: {query}")
        return self.client.get_search(query, data_type='issues')

    # API: Worklogs
    def filter_worklogs(self, issue_key):
        query = WORKLOG_URL_TEMPLATE.format(issue_key=issue_key)
        print("function: filter_work_logs")
        print(f"DIAGNOSTIC - query: {query}")
        return self.client.get_search(query, data_type='worklogs')


class JiraClient(Jira):
    def __init__(self):
        super().__init__()
        self.db = DatabaseJira()

    def jira_qa_requests(self):
        payload = self.filters()
        print(payload)

        self.db.qa_requests_delete(ReportJiraQARequests)

        data_frame = self.db.report_jira_qa_requests_payload(payload)
        print(data_frame)

        self.db.report_jira_qa_requests_insert(data_frame)

    def jira_qa_requests_new_issue_types(self):
        payload = self.filters_new_issue_type()
        print("This is the payload returning from filter")
        print(payload)

        self.db.qa_requests_delete(ReportJIraQARequestsNewIssueType)

        data_frame = self.db.report_jira_qa_requests__new_issue_types_payload(payload) # noqa
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

    def qa_requests_delete(self, table):
        """ Wipe out all test suite data.
        NOTE: we'll renew this data from Testrail every session."""
        print("Delete entries from db first")
        self.session.query(table).delete()
        self.session.commit()

    def report_jira_qa_requests_payload(self, payload):
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

        return df_selected

    def report_jira_qa_requests__new_issue_types_payload(self, payload):
        # Normalize the JSON data
        self.session.query(ReportJIraQARequestsNewIssueType).delete()
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
                                                      jira_story_points=row['jira_story_points'], # noqa
                                                      jira_status=row['jira_status'], # noqa
                                                      jira_assignee_username=row['jira_assignee_username'], # noqa
                                                      jira_labels=row['jira_labels'], # noqa
                                                      jira_tested_train=row['jira_tested_train'], # noqa
                                                      jira_issue_type=row['jira_issue_type'], # noqa
                                                      jira_parent_link=row['jira_parent_link']) # noqa
            self.session.add(report)
        self.session.commit()

    def report_jira_qa_needed(self, payload):
        # Normalize the JSON data
        df = pd.json_normalize(payload, sep='_')
        total_rows = len(df)

        # Ensure 'fields_labels' exists
        if 'fields_labels' not in df.columns:
            df['fields_labels'] = [[] for _ in range(len(df))]

        # Join list of labels into a single string
        df['fields_labels'] = df['fields_labels'].apply(
            lambda x: ','.join(x) if isinstance(x, list)
            else (x if pd.notnull(x) else '')
        )

        # Calculate Nightly Verified label
        verified_nightly_count = df['fields_labels'].str.contains(
            'verified', case=False, na=False
        ).sum()
        not_verified_count = total_rows - verified_nightly_count

        return [total_rows, not_verified_count, verified_nightly_count]

    def report_jira_qa_needed_insert(self, payload):
        report = ReportJiraQANeeded(jira_total_qa_needed=payload[0],
                                    jira_qa_needed_not_verified=payload[1],
                                    jira_qa_needed_verified_nightly=payload[2])

        self.session.add(report)
        self.session.commit()
