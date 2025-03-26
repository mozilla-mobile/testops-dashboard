import os
import sys

import pandas as pd
import numpy as np

from lib.sentry_conn import APIClient

from database import (
    Database,
    ReportSentryUnassignedIssues,
)

from utils.datetime_utils import DatetimeUtils as dt
from utils.payload_utils import PayloadUtils as pl

class Sentry:
    
    def __init__(self, organization_slug, project_slug):
        try:
            self.client = APIClient(os.environ['SENTRY_HOST'])
            self.project_slug = os.environ['SENTRY_PROJECT_SLUG']
            self.organization_slug = os.environ['SENTRY_ORGANIZATION_SLUG']
            self.project_id = os.environ['SENTRY_PROJECT_ID']
            self.client.api_token = os.environ['SENTRY_API_TOKEN']
        except KeyError:
            print("ERROR: Missing Sentry env var")
            sys.exit(1)
            
    # API: top unassigned issues
    # https://sentry.io/api/0/organizations/mozilla/issues/?limit=10&project={{project_id}}&query=is:for_review release.version:136.2&sort=freq&statsPeriod=24h
    def top_unassigned_issues(self, release, num_issues=10):
        return self.client.get(
            'issues/?limit={0}&project={1}&query=is:for_review release.version:{2}&sort=freq&statsPeriod=24h'
            .format(num_issues, self.project_id, release)
        )
        
    ## API: Crash free rate (user)
    ## API: Crash free rate (session)

class SentryClient(Sentry):

    def __init__(self):
        super().__init__()
        #self.db = DatabaseSentry()

    def data_pump(self):
        # what should we do in data_pump for Sentry?
        pass

    def sentry_top_unassigned_issues(self, release):
        # delete all issues?
        # self.db.sentry_delete_issues()
        top_unassigned_issues = self.sentry_top_unassigned_issues(release)
        print(json.dumps(top_unassigned_issues, indent=2)) 

        self.db.Sentry_milestons_delete()

        project_ids_list = self.Sentry_project_ids(project)
        milestones_all = pd.DataFrame()

        for project_ids in project_ids_list:
            projects_id = project_ids[0]
            Sentry_project_id = project_ids[1]

            payload = self.milestones(Sentry_project_id)
            if not payload:
                print(f"No milestones found for project {Sentry_project_id}. Skipping...") # noqa
                milestones_all = pd.DataFrame()  # Empty DataFrame to avoid errors # noqa

            else:
                # Convert JSON to DataFrame
                milestones_all = pd.json_normalize(payload)

            # Ensure DataFrame is not empty before processing
            if milestones_all.empty:
                print(f"Milestones DataFrame is empty for project {Sentry_project_id}. Skipping...") # noqa
                # Continue to next project (if inside a loop)
            else:
                # Define selected columns
                selected_columns = {
                    "id": "Sentry_milestone_id",
                    "name": "name",
                    "started_on": "started_on",
                    "is_completed": "is_completed",
                    "description": "description",
                    "completed_on": "completed_on",
                    "url": "url"
                }

                # Select specific columns (only if they exist)
                existing_columns = [col for col in selected_columns.keys() if col in milestones_all.columns] # noqa
                df_selected = milestones_all[existing_columns].rename(columns={k: v for k, v in selected_columns.items() if k in milestones_all.columns}) # noqa

                # Convert valid timestamps, leave empty ones as NaT
                if 'started_on' in df_selected.columns:
                    df_selected['started_on'] = pd.to_datetime(df_selected['started_on'], unit='s', errors='coerce') # noqa
                    df_selected['started_on'] = df_selected['started_on'].replace({np.nan: None}) # noqa

                if 'completed_on' in df_selected.columns:
                    df_selected['completed_on'] = pd.to_datetime(df_selected['completed_on'], unit='s', errors='coerce') # noqa
                    df_selected['completed_on'] = df_selected['completed_on'].replace({np.nan: None}) # noqa

                # Apply transformations only if description column exists
                if 'description' in df_selected.columns:
                    df_selected['testing_status'] = df_selected['description'].apply(pl.extract_testing_status) # noqa
                    df_selected['testing_recommendation'] = df_selected['description'].apply(pl.extract_testing_recommendation) # noqa

                # Apply transformations only if name column exists
                if 'name' in df_selected.columns:
                    df_selected['build_name'] = df_selected['name'].apply(pl.extract_build_name) # noqa
                    df_selected['build_version'] = df_selected['build_name'].apply(pl.extract_build_version) # noqa

                # Insert into database only if there is data
                if not df_selected.empty:
                    self.db.report_milestones_insert(projects_id, df_selected)
                else:
                    print(f"No milestones data to insert into database for project {Sentry_project_id}.") # noqa


class DatabaseSentry(Database):

    def __init__(self):
        super().__init__()
        #self.db = Database()

    def sentry_delete_issues(self):
        #self.session.query(ReportSentryUnassignedIssues).delete()
        #self.session.commit()
        pass