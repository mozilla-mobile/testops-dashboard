from api_jira import JiraClient


def handle_jira_qa_requests(args):
    client = JiraClient()
    client.jira_qa_requests()
    client.jira_qa_requests_new_issue_types()


def handle_jira_qa_needed(args):
    client = JiraClient()
    client.jira_qa_needed()


def handle_jira_softvision_worklogs(args):
    client = JiraClient()
    client.jira_softvision_worklogs()
