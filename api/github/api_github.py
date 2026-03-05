#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sys
import requests
from datetime import datetime, timedelta, UTC

from lib.github_conn import APIClient

from database import (
    Database,
    ReportGithubBugs
)
from sqlalchemy.exc import IntegrityError

import pandas as pd


API_BASE = 'https://api.github.com'
OWNER = 'mozilla-mobile'


LABELS = [
    'eng:intermittent-test',
    'eng:but-auto-found',
    'crash', 'b:crash',
    '🐞 bug', 'Bug 🐞',
    'P1', 'P2', 'P3',
]

DATE_TYPES = [
    'created_at',
    'updated_at',
    'closed_at',
    'merged_at',
]


class Github:

    def __init__(self):
        try:
            self.client = APIClient(API_BASE)
        except KeyError as e:
            missing = e.args[0]
            print(f"ERROR: Missing environment variable {missing}")
            sys.exit(1)

    '''
    try:
        API_TOKEN = os.environ['GITHUB_TOKEN']
        API_HEADER = {'Authorization': API_TOKEN, 'accept': 'application/json'}
    except KeyError:
        print("ERROR: GITHUB_TOKEN env var not set")
        sys.exit()
    '''
    # UTILS
    def path_date_range(self, issue_status, date_lower_limit, date_upper_limit): # noqa
        # created_at, updated_at, closed_at, merged_at
        path = ''
        date_type = ''
        for item in DATE_TYPES:
            if issue_status in item:
                date_type = item

        if date_lower_limit:
            path += '+{0}:>={1}'.format(date_type, date_lower_limit)
        if date_upper_limit:
            path += '+{0}:<{1}'.format(date_type, date_upper_limit)
        return path

    def path_labels(self, label_matcher):
        # Given a string 'label_matcher' will check for all
        # matching labels in LABELS and append to path
        path = ''
        for label in LABELS:
            if label_matcher.lower() in label.lower():
                path += '+label:{0}'.format(label)
        return path

    # URL: ISSUES
    def issues_url_base(self, project):
        return '{0}/search/issues?q=repo:{1}/{2}'.format(API_BASE, OWNER, project) # noqa

    def url_is_issue(self, project, label_matcher, issue_status='', date_lower_limit='', date_upper_limit=''): # noqa
        url_base = self.issues_url_base(project)
        url = '{0}+is:issue'.format(url_base)
        if label_matcher:
            labels = self.path_labels(label_matcher)
            url += labels
        if issue_status:
            date_range = self.path_date_range(issue_status,
                                              date_lower_limit,
                                              date_upper_limit)
            url += date_range
        return url

    def url_is_pr(self, project):
        url_base = self.issues_url_base(project)
        return '{0}+is:pr'.format(url_base)

    def url_date_range(self, project, url_type, created_date):
        """
        is:open
        is:closed
        label:<label>
        label:bug
        label:crash
        """
        url_base = self.issues_url_base(project)
        url = '{0}+is:issue'.format(url_base)
        url = '{0}+created:>=2020-08-15'.format(url_base)
        return url

    # URL: New Issues last n days
    def new_bugs(self, project, timestamp):
        # Use search API to get newly created issues, not updated issues
        # Exclude data-sync-user directly in the query
        return self.client.http_get(
            'search/issues?q=repo:{0}/{1}+is:issue+state:open+'
            'no:assignee+created:>={2}+-author:data-sync-user'
            .format(OWNER, project, timestamp) # noqa
        )

    # URL: Get info on an existing issue.
    def get_existing_issue_by_number(self, project, github_number):
        return self.client.http_get(
            'repos/{0}/{1}/issues/{2}'.format(OWNER, project, github_number)
        )

    def mozilla_mobile_members(self):
        return self.client.http_get('orgs/{0}/members?filter=all'.format(OWNER))

    # URL: PULLS
    def pulls_url_base(self, project):
        return  '{0}/repos/{1}/{2}/pulls?state=closed'.format(API_BASE, OWNER, project) # noqa


