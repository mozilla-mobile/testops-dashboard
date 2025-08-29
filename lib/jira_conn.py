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
        self.user = ''
        self.password = ''
        if not base_url.endswith('/'):
            base_url += '/'
        self.__url = base_url

    def get_search(self, query, data_type):
        """Issue a GET request (read) against the API.

        Args:
            filter{id}: The API method to call including parameters,
            e.g. GET /rest/api/3/filter/{id}.

        Returns:
            JSON representation of the search results.
        """
        return self.__send_request('GET', query, data_type)

    def __send_request(self, method, query, data_type):

        print(f"self.__url: {self.__url}")
        url = self.__url + query
        print(f"url: {url}")
        import sys
        sys.exit(1)
        # Store all results
        all_results = []
        params = {"startAt": 0, "maxResults": 100}  # Set pagination params
        headers = {"Content-Type": "application/json"}

        print(f"Fetching data from: {url}")

        while True:
            # Send GET request
            response = requests.get(
                url,
                headers=headers,
                auth=HTTPBasicAuth(self.user, self.password),
                params=params
            )

            data = response.json()

            # Ensure the expected key exists in the response
            if data_type not in data:
                print(f"⚠️ Warning: {data_type} not found in response! Full response: {data}") # noqa
                break

            # Extend the results
            all_results.extend(data[data_type])

            print(f"Retrieved {len(all_results)} of {data.get('total', 'unknown')} total {data_type}") # noqa

            # If we've retrieved all results, break the loop
            if params['startAt'] + params['maxResults'] >= data.get('total', 0): # noqa
                break

            # Increment the startAt parameter to get the next batch
            params['startAt'] += params['maxResults']

        print(f"✅ Total {data_type} retrieved: {len(all_results)}")
        return all_results
