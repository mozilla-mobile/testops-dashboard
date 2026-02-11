#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import requests
from requests.exceptions import HTTPError


class APIClient:
    def __init__(self, base_url='https://api.github.com'):
        if not base_url.endswith('/'):
            base_url += '/'
        self.__url = base_url
        self.api_token = os.environ.get('GITHUB_TOKEN', '')

    def http_get(self, uri):
        headers = {
            'Authorization': f'token {self.api_token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        url = self.__url + uri
        all_results = []

        while url:
            print(f"Fetching: {url}")
            response = requests.get(url, headers=headers)
            try:
                response.raise_for_status()
            except HTTPError:
                print(f"HTTP error occurred: {response.status_code} - {response.text}")
                return None

            data = response.json()
            if isinstance(data, list):
                all_results.extend(data)
                print(f"Received {len(all_results)} items")
            else:
                return data  # For non-list endpoints

            link_header = response.headers.get("Link", "")
            next_url = None
            
            if link_header:
                for link in link_header.split(','):
                    link = link.strip()
                    if '; rel="next"' in link:
                        next_url = link.split('<')[1].split('>')[0]
                        break

            url = next_url

        return all_results