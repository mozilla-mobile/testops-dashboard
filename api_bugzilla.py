#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import sys
import os
import pandas as pd
import datetime

from constants import PRODUCTS, FIELDS
from lib.bugzilla_conn import BugzillaAPIClient
from sqlalchemy import func
from datetime import timedelta

from database import (
    Database,
    ReportBugzillaQEVerifyCount,
    ReportBugzillaQENeeded,
    ReportBugzillaSoftvisionBugs
)


class Bugz:

    def __init__(self) -> None:
        self.conn = BugzillaAPIClient()

    def get_bugs(self, bug_ids: list) -> list:
        bugs = self.conn.bz_client.getbugs(bug_ids)
        return bugs

    def build_query(self, query: dict) -> dict:
        formatted_query = self.conn.bz_client.build_query(query)
        return formatted_query

    def query(self, query: dict) -> list:
        bugs = self.conn.bz_client.query(query)
        return bugs

    def get_query_from_url(self, url: str) -> dict:
        query = self.conn.bz_client.url_to_query(url)
        return query


class BugzillaHelper:
    def __init__(self) -> None:
        self.bugzilla = Bugz()

    def get_bugs(self, bugs: list) -> list:
        """Get a list of bugs from Bugzilla."""
        return self.bugzilla.get_bugs(bugs)

    def build_query(self, query: dict) -> dict:
        """Build a query for Bugzilla."""
        return self.bugzilla.build_query(query)

    def query(self, query: dict) -> list:
        """Query Bugzilla."""
        return self.bugzilla.query(query)

    def get_query_from_url(self, url: str) -> dict:
        """Get a query from a Bugzilla URL."""
        return self.bugzilla.get_query_from_url(url)


