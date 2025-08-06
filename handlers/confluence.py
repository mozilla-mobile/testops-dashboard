import api.confluence.api_confluence as api_confluence


def handle_confluence_build_validation(args):
    api_confluence.page_report_build_validation()


def handle_confluence_updates(args):
    api_confluence.main()
