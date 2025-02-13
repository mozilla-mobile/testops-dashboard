import sys
import os

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
            self.BITRISE_APP_SLUG = os.environ['BITRISE_APP_SLUG']
        except KeyError:
            print("ERROR: Missing bitrise env var")
            sys.exit(1)

    # API: Projects
    def builds(self):
        return self.client.get_builds(self.BITRISE_APP_SLUG)


class BitriseClient(Bitrise):

    def __init__(self):
        super().__init__()
        print("Init")
        self.db = DatabaseBitrise()

    def builds_count(self):
        # Pull JSON blob from Bitrise
        payload = self.builds()

        data_frame = self.db.report_bitrise_builds_count(payload)
        self.db.report_bitrise_builds_count_insert(data_frame)


class DatabaseBitrise(Database):

    def __init__(self):
        super().__init__()
        self.db = Database()

    def report_bitrise_builds_count(self, payload):
        # Normalize the JSON data
        total_count = payload.get("paging", {}).get("total_item_count")

        data = [total_count]
        return data

    def report_bitrise_builds_count_insert(self, payload):
        report = ReportBitriseBuildsCount(total_builds=payload[0])

        self.session.add(report)
        self.session.commit()
