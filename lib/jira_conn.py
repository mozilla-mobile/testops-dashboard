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


class JiraAPIClient:
    def __init__(self, base_url):
        self.user = ''          # Jira account email
        self.password = ''      # API token (not your account password)
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

        params = {"maxResults": 100, "fields": "key,summary"}
        all_results = []
        next_token = None

        print(f"Fetching data from: {url}")

        while True:
            effective_params = dict(params)
            if next_token:
                effective_params["nextPageToken"] = next_token

            response = requests.get(
                url,
                headers=headers,
                auth=HTTPBasicAuth(self.user, self.password),
                params=effective_params,
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()

            # Ensure the expected key exists in the response
            if data_type not in data:
                print(f"⚠️ Warning: {data_type} not found in response! Full response: {data}") # noqa
                break

            # Extend the results
            items = data[data_type]
            all_results.extend(items)

            print(f"Retrieved {len(all_results)} {data_type} so far...")

            next_token = data.get("nextPageToken")
            is_last = data.get("isLast", next_token is None)

            if is_last or not items:
                break

        print(f"✅ Total {data_type} retrieved: {len(all_results)}")
        return all_results
