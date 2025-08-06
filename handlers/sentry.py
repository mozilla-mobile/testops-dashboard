from api_sentry import SentryClient


def handle_sentry_issues(args):
    client = SentryClient()
    client.sentry_issues()


def handle_sentry_rates(args):
    client = SentryClient()
    client.sentry_rates()
