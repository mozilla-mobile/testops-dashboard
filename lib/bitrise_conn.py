#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import requests


logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)


class BitriseAPIClient:

    def __init__(self, base_url):
        try:
            self.token = ''
            self.API_HEADER = {'accept': 'application/json',
                               'Authorization': self.token}
            self.BITRISE_APP_SLUG = ''
            self.__url = base_url

        except KeyError:
            print("ERROR: must set BITRISE_TOKEN")
            exit()

    def get_apps(self):
        url = self.__url
        resp = requests.get(url,
                            headers=self.API_HEADER)
        if resp.status_code != 200:
            raise print('GET /apps/ {}'.format(resp.status_code))
        return resp.json()

    def set_app(self, project, apps):
        if apps is not None:
            if project == "android":
                self.BITRISE_APP_SLUG = apps['data'][0]['slug']
            elif project == "ios":
                self.BITRISE_APP_SLUG = apps['data'][1]['slug']

    def get_app(self, project, apps):
        url = self.__url
        if not self.BITRISE_APP_SLUG:
            resp = requests.get('{0}''{1}'.
                                format(url, self.BITRISE_APP_SLUG),
                                headers=self.API_HEADER)
            if resp.status_code != 200:
                raise _logger.error('GET /apps/ {}'.format(resp.status_code))
            return resp.json()

    def workflows(self, BITRISE_APP_SLUG):
        url = self.__url
        resp = \
            requests.get('{0}{1}'
                         '/build-workflows'.format(url, self.BITRISE_APP_SLUG),
                         headers=self.API_HEADER)
        if resp.status_code != 200:
            raise _logger.error('GET /apps/ {}'.format(resp.status_code))
        return resp.json()

    def builds(self, BITRISE_APP_SLUG):
        url = self.__url

        # Change to BITRISE_HOST
        resp = \
            requests.get('{0}{1}'
                         '/builds'.format(url, BITRISE_APP_SLUG), # noqa
                         headers=self.API_HEADER)
        if resp.status_code != 200:
            raise _logger.error('GET /apps/ {}'.format(resp.status_code))
        return resp.json()

    def builds_after_time(self, BITRISE_APP_SLUG, after):
        builds_data = []
        next_cursor = None  # Start without pagination cursor
        base_url = f"https://api.bitrise.io/v0.1/apps/{self.BITRISE_APP_SLUG}/builds" # noqa

        while True:
            url = f"{base_url}?after={after}"
            print(url)
            if next_cursor:
                url += f"&next={next_cursor}"

            response = requests.get(url, headers=self.API_HEADER)
            if response.status_code != 200:
                print(f"Error fetching builds: {response.status_code}")
                return builds_data

            page_data = response.json().get("data", [])
            builds_data.extend(page_data)

            next_cursor = response.json().get("paging", {}).get("next")
            if not next_cursor or next_cursor.lower() == "string":
                break

        return builds_data
