import os
import sys

import pandas as pd
import numpy as np
import json

from lib.sentry_conn import APIClient

# TODO: Find out the env vars before importing database
#   CLOUD_SQL_DATABASE_USERNAME
#   CLOUD_SQL_DATABASE_PASSWORD
#   CLOUD_SQL_DATABASE_NAME
# I have tried 1Password vault. Also searched 1Password.
#from database import (
#    Database,
#    ReportSentryTopUnassignedIssues
#)

class Sentry:
    
    def __init__(self):
        try:
            self.client = APIClient(os.environ['SENTRY_HOST'])
            self.client.api_token = os.environ['SENTRY_API_TOKEN']
            self.client.organization_slug = os.environ['SENTRY_ORGANIZATION_SLUG']
            self.project_id = os.environ['SENTRY_PROJECT_ID']
            self.project_slug = 'mozilla'
        except KeyError:
            print("ERROR: Missing testrail env var")
            sys.exit(1)
            
    # API: Top unassigned issue
    # TODO: Just "issues"
    # https://sentry.io/api/0/organizations/mozilla/issues/?limit=10&project={{project_id}}&query=is:for_review release.version:136.2&sort=freq&statsPeriod=24h
    def top_unassigned_issues(self, release, num_issues=10):
        return self.client.get(
            '{0}/issues/?limit={1}&project={2}&query=is:for_review release.version:{3}&sort=freq&statsPeriod=7d'
            .format(self.project_slug, num_issues, self.project_id, release)
        )
    
    # API: Issues
    # Question: Should we just get all issues, whether they are for_review or not?
    # Question: What should we use as a limit? 100? 50? 10? 5?
    # https://sentry.io/api/0/projects/mozilla/issues/?limit=10&query=is:for_review&sort=freq&statsPeriod=7d
    def issues(self, num_issues=10):
        return self.client.get(
            '{0}/issues/?limit={1}&project={2}&query=is:for_review&sort=freq&statsPeriod=7d'
            .format(self.project_slug, num_issues, self.project_id)
        )
        
    # API: Releases
    # todo: need pagination
    def releases(self, per_page=10):
        return self.client.get(
            '{0}/releases/?per_page={1}&project={2}&statsPeriod=7d'.format(self.project_slug, per_page, self.project_id)
        )
    
class SentryClient(Sentry):
    
    def __init__(self):
        print("SentryClient.__init__()")
        super().__init__()
        self.db = DatabaseSentry() # from api_testrail
        
    def data_pump():
        # TODO: Query all IDs of issues in DB
        # TODO: Wipe all old issues
        # TODO: Insert new issues
        # TODO: How to test data_pump()?
        print("SentryClient.data_pump()")
        pass
    
    # TODO: Should just be "issues" instead of "top_unassigned_issues"
    def sentry_top_unassigned_issues(self, release):
        print("SentryClient.sentry_top_unassigned_issues()")
        # Get JSON from Sentry
        # TODO: Query all releases
        top_unassigned_issues = self.top_unassigned_issues(release)
        # Get the following fields: title, permalink
        print(json.dumps(top_unassigned_issues, indent=2)) 
        # TODO: Format data
        # TODO: Insert data into DB
        
    def sentry_releases(self):
        print("SentryClient.sentry_release()")
        releases = self.releases()
        versions = []
        for release in releases:
            versions.append(release.get("versionInfo").get("version").get("raw"))
        print(versions)
        
        
    def sentry_issues(self):
        print("SentryClient.sentry_issues()")
        issues = self.issues(20)

        # Insert selected fields from the json blob to pandas 
        # using the "id" as the index
        issues_all = pd.DataFrame()
        selected_columns = ["id", "title", "permalink", "assignedTo", "lastSeen"]
        issues_all = pd.json_normalize(issues)
        selected_issues = issues_all[selected_columns]
        issues_all.set_index('id', inplace=True)

        # TODO: no transformation needed?
        print(issues_all[["title", "permalink"]])
        
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