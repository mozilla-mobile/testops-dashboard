#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import unittest
import requests

from unittest.mock import MagicMock, patch
from lib.jira_conn import JiraAPIClient
from constants import HOST_JIRA

JIRA_HOST = f"https://{HOST_JIRA}/rest/api/3/"


class TestsJiraAPIClient(unittest.TestCase):
    def setUp(self):
        self.client = JiraAPIClient(JIRA_HOST)
        self.client.user = ""
        self.client.password = ""

    @patch("lib.jira_conn.requests.get")
    def test_get_search_enhanced_no_fields_no_params(self, mock_get):
        page = {"issues": [], "isLast": True}
        mock_get.return_value = MagicMock(status_code=200, json=lambda: page)

        query = "search/jql?jql=project=MTE"
        self.client.get_search(query, "issues")
        params_used = mock_get.call_args.kwargs["params"]
        self.assertEqual(params_used["fields"], "key,summary")

    @patch("lib.jira_conn.requests.get")
    def test_get_search_url_construction(self, mock_get):
        """Test that full URL is constructed correctly"""
        page = {"issues": [], "isLast": True}
        mock_get.return_value = MagicMock(status_code=200, json=lambda: page)

        query = "search/jql?jql=project=MTE"
        self.client.get_search(query, "issues")

        # Verify the full URL passed to requests.get
        called_url = mock_get.call_args.args[0]
        expected_url = f"{JIRA_HOST}search/jql?jql=project=MTE"
        self.assertEqual(called_url, expected_url)

    @patch("lib.jira_conn.requests.get")
    def test_get_search_enhanced_with_fields_in_query(self, mock_get):
        """Test that fields param is not added if already in query"""
        page = {"issues": [], "isLast": True}
        mock_get.return_value = MagicMock(status_code=200, json=lambda: page)

        query = "search/jql?jql=project=MTE&fields=key,status,assignee"
        self.client.get_search(query, "issues")
        params_used = mock_get.call_args.kwargs["params"]
        # Should not override fields since it's already in query
        self.assertNotIn("fields", params_used)

    @patch("lib.jira_conn.requests.get")
    def test_get_search_enhanced_pagination(self, mock_get):
        """Test pagination with multiple pages using nextPageToken"""
        page1 = {
            "issues": [{"key": "MTE-1"}, {"key": "MTE-2"}],
            "nextPageToken": "token123",
            "isLast": False
        }
        page2 = {
            "issues": [{"key": "MTE-3"}],
            "isLast": True
        }
        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: page1),
            MagicMock(status_code=200, json=lambda: page2)
        ]

        query = "search/jql?jql=project=MTE"
        results = self.client.get_search(query, "issues")

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["key"], "MTE-1")
        self.assertEqual(results[2]["key"], "MTE-3")
        self.assertEqual(mock_get.call_count, 2)

        # Check that second call includes nextPageToken
        second_call_params = mock_get.call_args_list[1].kwargs["params"]
        self.assertEqual(second_call_params["nextPageToken"], "token123")

    @patch("lib.jira_conn.requests.get")
    def test_get_search_enhanced_stops_on_empty_results(self, mock_get):
        """Test that pagination stops when no items are returned"""
        page = {"issues": [], "isLast": False, "nextPageToken": "token123"}
        mock_get.return_value = MagicMock(status_code=200, json=lambda: page)

        query = "search/jql?jql=project=MTE"
        results = self.client.get_search(query, "issues")

        self.assertEqual(len(results), 0)
        self.assertEqual(mock_get.call_count, 1)

    @patch("lib.jira_conn.requests.get")
    def test_get_search_enhanced_raises_on_invalid_data_type(self, mock_get):
        """Test that KeyError is raised when data_type is not a list"""
        page = {"issues": "not a list", "isLast": True}
        mock_get.return_value = MagicMock(status_code=200, json=lambda: page)

        query = "search/jql?jql=project=MTE"

        with self.assertRaises(KeyError) as context:
            self.client.get_search(query, "issues")
        self.assertIn("Expected list", str(context.exception))

    @patch("lib.jira_conn.requests.get")
    def test_get_search_worklog_url_construction(self, mock_get):
        """Test that worklog URL is constructed correctly"""
        response = {"worklogs": [], "total": 0, "maxResults": 100}
        mock_get.return_value = MagicMock(status_code=200, json=lambda: response)

        query = "issue/MTE-123/worklog"
        self.client.get_search(query, "worklogs")

        # Verify the full URL passed to requests.get
        called_url = mock_get.call_args.args[0]
        expected_url = f"{JIRA_HOST}issue/MTE-123/worklog"
        self.assertEqual(called_url, expected_url)

    @patch("lib.jira_conn.requests.get")
    def test_get_search_worklog_single_page(self, mock_get):
        """Test worklog endpoint with single page"""
        response = {
            "worklogs": [
                {"id": "1", "timeSpent": "1h"},
                {"id": "2", "timeSpent": "2h"}
            ],
            "total": 2,
            "maxResults": 100
        }
        mock_get.return_value = MagicMock(status_code=200, json=lambda: response)

        query = "issue/MTE-123/worklog"
        results = self.client.get_search(query, "worklogs")

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["id"], "1")
        self.assertEqual(mock_get.call_count, 1)

    @patch("lib.jira_conn.requests.get")
    def test_get_search_worklog_pagination(self, mock_get):
        """Test worklog endpoint with multiple pages"""
        page1 = {
            "worklogs": [{"id": str(i)} for i in range(100)],
            "total": 150,
            "maxResults": 100
        }
        page2 = {
            "worklogs": [{"id": str(i)} for i in range(100, 150)],
            "total": 150,
            "maxResults": 100
        }
        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: page1),
            MagicMock(status_code=200, json=lambda: page2)
        ]

        query = "issue/MTE-123/worklog"
        results = self.client.get_search(query, "worklogs")

        self.assertEqual(len(results), 150)
        self.assertEqual(mock_get.call_count, 2)

        # Verify startAt parameter in second call
        second_call_params = mock_get.call_args_list[1].kwargs["params"]
        self.assertEqual(second_call_params["startAt"], 100)

    @patch("lib.jira_conn.requests.get")
    def test_get_search_worklog_empty(self, mock_get):
        """Test worklog endpoint with no worklogs"""
        response = {"worklogs": [], "total": 0, "maxResults": 100}
        mock_get.return_value = MagicMock(status_code=200, json=lambda: response)

        query = "issue/MTE-123/worklog"
        results = self.client.get_search(query, "worklogs")

        self.assertEqual(len(results), 0)
        self.assertEqual(mock_get.call_count, 1)

    @patch("lib.jira_conn.requests.get")
    def test_get_search_default_endpoint_url_construction(self, mock_get):
        """Test that default endpoint URL is constructed correctly"""
        response = {"projects": [{"key": "MTE"}]}
        mock_get.return_value = MagicMock(status_code=200, json=lambda: response)

        query = "project"
        self.client.get_search(query, "projects")

        # Verify the full URL passed to requests.get
        called_url = mock_get.call_args.args[0]
        expected_url = f"{JIRA_HOST}project"
        self.assertEqual(called_url, expected_url)

    @patch("lib.jira_conn.requests.get")
    def test_get_search_default_endpoint_with_data_type(self, mock_get):
        """Test default endpoint that returns data_type from response"""
        response = {
            "projects": [
                {"key": "MTE", "name": "Mobile Test Engineering"},
                {"key": "FOX", "name": "Firefox"}
            ]
        }
        mock_get.return_value = MagicMock(status_code=200, json=lambda: response)

        query = "project"
        results = self.client.get_search(query, "projects")

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["key"], "MTE")

    @patch("lib.jira_conn.requests.get")
    def test_get_search_default_endpoint_empty_data_type(self, mock_get):
        """Test default endpoint with empty data_type returns whole payload"""
        response = {"key": "MTE-123", "summary": "Test issue"}
        mock_get.return_value = MagicMock(status_code=200, json=lambda: response)

        query = "issue/MTE-123"
        results = self.client.get_search(query, "")

        self.assertEqual(results["key"], "MTE-123")
        self.assertEqual(results["summary"], "Test issue")

    @patch("lib.jira_conn.requests.get")
    def test_get_search_default_endpoint_with_fields_in_query(self, mock_get):
        """Test default endpoint doesn't add fields if already in query"""
        response = {"projects": [{"key": "MTE"}]}
        mock_get.return_value = MagicMock(status_code=200, json=lambda: response)

        query = "project?fields=key,name"
        self.client.get_search(query, "projects")

        params_used = mock_get.call_args.kwargs["params"]
        # Should be None since fields already in URL
        self.assertIsNone(params_used)

    @patch("lib.jira_conn.requests.get")
    def test_get_search_http_error(self, mock_get):
        """Test that HTTP errors are raised"""
        mock_response = MagicMock()
        error = requests.HTTPError("401 Unauthorized")
        mock_response.raise_for_status.side_effect = error
        mock_get.return_value = mock_response

        query = "search/jql?jql=project=MTE"

        with self.assertRaises(requests.HTTPError):
            self.client.get_search(query, "issues")

    def test_base_url_trailing_slash(self):
        """Test that base URL gets trailing slash if missing"""
        client_without_slash = JiraAPIClient("https://example.com/api")
        # Access private attribute for testing
        self.assertTrue(client_without_slash._JiraAPIClient__url.endswith('/'))

    def test_base_url_keeps_trailing_slash(self):
        """Test that base URL keeps trailing slash if present"""
        client_with_slash = JiraAPIClient("https://example.com/api/")
        self.assertTrue(client_with_slash._JiraAPIClient__url.endswith('/'))
        # Should not have double slash
        self.assertFalse(client_with_slash._JiraAPIClient__url.endswith('//'))


