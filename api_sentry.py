#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys

from datetime import datetime

import pandas as pd

from lib.sentry_conn import APIClient

from database import (
    Database,
    ReportSentryIssues,
    ReportSentryCrashFreeRate
)

# The 2 major versions are beta and release.
NUM_MAJOR_VERSIONS = 2


class Sentry:

    def __init__(self):
        try:
            self.client = APIClient(os.environ['SENTRY_HOST'])
            self.client.api_token = os.environ['SENTRY_API_TOKEN']
            self.organization_slug = os.environ['SENTRY_ORGANIZATION_SLUG']
            self.project_id = os.environ['SENTRY_PROJECT_ID']
        except KeyError:
            print("ERROR: Missing testrail env var")
            sys.exit(1)

    # API: Issues
    # Only the unassigned issues past day sorted by frequency:
    # organization/mozilla/issues/
    # ?limit=10&query=is:for_review&sort=freq&statsPeriod=1d
    def issues(self, release_version):
        return self.client.http_get(
            (
                'organizations/{0}/issues/'
                '?project={1}'
                '&query=is:for_review release.version:{2}'
                '&sort=freq&statsPeriod=1d'
            ).format(
                self.organization_slug,
                self.project_id,
                release_version
            )
        )

    # API: Releases
    # The most recent releases of the project:
    # projects/mozilla/firefox-ios/releases/
    # ?per_page=100&project=1111111111
    # &statsPeriod=1d&environment=Production
    def releases(self):
        return self.client.http_get(
            (
                'projects/{0}/firefox-ios/releases/'
                '?&project={1}&statsPeriod=1d'
                '&environment=Production'
            ).format(self.organization_slug, self.project_id)
        )
    
    # API: Session (crash free rate (session) and crash free rate (user)) 
    # The crash free rate for the past 24 hours   
    def sentry_session_crash_free(self, crash_free_rate_type, release):
        return self.client.http_get(
            (
                'organizations/{0}/sessions/?field=crash_free_rate%28{1}%29'
                '&interval=15m&project={2}&query=release.version%3A{3}'
                '&statsPeriod=24h'
            ).format(
                self.organization_slug, crash_free_rate_type,
                self.project_id, release)
        )


class SentryClient(Sentry):

    def __init__(self):
        print("SentryClient.__init__()")
        super().__init__()
        self.db = DatabaseSentry()

    def data_pump(self):
        # Let's leave this to stay consistent with other
        # api_*.py files.
        pass

    def sentry_releases(self):
        print("SentryClient.sentry_releases()")
        releases = self.releases()
        release_versions = self.db.report_version_strings(releases)
        return release_versions
    
    # Top-level entry for all Sentry reports: 
    # Top unassigned issue, crash free rate, adoption rate (TODO)
    def sentry_reports(self):
        releases = self.sentry_releases()
        self.sentry_crash_free_rate(releases)
        self.sentry_issues(releases)
        
    
    def sentry_crash_free_rate(self, releases):
        print("SentryClient.sentry_crash_free_rate()")
        for release in releases:
            response_session = self.sentry_session_crash_free("session", release)
            response_user = self.sentry_session_crash_free("user", release)
            self.db.crash_free_rate_insert(response_session, response_user, release)

    def sentry_issues(self, releases):
        print("SentryClient.sentry_issues()")

        df_issues = pd.DataFrame()
        for release in releases:
            issues = self.issues(release)
            # NOTE: Use just the last two major releases for now
            df_issues_release = self.db.report_issue_payload(issues,
                                                             release)
            # output CSV for debugging
            df_issues_release.to_csv(
                "sentry_issues_{0}.csv".format(release),
                index=False)

            # Insert issues from this release into the same dataframe
            df_issues = pd.concat([df_issues, df_issues_release], axis=0)

        # Insert into database
        self.db.issue_insert(df_issues)


class DatabaseSentry:

    def __init__(self):
        print("DatabaseSentry.__init__()")
        super().__init__()
        self.db = Database()

    # Filter out the non-production versions such as 9000
    def _production_versions(self, version):
        version = version.strip()
        if version is None or version == '' or version == '9000':
            return False
        if "(" in version or ")" in version:
            return False
        if "org.mozilla.ios.Firefox" in version:
            return False
        parts = version.split('.')
        return all(p.isdigit() for p in parts) and len(parts) > 0

    # Get the beta and the release versions and all their
    # dot releases.
    def _all_new_production_dot_versions(self, versions):
        major_versions = []
        for version in versions:
            parts = version.split('.')
            major = parts[0]
            major_versions.append(major)
        major_versions = sorted(list(set(major_versions)), reverse=True)
        major_versions = major_versions[:NUM_MAJOR_VERSIONS]
        payload = []
        for major_version in major_versions:
            for version in versions:
                if version.startswith(major_version+"."):
                    payload.append(version)
        payload = sorted(list(set(payload)), reverse=True)
        print("Most recent {0} major versions:".format(NUM_MAJOR_VERSIONS))
        print(payload)
        return payload

    # Get the last two major versions
    def report_version_strings(self, releases):
        payload = []

        for release in releases:
            # Production only. Fiter out beta and interim versions
            description = release['versionInfo']['description']
            if self._production_versions(description):
                payload.append(description)

        payload = self._all_new_production_dot_versions(payload)

        # Just a list of released versions, not a dataframe
        return payload

    def report_issue_payload(self, issues, release):
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
                   release, permalink]
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
            
    # Insert crash free rate (session) of the day
    def crash_free_rate_insert(self, payload_session, payload_user, release):
        # crash free rate is a float
        session_rate = payload_session['groups'][0]['totals'][
            'crash_free_rate(session)'
        ]
        percentage_session_rate = round(session_rate * 100, 3)
        user_rate = payload_user['groups'][0]['totals'][
            'crash_free_rate(user)'
        ]
        percentage_user_rate = round(user_rate * 100, 3)
        now = datetime.now()
        row = ReportSentryCrashFreeRate(
            crash_free_rate_session=percentage_session_rate,
            crash_free_rate_user=percentage_user_rate,
            release_version=release,
            created_at=now
        )
        print(
            "[{0}] Crash free rate for {1}: {2}% (session) {3}% (user)".format(
                now, release, percentage_session_rate, percentage_user_rate
            )
        )
        self.db.session.add(row)
        self.db.session.commit()

    # A quick way to cleanup the database for testing
    def issues_delete_all(self):
        print("DatabaseSentry.issue_delete_all()")
        self.db.session.query(ReportSentryIssues).delete()
        self.db.session.query(ReportSentryCrashFreeRate).delete()
        self.db.session.commit()
