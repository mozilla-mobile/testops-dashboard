from api.sentry.api_sentry import SentryClient


def handle_sentry_issues(args):
    client = SentryClient(project=args.project)
    client.sentry_issues()


def handle_sentry_rates(args):
    client = SentryClient(project=args.project)
    client.sentry_rates()
