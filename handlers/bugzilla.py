from api_bugzilla import BugzillaClient


def handle_bugzilla_desktop_bugs(args):
    client = BugzillaClient()
    client.bugzilla_query_desktop_bugs()


def handle_bugzilla_meta_bugs(args):
    client = BugzillaClient()
    client.bugzilla_meta_bug(meta_bug_id=args.meta_bug_id)


def handle_bugzilla_qe_verify(args):
    client = BugzillaClient()
    client.bugzilla_qe_verify()
