import os
import sys

import pandas as pd


from lib.sentry_conn import APIClient

# TODO: Database
from database import (
    Database,
    ReportSentryIssues
)


class Sentry:

    def __init__(self):
        try:
            self.client = APIClient(os.environ['SENTRY_HOST'])
            self.client.api_token = os.environ['SENTRY_API_TOKEN']
            self.organization_slug = \
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
    # organization/mozilla/issues/
    # ?limit=10&query=is:for_review&sort=freq&statsPeriod=1d
    def issues(self, release_version='137.0'):
        return self.client.get(
            (
                'organizations/{0}/issues/'
                '?project={1}'
                '&query=is:for_review release.version:{2}'
                '&sort=freq&statsPeriod=1d'
            ).format(self.organization_slug, self.project_id, release_version)
        )
        
    def releases(self):
        # projects/mozilla/firefox-ios/releases/
        # ?per_page=100&project=1111111111
        # &statsPeriod=1d&environment=Production
        return self.client.get(
            (
            'projects/{0}/firefox-ios/releases/'
            '?per_page=10&project={2}&statsPeriod=7d'
            '&environment=Production'         
            ).format(self.organization_slug,
                   self.project_slug, self.project_id)
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
    
    def sentry_releases(self):
        releases = self.releases()
        # TODO: just get versionInfo -> description
        # return all versions strings in a list
        return releases

    def sentry_issues(self):
        print("SentryClient.sentry_issues()")
        
        # TEMPORARY: Delete all issues before inserting new ones
        self.db.issues_delete_all()

        # TODO: Get release versions
        sentry_releases = self.sentry_releases()
        release_versions = self.db.report_version_strings(sentry_releases)
        # release_versions = ['138.0', '137.2', '137.1', '137.0', '136.3']

        df_issues = pd.DataFrame()
        # TODO: Replace release_version with self.sentry_releases()
        for release_version in release_versions:
            issues = self.issues(release_version)
            df_issues_release = self.db.report_issue_payload(issues,
                                                             release_version)
            # output CSV for debugging
            df_issues_release.to_csv(
                "sentry_issues_{0}.csv".format(release_version),
                index=False)

            # Insert issues from this release into the same dataframe
            df_issues = pd.concat([df_issues, df_issues_release], axis=0)

        # Ensure we have all the columns after merging all dataframes
        print(df_issues_release.columns)

        # Insert into database
        self.db.issue_insert(df_issues)


class DatabaseSentry():

    def __init__(self):
        print("DatabaseSentry.__init__()")
        super().__init__()
        self.db = Database()
        
    def _is_version_numeric(version):
        if version is None or version == '':
            return False
        if "(" in version or ")" in version:
            return False
        if "org.mozilla.ios.Firefox" in version:
            return False
        parts = version.split('.')
        return all(p.isdigit() for p in parts) and len(parts) > 0
    
    def report_version_strings(self, release_versions):
        payload = []

        for release_version in release_versions:
            # Production only. Fiter out beta and interim versions
            description = release_version['versionInfo']['description']
            print(description)
            if self._is_version_numeric(description):
                payload.append(description)

        # Just a list of released versions, not a dataframe
        return payload 

    def report_issue_payload(self, issues, release_version):
        payload = []
        MAX_STRING_LEN = 250
        for issue in issues:
            sentry_id = issue['id']
            culprit = issue['culprit']
            title = issue['title'][:MAX_STRING_LEN]
            permalink = issue['permalink']
            lifetime = issue['lifetime']
            count = lifetime.get('count', 0)
            user_count = lifetime.get('userCount', 0)
            row = [sentry_id, culprit, title, count, user_count,
                   release_version, permalink]
            payload.append(row)

        # sentry_id: ID given by sentry. Maybe in the permalink as well
        # culprit: Module where the error is happening (NEED)
        # title: Title of the issue (NEED)
        # count: Lifetime count of the occurrences (NEED)
        # user_count: Lifetime count of the users affected (NEED)
        # release_version: We separate queries by release version for now
        # permalink: Click to open Sentry page of the issue (Maybe for Slack)
        df = pd.DataFrame(data=payload,
                          columns=["sentry_id", "culprit", "title",
                                   "count", "user_count", "release_version",
                                   "permalink"])
        return df
        
    def issue_insert(self, payload):
        for index, row in payload.iterrows():
            print(row)
            issue = ReportSentryIssues(
                sentry_id=row['sentry_id'],
                culprit=row['culprit'],
                title=row['title'],
                count=row['count'],
                user_count=row['user_count'],
                release_version=row['release_version'],
                permalink=row['permalink']
            )
            self.db.session.add(issue)
            self.db.session.commit()

    def issues_delete_all(self):
        print("DatabaseSentry.issue_delete_all()")
        self.db.session.query(ReportSentryIssues).delete()
        self.db.session.commit()
