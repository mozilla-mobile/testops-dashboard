#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys

from lib.jira_conn import JiraAPIClient

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
