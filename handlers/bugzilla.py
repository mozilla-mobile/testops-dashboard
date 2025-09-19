from api.bugzilla.api_bugzilla import BugzillaClient


def handle_bugzilla_desktop_bugs(args):
    client = BugzillaClient()
    client.bugzilla_query_desktop_bugs()


def handle_bugzilla_desktop_release_flags_for_bugs(args):
    client = BugzillaClient()
    client.bugzilla_query_release_flags_for_tracked_bugs(5, 100, True)


def handle_bugzilla_meta_bugs(args):
    client = BugzillaClient()
    client.bugzilla_meta_bug(meta_bug_id=args.meta_bug_id)


def handle_bugzilla_qe_verify(args):
    client = BugzillaClient()
    client.bugzilla_qe_verify()


def handle_bugzilla_query_by_keyword(args):
    client = BugzillaClient()
    client.bugzilla_query_by_keyword(keyword=args.bz_keyword)
