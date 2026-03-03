from api.github.api_github import GithubClient


def handle_github_issue_regression(args):
    client = GithubClient()
    client.github_issue_regression(args.project)


def handle_github_update_database(args):
    client = GithubClient()
    client.github_update_database(args.project, args.num_days)
