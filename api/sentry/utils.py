import json
import csv
import argparse
from pathlib import Path
import requests
import yaml

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


# Rate-related functions
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
    looker_dashboard_url = project_config.get(project).get(
        'looker_dashboard_url', None)
    confluence_report_url = project_config.get(project).get(
        'confluence_report_url', None)
    with open(csv_file, 'r') as file:
        rows = csv.DictReader(file)
        table_rows = []
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

                table_row = [
                    {"type": "raw_text", "text": release_version},
                    {"type": "raw_text", "text": crash_free_rate_session + "%"},
                    {"type": "raw_text", "text": crash_free_rate_user + "%"},
                    {"type": "raw_text", "text": adoption_rate_user + "%"},
                ]
                table_rows.append(table_row)
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

        insert_table(json_data, table_rows)
        insert_buttons(json_data, looker_dashboard_url, confluence_report_url)

        if flag_low_crash_free_rate_detected:
            json_data["attachments"][0]["blocks"].append(
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "❗ Low crash-free rate(s) (<{0}%) detected"
                            .format(low_crash_free_rate_threshold)
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


def insert_table(json_data, table_rows):
    """Insert a table with headers for the Sentry health report."""
    header_row = [
        _create_table_header_cell("Version"),
        _create_table_header_cell("Crash-Free Sessions"),
        _create_table_header_cell("Crash-Free Users"),
        _create_table_header_cell("Adoption Rate")
    ]

    table = {
        "type": "table",
        "rows": [header_row] + table_rows
    }

    json_data["attachments"][0]["blocks"].append(table)


def insert_buttons(json_data, looker_dashboard_url, confluence_report_url):
    buttons_elements = []
    # Add Trends button if looker_dashboard_url is defined
    if looker_dashboard_url:
        buttons_elements.append({
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": ":chart_with_upwards_trend: Trends",
                "emoji": True
            },
            "value": "trends_click",
            "action_id": "trends",
            "url": looker_dashboard_url
        })

    # Add Report button if confluence_report_url is defined
    if confluence_report_url:
        buttons_elements.append({
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": ":scroll: Report",
                "emoji": True
            },
            "value": "report_click",
            "action_id": "report",
            "url": confluence_report_url
        })

    # Only add the actions block if we have at least one button
    if buttons_elements:
        json_data["attachments"][0]["blocks"].append({
            "type": "actions",
            "elements": buttons_elements
        })


def init_json(project):
    now = DatetimeUtils.start_date('0')
    icon = project_config.get(project).get('icon')
    product = project_config.get(project).get('product')
    json_data = {
        "attachments": [
            {
                "color": "#008000",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": (
                                "*:health: {0} Product Health: {1} "
                                "({2})*"
                            ).format(icon, product, now)
                        }
                    }
                ]
            }
        ]
    }
    return json_data


def main_rates(file_csv: str, project: str) -> None:
    json_data = init_json(project)
    insert_rates(json_data, file_csv, project)
    insert_json_footer(json_data)

    output_path = Path('sentry-slack-{0}.json'.format(project))
    output_path.write_text(json.dumps(json_data, indent=4))

    print(f"Slack message written to {output_path.resolve()}")


# Spike issues-related functions
def init_spike_json(project):
    """Initialize JSON structure for spike issues notification."""
    now = DatetimeUtils.start_date('0')
    icon = project_config.get(project).get('icon')
    product = project_config.get(project).get('product')
    json_data = {
        "attachments": [
            {
                "color": "#ff4444",  # Red for urgent spike issues
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": (
                                "*:rotating_light: {0} Spike Issues Alert: {1} "
                                "({2})*"
                            ).format(icon, product, now)
                        }
                    }
                ]
            }
        ]
    }
    return json_data


def insert_spike_issues(json_data, file_csv):
    """Insert spike issues data into the Slack message in table format."""
    try:
        with open(file_csv, 'r') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            issues = list(csv_reader)

        # Add summary
        json_data["attachments"][0]["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f":exclamation: *{len(issues)} spike issue(s) found*"
            }
        })

        # Create table headers
        header_row = [
            _create_table_header_cell("Issue Title"),
            _create_table_header_cell("Culprit"),
            _create_table_header_cell("Users"),
            _create_table_header_cell("Count"),
            _create_table_header_cell("Version")
        ]

        # Create table rows for each issue
        table_rows = []
        for issue in issues:
            title = issue['title']
            culprit = issue['culprit'] if issue['culprit'] else "N/A"
            user_count = issue['user_count']
            count = issue['count']
            version = issue['release_version']
            permalink = issue['permalink']

            # Create table row
            row = [
                {
                    "type": "rich_text",
                    "elements": [
                        {
                            "type": "rich_text_section",
                            "elements": [
                                {
                                    "type": "link",
                                    "text": title,
                                    "url": permalink
                                }
                            ]
                        }
                    ]
                },
                {
                    "type": "rich_text",
                    "elements": [
                        {
                            "type": "rich_text_section",
                            "elements": [{"type": "text", "text": culprit}]
                        }
                    ]
                },
                {
                    "type": "rich_text",
                    "elements": [
                        {
                            "type": "rich_text_section",
                            "elements": [{"type": "text", "text": user_count}]
                        }
                    ]
                },
                {
                    "type": "rich_text",
                    "elements": [
                        {
                            "type": "rich_text_section",
                            "elements": [{"type": "text", "text": count}]
                        }
                    ]
                },
                {
                    "type": "rich_text",
                    "elements": [
                        {
                            "type": "rich_text_section",
                            "elements": [{"type": "text", "text": f"v{version}"}]
                        }
                    ]
                }
            ]
            table_rows.append(row)

        # Insert the table
        table = {
            "type": "table",
            "rows": [header_row] + table_rows
        }
        json_data["attachments"][0]["blocks"].append(table)

    except FileNotFoundError:
        json_data["attachments"][0]["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":warning: *Error:* Spike issues CSV file not found."
            }
        })
    except Exception as e:
        json_data["attachments"][0]["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f":warning: *Error processing spike issues:* {str(e)}"
            }
        })


def main_spike_issues(file_csv: str, project: str) -> None:
    """Generate Slack message for spike issues."""
    json_data = init_spike_json(project)
    insert_spike_issues(json_data, file_csv)
    insert_json_footer(json_data)

    output_path = Path('sentry-spike-slack-{0}.json'.format(project))
    output_path.write_text(json.dumps(json_data, indent=4))

    print(f"Spike issues Slack message written to {output_path.resolve()}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generate Slack message from Sentry CSV data')
    parser.add_argument('--file', required=True, help='Path to the input CSV file')
    parser.add_argument('--project', required=True,
                        help='Sentry project name (firefox-ios or fenix)')
    parser.add_argument('--type', choices=['rates', 'spike-issues'], default='rates',
                        help='Type of Slack message to generate (default: rates)')

    args = parser.parse_args()

    if args.type == 'spike-issues':
        main_spike_issues(args.file, args.project)
    else:
        main_rates(args.file, args.project)
