# flake8: noqa
"""TestRail API binding for Python 3.x.

(API v2, available since TestRail 3.0)

Compatible with TestRail 3.0 and later.

Learn more:

http://docs.gurock.com/testrail-api2/start
http://docs.gurock.com/testrail-api2/accessing

Copyright Gurock Software GmbH. See license.md for details.
"""

import base64
import json

import requests


class APIClient:
    def __init__(self, base_url):
        self.user = ''
        self.password = ''
        if not base_url.endswith('/'):
            base_url += '/'
        self.__url = base_url + 'index.php?/api/v2/'

    def send_get(self, uri, filepath=None):
        """Issue a GET request (read) against the API.

        Args:
            uri: The API method to call including parameters, e.g. get_case/1.
            filepath: The path and file name for attachment download; used only
                for 'get_attachment/:attachment_id'.

        Returns:
            A dict containing the result of the request.
        """
        return self.__send_request('GET', uri, filepath)

    def send_post(self, uri, data):
        """Issue a POST request (write) against the API.

        Args:
            uri: The API method to call, including parameters, e.g. add_case/1.
            data: The data to submit as part of the request as a dict; strings
                must be UTF-8 encoded. If adding an attachment, must be the
                path to the file.

        Returns:
            A dict containing the result of the request.
        """
        return self.__send_request('POST', uri, data)

    def __send_request(self, method, uri, data):
        url = self.__url + uri

        auth = str(
            base64.b64encode(
                bytes('%s:%s' % (self.user, self.password), 'utf-8')
            ),
            'ascii'
        ).strip()
        headers = {'Authorization': 'Basic ' + auth}

        if method == 'POST':
            if uri[:14] == 'add_attachment':    # add_attachment API method
                files = {'attachment': (open(data, 'rb'))}
                response = requests.post(url, headers=headers, files=files)
                files['attachment'].close()
            else:
                headers['Content-Type'] = 'application/json'
                payload = bytes(json.dumps(data), 'utf-8')
                response = requests.post(url, headers=headers, data=payload)
        else:
            all_items = []
            offset = 0
            limit = 250

            headers['Content-Type'] = 'application/json'

            while True:
                response = requests.get(f"{url}&limit={limit}&offset={offset}", headers=headers)
                data = response.json()
                print(data)

                # Check if 'cases' key exists in the response
                if 'cases' in data:
                    all_items.extend(data['cases'])

                    # Break if fewer items are returned than the limit, indicating the last page
                    if len(data['cases']) < limit:
                        break
                if 'milestones' in data:
                    all_items.extend(data['milestones'])

                    # Break if fewer items are returned than the limit, indicating the last page
                    if len(data['milestones']) < limit:
                        break
                else:
                    all_items = data
                    break  # If 'cases' key is not present, exit the loop

                offset += limit

            return all_items

        if response.status_code > 201:
            try:
                error = response.json()
            except requests.exceptions.HTTPError:     # response.content not formatted as JSON
                error = str(response.content)
            raise APIError('TestRail API returned HTTP %s (%s)' % (response.status_code, error))
        else:
            if uri[:15] == 'get_attachment/':   # Expecting file, not JSON
                try:
                    open(data, 'wb').write(response.content)
                    return (data)
                except FileNotFoundError:
                    return ("Error saving attachment.")
            else:
                try:
                    return response.json()
                except requests.exceptions.HTTPError: 
                    return {}


class APIError(Exception):
    pass
