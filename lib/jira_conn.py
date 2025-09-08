#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Jira API binding for Python 3.x

Learn more:

https://docs.atlassian.com/software/jira/docs/api/REST/9.16.0/

Copyright Atlassian developer. See license.md for details.
"""
import requests

from requests.auth import HTTPBasicAuth
from urllib.parse import urlsplit, parse_qsl


class JiraAPIClient:
    def __init__(self, base_url):
        self.user = ''
        self.password = ''
        if not base_url.endswith('/'):
            base_url += '/'
        self.__url = base_url

    def get_search(self, query, data_type):
        """
        Fetch data from Jira Cloud v3 Enhanced Search endpoint.

        Args:
            query (str): API path with params, e.g.
                         'rest/api/3/search/jql?jql=project=FOX ORDER BY created DESC'
            data_type (str): key to collect from each page (usually 'issues').

        Returns:
            list: concatenated results across all pages.
        """
        return self.__send_request(query, data_type)

    def __send_request(self, query, data_type):
        url = self.__url + query
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        # detect endpoint
        parts = urlsplit(url)
        qparams = dict(parse_qsl(parts.query or ""))
        has_fields_in_query = "fields" in qparams

        is_enhanced_search = "/rest/api/3/search/jql" in parts.path
        is_worklog = parts.path.endswith("/worklog")

        print(f"Fetching data from: {url}")

        if is_enhanced_search:
            # Enhanced JQL search: nextPageToken + isLast
            params = {"maxResults": 100}
            if not has_fields_in_query:
                params["fields"] = "key,summary"

            all_results, next_token = [], None
            while True:
                effective = dict(params)
                if next_token:
                    effective["nextPageToken"] = next_token
                r = requests.get(url, headers=headers,
                                 auth=HTTPBasicAuth(self.user, self.password),
                                 params=effective, timeout=60)
                r.raise_for_status()
                data = r.json()

                items = data.get(data_type, [])
                if not isinstance(items, list):
                    raise KeyError(f"Expected list at '{data_type}', got keys: {list(data.keys())}") # noqa
                all_results.extend(items)
                print(f"Retrieved {len(all_results)} {data_type} so far...")

                next_token = data.get("nextPageToken")
                is_last = data.get("isLast", next_token is None)
                if is_last or not items:
                    break

            print(f"✅ Total {data_type} retrieved: {len(all_results)}")
            return all_results

        if is_worklog:
            # Worklogs: startAt + maxResults + total (no fields param here)
            params = {"startAt": 0, "maxResults": 100}
            all_logs = []
            while True:
                r = requests.get(url, headers=headers,
                                 auth=HTTPBasicAuth(self.user, self.password),
                                 params=params, timeout=60)
                r.raise_for_status()
                data = r.json()

                logs = data.get("worklogs", [])
                total = data.get("total", 0)
                all_logs.extend(logs)
                got = params["startAt"] + len(logs)
                print(f"Retrieved {len(all_logs)} of {total} total worklogs")

                if got >= total or not logs:
                    break

                params["startAt"] += data.get("maxResults", params["maxResults"])

            print(f"✅ Total worklogs retrieved: {len(all_logs)}")
            return all_logs

        # Default: single GET; only add fields
        params = {}
        if not has_fields_in_query and data_type and "." not in data_type:
            # Safe default for simple top-level collections
            params["fields"] = "key,summary"

        r = requests.get(url, headers=headers,
                         auth=HTTPBasicAuth(self.user, self.password),
                         params=params or None, timeout=60)
        r.raise_for_status()
        data = r.json()

        # Try top-level, else return whole payload (data_type="" to get all)
        return data.get(data_type, data)