class TestJiraCredentialsIntegration(unittest.TestCase):
    """
    Integration test — hits the real Jira API using JIRA_USER and JIRA_PASSWORD
    env vars. Fails if credentials are missing, expired, or revoked.
    """
    def setUp(self):
        self.user = os.environ["JIRA_USER"]
        self.password = os.environ["JIRA_PASSWORD"]
        self.base_url = f"https://{HOST_JIRA}/rest/api/3/"

    def test_credentials_are_valid(self):
        r = requests.get(
            self.base_url + "myself",
            headers={"Accept": "application/json"},
            auth=(self.user, self.password),
            timeout=60,
        )
        self.assertEqual(
            r.status_code, 200,
            f"Auth failed for {self.user} — {r.status_code}: {r.text}"
        )


class TestJiraWorklogs(unittest.TestCase):

    @patch("api.jira.report_worklogs._jira")
    def test_raises_if_no_issues_returned(self, mock_jira):
        """If the board returns 0 issues, raise ValueError and do not touch the DB."""
        from api.jira.report_worklogs import jira_worklogs

        mock_jira.return_value.filter_sv_parent_in_board.return_value = []

        with self.assertRaises(ValueError) as ctx:
            jira_worklogs()

        self.assertIn("No issues returned", str(ctx.exception))

    @patch("api.jira.report_worklogs.jira_delete")
    @patch("api.jira.report_worklogs._jira")
    def test_db_not_cleared_when_no_issues(self, mock_jira, mock_delete):
        """jira_delete must not be called if 0 issues are returned."""
        from api.jira.report_worklogs import jira_worklogs

        mock_jira.return_value.filter_sv_parent_in_board.return_value = []

        try:
            jira_worklogs()
        except ValueError:
            pass

        mock_delete.assert_not_called()

    @patch("api.jira.report_worklogs.jira_delete")
    @patch("api.jira.report_worklogs._jira")
    def test_db_not_cleared_when_no_worklogs(self, mock_jira, mock_delete):
        """jira_delete must not be called if issues exist but all have 0 worklogs."""
        from api.jira.report_worklogs import jira_worklogs

        mock_client = mock_jira.return_value
        mock_client.filter_sv_parent_in_board.return_value = [
            {"key": "QATT-1", "fields": {"summary": "Test issue", "parent": None}}
        ]
        mock_client.filter_child_issues.return_value = []
        mock_client.filter_worklogs.return_value = []

        with self.assertRaises(ValueError) as ctx:
            jira_worklogs()

        self.assertIn("no worklog data found", str(ctx.exception))
        mock_delete.assert_not_called()