class GithubClient(Github):

    EXCLUDED = []

    def __init__(self):
        super().__init__()
        self.database = DatabaseGithub()

    def add_rows(self, table,  data, row_count):
        for repository in data:
            title = repository["title"]
            merged_at = repository["merged_at"]
            user = repository["user"]["login"]

            if user not in self.EXCLUDED:
                if merged_at:
                    table.add_row([row_count, title, merged_at, user])
                    row_count += 1

        return table, row_count

    def paginate(self, project, table):
        # github API paginates data: default == 30, max == 100
        PER_PAGE_MAX = 100

        # starting values
        count = 1
        row_count = 1
        another_page = True

        api = self.github.url_pulls_base(project)

        while another_page:
            params = {'page': count, 'per_page': PER_PAGE_MAX}
            response = requests.get(api, params=params, headers=self.API_HEADER) # noqa
            print(response)
            r = response.json()

            # check if there is a next page
            if 'next' in response.links:
                api = response.links['next']['url']
                print(api)
                table, row_count = self.add_rows(table, r, row_count)
                count += 1
                another_page = True
            else:
                another_page = False
        return table

    def github_issue_regression(self, project):
        issue_status = 'created'
        date_lower_limit = '2021-09-01'
        date_upper_limit = '2021-10-01'

        g = Github()
        g.issues_url_base(project)
        g.url_is_issue(project, 'intermit', issue_status,
                       date_lower_limit, date_upper_limit)
        label_matcher = 'INTERMIT'
        g.path_labels(label_matcher)

    def diagnostic(self, project, table):
        from prettytable import PrettyTable
        table = PrettyTable()
        table.field_names = ["count", "title", "merged_at", "user"]
        table.align['count'] = "l"
        table.align['title'] = "l"
        table.align['merged_at'] = "l"
        table.align['user'] = "l"
        table = self.paginate(project, table)
        print(table)

    # URL: Entry point to update existing bugs and add new bugs from last n days
    def github_update_database(self, project, num_days=1):
        self.github_update_bugs(project)
        self.github_new_bugs(project, num_days)

    # URL: New bugs last n days
    def github_new_bugs(self, project, num_days=1):
        since_when = datetime.now(UTC) - timedelta(days=int(num_days))
        timestamp = since_when.strftime('%Y-%m-%dT%H:%M:%SZ')
        search_result = self.new_bugs(project, timestamp)

        # Extract items from search API response
        all_bugs = search_result.get('items', []) if search_result else []

        # Filter out bugs from org members and contributors
        EXCLUDED_ASSOCIATIONS = {'OWNER', 'MEMBER'}
        all_bugs = [
            bug for bug in all_bugs
            if bug.get('author_association') not in EXCLUDED_ASSOCIATIONS
        ]

        # Print all bug titles using list comprehension
        [print(bug.get('title', 'No title')) for bug in all_bugs]

        # Create DataFrame with bug data
        bug_data = []
        for bug in all_bugs:
            bug_data.append({
                'github_number': bug.get('number', ''),
                'github_title': bug.get('title', '(No title)'),
                'github_state': bug.get('state', ''),
                'github_url': bug.get('html_url', ''),
                'github_created_at': bug.get('created_at', ''),
                'github_updated_at': bug.get('updated_at', ''),
                'github_closed_at': bug.get('closed_at', ''),
                'github_user': bug.get('user', {}).get('login', ''),
                'github_author_association': bug.get('author_association', '')
            })

        df_new_bugs = pd.DataFrame(bug_data)

        # Save to CSV with today's date
        today = datetime.now().strftime('%Y-%m-%d')
        csv_filename = f'github_new_bugs_{project}_{today}.csv'
        df_new_bugs.to_csv(csv_filename, index=False)
        print(f"Saved {len(df_new_bugs)} bugs to {csv_filename}")

        # Insert issues to the database
        self.database.issue_insert(df_new_bugs, project)

        return df_new_bugs

    # URL: Update bugs fetched from last time
    def github_update_bugs(self, project):
        issues = self.database.get_all_issues(project)
        print(f"Found {len(issues)} issues. Checking for updates...")
        updated_count = 0

        for issue in issues:
            issue_data = self.get_existing_issue_by_number(
                issue.github_project, issue.github_number
            )
            if not issue_data:
                continue
            api_updated_at = issue_data.get('updated_at')
            db_updated_at = (
                issue.github_updated_at.strftime('%Y-%m-%dT%H:%M:%SZ')
                if issue.github_updated_at else None
            )
            if api_updated_at != db_updated_at:
                self.database.update_issue(issue_data, issue.github_project)
                updated_count += 1

        print(f"Updated {updated_count} issues.")


