from api.github.api_github import GithubClient


def handle_github_issue_regression(args):
    client = GithubClient()
    client.github_issue_regression(args.project)
