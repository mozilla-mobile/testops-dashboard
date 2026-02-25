from api.github.api_github import GithubClient


def handle_github_issue_regression(args):
    client = GithubClient()
    client.github_issue_regression(args.project)


def handle_github_new_bugs(args):
    client = GithubClient()
    client.github_new_bugs(args.project, args.num_days)


def handle_github_newly_resolved_bugs(args):
    client = GithubClient()
    client.github_newly_resolved_bugs(args.project)
