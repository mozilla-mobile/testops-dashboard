import datetime
import time

import logging
import requests


logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)


class BitriseAPIClient:

    def __init__(self, base_url):
        try:
            self.API_HEADER = {'accept': 'application/json'}
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

    def get_workflows(self, BITRISE_APP_SLUG):
        url = self.__url
        resp = \
            requests.get('{0}{1}'
                         '/build-workflows'.format(url, self.BITRISE_APP_SLUG),
                         headers=self.API_HEADER)
        if resp.status_code != 200:
            raise _logger.error('GET /apps/ {}'.format(resp.status_code))
        return resp.json()

    def get_builds(self, BITRISE_APP_SLUG):
        url = self.__url
        days_ago = 1
        today = datetime.datetime.utcnow().date()
        past_date = today - datetime.timedelta(days=days_ago)
        print(past_date)
        past_date_timestamp = int(time.mktime(past_date.timetuple()))
        print(past_date_timestamp)

        # Change to BITRISE_HOST
        resp = \
            requests.get('{0}{1}'
                         '/builds?after={2}'.format(url, BITRISE_APP_SLUG, past_date_timestamp), # noqa
                         headers=self.API_HEADER)
        if resp.status_code != 200:
            raise _logger.error('GET /apps/ {}'.format(resp.status_code))
        return resp.json()
