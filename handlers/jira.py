import api.jira.report_qa_needed as qa_needed
import api.jira.report_qa_requests as requests
import api.jira.report_qa_requests_desktop as requests_desktop
import api.jira.report_worklogs as worklogs


def handle_jira_qa_requests(args):
    requests.jira_qa_requests()
    requests.jira_qa_requests_workload()


def handle_jira_qa_needed(args):
    qa_needed.jira_qa_needed()


def handle_jira_softvision_worklogs(args):
    worklogs.jira_worklogs()


def handle_jira_qa_requests_desktop(args):
    requests_desktop.jira_qa_requests_desktop()
