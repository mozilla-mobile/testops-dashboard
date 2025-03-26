import requests

from database import (
    Database
)


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
        # type_type = created_at, updated_at, closed_at, merged_at
        issue_status = 'created'
        date_lower_limit = '2021-09-01'
        date_upper_limit = '2021-10-01'

        g = Github()
        b = g.issues_url_base(project)
        # p = g.pulls_url_base(project)
        u = g.url_is_issue(project, 'intermit', issue_status,
                           date_lower_limit, date_upper_limit)
        print(u)
        print(b)
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
