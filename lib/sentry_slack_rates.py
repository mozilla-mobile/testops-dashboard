import json
import csv
import sys
from pathlib import Path

from utils.datetime_utils import DatetimeUtils


def insert_rates(json_data, csv_file):
    with open(csv_file, 'r') as file:
        rows = csv.DictReader(file)
        for row in rows:
            print(row)
            crash_free_rate_user = row['crash_free_rate_user']
            crash_free_rate_session = row['crash_free_rate_session']
            release_version = row['release_version']
            user_adoption_rate = row['user_adoption_rate']
            json_data["blocks"].append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            "*v{0}* → :iphone: {1}%  "
                            ":bust_in_silhouette: {2}% "
                            ":rocket: {3}%"
                        ).format(
                            release_version,
                            crash_free_rate_session,
                            crash_free_rate_user,
                            user_adoption_rate
                        )
                    }
                }
            )
            print(
                "crash_free_rate_user: {0}, crash_free_rate_session: {1}, "
                "user_adoption_rate: {2}, release_version: {3}".format(
                    crash_free_rate_user,
                    crash_free_rate_session,
                    user_adoption_rate,
                    release_version
                )
            )
        json_data["blocks"].append(
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": ":chart_with_upwards_trend: Trends",
                            "emoji": True
                        },
                        "value": "trends_click",
                        "action_id": "trends",
                        "url": (
                            "https://mozilla.cloud.looker.com/dashboards/2381"
                        )
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": ":scroll: Report",
                            "emoji": True
                        },
                        "value": "report_click",
                        "action_id": "report",
                        "url": (
                            "https://mozilla-hub.atlassian.net/wiki/spaces/"
                            "MTE/pages/1631911951/iOS+Health+Monitor+Report"
                        )
                    }
                ]
            }
        )
        json_data["blocks"].append(
            {
                "type": "divider"
            }
        )
        json_data["blocks"].append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": (
                            ":iphone: Crash-Free Sessions "
                            ":bust_in_silhouette: Crash-Free Users "
                            ":rocket: User Adoption Rate"
                        )
                    }
                ]
            }
        )
    return json_data


def insert_json_content(json_data, versions):
    for version in versions:
        this_version = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Release: v{version}"
            }
        }
        json_data["blocks"].append(this_version)


def init_json():
    now = DatetimeUtils.start_date('0')
    json_data = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        "*:health: iOS Health Report ({0}) :sentry:*"
                    ).format(now)
                }
            }
        ]
    }
    return json_data


def main(csv_filename):
    json_data = init_json()
    insert_rates(json_data, csv_filename)

    output_path = Path('sentry-slack.json')
    output_path.write_text(json.dumps(json_data, indent=4))

    print(f"Slack message written to {output_path.resolve()}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python sentry_slack.py <csv_filename>")
        sys.exit(1)
    main(sys.argv[1])