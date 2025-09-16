from api.bugzilla.api_bugzilla import BugzillaClient


def handle_bugzilla_desktop_bugs(args):
    client = BugzillaClient()
    #client.bugzilla_query_desktop_bugs()
    print("NEW")
    #client.bugzilla_collect_version_flags_daily_dynamic(24)
    client.bugzilla_collect_version_flags_for_tracked_bugs(5, 400, True)
    #client.collect_version_flags_snapshot_fixed_only(5, 400, True)
def handle_bugzilla_meta_bugs(args):
    client = BugzillaClient()
    client.bugzilla_meta_bug(meta_bug_id=args.meta_bug_id)


def handle_bugzilla_qe_verify(args):
    client = BugzillaClient()
    client.bugzilla_qe_verify()


def handle_bugzilla_query_by_keyword(args):
    client = BugzillaClient()
    client.bugzilla_query_by_keyword(keyword=args.bz_keyword)
