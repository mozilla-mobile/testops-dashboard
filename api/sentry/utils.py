import json
import requests

from utils.datetime_utils import DatetimeUtils

project_config = {
    "firefox-ios": {
        "icon": ":testops-apple:",
        "product": "Firefox iOS",
        "looker_dashboard_url": (
            "https://mozilla.cloud.looker.com/dashboards/"
            "2667?Sentry+Project+ID=6176941&Created+Month=30+days"
        ),
        "confluence_report_url": (
            "https://mozilla-hub.atlassian.net/wiki/spaces/"
            "MTE/pages/1631911951/iO+Health+Monitor+Report"
        )
    },
    "fenix": {
        "icon": ":testops-android:",
        "product": "Firefox Android",
        "looker_dashboard_url": (
            "https://mozilla.cloud.looker.com/dashboards/"
            "2667?Sentry+Project+ID=6375561&Created+Month=30+days"
        ),
        "confluence_report_url": (
            "https://mozilla-hub.atlassian.net/wiki/spaces/"
            "MTE/pages/1695154291/Android+Health+Monitor+Report"
        )
    },
    "fenix-beta": {
        "icon": ":testops-android:",
        "product": "Firefox Android (Beta)",
        "looker_dashboard_url": (
            "https://mozilla.cloud.looker.com/dashboards/"
            "2667?Sentry+Project+ID=6295551&Created+Month=30+days"
        ),
        "confluence_report_url": (
            "https://mozilla-hub.atlassian.net/wiki/spaces/"
            "MTE/pages/1695154291/Android+Health+Monitor+Report"
        )
    }
}


# Shared utility functions
def get_all_future_versions():
    response = requests.get('https://whattrainisitnow.com/api/firefox/releases/future/')
    if response.status_code != 200:
        return None
    else:
        return sorted(list(response.json().keys()))


def _create_table_header_cell(text):
    """Create a rich text table header cell with optional bold styling and emoji."""
    elements = [{"type": "text", "text": text, "style": {"bold": True}}]

    return {
        "type": "rich_text",
        "elements": [
            {
                "type": "rich_text_section",
                "elements": elements
            }
        ]
    }


def insert_json_footer(json_data):
    divider = {
            "type": "divider"
        }
    footer_block = {
        "type": "context",
        "elements": [
            {
                "type": "image",
                "image_url": (
                    "https://avatars.slack-edge.com/2025-06-24/"
                    "9097205871668_a01e2ac8089c067ea5f8_72.png"
                ),
                "alt_text": "TestOps logo"
            },
            {
                "type": "mrkdwn",
                "text": "Created by Mobile Test Engineering | Data From Sentry :sentry:"
            }
        ]
    }
    json_data["attachments"][0]["blocks"].append(divider)
    json_data["attachments"][0]["blocks"].append(footer_block)


