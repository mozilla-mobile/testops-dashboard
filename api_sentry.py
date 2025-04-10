import os
import sys

import pandas as pd


from lib.sentry_conn import APIClient

# TODO: Database

class Sentry:

    def __init__(self):
        try:
            self.client = APIClient(os.environ['SENTRY_HOST'])
            self.client.api_token = os.environ['SENTRY_API_TOKEN']
            self.client.organization_slug = \
                os.environ['SENTRY_ORGANIZATION_SLUG']
            self.project_id = os.environ['SENTRY_PROJECT_ID']
            self.project_slug = 'mozilla'
        except KeyError:
            print("ERROR: Missing testrail env var")
            sys.exit(1)

    # API: Issues
    # Question: Should we just list the for_review issues?
    #           Any other types of issues?
    # Only the unassigned issues past day sorted by frequency:
    # /issues/?limit=10&query=is:for_review&sort=freq&statsPeriod=1d
    def issues(self, release_version='137.0'):
        return self.client.get(
            (
                '{0}/issues/?project={1}'
                '&query=is:for_review release.version{2}&sort=freq&statsPeriod=1d'
            ).format(self.project_slug, self.project_id, release_version)
        )


class SentryClient(Sentry):

    def __init__(self):
        print("SentryClient.__init__()")
        super().__init__()
        self.db = DatabaseSentry()  # from api_testrail

    def data_pump():
        # TODO: Query all IDs of issues in DB
        # TODO: Wipe all old issues
        # TODO: Insert new issues
        # TODO: How to test data_pump()?
        print("SentryClient.data_pump()")
        pass

    def sentry_issues(self):
        print("SentryClient.sentry_issues()")
        
        for release_version in ['138.0', '137.1', '137.0', '136.3']:
            issues = self.issues(release_version)

            # Insert selected fields from the json blob to pandas
            issues_all = pd.DataFrame()
            # TODO: Determine the list of columns to select
            issues_all = pd.json_normalize(issues)
            print(issues_all.columns)
            issues_all.rename(columns={
                "id": "sentry_id",
            }, inplace=True)

            issues_all.to_csv("sentry_issues_{0}.csv".format(release_version), index=False)


class DatabaseSentry():

    def __init__(self):
        print("DatabaseSentry.__init__()")
        super().__init__()
        # self.db = Database()
        # TODO: import Database

    # TBD: Wipe database
    def issues_delete(self):
        print("DatabaseSentry.issue_delete()")
        pass
