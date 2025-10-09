import json
import csv
import argparse
from pathlib import Path
import requests
import yaml

from utils.datetime_utils import DatetimeUtils


def get_all_future_versions():
    response = requests.get('https://whattrainisitnow.com/api/firefox/releases/future/')
    if response.status_code != 200:
        return None
    else:
        return sorted(list(response.json().keys()))


def insert_rates(json_data, csv_file, project):
    all_future_versions = get_all_future_versions()
    print(all_future_versions)
    low_crash_free_rate_threshold = None
    with open('config/sentry/rules.yml', 'r') as rules_file:
        rules = yaml.safe_load(rules_file)
        low_crash_free_rate_threshold = rules.get(project).get(
            'LOW_CRASH_FREE_RATE_THRESHOLD', 99.5)
    flag_low_crash_free_rate_detected = False
    with open(csv_file, 'r') as file:
        rows = csv.DictReader(file)
        for row in rows:
            print(row)
            if float(row['adoption_rate_user']) > 1:
                crash_free_rate_user = (
                    "NaN" if float(row['crash_free_rate_user']) < 0
                    else row['crash_free_rate_user']
                )
                crash_free_rate_session = (
                    "NaN" if float(row['crash_free_rate_session']) < 0
                    else row['crash_free_rate_session']
                )
                adoption_rate_user = (
                    "NaN" if float(row['adoption_rate_user']) < 0
                    else row['adoption_rate_user']
                )
                release_version = row['release_version']
                if all_future_versions is not None:
                    if release_version in all_future_versions:
                        release_version = release_version + " (Beta)"
                if float(crash_free_rate_session) < low_crash_free_rate_threshold or \
                   float(crash_free_rate_user) < low_crash_free_rate_threshold:
                    flag_low_crash_free_rate_detected = True
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
                                adoption_rate_user
                            )
                        }
                    }
                )
                print(
                    "crash_free_rate_user: {0}, crash_free_rate_session: {1}, "
                    "user_adoption_rate: {2}, release_version: {3}".format(
                        crash_free_rate_user,
                        crash_free_rate_session,
                        adoption_rate_user,
                        release_version
                    )
                )
            else:
                print("Version {0}'s adoption rate is less than 1%. Skipping."
                      .format(row['release_version']))
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
        if flag_low_crash_free_rate_detected:
            json_data["blocks"].append(
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "⚠️ Low crash-free rate(s) (<{0}%) detected ⚠️"
                            .format(low_crash_free_rate_threshold)
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


def init_json(project):
    now = DatetimeUtils.start_date('0')
    project_config = {
        "firefox-ios": ":apple: iOS",
        "fenix": ":android: Android",
        "fenix-beta": ":android: Android (Beta)"
    }
    platform = project_config.get(project, ":android: Android")
    json_data = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        "*:health: {0} Health Report ({1}) :sentry:*"
                    ).format(platform, now)
                }
            }
        ]
    }
    return json_data


def main(file_csv: str, project: str) -> None:
    json_data = init_json(project)
    insert_rates(json_data, file_csv, project)

    output_path = Path('sentry-slack-{0}.json'.format(project))
    output_path.write_text(json.dumps(json_data, indent=4))

    print(f"Slack message written to {output_path.resolve()}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generate Slack message from Sentry CSV data')
    parser.add_argument('--file', required=True, help='Path to the input CSV file')
    parser.add_argument('--project', required=True,
                        help='Sentry project name (firefox-ios or fenix)')

    args = parser.parse_args()
    main(args.file, args.project)
