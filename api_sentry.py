import os
import sys
import pandas as pd
from lib.sentry_conn import APIClient
from database import Database, ReportSentryIssues

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
            print("ERROR: Missing Sentry environment variable")
            sys.exit(1)

    def issues(self, release_version):
        return self.client.http_get(
            (
                'organizations/{0}/issues/'
                '?project={1}'
                '&query=is:for_review release.version:{2}'
                '&sort=freq&statsPeriod=1d'
            ).format(self.organization_slug, self.project_id, release_version)
        )

    def events_from_issue(self, issue_id):
        return self.client.http_get(
            (
                'organizations/{0}/issues/{1}/events/'
            ).format(self.organization_slug, issue_id)
        )

    def releases(self):
        return self.client.http_get(
            (
                'projects/{0}/firefox-ios/releases/'
                '?&project={1}&statsPeriod=1d'
                '&environment=Production'
            ).format(self.organization_slug, self.project_id)
        )

    def event(self, event_id):
        return self.client.http_get(
            (
                'projects/{0}/firefox-ios/events/{1}/'
            ).format(self.organization_slug, event_id)
        )


class SentryClient(Sentry):

    def __init__(self):
        print("SentryClient.__init__()")
        super().__init__()
        self.db = DatabaseSentry()

    def data_pump(self):
        pass

    def sentry_releases(self):
        print("SentryClient.sentry_releases()")
        releases = self.releases()
        release_versions = self.db.report_version_strings(releases)
        return release_versions

    def sentry_issues(self):
        print("SentryClient.sentry_issues()")

        release_versions = self.sentry_releases()

        df_issues = pd.DataFrame()
        release_versions = ['138.2'] # Will add back all release_versions later
        for release_version in release_versions:
            issues = self.issues(release_version)

            # Get categories for each issue
            categories = []
            issue_ids = [issue['id'] for issue in issues]
            for issue_id in issue_ids:
                category = self.sentry_event_category_from_issue(issue_id)
                categories.append({'id': issue_id, 'categories': category})
            print(categories)

            # NOTE: Use just the last two major releases for now
            df_issues_release = self.db.report_issue_payload(
                issues, release_version
            )
            # Output CSV for debugging
            df_issues_release.to_csv(
                "sentry_issues_{0}.csv".format(release_version),
                index=False
            )

            # Insert issues from this release into the same dataframe
            df_issues = pd.concat([df_issues, df_issues_release], axis=0)

        # Insert into database
        self.db.issue_insert(df_issues)

    def sentry_event_category_from_issue(self, issue_id):
        print("SentryClient.sentry_events_from_issue()")

        # Get all events associated with the issue
        issue_events = self.events_from_issue(issue_id)
        event_ids = [event['id'] for event in issue_events]

        # Get all categories from the breadcrumbs of each event
        categories = []
        print("Fetching {0} events".format(len(event_ids)))
        for event_id in event_ids:
            event = self.event(event_id)
            category = self.db.report_category_from_event_breadcrumbs(event)
            categories.extend(category)
        categories = sorted(set(categories))

        return categories


class DatabaseSentry:

    def __init__(self):
        print("DatabaseSentry.__init__()")
        self.db = Database()

    def _production_versions(self, version):
        version = version.strip()
        if not version or version == '9000':
            return False
        if "(" in version or ")" in version:
            return False
        if "org.mozilla.ios.Firefox" in version:
            return False
        parts = version.split('.')
        return all(p.isdigit() for p in parts)

    def _all_new_production_dot_versions(self, versions):
        major_versions = sorted(
            set(version.split('.')[0] for version in versions),
            reverse=True
        )[:NUM_MAJOR_VERSIONS]
        payload = [
            version for major_version in major_versions
            for version in versions if version.startswith(major_version + ".")
        ]
        payload = sorted(set(payload), reverse=True)
        print("Most recent {0} major versions:".format(NUM_MAJOR_VERSIONS))
        print(payload)
        return payload

    def report_version_strings(self, release_versions):
        payload = [
            release_version['versionInfo']['description']
            for release_version in release_versions
            if self._production_versions(
                release_version['versionInfo']['description']
            )
        ]
        return self._all_new_production_dot_versions(payload)

    def report_issue_payload(self, issues, release_version):
        MAX_STRING_LEN = 250
        payload = [
            [
                issue['id'],
                issue['culprit'],
                issue['title'][:MAX_STRING_LEN],
                issue['lifetime'].get('count', 0),
                issue['lifetime'].get('userCount', 0),
                release_version,
                issue['permalink']
            ]
            for issue in issues
        ]
        return pd.DataFrame(
            data=payload,
            columns=[
                "sentry_id", "culprit", "title", "count", "user_count",
                "release_version", "permalink"
            ]
        )

    def report_category_from_event_breadcrumbs(self, event):
        categories = []
        for entry in event['entries']:
            if entry['type'] == 'breadcrumbs':
                categories.extend(
                    value['category'] for value in entry['data']['values']
                )
        return categories

    def issue_insert(self, payload):
        for _, row in payload.iterrows():
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
