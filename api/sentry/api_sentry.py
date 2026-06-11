#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys
import tomllib
import requests
import pandas as pd

from packaging.version import Version
from lib.sentry_conn import APIClient
from datetime import datetime

from database import (
    Database,
    ReportSentryIssues,
    ReportSentryRates
)

# The 2 major versions are beta and release.
NUM_MAJOR_VERSIONS = 2

# Notifications query this many of the most recent dot releases.
NUM_DOT_RELEASES = 2

# Minimum user-adoption percentage for a release to count as "live". Releases
# registered in Sentry but not yet shipped sit near 0% and are skipped. Matches
# the crash-free-rate report's threshold in api/sentry/utils.py insert_rates.
MIN_ADOPTION_RATE = 1


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
                "fenix-beta": {
                    "id": os.environ["SENTRY_FENIX_BETA_PROJECT_ID"],
                    "env": "beta",
                    "pkg": "org.mozilla.firefox_beta",
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

        try:
            with open('config/sentry/projects.toml', 'rb') as f:
                _projects_config = tomllib.load(f)
            self.excluded_issue_titles = (
                _projects_config.get(project, {})
                .get('excluded_issue_titles', [])
            )
        except (FileNotFoundError, tomllib.TOMLDecodeError):
            self.excluded_issue_titles = []

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
                '?adoptionStages=1&project={1}&environment={0}&health=1'
                '&query=release.package:{2}&status=open&summaryStatsPeriod=7d'
                '&adoptionStages=1&sort=adoption'
            ).format(self.environment, self.sentry_project_id, self.package)
        )

    # Workaround: Get the largest/latest version through whattrainisitnow
    def get_latest_train_release(self):
        response = requests.get('https://whattrainisitnow.com/api/firefox/releases/')
        return list(response.json().keys())

    def get_future_train_release(self):
        response = requests.get(
            'https://whattrainisitnow.com/api/firefox/releases/esr/future/')
        return list(response.json().keys())

    # API: Top unresolved issues first seen in a given release, sorted by
    # frequency over the past 7 days. Matches Sentry's release "New Issues"
    # tab, which includes both the "new" and "escalating" substatuses.
    # first_release is the URL-encoded "<package>%40<version>" value.
    def unhandled_issues(self, limit=5, first_release=None):
        query = 'is%3Aunresolved'
        if first_release:
            query += '%20firstRelease%3A' + first_release
        return self.client.http_get(
            (
                'organizations/{0}/issues/'
                '?project={1}'
                '&query={4}'
                '&sort=freq&statsPeriod=7d'
                '&environment={2}&limit={3}'
            ).format(
                self.organization_slug, self.sentry_project_id,
                self.environment, limit, query
            ),
            paginate=False
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
                self.sentry_project_id, release
            )
        )

    # API: Total distinct app users over the past 24 hours.
    # Used as the denominator for the user-adoption rate. Sentry's
    # release-health `adoption` field divides each release's users by the
    # whole project's user count, but this project also receives Focus and
    # Klar (org.mozilla.ios.Focus / .Klar) sessions, which would understate
    # Firefox adoption by ~25%. Scope to release.package so the denominator
    # is Firefox-only, and use the same 24h window as the crash-free queries.
    def sentry_total_users(self):
        return self.client.http_get(
            (
                'organizations/{0}/sessions/?field=count_unique%28user%29'
                '&interval=1d&project={1}&environment={2}'
                '&query=release.package%3A{3}&statsPeriod=24h'
            ).format(
                self.organization_slug, self.sentry_project_id,
                self.environment, self.package
            )
        )

    # API: Distinct users for a single release over the past 24 hours.
    # Numerator for the user-adoption rate. Scoped to package + version (and
    # the same environment / 24h window as sentry_total_users) so the ratio
    # numerator/denominator is consistent and the numerator is a strict
    # subset of the denominator.
    def sentry_release_users(self, release):
        return self.client.http_get(
            (
                'organizations/{0}/sessions/?field=count_unique%28user%29'
                '&interval=1d&project={1}&environment={2}'
                '&query=release.package%3A{3}%20release.version%3A{4}'
                '&statsPeriod=24h'
            ).format(
                self.organization_slug, self.sentry_project_id,
                self.environment, self.package, release
            )
        )


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
        if self.sentry_project == 'fenix-beta':
            get_train_release = self.get_future_train_release()[0]
        else:
            get_train_release = self.get_latest_train_release()[-1]
        release_versions = self._report_version_strings(
            releases, get_train_release)
        if not release_versions:
            print("Warning: No releases found for '{0}', skipping.".format(
                self.sentry_project))
            return []
        print(release_versions)
        return release_versions

    def sentry_issues(self, release=[]):
        print("SentryClient.sentry_issues()")

        if release == []:
            release_versions = self.sentry_releases()
        else:
            release_versions = [release]

        if not release_versions:
            return

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

    def _adopted_dot_releases(self, n):
        """Return the newest n dot-release versions (e.g. 151.3) whose user
        adoption exceeds MIN_ADOPTION_RATE percent.

        Releases are registered in Sentry as soon as a build is uploaded, so
        the highest version number is often a not-yet-shipped build sitting
        near 0% adoption. Filtering by adoption keeps the actually-live
        release(s) instead of those future builds.
        """
        releases = self.releases()
        if not releases:
            return []
        latest = self.get_latest_train_release()[-1]
        # Map raw version -> adoption percent from the same (health=1) response.
        adoption = {}
        for release in releases:
            try:
                raw = release['versionInfo']['version']['raw']
            except (KeyError, TypeError):
                continue
            projects = release.get('projects') or []
            match = next(
                (p for p in projects
                 if str(p.get('id')) == str(self.sentry_project_id)),
                projects[0] if projects else None,
            )
            health = (match or {}).get('healthData') or {}
            adoption[raw] = float(health.get('adoption', 0) or 0)
        selected = []
        seen = set()
        for raw in self._report_version_strings(releases, latest):
            dot = raw.split('+')[0]
            if dot in seen:
                continue
            seen.add(dot)
            rate = adoption.get(raw, 0.0)
            if rate > MIN_ADOPTION_RATE:
                print(f"Live release {dot}: adoption {rate}%")
                selected.append(dot)
            else:
                print(f"Skipping low-adoption release {dot}: {rate}%")
            if len(selected) >= n:
                break
        return selected

    def sentry_unhandled_issues(self, limit=3, longform=False):
        print(f"SentryClient.sentry_unhandled_issues(longform={longform})")
        if self.sentry_project == 'fenix-beta':
            # Beta is intentionally low-adoption; use the upcoming train
            # release rather than filtering on adoption.
            dot_releases = [
                self.get_future_train_release()[0].split('+')[0]
            ][:NUM_DOT_RELEASES]
        else:
            dot_releases = self._adopted_dot_releases(NUM_DOT_RELEASES)
            if not dot_releases:
                print(
                    f"Warning: No live (adopted) releases found for "
                    f"'{self.sentry_project}', skipping."
                )
                return

        fetch_limit = limit + len(self.excluded_issue_titles) + 5
        MAX_STRING_LEN = 250
        payload = []

        queries = [(v, v) for v in dot_releases]

        for query_version, stored_version in queries:
            print(f"Filtering by release: {query_version}")
            first_release = f"{self.package}%40{query_version}"
            raw_issues = (
                self.unhandled_issues(
                    limit=fetch_limit,
                    first_release=first_release,
                )
                or []
            )
            # Keep all candidates (already freq-sorted) after the exclusion
            # list; the Slack formatter applies the >500 threshold before
            # selecting the top 3 per dot release.
            issues = [
                issue for issue in raw_issues
                if not any(
                    excl.lower() in issue['title'].lower()
                    for excl in self.excluded_issue_titles
                )
            ]
            for issue in issues:
                payload.append([
                    issue['id'],
                    issue.get('shortId', ''),
                    issue['title'][:MAX_STRING_LEN],
                    issue.get('culprit', ''),
                    issue.get('count', 0),
                    issue.get('userCount', 0),
                    issue.get('permalink', ''),
                    stored_version,
                ])
        df = pd.DataFrame(
            data=payload,
            columns=['sentry_id', 'short_id', 'title', 'culprit', 'count',
                     'user_count', 'permalink', 'release_version']
        )
        suffix = '_long' if longform else ''
        csv_path = (
            f'sentry_unhandled_issues{suffix}_{self.sentry_project}.csv'
        )
        df.to_csv(csv_path, index=False)
        print(f"Unhandled issues written to {csv_path}")

    def sentry_rates(self, releases=[]):
        print("SentryClient.sentry_rates()")

        if releases == []:
            release_versions = self.sentry_releases()
        else:
            release_versions = [releases]

        # Firefox-only distinct-user total over the past 24h, used as the
        # adoption denominator. Sentry's release-health adoption divides by
        # the whole project, but this project also receives Focus/Klar
        # sessions, so we scope the denominator to our package instead.
        total_users = self.db.parse_user_count(self.sentry_total_users())

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
            response_release_users = self.sentry_release_users(
                short_release_version
            )
            df_rate = self.db.report_rates_payload(
                response_crash_free_rate_user,
                response_crash_free_rate_session,
                response_release_users, total_users,
                short_release_version
            )
            # If any of the rate is null, do not insert into the database.
            if df_rate is not None:
                df_rates = pd.concat(
                    [df_rates, df_rate], axis=0
                )

        if df_rates.empty:
            print(
                "Warning: No rates retrieved for project '{0}', generating empty CSV."
                .format(self.sentry_project)
            )
            pd.DataFrame(columns=[
                "crash_free_rate_user", "crash_free_rate_session",
                "adoption_rate_user", "release_version",
                "created_at", "sentry_project_id"
            ]).to_csv("sentry_rates.csv", index=False)
            return

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
            if self.sentry_project == 'fenix-beta':
                if major_version >= latest_major_version and int(build_code) % 2 == 1:
                    payload.append(raw_version)
            else:
                if oldest_major_version < major_version and \
                   major_version <= latest_major_version:
                    if self.sentry_project == 'firefox-ios' and build_code is None:
                        payload.append(raw_version)
                    if self.sentry_project == 'fenix' and build_code is not None:
                        if int(build_code) % 2 == 1:
                            payload.append(raw_version)

        payload.sort(key=Version, reverse=True)

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
        for issue in issues or []:
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

    def parse_user_count(self, response):
        """Pull the distinct-user total (count_unique(user)) out of a Sentry
        sessions response, or 0 if it is missing/empty."""
        if response and response.get('groups'):
            return (
                response['groups'][0]['totals'].get('count_unique(user)', 0)
                or 0
            )
        return 0

    def report_rates_payload(
        self,
        response_crash_free_rate_user,
        response_crash_free_rate_session,
        response_release_users,
        total_users,
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
        # Adoption = this release's distinct users / all distinct users for
        # the app over the same 24h window. total_users is the package-scoped
        # denominator (excludes Focus/Klar, which also report into this
        # project). None if we cannot compute it (no denominator).
        adoption_rate_user = None
        if total_users:
            release_users = self.parse_user_count(response_release_users)
            adoption_rate_user = release_users / total_users * 100

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
        if adoption_rate_user is not None:
            percentage_adoption_rate_user = round(adoption_rate_user, 2)

        now = datetime.now()
        row = [
            percentage_crash_free_rate_user,
            percentage_crash_free_rate_session,
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
