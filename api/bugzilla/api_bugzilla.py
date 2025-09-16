#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import re, requests, itertools, time
import pandas as pd
<<<<<<< HEAD
=======
from datetime import datetime
from sqlalchemy import func, distinct

>>>>>>> 509d61f (working changes)

from constants import PRODUCTS, FIELDS
from constants import BUGZILLA_BUGS_FIELDS, BUGZILLA_QA_WHITEBOARD_FILTER
from datetime import datetime
from lib.bugzilla_conn import BugzillaAPIClient
from sqlalchemy import func
from utils.datetime_utils import DatetimeUtils
from utils.retry_bz import with_retry

from database import (
    Database,
    ReportBugzillaQEVerifyCount,
    ReportBugzillaQENeeded,
    ReportBugzillaSoftvisionBugs,
    ReportBugzillaMetaBugs,
    ReportBugzillaQueryByKeyword,
)

#_CF_STATUS_RE = re.compile(r"^cf_status_firefox(\d+)$")
_CF_REL_RE = re.compile(r"^cf_status_firefox(\d+)$")
_FIELDS_URL = "https://bugzilla.mozilla.org/rest/field/bug"

class Bugz:

    def __init__(self) -> None:
        self.conn = BugzillaAPIClient()

    def get_bugs(self, bug_ids: list) -> list:
        bugs = with_retry(self.conn.bz_client.getbugs, bug_ids)
        return bugs

    def get_bug(self, bug_ids: list) -> list:
        bugs = with_retry(self.conn.bz_client.getbug, bug_ids)
        return bugs

    def build_query(self, query: dict) -> dict:
        formatted_query = with_retry(self.conn.bz_client.build_query, query)
        return formatted_query

    def query(self, query: dict) -> list:
        bugs = with_retry(self.conn.bz_client.query, query)
        return bugs

    def get_query_from_url(self, url: str) -> dict:
        query = with_retry(self.conn.bz_client.url_to_query, url)
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

    # 1) Discover only release-train fields, keep last N numerically
    def _discover_release_status_fields(self, keep_last_n: int = 5) -> list[str]:
        r = requests.get(_FIELDS_URL, timeout=30)
        r.raise_for_status()
        names = [f["name"] for f in r.json().get("fields", []) if "name" in f]

        releases = []
        for n in names:
            m = _CF_REL_RE.match(n)
            if m:
                releases.append((int(m.group(1)), n))
        releases.sort(key=lambda t: t[0])  # sort by version number

        if keep_last_n and len(releases) > keep_last_n:
            releases = releases[-keep_last_n:]  # keep the 5 most recent trains

        kept = [name for _, name in releases]
        versions = [v for v, _ in releases]
        print(f"[version-flags] Keeping last {len(kept)} release trains: {kept} (versions={versions})")
        return kept


    def get_distinct_bug_ids(self) -> list[int]:
        """
        Efficiently fetch distinct bug_ids you already track.
        Adjust the ORM model/class name & column to your schema.
        """
        # Example ORM model: ReportBugzillaDesktopBugs with .bug_id column
        q = (
            self.db.session
            .query(distinct(ReportBugzillaSoftvisionBugs.bugzilla_key))
        )
        # Optional: add where-clauses if you want to scope (e.g., only platform='desktop')
        # q = q.filter(ReportBugzillaDesktopBugs.platform == 'desktop')

        # Pull as Python ints
        bug_ids = [int(row[0]) for row in q.all() if row[0] is not None]
        return bug_ids

    def _chunked(self, iterable, size):
        it = iter(iterable)
        while True:
            batch = list(itertools.islice(it, size))
            if not batch:
                break
            yield batch

    def fetch_bug_history(self, bug_id: int, timeout=30):
        url = f"https://bugzilla.mozilla.org/rest/bug/{bug_id}/history"
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        j = r.json()
        # history is usually under j["bugs"][0]["history"]
        hist = []
        for b in j.get("bugs", []):
            hist.extend(b.get("history", []))
        # Normalize to list of (when, field_name, added, removed)
        out = []
        for h in hist:
            when = pd.to_datetime(h.get("when"), errors="coerce")
            for ch in h.get("changes", []):
                out.append((when, ch.get("field_name"), (ch.get("added") or "").strip().lower(), (ch.get("removed") or "").strip().lower()))
        # sort by time
        out.sort(key=lambda x: x[0] if pd.notna(x[0]) else pd.Timestamp.min)
        return out

    def first_time_flag_became_fixed_or_verified(self, history_rows, major: int):
        """Return the earliest timestamp when cf_status_firefox{major} became fixed/verified, or None."""
        field = f"cf_status_firefox{major}"
        first = None
        for when, fname, added, removed in history_rows:
            if fname == field and added in ("fixed", "verified"):
                first = when
                break
        return first

    def add_fixed_verified_timestamp(self, df: pd.DataFrame, sleep_sec=0.2):
        # Fast-path: if we already have cf_last_resolved and status fixed/verified, use it.
        # (cf_last_resolved comes back as string; coerce to Timestamp.)
        if "cf_last_resolved" in df.columns:
            df["cf_last_resolved"] = pd.to_datetime(df["cf_last_resolved"], errors="coerce")

        def fast_ts(row):
            if row["status"] in ("fixed", "verified") and pd.notna(row.get("cf_last_resolved")):
                return row["cf_last_resolved"]
            return pd.NaT

        df["flag_fixed_verified_at"] = df.apply(fast_ts, axis=1)

        # Choose bugs that still need history (no fast ts) but are actually fixed/verified
        need_mask = (
            (df["flag_fixed_verified_at"].isna()) &
            (
                df["status"].isin(["fixed", "verified"]) |
                (df.get("resolution", "").astype(str).str.lower() == "fixed")
            )
        )
        candidates = df.loc[need_mask, "bug_id"].dropna().astype(int).unique().tolist()
        if not candidates:
            return df

        # Fetch history once per bug_id
        hist_cache = {}
        for i, bid in enumerate(candidates, 1):
            try:
                hist_cache[bid] = self.fetch_bug_history(int(bid))
            except Exception as e:
                print(f"[history] bug {bid} error: {e}")
                hist_cache[bid] = []
            time.sleep(sleep_sec)  # be polite

        def compute_row_ts(row):
            # if we already filled from cf_last_resolved, keep it
            if pd.notna(row["flag_fixed_verified_at"]):
                return row["flag_fixed_verified_at"]
            # if not fixed/verified, leave NaT
            if (row["status"] not in ("fixed", "verified")) and (str(row.get("resolution","")).lower() != "fixed"):
                return pd.NaT
            hist = hist_cache.get(int(row["bug_id"]), [])
            ts = self.first_time_flag_became_fixed_or_verified(hist, int(row["version"]))
            return ts

        df["flag_fixed_verified_at"] = df.apply(compute_row_ts, axis=1)
        return df

    def bugzilla_collect_version_flags_for_tracked_bugs(self, keep_last_n: int = 5, batch_size: int = 400, save_csv: bool = True):
        """
        - discovers latest N cf_status_firefox* fields
        - fetches only for bug_ids already in your DB
        - returns a df with columns: bug_id, version, status, snapshot_date, last_change_time
        - optionally writes a timestamped CSV you can inspect
        """
        # 1) Discover release-train fields (you already have this)
        version_fields = self._discover_release_status_fields(keep_last_n=keep_last_n)
        if not version_fields:
            print("[version-flags] No cf_status_firefox* release fields found.")
            return pd.DataFrame()

        bug_ids = self.get_distinct_bug_ids()
        if not bug_ids:
            print("[version-flags] No tracked bug ids found in DB.")
            return pd.DataFrame()

        print(f"[version-flags] Collecting fields: {version_fields}")
        print(f"[version-flags] Tracked bug ids: {len(bug_ids)}")

        include_fields = [
            "id",
            "last_change_time",
            "qa_whiteboard",
            "cf_qa_whiteboard",
            "resolution",
            "cf_last_resolved",
        ] + version_fields
        snapshot_date = pd.Timestamp.utcnow().date()

        rows = []
        for batch in self._chunked(bug_ids, batch_size):
            query = {"id": ",".join(map(str, batch)), "include_fields": include_fields}
            bugs = BugzillaHelper().query(query)

            for bug in bugs:
                bug_last_change = (
                    pd.to_datetime(str(getattr(bug, "last_change_time", None)))
                    if getattr(bug, "last_change_time", None)
                    else pd.Timestamp.utcnow()
                )

                # capture once (same for all versions)
                cf_last_resolved = getattr(bug, "cf_last_resolved", None)

                for fname in version_fields:
                    m = _CF_REL_RE.match(fname)
                    if not m:
                        continue
                    version = int(m.group(1))
                    raw = getattr(bug, fname, None)
                    status = (str(raw).strip().lower() if raw and str(raw).strip() else '---')

                    rows.append({
                        "bug_id": int(bug.id),
                        "version": version,
                        "status": status,
                        "snapshot_date": snapshot_date,
                        "last_change_time": bug_last_change,
                        "qa-found-in": getattr(bug, "cf_qa_whiteboard", ""),          # <-- renamed, no hyphen
                        "resolution": getattr(bug, "resolution", None),
                        "cf_last_resolved": cf_last_resolved, # <-- for fast-path
                    })

        df = pd.DataFrame(rows)
        if df.empty:
            print(f"[version-flags] Snapshot {snapshot_date}: no rows")
            return df

        # Enrich with per-flag first-fixed/verified timestamp (fast-path + history where needed)
        df = self.add_fixed_verified_timestamp(df)

        print("[version-flags] Full dataframe (first 50 rows):")
        print(df.head(50).to_string(index=False))

        if save_csv:
            snapshot_ts = pd.Timestamp.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"version_flags_snapshot_{snapshot_ts}.csv"
            df.to_csv(filename, index=False)
            print(f"[version-flags] Saved snapshot to {filename}")

        print(
            f"[version-flags] Snapshot {snapshot_date}: {len(df)} rows | "
            f"versions={sorted(df['version'].unique())} | bugs={df['bug_id'].nunique()}"
        )
        return df

    def bugzilla_query_desktop_bugs(self):
        # Get latest entry in database to update bugs
        now_utc = datetime.utcnow()
        last_creation_time = self.db.session.query(func.max(ReportBugzillaSoftvisionBugs.bugzilla_bug_created_at)).scalar() # noqa
        creation_time = (last_creation_time + DatetimeUtils.delta_seconds(1)).strftime("%Y-%m-%dT%H:%M:%SZ") # noqa
        print(f"Last fetched bug created_at: {last_creation_time}")
        print(f"Fetch new bugs after : {creation_time}")
        print(f"Fetch new bugs up until : {now_utc.strftime('%Y-%m-%dT%H:%M:%SZ')}")

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
        self.db.report_bugzilla_desktop_bugs_update_insert(df_new)

        # Update data
        self.bugzilla_query_desktop_bugs_update()
        return df_new

    def bugzilla_query_desktop_bugs_update(self):
        # Query bugzilla with these fields where updated is > fecha query

        # Calculate start of yesterday in UTC
        last_change_time = (datetime.utcnow() - DatetimeUtils.delta_hours(48)).strftime("%Y-%m-%dT%H:%M:%SZ") # noqa
        print(f"Update bugs if any after {last_change_time}")

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

        self.db.report_bugzilla_desktop_bugs_update_insert(df_update)

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
                "creation_time": pd.to_datetime(str(b.creation_time)),
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

    def bugzilla_helper_refresh_bugs(self, bug_ids: list[int]):
        print(f"Refreshing {len(bug_ids)} bugs: {bug_ids}")
        bugs = BugzillaHelper().get_bugs(bug_ids)  # .get_bugs() fetches by ID list

        rows = []
        for bug in bugs:
            resolved_raw = getattr(bug, "cf_last_resolved", None)
            resolved_at = pd.to_datetime(str(resolved_raw)) if resolved_raw else None

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

        df_update = pd.DataFrame(rows)

        # This method does an UPDATE on conflict (not INSERT)
        self.db.bugzilla_desktop_bugs_update_insert(df_update)
        print(f"Updated {len(df_update)} bugs in database.")

    def bugzilla_query_by_keyword(self, keyword: str):
        """
        Query Bugzilla for all bugs with the given keyword.

        Parameters:
        - keyword (str): The keyword to search for in Bugzilla.

        Returns:
        - pd.DataFrame: A DataFrame of bugs matching the keyword.
        """
        query = {
            "keywords": keyword,
            "keywords_type": "allwords",
            "include_fields": BUGZILLA_BUGS_FIELDS
        }

        bugs = BugzillaHelper().query(query)

        rows = []
        for bug in bugs:
            resolved_raw = getattr(bug, "cf_last_resolved", None)
            resolved_at = pd.to_datetime(str(resolved_raw)) if resolved_raw else None

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

        df_bugs = pd.DataFrame(rows)
        print(df_bugs)
        print(f"Found {len(df_bugs)} bugs with keyword '{keyword}'.")

        self.db.clean_table(ReportBugzillaQueryByKeyword)
        self.db.report_bugzilla_query_by_keyword_insert(df_bugs)

        return df_bugs


