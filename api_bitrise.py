import time
import sys
import os

import pandas as pd
from datetime import datetime
from datetime import timezone
from sqlalchemy import func

from lib.bitrise_conn import BitriseAPIClient
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
        return self.client.get_builds(self.client.BITRISE_APP_SLUG, past_date_timestamp) # noqa

    def get_builds_range_date(self, after):
        return self.client.get_builds_time(self.client.BITRISE_APP_SLUG, after)


class BitriseClient(Bitrise):

    def __init__(self):
        super().__init__()
        self.db = DatabaseBitrise()

    def builds_daily_count(self):
        days_ago = 1
        today = datetime.datetime.utcnow().date()
        past_date = today - datetime.timedelta(days=days_ago)
        print(past_date)
        past_date_timestamp = int(time.mktime(past_date.timetuple()))
        print(past_date_timestamp)

        # Pull JSON blob from Bitrise
        # payload = self.builds(past_date_timestamp)

        # data_frame = self.db.report_bitrise_builds_count(payload)
        # self.db.report_bitrise_builds_count_insert(data_frame)

    def builds_detailed_info(self):
        # Read latest timestamp from database
        after = self.get_latest_build()
        print(after)

        # Query bitrise using after that date
        data = self.get_builds_range_date(after)

        payload = pd.DataFrame(data, columns=["build_number", "branch", "status", "status_text", "triggered_workflow", "triggered_by", "triggered_at"]) # noqa
        payload_filtered = payload[payload["status_text"] != "in-progress"]
        print(payload_filtered)

        self.db.report_bitrise_builds_info(payload_filtered)

    def get_latest_build(self):
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

    def parse_iso_timestamp(self, ts):
        if ts:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return None

    def report_bitrise_builds_info(self, payload):
        for index, row in payload.iterrows():
            report = ReportBitriseBuildsCount(
                build_number=row['build_number'],
                branch=row['branch'],
                status=row['status'],
                status_text=row['status_text'],
                triggered_workflow=row['triggered_workflow'],
                triggered_by=row['triggered_by'],
                triggered_at=self.parse_iso_timestamp(row['triggered_at'])
            )
            self.session.add(report)
            self.session.commit()

    def report_bitrise_builds_count(self, payload):
        # Normalize the JSON data
        total_count = payload.get("paging", {}).get("total_item_count")

        data = [total_count]
        print(data)
        return data

    def report_bitrise_builds_count_insert(self, payload):
        # report = ReportBitriseBuildsCount(total_builds=payload[0])

        # self.session.add(report)
        # self.session.commit()
        return
