#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sys
import os

import pandas as pd
from datetime import timezone
from sqlalchemy import func

from lib.bitrise_conn import BitriseAPIClient
from utils.datetime_utils import DatetimeUtils as dt
from database import (
    Database,
    ReportBitriseBuildsCount
)


class Bitrise:

    def __init__(self):
        try:
            BITRISE_HOST = os.environ['BITRISE_HOST']
            self.client = BitriseAPIClient(BITRISE_HOST)
            self.client.BITRISE_APP_SLUG = os.environ['BITRISE_APP_SLUG']
            self.client.token = os.environ['BITRISE_TOKEN']
        except KeyError:
            print("ERROR: Missing bitrise env var")
            sys.exit(1)

    # API: Builds
    def builds(self, past_date_timestamp):
        return self.client.builds(self.client.BITRISE_APP_SLUG, past_date_timestamp) # noqa

    def builds_after_date(self, after):
        return self.client.builds_after_time(self.client.BITRISE_APP_SLUG, after) # noqa


class BitriseClient(Bitrise):

    def __init__(self):
        super().__init__()
        self.db = DatabaseBitrise()

    def bitrise_builds_detailed_info(self):
        # Read latest timestamp from database
        after = self.database_latest_build()
        print(after)

        # Query bitrise using after that date
        data = self.builds_after_date(after)

        payload = pd.DataFrame(data, columns=["build_number", "branch", "status", "status_text", "triggered_workflow", "triggered_by", "triggered_at"]) # noqa
        payload_filtered = payload[payload["status_text"] != "in-progress"]
        payload_filtered = payload_filtered.astype(object).where(pd.notna(payload_filtered), None) # noqa
        print(payload_filtered)

        self.db.report_bitrise_builds_info(payload_filtered)

    def database_latest_build(self):
        # Fetch latest triggered_at
        latest_ts = self.db.session.query(func.max(ReportBitriseBuildsCount.triggered_at)).scalar() # noqa
        print(latest_ts)
        # Assuming you already have this from your DB
        dt = latest_ts

        # Ensure it's timezone-aware (UTC), then convert to timestamp
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)

        unix_timestamp = int(dt.timestamp())
        print(f"Latest timestamp in database:{unix_timestamp}")
        return unix_timestamp


class DatabaseBitrise(Database):

    def __init__(self):
        super().__init__()
        self.db = Database()

    def report_bitrise_builds_info(self, payload):
        for index, row in payload.iterrows():
            report = ReportBitriseBuildsCount(
                build_number=row['build_number'],
                branch=row['branch'],
                status=row['status'],
                status_text=row['status_text'],
                triggered_workflow=row['triggered_workflow'],
                triggered_by=row['triggered_by'],
                triggered_at=dt.parse_iso_timestamp(row['triggered_at'])
            )
            self.session.add(report)
            self.session.commit()

    def report_bitrise_builds_count(self, payload):
        # Normalize the JSON data
        total_count = payload.get("paging", {}).get("total_item_count")

        data = [total_count]
        return data