class BugzillaClient(Bugz):
    def __init__(self):
        super().__init__()
        self.db = DatabaseBugzilla()
        self.BugzillaHelperClient = BugzillaHelper()

    def contains_flags(self, entry, criteria):
        return all(entry.get(key) == value for key, value in criteria.items())


    def bugzilla_query_qa_found_in(self):
        CSV_PATH = "bugzilla_qa_found_in.csv"

        # Load existing data (if any)
        ''' Debugging with spreadsheet
        if os.path.exists(CSV_PATH):
            df_existing = pd.read_csv(CSV_PATH, parse_dates=["created_at"])
            last_created_at = df_existing["created_at"].max()
        else:
            df_existing = pd.DataFrame()
            # fallback start date
            last_created_at = datetime.datetime(2025, 6, 19)
        '''

        # Format for Bugzilla API
        #creation_time = last_created_at.strftime("%Y-%m-%dT%H:%M:%SZ")

        last_creation_time = self.db.session.query(func.max(ReportBugzillaSoftvisionBugs.bugzilla_bug_created_at)).scalar() # noqa
        next_day = (last_creation_time + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        creation_time = next_day.strftime("%Y-%m-%dT%H:%M:%SZ")
        print(f"Last fetched bug created_at: {last_creation_time}")
        print(creation_time)
        
        # Query new bugs
        query = {
            "cf_qa_whiteboard_type": "substring",
            "cf_qa_whiteboard": "qa-found-in-",
            "creation_time": creation_time,
            "include_fields": ["id", "summary", "product", "cf_qa_whiteboard", "severity", "priority", "status", "resolution", "creation_time", "last_change_time"]
        }

        # Use existing helper
        bugs = BugzillaHelper().query(query)

        # Transform to list of dicts
        rows = []
        for bug in bugs:
            rows.append({
                "bug_id": bug.id,
                "summary": bug.summary,
                "product": bug.product,
                "qa_whiteboard": getattr(bug, "cf_qa_whiteboard", ""),
                "severity": bug.severity,
                "priority": bug.priority,
                "status": bug.status,
                "resolution": bug.resolution,
                "created_at": pd.to_datetime(str(bug.creation_time)),
                "last_change_time": pd.to_datetime(str(bug.last_change_time))
            })
        # Convert to DataFrame
        df_new = pd.DataFrame(rows)
        print(df_new)
        '''
        # Append to existing (with deduplication)
        if not df_existing.empty:
            df_all = pd.concat([df_existing, df_new]).drop_duplicates(subset="bug_id")
        else:
            df_all = df_new
        '''
        # Save back to CSV
        #df_all.to_csv(CSV_PATH, index=False)

        print(f"Saved {len(df_new)} new bugs. Total now: {len(df_new)}")
        print(df_new)
        self.db.report_bugzilla_softvision_bugs(df_new)
        return df_new

    def bugzilla_query(self):
        all_bugs = []
        for product in PRODUCTS:
            query = dict(product=product, include_fields=FIELDS)
            bugs = self.BugzillaHelperClient.query(query)

            for bug in bugs:
                bug_ = [bug.id, bug.summary, bug.flags,
                        bug.severity, bug.priority, bug.status, bug.resolution]
                all_bugs.append(bug_)

        return all_bugs

    def bugzilla_query_qe_verify(self):
        qe_bugs = []
        search_criteria = {'name': 'qe-verify'}

        payload = self.bugzilla_query()
        for bug in payload:
            result = any(self.contains_flags(entry, search_criteria) for entry in bug[2]) # noqa
            if result:
                qe_bugs.append(bug)
        return qe_bugs

    def bugzilla_query_severity(self):
        # payload = self.bugzilla_query()

        # TBD to get all NEW bugs
        return

    def bugzilla_qe_verify(self):
        payload = self.bugzilla_query_qe_verify()
        rows = []
        # Based on the filter, this is an example of a bug
        # [1909150, 'Description',
        # [{'id': 2244803, 'setter': 'email@mozilla.com', 'type_id': 864,
        # 'creation_date': <DateTime '20240917T09:39:02' at 0x147cb6cf0>,
        # 'name': 'qe-verify',
        # 'modification_date': <DateTime '20240917T09:39:02' at 0x147cb6d50>,
        # 'status': '+'}], 'N/A', 'P2', 'RESOLVED', 'FIXED']

        for bug in payload:
            bug_id = bug[0]       # 1909150
            description = bug[1]  # 'Description of the bug'
            severity = bug[3]     # 'S2'
            priority = bug[4]     # 'P1'
            status = bug[5]       # 'RESOLVED'
            resolution = bug[6]   # 'FIXED'
            # If there are additional fields due to flag field(sub-entry)
            # iterate over them
            for sub_entry in bug[2]: # [{'id': 2244803, 'setter': 'email@mozilla.com', 'type_id': 864, # noqa
                                     # 'creation_date': '20240917T09:39:02', 'name': 'qe-verify',      # noqa
                                     # 'modification_date': '20240917T09:39:02', 'status': '+'}]       # noqa
                if sub_entry['name'] == 'qe-verify' and sub_entry['status'] == '+':                    # noqa
                    row = {"bug_id": bug_id, "description": description,
                           **sub_entry, "severity": severity,
                           "priority": priority,
                           "bug_status": status, "resolution": resolution}

                    rows.append(row)

        self.db.qa_needed_delete()

        if not rows:
            print("There are no bugs to verify today")

        else:
            # Create the DataFrame
            df = pd.DataFrame(rows)

            df['modification_date'] = pd.to_datetime(df['modification_date'], format='%Y%m%dT%H:%M:%S') # noqa
            df['creation_date'] = pd.to_datetime(df['creation_date'], format='%Y%m%dT%H:%M:%S') # noqa

            # Drop the columns 'type_id' and 'id'
            df_cleaned = df.drop(columns=["type_id", "id"])

            data_frame = self.db.report_bugzilla_qa_needed(df_cleaned)
            self.db.report_bugzilla_qa_needed_insert(data_frame)

            qe_needed_count = self.db.report_bugzilla_qa_needed_count(data_frame) # noqa
            self.db.report_bugzilla_qa_needed_count_insert(qe_needed_count)


class DatabaseBugzilla(Database):

    def __init__(self):
        super().__init__()
        self.db = Database()

    def qa_needed_delete(self):
        """ Wipe out all bugs.
        NOTE: we'll print daily bugs data from Bugzilla every day."""
        print("Delete entries from db first")
        self.session.query(ReportBugzillaQENeeded).delete()
        self.session.commit()

    def report_bugzilla_softvision_bugs(self, payload):
        for index, row in payload.iterrows():
            try:
                report = ReportBugzillaSoftvisionBugs(
                            bugzilla_key=row['bug_id'],
                            bugzilla_summary=row['summary'],
                            bugzilla_product=row['product'],
                            bugzilla_qa_whiteboard=row['qa_whiteboard'],
                            bugzilla_bug_severity=row['severity'],
                            bugzilla_bug_priority=row['priority'],
                            bugzilla_bug_status=row['status'],
                            bugzilla_bug_resolution= None if pd.isna(row['resolution']) else row['resolution'],
                            bugzilla_bug_created_at=row['created_at'],
                            bugzilla_bug_last_change_time=row['last_change_time']
                    )
            except KeyError as e:
                print(f"Missing key: {e} in row {index}")
            self.session.add(report)
        self.session.commit()


    def report_bugzilla_qa_needed(self, payload):

        selected_columns = {
            'bug_id': 'bugzilla_key',
            'description': 'bugzilla_summary',
            'modification_date': 'bugzilla_modified_at',
            'name': 'bugzilla_tag_name',
            'creation_date': 'bugzilla_created_at',
            'status': 'bugzilla_tag_status',
            'setter': 'bugzilla_tag_setter',
            'severity': 'bugzilla_bug_severity',
            'priority': 'bugzilla_bug_priority',
            'bug_status': 'bugzilla_bug_status',
            'resolution': 'bugzilla_bug_resolution'
        }

        # Select specific columns
        df = payload[selected_columns.keys()]

        # Rename columns
        df = df.rename(columns=selected_columns)
        return df

    def report_bugzilla_qa_needed_insert(self, payload):
        for index, row in payload.iterrows():
            print(row)
            try:
                report = ReportBugzillaQENeeded(
                            bugzilla_key=row['bugzilla_key'],
                            bugzilla_summary=row['bugzilla_summary'],
                            buzilla_modified_at=row['bugzilla_modified_at'],
                            bugzilla_tag_name=row['bugzilla_tag_name'],
                            bugzilla_created_at=row['bugzilla_created_at'],
                            bugzilla_tag_status=row['bugzilla_tag_status'],
                            bugzilla_tag_setter=row['bugzilla_tag_setter'],
                            bugzilla_bug_severity=row['bugzilla_bug_severity'],
                            bugzilla_bug_priority=row['bugzilla_bug_priority'],
                            bugzilla_bug_status=row['bugzilla_bug_status'],
                            bugzilla_bug_resolution=row['bugzilla_bug_resolution'] # noqa
                    )
            except KeyError as e:
                print(f"Missing key: {e} in row {index}")
            self.session.add(report)
        self.session.commit()

    def report_bugzilla_qa_needed_count(self, payload):
        total_rows = len(payload)
        data = [total_rows]
        return data

    def report_bugzilla_qa_needed_count_insert(self, payload):
        report = ReportBugzillaQEVerifyCount(
                        bugzilla_total_qa_needed=payload[0])

        self.session.add(report)
        self.session.commit()
