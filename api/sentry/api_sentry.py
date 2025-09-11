#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys

import pandas as pd

from lib.sentry_conn import APIClient
from utils.datetime_utils import DatetimeUtils

from database import (
    Database,
    ReportSentryIssues,
    ReportSentryRates
)

# The 2 major versions are beta and release.
NUM_MAJOR_VERSIONS = 2


class Sentry:

    def __init__(self):
        try:
            self.client = APIClient(os.environ['SENTRY_HOST'])
            self.client.api_token = os.environ['SENTRY_API_TOKEN']
            self.organization_slug = \
                os.environ['SENTRY_ORGANIZATION_SLUG']
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
            ).format(self.organization_slug, self.project_id, release_version)
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
    def sentry_sessions_crash_free_rate(self, crash_free_rate_type, release):
        return self.client.http_get(
            (
                'organizations/{0}/sessions/?field=crash_free_rate%28{1}%29'
                '&interval=15m&project={2}&query=release.version%3A{3}'
                '&statsPeriod=24h'
            ).format(
                self.organization_slug, crash_free_rate_type,
                self.project_id, release
            )
        )

    # API: Adoption Rate (Users)
    def sentry_adoption_rate(self, release):
        health_info_release = self.client.http_get(
            (
                "organizations/{0}/releases/org.mozilla.ios.Firefox%40{1}/"
                "?health=1&summaryStatsPeriod=7d&project={2}"
                "&environment=Production&adoptionStages=1"
            ).format(self.organization_slug, release, self.project_id)
        )
        # Long version name could be beta
        if health_info_release is None:
            return self.client.http_get(
                (
                    "organizations/{0}/releases/"
                    "org.mozilla.ios.FirefoxBeta%40{1}/"
                    "?health=1&summaryStatsPeriod=7d&project={2}"
                    "&environment=Production&adoptionStages=1"
                ).format(self.organization_slug, release, self.project_id)
            )
        else:
            return health_info_release


class SentryClient(Sentry):

    def __init__(self):
        print("SentryClient.__init__()")
        super().__init__()
        self.db = DatabaseSentry()

    def data_pump():
        # Let's leave this to stay consistent with other
        # api_*.py files.
        pass

    # A one-stop function to fetch data on issues and crash free rate
    def sentry_reports(self):
        release_versions = self.sentry_releases()
        self.sentry_rates(release_versions)
        self.sentry_issues(release_versions)

    def sentry_releases(self):
        print("SentryClient.sentry_releases()")
        releases = self.releases()
        release_versions = self.db.report_version_strings(releases)
        return release_versions

    def sentry_issues(self, release=[]):
        print("SentryClient.sentry_issues()")

        if release == []:
            release_versions = self.sentry_releases()
        else:
            release_versions = [release]

        df_issues = pd.DataFrame()
        for release_version in release_versions:
            issues = self.issues(release_version)
            # NOTE: Use just the last two major releases for now
            df_issues_release = self.db.report_issue_payload(issues,
                                                             release_version)
            # output CSV for debugging
            df_issues_release.to_csv(
                "sentry_issues_{0}.csv".format(release_version),
                index=False)

            # Insert issues from this release into the same dataframe
            df_issues = pd.concat([df_issues, df_issues_release], axis=0)

        # Insert into database
        self.db.issue_insert(df_issues)

    def sentry_rates(self, releases=[]):
        print("SentryClient.sentry_rates()")

        if releases == []:
            release_versions = self.sentry_releases()
        else:
            release_versions = [releases]

        df_rates = pd.DataFrame()
        for release_version in release_versions:
            response_crash_free_rate_session = (
                self.sentry_sessions_crash_free_rate(
                    "session", release_version)
            )
            response_crash_free_rate_user = (
                self.sentry_sessions_crash_free_rate(
                    "user", release_version)
            )
            response_adoption_rate = self.sentry_adoption_rate(
                release_version
            )
            df_rate = self.db.report_rates_payload(
                response_crash_free_rate_user,
                response_crash_free_rate_session,
                response_adoption_rate, release_version
            )
            # If any of the rate is null, do not insert into the database.
            if df_rate is not None:
                df_rates = pd.concat(
                    [df_rate, df_rates], axis=0
                )
        # TODO: Insert adoption rate into the database
        self.db.rate_insert(df_rates)
        df_rates.to_csv(
            "sentry_rates.csv",
            index=False
        )


class DatabaseSentry:

    def __init__(self):
        print("DatabaseSentry.__init__()")
        super().__init__()
        self.project_id = os.environ['SENTRY_PROJECT_ID']
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
    def report_version_strings(self, release_versions):
        payload = []

        for release_version in release_versions:
            # Production only. Filter out beta and interim versions
            description = release_version['versionInfo']['description']
            if self._production_versions(description):
                payload.append(description)

        payload = self._all_new_production_dot_versions(payload)

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
            project_id = self.project_id
            row = [sentry_id, culprit, title, count, user_count,
                   release_version, permalink, project_id]
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
                permalink=row['permalink'],
                project_id=row['project_id']
            )
            self.db.session.add(issue)
            self.db.session.commit()

    def report_rates_payload(
        self,
        response_crash_free_rate_user,
        response_crash_free_rate_session,
        response_adoption_rate,
        release_version
    ):
        crash_free_rate_session = None
        if response_crash_free_rate_session:
            crash_free_rate_session = (
                response_crash_free_rate_session['groups'][0]['totals'].get(
                    'crash_free_rate(session)', None
                )
            )
        crash_free_rate_user = None
        if response_crash_free_rate_user:
            crash_free_rate_user = (
                response_crash_free_rate_user['groups'][0]['totals'].get(
                    'crash_free_rate(user)', None
                )
            )
        # Sometimes the REST API calls return null values in the field
        # Return None if either rate is null
        adoption_rate_user = None
        if response_adoption_rate:
            adoption_rate_user = (
                response_adoption_rate['projects'][0]['healthData']
                .get('adoption', 0) or 0.0
            )

        # Let me use -1 to indicate null values
        percentage_crash_free_rate_session = -1
        if crash_free_rate_session:
            percentage_crash_free_rate_session = round(
                crash_free_rate_session * 100, 2
            )
        percentage_crash_free_rate_user = -1
        if crash_free_rate_user:
            percentage_crash_free_rate_user = round(
                crash_free_rate_user * 100, 2
            )
        percentage_adoption_rate_user = -1
        if adoption_rate_user:
            percentage_adoption_rate_user = round(adoption_rate_user, 2)

        now = DatetimeUtils.start_date('0')
        row = [
            percentage_crash_free_rate_session,
            percentage_crash_free_rate_user,
            percentage_adoption_rate_user,
            release_version,
            now,
            self.project_id
        ]
        df = pd.DataFrame(
            data=[row],
            columns=[
                'crash_free_rate_user',
                'crash_free_rate_session',
                'adoption_rate_user',
                'release_version',
                'created_at',
                'project_id'
            ]
        )
        return df

    # Insert crash free rates of the day
    def rate_insert(self, payload):
        for index, row in payload.iterrows():
            print(row)
            rates = ReportSentryRates(
                crash_free_rate_session=row['crash_free_rate_session'],
                crash_free_rate_user=row['crash_free_rate_user'],
                adoption_rate_user=row['adoption_rate_user'],
                release_version=row['release_version'],
                created_at=row['created_at'],
                project_id=row['project_id']
            )
            self.db.session.add(rates)
            self.db.session.commit()
