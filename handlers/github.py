from api_github import GithubClient


def handle_bitrise_builds(args):
    client = BitriseClient()
    client.bitrise_builds_detailed_info()
