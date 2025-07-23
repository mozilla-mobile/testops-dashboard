#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import pandas as pd
from datetime import datetime
from sqlalchemy import func

from constants import PRODUCTS, FIELDS
from constants import BUGZILLA_BUGS_FIELDS, BUGZILLA_QA_WHITEBOARD_FILTER
from lib.bugzilla_conn import BugzillaAPIClient
from utils.datetime_utils import DatetimeUtils

from database import (
    Database,
    ReportBugzillaQEVerifyCount,
    ReportBugzillaQENeeded,
    ReportBugzillaSoftvisionBugs,
    ReportBugzillaMetaBugs,
)


class Bugz:

    def __init__(self) -> None:
        self.conn = BugzillaAPIClient()

    def get_bugs(self, bug_ids: list) -> list:
        bugs = self.conn.bz_client.getbugs(bug_ids)
        return bugs

    def get_bug(self, bug_ids: list) -> list:
        bugs = self.conn.bz_client.getbug(bug_ids)
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

    def get_bug(self, bug: int) -> list:
        """Get a list of bugs from Bugzilla."""
        return self.bugzilla.get_bug(bug)

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

    def bugzilla_query_desktop_bugs(self):
        # Get latest entry in database to update bugs
        last_creation_time = self.db.session.query(func.max(ReportBugzillaSoftvisionBugs.bugzilla_bug_created_at)).scalar() # noqa
        next_day = (last_creation_time + DatetimeUtils.delta_days(1)).replace(hour=0, minute=0, second=0, microsecond=0) # noqa
        creation_time = next_day.strftime("%Y-%m-%dT%H:%M:%SZ")
        print(f"Last fetched bug created_at: {last_creation_time}")
        print(f"Fetch new bugs up until : {creation_time}")

        # Query new bugs
        query = {
            **BUGZILLA_QA_WHITEBOARD_FILTER,
            "creation_time": creation_time,
            "include_fields": BUGZILLA_BUGS_FIELDS

        }

        # Use existing helper
        bugs = BugzillaHelper().query(query)

        rows = []
        for bug in bugs:
            resolved_raw = getattr(bug, "cf_last_resolved", None)
            resolved_at = pd.to_datetime(str(resolved_raw)) if resolved_raw else None # noqa

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
                "last_change_time": pd.to_datetime(str(bug.last_change_time)),
                "whiteboard": bug.whiteboard,
                "keyword": bug.keywords,
                "resolved_at": resolved_at
            })

        # Convert to DataFrame
        df_new = pd.DataFrame(rows)
        print(df_new)
        print(f"Saved {len(df_new)} new bugs. Total now: {len(df_new)}")

        # Insert data
        self.db.report_bugzilla_desktop_bugs(df_new)

        # Update data
        self.bugzilla_query_desktop_bugs_update()
        return df_new

    def bugzilla_query_desktop_bugs_update(self):
        # Query bugzilla with these fields where updated is > fecha query

        # Calculate start of yesterday in UTC
        yesterday = datetime.utcnow().date() - DatetimeUtils.delta_days(1)
        last_change_time = f"{yesterday}T00:00:00Z"
        print(f"Update bugs if any after yesterday {last_change_time}")

        query = {
            **BUGZILLA_QA_WHITEBOARD_FILTER,
            "last_change_time": last_change_time,
            "include_fields": BUGZILLA_BUGS_FIELDS
        }

        # Use existing helper
        bugs = BugzillaHelper().query(query)

        rows = []
        for bug in bugs:
            resolved_raw = getattr(bug, "cf_last_resolved", None)
            resolved_at = pd.to_datetime(str(resolved_raw)) if resolved_raw else None # noqa

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
                "last_change_time": pd.to_datetime(str(bug.last_change_time)),
                "whiteboard": bug.whiteboard,
                "keyword": bug.keywords,
                "resolved_at": resolved_at
            })

        # Convert to DataFrame
        df_update = pd.DataFrame(rows)
        print(f"Updated {len(df_update)} bugs")

        self.db.bugzilla_desktop_bugs_update_insert(df_update)

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

    def bugzilla_meta_bug(self, meta_bug_id: int):
        bug = self.BugzillaHelperClient.get_bug(meta_bug_id)
        print(f"Bug {bug.id}: {bug.summary}")
        print("Depends on:", bug.depends_on)

        query = {
            "bug_id": bug.depends_on,
            "include_fields": BUGZILLA_BUGS_FIELDS + ["assigned_to", "product"]
        }
        child_bugs = BugzillaHelper().query(query)

        rows = []
        for b in child_bugs:
            resolved_raw = getattr(b, "cf_last_resolved", None)
            resolved_at = pd.to_datetime(str(resolved_raw)) if resolved_raw else None # noqa

            rows.append({
                "id": b.id,
                "status": b.status,
                "summary": b.summary,
                "creation_time": pd.to_datetime(str(bug.creation_time)),
                "resolution": b.resolution,
                "severity": b.severity,
                "priority": b.priority,
                "assigned_to": getattr(b, "assigned_to", None),
                "keywords": ", ".join(b.keywords),
                "cf_last_resolution": resolved_at,
                "parent_bug_id": meta_bug_id,
                "product": b.product,
            })

        # Create DataFrame
        df = pd.DataFrame(rows)
        self.db.clean_table(ReportBugzillaMetaBugs)

        self.db.report_bugzilla_meta_bug(df)

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
        self.clean_table(ReportBugzillaQENeeded)

    def clean_table(self, table):
        self.session.query(table).delete()
        self.session.commit()

    def bugzilla_desktop_bugs_update_insert(self, payload):
        for index, row in payload.iterrows():
            try:
                kw = row.get('keyword', [])
                bugzilla_bug_keyword = ", ".join(kw) if isinstance(kw, list) and kw else None # noqa

                bug_id = row['bug_id']

                # Check if the bug already exists
                existing = self.session.query(ReportBugzillaSoftvisionBugs).filter_by( # noqa
                    bugzilla_key=bug_id
                ).one_or_none()
                if existing:
                    print(f"Updating bug {bug_id}")
                    # Compare last_change_time to update
                    last_change_remote = pd.to_datetime(row['last_change_time']) # noqa
                    if last_change_remote > existing.bugzilla_bug_last_change_time: # noqa
                        existing.bugzilla_summary = row['summary']
                        existing.bugzilla_product = row['product']
                        existing.bugzilla_qa_whiteboard = row['qa_whiteboard']
                        existing.bugzilla_bug_severity = row['severity']
                        existing.bugzilla_bug_priority = row['priority']
                        existing.bugzilla_bug_status = row['status']
                        existing.bugzilla_bug_resolution = None if pd.isna(row['resolution']) else row['resolution'] # noqa
                        existing.bugzilla_bug_created_at = row['created_at']
                        existing.bugzilla_bug_last_change_time = row['last_change_time'] # noqa
                        existing.bugzilla_bug_whiteboard = None if pd.isna(row['whiteboard']) else row['whiteboard'] # noqa

                        existing.bugzilla_bug_keyword = bugzilla_bug_keyword,
                        existing.bugzilla_bug_resolved_at = None if pd.isna(row['resolved_at']) else row['resolved_at'] # noqa
            except KeyError as e:
                print(f"Missing key: {e} in row {index}")

        self.session.commit()

    def report_bugzilla_desktop_bugs(self, payload):
        for index, row in payload.iterrows():
            try:
                kw = row.get('keyword', [])
                bugzilla_bug_keyword = ", ".join(kw) if isinstance(kw, list) and kw else None # noqa

                report = ReportBugzillaSoftvisionBugs(
                            bugzilla_key=row['bug_id'],
                            bugzilla_summary=row['summary'],
                            bugzilla_product=row['product'],
                            bugzilla_qa_whiteboard=row['qa_whiteboard'],
                            bugzilla_bug_severity=row['severity'],
                            bugzilla_bug_priority=row['priority'],
                            bugzilla_bug_status=row['status'],
                            bugzilla_bug_resolution=None if pd.isna(row['resolution']) else row['resolution'], # noqa
                            bugzilla_bug_created_at=row['created_at'],
                            bugzilla_bug_last_change_time=row['last_change_time'], # noqa
                            bugzilla_bug_whiteboard=None if pd.isna(row['whiteboard']) else row['whiteboard'], # noqa
                            bugzilla_bug_keyword=bugzilla_bug_keyword,
                            bugzilla_bug_resolved_at=None if pd.isna(row['resolved_at']) else row['resolved_at'] # noqa
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

    def report_bugzilla_meta_bug(self, payload):
        for index, row in payload.iterrows():
            print(row)
            try:
                report = ReportBugzillaMetaBugs(
                    bugzilla_key=row['id'],
                    bugzilla_summary=row['summary'],
                    bugzilla_bug_status=row['status'],
                    bugzilla_bug_created_at=row['creation_time'],
                    bugzilla_bug_resolution=None if pd.isna(row['resolution']) else row['resolution'], # noqa
                    bugzilla_bug_severity=row['severity'],
                    bugzilla_bug_priority=row['priority'],
                    bugzilla_bug_assigned_to=row['assigned_to'],
                    bugzilla_bug_keyword=row['keywords'],
                    bugzilla_bug_resolved_at=None if pd.isna(row['cf_last_resolution']) else row['cf_last_resolution'], # noqa            
                    bugzilla_bug_parent=row['parent_bug_id'],
                    bugzilla_bug_product=row['product']
                )
            except KeyError as e:
                print(f"Missing key: {e} in row {index}")
            self.session.add(report)
        self.session.commit()
