import json
import csv
import argparse
import tomllib
from pathlib import Path
from urllib.parse import urlencode
import requests
import yaml

from utils.datetime_utils import DatetimeUtils


try:
    with open('config/sentry/projects.toml', 'rb') as f:
        project_config = tomllib.load(f)
except FileNotFoundError:
    raise FileNotFoundError("config/sentry/projects.toml not found")
except PermissionError:
    raise PermissionError("Permission denied reading config/sentry/projects.toml")
except tomllib.TOMLDecodeError:
    raise


def build_url(base_url: str, params: dict | None = None) -> str:
    if not params:
        return base_url
    return f"{base_url}?{urlencode(params)}"


def get_all_future_versions():
    response = requests.get('https://whattrainisitnow.com/api/firefox/releases/future/')
    if response.status_code != 200:
        return None
    else:
        return sorted(list(response.json().keys()))


def insert_rates(json_data, csv_file, project, shortform=False):
    all_future_versions = get_all_future_versions()
    print(all_future_versions)
    low_crash_free_rate_threshold = None
    with open('config/sentry/rules.yml', 'r') as rules_file:
        rules = yaml.safe_load(rules_file)
        low_crash_free_rate_threshold = rules.get(project).get(
            'LOW_CRASH_FREE_RATE_THRESHOLD', 99.5)
    flag_low_crash_free_rate_detected = False
    looker_config = project_config.get(project, {}).get('looker', {})
    looker_dashboard_url = build_url(
        looker_config['base_url'], looker_config.get('params')
    ) if looker_config else None
    confluence_report_url = project_config.get(project, {}).get(
        'confluence', {}).get('url', None)
    is_low_adoption = False
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
                is_low_adoption = True
                print("Version {0}'s adoption rate is less than 1%. Skipping."
                      .format(row['release_version']))

        # If no rates are reported, add a warning message rather than
        # sending a blank message.
        if len(table_rows) == 0:
            if is_low_adoption:
                explanation = (
                    ":information_source: Adoption rate(s) for all "
                    "versions are less than 1%."
                )
            else:
                explanation = ":warning: No data available"
            json_data["blocks"].append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": explanation
                    }
                },
            )
        else:
            insert_table(json_data, table_rows, shortform)

        if not shortform:
            insert_buttons(json_data, looker_dashboard_url, confluence_report_url)

        if flag_low_crash_free_rate_detected:
            json_data["blocks"].append(
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


def insert_table(json_data, table_rows, shortform=False):
    """Insert a table with headers for the Sentry health report."""
    header_row = [
        _create_table_header_cell("Version"),
        _create_table_header_cell("Crash-Free Sessions"),
        _create_table_header_cell("Crash-Free Users"),
        _create_table_header_cell("Adoption Rate")
    ]

    if shortform:
        table_rows = table_rows[:2]

    table = {
        "type": "table",
        "rows": [header_row] + table_rows
    }

    json_data["blocks"].append(table)


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
        json_data["blocks"].append({
            "type": "actions",
            "elements": buttons_elements
        })


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
    json_data["blocks"].append(divider)
    json_data["blocks"].append(footer_block)


def init_json(project, shortform=False):
    if shortform:
        sentry_config = project_config.get(project, {}).get('sentry', {})
        sentry_url = build_url(
            sentry_config['base_url'], sentry_config.get('params')
        )
        json_data = {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (":bar_chart: <{0}|Release Monitoring> "
                                 "(from Sentry :sentry2:)").format(sentry_url)
                    }
                }
            ]
        }
    else:
        now = DatetimeUtils.start_date('0')
        icon = project_config.get(project).get('icon')
        product = project_config.get(project).get('product')
        json_data = {
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
    return json_data


def insert_unhandled_issues(json_data, csv_file):
    with open(csv_file, 'r') as file:
        rows = list(csv.DictReader(file))

    if not rows:
        json_data["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                        ":white_check_mark: No new unhandled issues "
                        "found in the last 7 days."
                    )
            }
        })
        return json_data

    lines = []
    for i, row in enumerate(rows, 1):
        title = row['title']
        count = row['count']
        user_count = row['user_count']
        permalink = row['permalink']
        lines.append(
            f"{i}. <{permalink}|{title}> — "
            f"{count} events, {user_count} users affected"
        )

    json_data["blocks"].append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "\n".join(lines)
        }
    })
    return json_data


def main_unhandled_issues(csv_file: str, project: str) -> None:
    icon = project_config.get(project).get('icon')
    product = project_config.get(project).get('product')
    now = DatetimeUtils.start_date('0')
    json_data = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*:bug: {icon} {product} "
                        f"New Unhandled Issues (Last 7 days): {now}*"
                    )
                }
            }
        ]
    }
    insert_unhandled_issues(json_data, csv_file)
    insert_json_footer(json_data)

    output_path = Path(f'sentry-slack-unhandled-{project}.json')
    output_path.write_text(json.dumps(json_data, indent=4))
    print(f"Slack message written to {output_path.resolve()}")


def main(file_csv: str, project: str, shortform: bool = False) -> None:
    json_data = init_json(project, shortform)
    insert_rates(json_data, file_csv, project, shortform)

    output_path = Path('sentry-slack-{0}.json'.format(project))
    output_path.write_text(json.dumps(json_data, indent=4))

    print(f"Slack message written to {output_path.resolve()}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generate Slack message from Sentry CSV data')
    parser.add_argument('--file', required=True, help='Path to the input CSV file')
    parser.add_argument('--project', required=True,
                        help='Sentry project name (firefox-ios or fenix)')
    parser.add_argument('--shortform', action='store_true', default=False,
                        help='Generate a shorter version of the report')
    parser.add_argument('--mode', default='rates',
                        choices=['rates', 'unhandled-issues'],
                        help='Report mode')

    args = parser.parse_args()
    if args.mode == 'unhandled-issues':
        main_unhandled_issues(args.file, args.project)
    else:
        main(args.file, args.project, args.shortform)
