#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import logging
import re
import requests
import time
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from requests.exceptions import HTTPError, RequestException
from sqlalchemy import func, select

from constants import PRODUCTS, FIELDS
from constants import BUGZILLA_BUGS_FIELDS, BUGZILLA_QA_WHITEBOARD_FILTER
from lib.bugzilla_conn import BugzillaAPIClient
from utils.datetime_utils import DatetimeUtils
from utils.retry_bz import with_retry

from database import (
    Database,
    ReportBugzillaQEVerifyCount,
    ReportBugzillaQENeeded,
    ReportBugzillaSoftvisionBugs,
    ReportBugzillaMetaBugs,
    ReportBugzillaQueryByKeyword,
    ReportBugzillaReleaseFlagsBugs,
)

FIREFOX_FLAG_STATUS_VERSION = re.compile(r"^cf_status_firefox(\d+)$")
BUGZILLA_API_BASE = "https://bugzilla.mozilla.org/rest"


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

    """
    Fetch the history of a Bugzilla bug safely
    """
    def fetch_bug_history(self, bug_id: int, timeout: int = 30) -> list[tuple]:
        url = f"{BUGZILLA_API_BASE}/bug/{bug_id}/history"
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        j = r.json()

        hist = []
        for b in j.get("bugs", []):
            hist.extend(b.get("history", []))

        out = []
        for h in hist:
            when = pd.to_datetime(h.get("when"), errors="coerce")
            for ch in h.get("changes", []):
                out.append((
                    when,
                    ch.get("field_name"),
                    (ch.get("added") or "").strip().lower(),
                    (ch.get("removed") or "").strip().lower(),
                ))
        out.sort(key=lambda x: x[0] if pd.notna(x[0]) else pd.Timestamp.min)
        return out

    """
    Fetch the history several bugs safely
    """
    def fetch_many_bug_histories(
        self,
        bug_ids: list[int],
        *,
        session: requests.Session | None = None,
        max_workers: int = 5,
        batch_size: int = 100,
        timeout: int = 30,
        retries: int = 2,
        sleep_sec: float = 0.2,
        stream_callback=None,
    ) -> dict[int, list[tuple]] | None:
        """
        Concurrently fetch histories for many Bugzilla bugs.

        - Uses ThreadPoolExecutor for concurrency (default 5 workers).
        - Processes IDs in batches to limit memory/pressure.
        - Retries with exponential backoff; honors Retry-After on 429.
        - If stream_callback is provided, calls stream_callback(bug_id, history)
          as results arrive and returns None. Otherwise returns {bug_id: history}.
        """

        results = {} if stream_callback is None else None
        # s = session or requests.Session()

        def _sleep_backoff(attempt: int, retry_after: float | None = None):
            if retry_after is not None and retry_after > 0:
                time.sleep(retry_after)
            else:
                time.sleep(sleep_sec * (2 ** attempt))

        def _fetch_one(bug_id: int) -> tuple[int, list[tuple]]:
            err: Exception | None = None
            for attempt in range(retries + 1):
                try:
                    # Reuse same session by temporarily swapping in self.fetch_bug_history's call # noqa
                    # fetch_bug_history accepts timeout; it constructs and uses requests.get directly. # noqa
                    # Keep using that method for consistency and single parsing logic.
                    history = self.fetch_bug_history(bug_id, timeout=timeout)
                    return bug_id, history
                except HTTPError as e:
                    err = e
                    retry_after = None
                    try:
                        # If the server rate-limits, honor Retry-After if available
                        retry_after_hdr = getattr(e.response, "headers", {}).get("Retry-After") # noqa
                        if retry_after_hdr:
                            try:
                                retry_after = float(retry_after_hdr)
                            except ValueError:
                                retry_after = None
                    except Exception:
                        retry_after = None
                    logging.warning(f"[history] {bug_id} HTTP error: {e}. attempt={attempt}/{retries}") # noqa
                    if attempt < retries:
                        _sleep_backoff(attempt, retry_after)
                except RequestException as e:
                    err = e
                    logging.warning(f"[history] {bug_id} request error: {e}. attempt={attempt}/{retries}") # noqa
                    if attempt < retries:
                        _sleep_backoff(attempt)
                except Exception as e:
                    err = e
                    logging.warning(f"[history] {bug_id} unexpected error: {e}. attempt={attempt}/{retries}") # noqa
                    if attempt < retries:
                        _sleep_backoff(attempt)

            # Final failure
            logging.warning(f"[history] failed permanently for bug {bug_id}: {err}")
            return bug_id, []

        # Work in batches to control memory and API pressure
        total = len(bug_ids)
        for i in range(0, total, batch_size):
            batch = bug_ids[i: i + batch_size]
            logging.info(f"[history] Fetching bug histories {i+1}–{i+len(batch)} of {total}" # noqa
                         f"(workers={max_workers}, batch_size={batch_size})")

            # Small politeness delay between batches
            if i > 0:
                time.sleep(sleep_sec)

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(_fetch_one, bid) for bid in batch]
                for fut in as_completed(futures):
                    bug_id, history = fut.result()
                    if stream_callback:
                        try:
                            stream_callback(bug_id, history)
                        except Exception as cb_err:
                            logging.error(f"[history] stream_callback failed for bug {bug_id}: {cb_err}") # noqa
                    else:
                        results[bug_id] = history
        return results


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

    def fetch_bug_history(self, bug_id: int, timeout: int = 30) -> list[tuple]:
        return self.bugzilla.fetch_bug_history(bug_id, timeout=timeout)

    def fetch_many_bug_histories(
                self,
                bug_ids: list[int],
                *,
                session: requests.Session | None = None,
                max_workers: int = 5,
                batch_size: int = 100,
                timeout: int = 30,
                retries: int = 2,
                sleep_sec: float = 0.2,
                stream_callback=None,
            ) -> dict[int, list[tuple]] | None:
        """
        Helper passthrough callers use workers/streaming without touching Bugz directly # noqa
        """
        return self.bugzilla.fetch_many_bug_histories(
            bug_ids=bug_ids,
            session=session,
            max_workers=max_workers,
            batch_size=batch_size,
            timeout=timeout,
            retries=retries,
            sleep_sec=sleep_sec,
            stream_callback=stream_callback,
        )


