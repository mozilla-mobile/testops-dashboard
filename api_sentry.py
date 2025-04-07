import os
import sys

import pandas as pd
# import numpy as np
# import json


from lib.sentry_conn import APIClient

# TODO: Find out the env vars before importing database
#   CLOUD_SQL_DATABASE_USERNAME
#   CLOUD_SQL_DATABASE_PASSWORD
#   CLOUD_SQL_DATABASE_NAME
# I have tried 1Password vault. Also searched 1Password.
# from database import (
#    Database,
#    ReportSentryTopUnassignedIssues
# )


class Sentry:

    def __init__(self):
        try:
            self.client = APIClient(os.environ['SENTRY_HOST'])
            self.client.api_token = os.environ['SENTRY_API_TOKEN']
            self.client.organization_slug = \
                os.environ['SENTRY_ORGANIZATION_SLUG']
            self.project_id = os.environ['SENTRY_PROJECT_ID']
            self.project_slug = 'mozilla'
        except KeyError:
            print("ERROR: Missing testrail env var")
            sys.exit(1)

    # API: Issues
    # Question: Should we just the for_review issues?
    # TODO: Query everyday. Only the unassigned issues past day.
    # TODO:
    # /issues/?limit=10&query=is:for_review&sort=freq&statsPeriod=1d
    def issues(self):
        return self.client.get(
            (
                '{0}/issues/?project={1}'
                '&query=is:for_review&sort=freq&statsPeriod=1d'
            ).format(self.project_slug, self.project_id)
        )


class SentryClient(Sentry):

    def __init__(self):
        print("SentryClient.__init__()")
        super().__init__()
        self.db = DatabaseSentry()  # from api_testrail

    def data_pump():
        # TODO: Query all IDs of issues in DB
        # TODO: Wipe all old issues
        # TODO: Insert new issues
        # TODO: How to test data_pump()?
        print("SentryClient.data_pump()")
        pass

    def sentry_issues(self):
        print("SentryClient.sentry_issues()")
        issues = self.issues()

        # Insert selected fields from the json blob to pandas
        issues_all = pd.DataFrame()
        # TODO: Determin the list of columns to select
        # selected_columns = ["id", "title", "permalink", "lastSeen"]
        issues_all = pd.json_normalize(issues)
        print(issues_all.columns)
        issues_all.rename(columns={
            "id": "sentry_id",
        }, inplace=True)
        # selected_issues = issues_all[selected_columns]
        # issues_all.set_index('sentry_id', inplace=True)

        issues_all.to_csv("sentry_issues.csv", index=False)


class DatabaseSentry():

    def __init__(self):
        print("DatabaseSentry.__init__()")
        super().__init__()
        # self.db = Database()
        # TODO: import Database

    # TODO: Wipe database
    # NOTE:
    # * self.session is from class Database
    # Questions:
    # *
    def issues_delete(self):
        print("DatabaseSentry.issue_delete()")
        pass