class DatabaseGithub(Database):

    def __init__(self):
        super().__init__()
        self.db = Database()

    def report_github_issues_totals(self, project_id, totals):
        return totals

    def report_github_issues_insert(self, project_id, totals):
        for total in totals:
            t = total

            # only count xxxxx
            if t['xxxxx']:
                pass
                """
                report = ReportTestRuns(projects_id=project_id,
                                        issue_id=t['issue_id'],
                                        issue_title=t['issue_title'], # noqa
                                        issue_types_id=t['issue_types_id'], # 1=issue,2=pr # noqa
                                        github_created_at=t['github_created_at'], # noqa
                                        github_updated_at=t['github_updated_at'], # noqa
                                        github_closed_at=t['github_closed_at'], # noqa
                                        github_merged_at=t['github_merged_at']) # noqa
                self.session.add(report)
                self.session.commit()
                """

    def issue_insert(self, payload, project):
        for index, row in payload.iterrows():
            issue_created_at = datetime.strptime(
                row['github_created_at'], '%Y-%m-%dT%H:%M:%SZ'
            ) if row['github_created_at'] else None
            issue_updated_at = datetime.strptime(
                row['github_updated_at'], '%Y-%m-%dT%H:%M:%SZ'
            ) if row['github_updated_at'] else None
            issue_closed_at = datetime.strptime(
                row['github_closed_at'], '%Y-%m-%dT%H:%M:%SZ'
            ) if row['github_closed_at'] else None
            issue = ReportGithubBugs(
                github_number=row['github_number'],
                github_title=row['github_title'],
                github_url=row['github_url'],
                github_created_at=issue_created_at,
                github_updated_at=issue_updated_at,
                github_closed_at=issue_closed_at,
                github_user=row['github_user'],
                github_author_association=row['github_author_association'],
                github_state=row['github_state'],
                github_project=project
            )
            print("Inserted Issue: {} - {}".format(
                row['github_number'], row['github_title']))
            try:
                self.db.session.add(issue)
                self.db.session.commit()
            except IntegrityError:
                self.db.session.rollback()
                print(f"Skipping duplicate issue #{row['github_number']}")

    def get_all_issues(self, project):
        return self.db.session.query(ReportGithubBugs).filter(
            ReportGithubBugs.github_project == project
        ).all()

    def update_issue(self, issue_data, project):
        record = self.db.session.query(ReportGithubBugs).filter(
            ReportGithubBugs.github_number == issue_data['number'],
            ReportGithubBugs.github_project == project
        ).first()

        if not record:
            print(f"Issue #{issue_data['number']} not found in DB, skipping.")
            return

        fmt = '%Y-%m-%dT%H:%M:%SZ'

        record.github_title = issue_data.get('title')
        record.github_url = issue_data.get('html_url')
        record.github_state = issue_data.get('state')
        record.github_user = issue_data.get('user', {}).get('login')
        record.github_author_association = issue_data.get('author_association')
        record.github_created_at = (
            datetime.strptime(issue_data['created_at'], fmt)
            if issue_data.get('created_at') else None
        )
        record.github_updated_at = (
            datetime.strptime(issue_data['updated_at'], fmt)
            if issue_data.get('updated_at') else None
        )
        record.github_closed_at = (
            datetime.strptime(issue_data['closed_at'], fmt)
            if issue_data.get('closed_at') else None
        )

        self.db.session.commit()
        print(f"Updated issue #{issue_data['number']}.")