class BugzillaClient(Bugz):
    def __init__(self):
        super().__init__()
        self.db = DatabaseBugzilla()
        self.BugzillaHelperClient = BugzillaHelper()

    def contains_flags(self, entry, criteria):
        print("CONTAIN_FLAGS")
        return all(entry.get(key) == value for key, value in criteria.items())

    def get_bugs_from_database(self, chunk_size: int = 10_000) -> str:
        """
        Export bugs from ReportBugzillaSoftvisionBugs where resolution is not in
        the filter, only those bugs will have status flags
        """
        R = ReportBugzillaSoftvisionBugs

        excluded_resolutions = [
                                "WONTFIX", "INVALID",
                                "WORKSFORME", "DUPLICATE", "MOVED"
                                ]

        norm_res = func.upper(func.trim(R.bugzilla_bug_resolution))

        filter_condition = (R.bugzilla_bug_resolution.is_(None)) | \
                           (func.trim(R.bugzilla_bug_resolution) == "") | \
                           (~norm_res.in_(excluded_resolutions))

        stmt = select(R.__table__).where(filter_condition)

        # Engine/connection bound to the session
        engine = self.db.session.get_bind()
        bug_ids: list[int] = []

        for chunk in pd.read_sql(stmt, engine, chunksize=chunk_size):
            # Collect bug IDs from bugzilla_key column
            bug_ids.extend(chunk["bugzilla_key"].dropna().astype(int).tolist())

        print(f"[export_filtered_bugs_to_csv_and_ids] Found {len(bug_ids)} bug IDs")
        return bug_ids

    def _discover_release_status_fields(self, keep_last_n: int = 5) -> list[str]:
        # Get last N release-train fields
        url = f"{BUGZILLA_API_BASE}/field/bug"
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        names = [f["name"] for f in r.json().get("fields", []) if "name" in f]

        releases = []
        for n in names:
            m = FIREFOX_FLAG_STATUS_VERSION.match(n)
            if m:
                releases.append((int(m.group(1)), n))
        releases.sort(key=lambda t: t[0])  # sort by version number

        if keep_last_n and len(releases) > keep_last_n:
            releases = releases[-keep_last_n:]  # keep the 5 most recent trains

        kept = [name for _, name in releases]
        versions = [v for v, _ in releases]
        print(f"[version-flags] last {len(kept)}: {kept} (versions={versions})")
        return kept

    def first_fixed_verified_by_version(self, history_rows):
        """
        Parse a bug's history and return {version:int -> first_timestamp: pd.Timestamp}
        for the earliest time each cf_status_firefox{version} became fixed/verified.
        """
        out = {}
        for when, fname, added, removed in history_rows:
            m = FIREFOX_FLAG_STATUS_VERSION.match(fname or "")
            if not m:
                continue
            if added in ("fixed", "verified"):
                v = int(m.group(1))
                # first occurrence only
                if v not in out:
                    out[v] = when
        return out

    def bugzilla_query_release_flags_for_tracked_bugs(
        self,
        keep_last_n: int = 5,
        batch_size: int = 400,
        save_csv: bool = True,
        *,
        hist_workers: int = 6,
        hist_batch_size: int = 200,
        hist_timeout: int = 30,
        hist_retries: int = 2,
    ):
        version_fields = self._discover_release_status_fields(keep_last_n=keep_last_n)
        if not version_fields:
            return pd.DataFrame()

        bug_ids = self.get_bugs_from_database()
        if not bug_ids:
            return pd.DataFrame()

        include_fields = ["id", "type", "cf_qa_whiteboard", "resolution",
                          "keywords", "severity"] + version_fields
        rows = []

        for i in range(0, len(bug_ids), batch_size):
            batch = bug_ids[i:i + batch_size]
            query = {"id": ",".join(map(str, batch)), "include_fields": include_fields}
            bugs = BugzillaHelper().query(query)

            for bug in bugs:
                for fname in version_fields:
                    m = FIREFOX_FLAG_STATUS_VERSION.match(fname)
                    if not m:
                        continue
                    version = int(m.group(1))
                    raw = getattr(bug, fname, None)
                    status = (str(raw).strip().lower() if raw and str(raw).strip() else '---') # noqa

                    rows.append({
                        "bugzilla_key": int(bug.id),
                        "type": bug.type,
                        "flag-version": version,
                        "status": status,
                        "keywords": ", ".join(bug.keywords),
                        "severity": bug.severity,
                        "qa-found-in": getattr(bug, "cf_qa_whiteboard", ""),
                        "resolution": getattr(bug, "resolution", None)
                    })

        df = pd.DataFrame(rows)
        if df.empty:
            return df

        # Only fetch histories for fixed/verified flags
        need_mask = df["status"].isin(["fixed", "verified"])
        candidate_ids = (
            df.loc[need_mask, "bugzilla_key"]
              .dropna().astype(int).unique().tolist()
        )

        if candidate_ids:
            # Concurrent history fetch (keeps results in memory)
            with requests.Session() as sess:
                hist_cache = self.BugzillaHelperClient.fetch_many_bug_histories(
                    candidate_ids,
                    session=sess,
                    max_workers=hist_workers,
                    batch_size=hist_batch_size,
                    timeout=hist_timeout,
                    retries=hist_retries,
                    stream_callback=None,  # return dict
                )

            # Precompute version->first_ts per bug
            first_ts_map = {
                bid: self.first_fixed_verified_by_version(hist_cache.get(bid, []))
                for bid in candidate_ids
            }

            def compute_row_ts(row):
                if row["status"] not in ("fixed", "verified"):
                    return pd.NaT
                bid = int(row["bugzilla_key"])
                v = int(row["flag-version"])
                return first_ts_map.get(bid, {}).get(v, pd.NaT)

            df["bugzilla_flag_fixed_at"] = df.apply(compute_row_ts, axis=1)
        else:
            df["bugzilla_flag_fixed_at"] = pd.NaT

        if save_csv:
            snapshot_ts = pd.Timestamp.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"version_flags_snapshot_{snapshot_ts}.csv"
            df.to_csv(filename, index=False)
            print(f"[version-flags] Saved snapshot to {filename}")

        print(f"versions={sorted(df['flag-version'].unique())} | bugs={df['bugzilla_key'].nunique()}") # noqa
        print(df)

        self.db.clean_table(ReportBugzillaReleaseFlagsBugs)
        self.db.report_bugzilla_query_release_flags_for_bugs(df)
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
        self.db.report_bugzilla_desktop_bugs_update_insert(df_update)
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

    def report_bugzilla_query_release_flags_for_bugs(self, payload):
        print(payload)
        for index, row in payload.iterrows():
            try:
                bugzilla_bug_keywords = (
                    ", ".join(row["keywords"])
                    if isinstance(row["keywords"], list)
                    else None
                )
                report = ReportBugzillaReleaseFlagsBugs(
                    bugzilla_key=row['bugzilla_key'],
                    bugzilla_bug_type=row['type'],
                    bugzilla_release_version=row['flag-version'],
                    bugzilla_bug_status=row['status'],
                    bugzilla_bug_keywords=bugzilla_bug_keywords,
                    bugzilla_bug_severity=row['severity'],
                    bugzilla_bug_qa_found_in=row['qa-found-in'],
                    bugzilla_bug_resolution=row['resolution'],
                    bugzilla_bug_flag_fixed_at=None if pd.isna(row['bugzilla_flag_fixed_at']) else row['bugzilla_flag_fixed_at']) # noqa
                self.session.add(report)
            except KeyError as e:
                print(f"Missing key: {e} in row {index}")
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
