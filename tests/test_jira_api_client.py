#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest

from unittest.mock import MagicMock, patch
from lib.jira_conn import JiraAPIClient

JIRA_HOST="https://mozilla-hub.atlassian.net/rest/api/3/"

class TestsJiraAPIClient(unittest.TestCase):
	def setUp(self):
		self.client = JiraAPIClient(JIRA_HOST)
		self.client.user = ""
		self.client.password = ""
		
	@patch("lib.jira_conn.requests.get")
	def test_get_search_enhanced_no_fields_no_params(self, mock_get):
		page = {"issues": [], "isLast": True}
		mock_get.return_value = MagicMock(status_code=200, json=lambda: page)

		query = "rest/api/3/search/jql=projects=MTE"
		self.client.get_search(query, "issues")
		params_used = mock_get.call_args.kwargs["params"]
		self.assertEqual(params_used["fields"], "key,summary")