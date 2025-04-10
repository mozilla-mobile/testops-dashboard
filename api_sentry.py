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
                '{0}/issues/'
                '?project={1}'
                '&query=is:for_review release.version:{2}'
                '&sort=freq&statsPeriod=1d'
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

        # TODO: Get release versions
        # IDEA: From whattrainisitnow.com
        df_issues = pd.DataFrame()
        for release_version in ['138.0', '137.1', '137.0', '136.3']:
            issues = self.issues(release_version)
            df_issues_release = self.db.report_issue_payload(issues,
                                                             release_version)
            # output CSV for debugging
            df_issues_release.to_csv(
                "sentry_issues_{0}.csv".format(release_version),
                index=False)
            df_issues = pd.concat([df_issues, df_issues_release], axis=0)

        # TODO: Insert into database
        # self.db.....


class DatabaseSentry():

    def __init__(self):
        print("DatabaseSentry.__init__()")
        super().__init__()
        # self.db = Database()
        # TODO: import Database

    def report_issue_payload(self, issues, release_version):
        payload = []
        for issue in issues:
            sentry_id = issue['id']
            culprit = issue['culprit']
            title = issue['title']
            permalink = issue['permalink']
            lifetime = issue['lifetime']
            count = lifetime.get('count', 0)
            userCount = lifetime.get('userCount', 0)
            row = [sentry_id, culprit, title, count, userCount,
                   release_version, permalink]
            payload.append(row)

        df = pd.DataFrame(data=payload,
                          columns=["sentry_id", "culprit", "title",
                                   "count", "userCount", "release_version",
                                   "permalink"])
        return df

    # TBD: Wipe database
    def issues_delete(self):
        print("DatabaseSentry.issue_delete()")
        pass