class TestJiraQARequestsEmptyPayload(unittest.TestCase):

    @patch("api.jira.report_qa_requests.jira_delete")
    @patch("api.jira.report_qa_requests._jira")
    def test_qa_requests_raises_on_empty_payload(self, mock_jira, mock_delete):
        """jira_delete must not be called if filters() returns no issues."""
        from api.jira.report_qa_requests import jira_qa_requests

        mock_jira.return_value.filters.return_value = []

        with self.assertRaises(ValueError) as ctx:
            jira_qa_requests()

        self.assertIn("empty payload", str(ctx.exception))
        mock_delete.assert_not_called()

    @patch("api.jira.report_qa_requests.jira_delete")
    @patch("api.jira.report_qa_requests._jira")
    def test_qa_requests_workload_raises_on_empty_payload(self, mock_jira, mock_delete):
        """jira_delete must not be called if filters_new_issue_type() returns empty."""
        from api.jira.report_qa_requests import jira_qa_requests_workload

        mock_jira.return_value.filters_new_issue_type.return_value = []

        with self.assertRaises(ValueError) as ctx:
            jira_qa_requests_workload()

        self.assertIn("empty payload", str(ctx.exception))
        mock_delete.assert_not_called()

    @patch("api.jira.report_qa_requests_desktop.jira_delete")
    @patch("api.jira.report_qa_requests_desktop._jira")
    def test_qa_requests_desktop_raises_on_empty_payload(self, mock_jira, mock_delete):
        """jira_delete must not be called if filters() returns no issues."""
        from api.jira.report_qa_requests_desktop import jira_qa_requests_desktop

        mock_jira.return_value.filters.return_value = []

        with self.assertRaises(ValueError) as ctx:
            jira_qa_requests_desktop()

        self.assertIn("empty payload", str(ctx.exception))
        mock_delete.assert_not_called()