class DatabaseBugzilla(Database):

    def __init__(self):
        super().__init__()
        self.db = Database()

    def qa_needed_delete(self):
        """ Wipe out all bugs.
        NOTE: we'll print daily bugs data from Bugzilla every day."""
        print("Delete entries from db first")
        self.clean_table(ReportBugzillaQENeeded)

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
            bugzilla_total_qa_needed=payload[0]
        )

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

    def report_bugzilla_desktop_bugs_update_insert(self, payload):
        for index, row in payload.iterrows():
            try:
                kw = row.get('keyword', [])
                bugzilla_bug_keyword = ", ".join(kw) if isinstance(kw, list) and kw else None # noqa

                bug_id = row['bug_id']

                # Check if the bug already exists
                existing = self.session.query(ReportBugzillaSoftvisionBugs).filter_by(
                    bugzilla_key=bug_id
                ).one_or_none()

                if existing:
                    print(f"Updating bug {bug_id}")
                    # Compare last_change_time to update
                    last_change_remote = pd.to_datetime(row['last_change_time'])
                    if last_change_remote > existing.bugzilla_bug_last_change_time:
                        existing.bugzilla_summary = row['summary']
                        existing.bugzilla_product = row['product']
                        existing.bugzilla_qa_whiteboard = row['qa_whiteboard']
                        existing.bugzilla_bug_severity = row['severity']
                        existing.bugzilla_bug_priority = row['priority']
                        existing.bugzilla_bug_status = row['status']
                        existing.bugzilla_bug_resolution = None if pd.isna(row['resolution']) else row['resolution'] # noqa
                        existing.bugzilla_bug_created_at = row['created_at']
                        existing.bugzilla_bug_last_change_time = row['last_change_time']
                        existing.bugzilla_bug_whiteboard = None if pd.isna(row['whiteboard']) else row['whiteboard'] # noqa
                        existing.bugzilla_bug_keyword = bugzilla_bug_keyword
                        existing.bugzilla_bug_resolved_at = None if pd.isna(row['resolved_at']) else row['resolved_at'] # noqa
                else:
                    print(f"Inserting new bug {bug_id}")
                    new_bug = ReportBugzillaSoftvisionBugs(
                        bugzilla_key=bug_id,
                        bugzilla_summary=row['summary'],
                        bugzilla_product=row['product'],
                        bugzilla_qa_whiteboard=row['qa_whiteboard'],
                        bugzilla_bug_severity=row['severity'],
                        bugzilla_bug_priority=row['priority'],
                        bugzilla_bug_status=row['status'],
                        bugzilla_bug_resolution=None if pd.isna(row['resolution']) else row['resolution'], # noqa
                        bugzilla_bug_created_at=row['created_at'],
                        bugzilla_bug_last_change_time=row['last_change_time'],
                        bugzilla_bug_whiteboard=None if pd.isna(row['whiteboard']) else row['whiteboard'], # noqa
                        bugzilla_bug_keyword=bugzilla_bug_keyword,
                        bugzilla_bug_resolved_at=None if pd.isna(row['resolved_at']) else row['resolved_at'] # noqa
                    )
                    self.session.add(new_bug)

            except KeyError as e:
                print(f"Missing key: {e} in row {index}")

        self.session.commit()

    def report_bugzilla_query_by_keyword_insert(self, payload):
        """
        Insert rows into the ReportBugzillaQueryByKeyword table.
        """
        for index, row in payload.iterrows():
            try:
                bugzilla_bug_keyword = (
                    ", ".join(row["keyword"])
                    if isinstance(row["keyword"], list)
                    else None
                )

                report = ReportBugzillaQueryByKeyword(
                    bugzilla_key=row["bug_id"],
                    bugzilla_summary=row["summary"],
                    bugzilla_product=row["product"],
                    bugzilla_qa_whiteboard=row["qa_whiteboard"],
                    bugzilla_bug_severity=row["severity"],
                    bugzilla_bug_priority=row["priority"],
                    bugzilla_bug_status=row["status"],
                    bugzilla_bug_resolution=(
                        None if pd.isna(row["resolution"]) else row["resolution"]
                    ),
                    bugzilla_bug_created_at=row["created_at"],
                    bugzilla_bug_last_change_time=row["last_change_time"],
                    bugzilla_bug_whiteboard=(
                        None if pd.isna(row["whiteboard"]) else row["whiteboard"]
                    ),
                    bugzilla_bug_keyword=bugzilla_bug_keyword,
                    bugzilla_bug_resolved_at=(
                        None if pd.isna(row["resolved_at"]) else row["resolved_at"]
                    ),
                )

                self.session.add(report)

            except KeyError as e:
                print(f"Missing key: {e} in row {index}")

        self.session.commit()
