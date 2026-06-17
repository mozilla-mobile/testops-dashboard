import api.jira.report_softvision_issues_qa_teams as softvision_issues_qa_teams
import api.jira.report_softvision_issues_other_teams as softvision_issues_other_teams
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


def handle_jira_softvision_issues_qa_teams(args):
    softvision_issues_qa_teams.jira_softvision_issues_qa_teams()


def handle_jira_softvision_issues_other_teams(args):
    softvision_issues_other_teams.jira_softvision_issues_other_teams()
