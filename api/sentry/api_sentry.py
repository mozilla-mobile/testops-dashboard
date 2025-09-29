#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys
import requests

import pandas as pd

from lib.sentry_conn import APIClient
from datetime import datetime

from database import (
    Database,
    ReportSentryIssues,
    ReportSentryRates
)

# The 2 major versions are beta and release.
NUM_MAJOR_VERSIONS = 2


class Sentry:

    def __init__(self, project=''):
        try:
            self.client = APIClient(os.environ['SENTRY_HOST'])
            self.client.api_token = os.environ['SENTRY_API_TOKEN']
            self.organization_slug = \
                os.environ['SENTRY_ORGANIZATION_SLUG']
            # Only fetch the platform from which the ID is defined.
            self.sentry_project_id = ""
            self.environment = ""
            self.package = ""
            self.sentry_project = project
            project_config = {
                "firefox-ios": {
                    "id": os.environ["SENTRY_IOS_PROJECT_ID"],
                    "env": "Production",
                    "pkg": "org.mozilla.ios.Firefox",
                },
                "fenix": {
                    "id": os.environ["SENTRY_FENIX_PROJECT_ID"],
                    "env": "release",
                    "pkg": "org.mozilla.firefox",
                },                
            }
            if project in project_config.keys():
                self.sentry_project_id = project_config[project]["id"]
                self.environment = project_config[project]["env"]
                self.package = project_config[project]["pkg"]
        except KeyError as e:
            missing = e.args[0]
            print(f"ERROR: Missing environment variable {missing}")
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
            ).format(self.organization_slug, self.sentry_project_id, release_version)
        )

    # API: Releases
    # /organizations/{{organization_slug}}/releases/
    # ?adoptionStages=1&environment={{environment}}&project={{project_id}}
    # &query=release.package:{{package}}&status=open&summaryStatsPeriod=24h
    # &sort=adoption&adoptionStages=adopted
    def releases(self):
        return self.client.http_get(
            (
                '/organizations/mozilla/releases/'
                '?adoptionStages=1&project={1}&environment={0}'
                '&query=release.package:{2}&status=open&summaryStatsPeriod=7d'
                '&adoptionStages=1&sort=adoption'
            ).format(self.environment, self.sentry_project_id, self.package)
        )

    # Workaround: Get the largest/latest version through whattrainisitnow
    def get_latest_train_release(self):
        response = requests.get('https://whattrainisitnow.com/api/firefox/releases/')
        return list(response.json().keys())

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
                self.sentry_project_id, release
            )
        )

    # API: Adoption Rate (Users)
    def sentry_adoption_rate(self, release):
        health_info_release = self.client.http_get(
            (
                "organizations/{0}/releases/{1}%40{2}/"
                "?health=1&summaryStatsPeriod=7d&project={3}"
                "&environment={4}&adoptionStages=1"
            ).format(
                self.organization_slug, self.package,
                release, self.sentry_project_id, self.environment)
        )
        return health_info_release


class SentryClient(Sentry):

    def __init__(self, project=''):
        print("SentryClient.__init__()")
        super().__init__(project=project)
        self.db = DatabaseSentry(project_id=self.sentry_project_id,
                                 sentry_project=project)

    def data_pump():
        # Let's leave this to stay consistent with other
        # api_*.py files.
        pass

    # Now output the "long" version. Example: org.mozilla.firefox@142.0.1+2016110936
    def sentry_releases(self):
        print("SentryClient.sentry_releases()")
        releases = self.releases()
        # Workaround: Do not use Fenix versions that are "too new".
        # Query whattrainisitnow.com for the latest version.
        # (Example: v170 exists while nightly now is only at v144.)
        get_latest_train_release = self.get_latest_train_release()[-1]
        release_versions = self._report_version_strings(
            releases, get_latest_train_release)
        print(release_versions)
        return release_versions

    def sentry_issues(self, release=[]):
        print("SentryClient.sentry_issues()")

        if release == []:
            release_versions = self.sentry_releases()
        else:
            release_versions = [release]

        df_issues = pd.DataFrame()
        for release_version in release_versions:
            short_release_version = release_version.split('+')[0]
            issues = self.issues(short_release_version)
            # NOTE: Use just the last two major releases for now
            df_issues_release = self.db.report_issue_payload(issues,
                                                             short_release_version)
            # output CSV for debugging
            df_issues_release.to_csv(
                "sentry_issues_{0}_{1}.csv"
                .format(self.sentry_project, short_release_version),
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
            short_release_version = release_version.split('+')[0]
            response_crash_free_rate_session = (
                self.sentry_sessions_crash_free_rate(
                    "session", short_release_version)
            )
            response_crash_free_rate_user = (
                self.sentry_sessions_crash_free_rate(
                    "user", short_release_version)
            )
            response_adoption_rate = self.sentry_adoption_rate(
                release_version
            )
            df_rate = self.db.report_rates_payload(
                response_crash_free_rate_user,
                response_crash_free_rate_session,
                response_adoption_rate, short_release_version
            )
            # If any of the rate is null, do not insert into the database.
            if df_rate is not None:
                df_rates = pd.concat(
                    [df_rate, df_rates], axis=0
                )

        # Output for Slack message
        df_rates.to_csv(
            "sentry_rates.csv",
            index=False
        )

        # Insert into database
        self.db.rate_insert(df_rates)

    # Get the last two major versions
    def _report_version_strings(self, release_versions, latest_version):
        payload = []
        latest_major_version = int(latest_version.split('.')[0])
        oldest_major_version = latest_major_version - 2

        for release_version in release_versions:
            version = release_version['versionInfo']['version']
            raw_version = version['raw']
            major_version = int(version['major'])
            build_code = version['buildCode']
            if oldest_major_version < major_version and \
               major_version <= latest_major_version:
                if self.sentry_project == 'firefox-ios' and build_code is None:
                    payload.append(raw_version)
                if self.sentry_project == 'fenix' and build_code is not None:
                    if int(build_code) % 2 == 1:
                        payload.append(raw_version)
        payload.sort()

        # Just a list of released versions, not a dataframe
        return payload


class DatabaseSentry:

    def __init__(self, project_id='', sentry_project='fenix'):
        print("DatabaseSentry.__init__()")
        super().__init__()
        self.db = Database()
        self.sentry_project_id = project_id
        self.sentry_project = sentry_project

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
            sentry_project_id = self.sentry_project_id
            row = [sentry_id, culprit, title, count, user_count,
                   release_version, permalink, sentry_project_id]
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
                                   "permalink", "sentry_project_id"])
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
                sentry_project_id=row['sentry_project_id']
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

        now = datetime.now()
        row = [
            percentage_crash_free_rate_session,
            percentage_crash_free_rate_user,
            percentage_adoption_rate_user,
            release_version,
            now,
            self.sentry_project_id
        ]
        df = pd.DataFrame(
            data=[row],
            columns=[
                'crash_free_rate_user',
                'crash_free_rate_session',
                'adoption_rate_user',
                'release_version',
                'created_at',
                'sentry_project_id'
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
                sentry_project_id=row['sentry_project_id']
            )
            self.db.session.add(rates)
            self.db.session.commit()
