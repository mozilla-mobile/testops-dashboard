import json
import csv
import argparse
import tomllib
from pathlib import Path
from urllib.parse import urlencode
import requests
import yaml

from packaging.version import Version

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


def format_count(value) -> str:
    """Render a count compactly in thousands (e.g. 5343 -> "5k").

    Values below 1000 are shown as-is to avoid misleading rounding
    (e.g. 600 -> "600", not "1k").
    """
    n = int(value)
    if n < 1000:
        return str(n)
    return f"{round(n / 1000)}k"


def package_for(project: str) -> str:
    """Parse the app package (e.g. org.mozilla.ios.Firefox) from the Sentry
    config's query string (`release.package:<package>`)."""
    query = (
        project_config.get(project, {}).get('sentry', {})
        .get('params', {}).get('query', '')
    )
    marker = 'release.package:'
    if marker in query:
        return query.split(marker, 1)[1].strip()
    return ''


def first_release_url(project_id, environment, package, version=None) -> str:
    """Build a Sentry issue-list URL for new issues, matching the query used
    to fetch them: unresolved issues first seen in the given release. When a
    version is provided, scope to `firstRelease:<package>@<version>`."""
    query = "is%3Aunresolved"
    if version and package:
        query += f"%20firstRelease%3A{package}%40{version}"
    return (
        f"https://mozilla.sentry.io/issues/?limit=5&project={project_id}"
        f"&query={query}"
        f"&environment={environment}&sort=freq&statsPeriod=7d"
    )


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


def _create_table_link_cell(text, url):
    return {
        "type": "rich_text",
        "elements": [
            {
                "type": "rich_text_section",
                "elements": [
                    {"type": "link", "url": url, "text": text}
                ]
            }
        ]
    }


def insert_unhandled_issues(
    json_data, rows, version=None, version_url=None, limit=None,
    sort_by_volume=False, threshold=1000, humanize_counts=False,
):
    if version is not None:
        header_text = (
            f"*<{version_url}|v{version}>*" if version_url else f"*v{version}*"
        )
        json_data["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": header_text
            }
        })

    # Preserve the order Sentry returned (sort=freq over statsPeriod=7d).
    # Don't re-sort by count/user_count — those are lifetime totals, so
    # re-sorting would surface old high-volume issues over recent ones.
    significant = [
        row for row in rows
        if int(row['user_count']) > threshold or int(row['count']) > threshold
    ]
    # The detailed report orders each version's issues by events, then
    # users affected (both descending), rather than Sentry's 7d freq order.
    if sort_by_volume:
        significant.sort(
            key=lambda row: (int(row['count']), int(row['user_count'])),
            reverse=True,
        )
    if limit is not None:
        significant = significant[:limit]
    if not significant:
        json_data["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "No significant new issue to report."
            }
        })
        return json_data

    header_row = [
        _create_table_header_cell("Issue ID"),
        _create_table_header_cell("Issue"),
        _create_table_header_cell("Events"),
        _create_table_header_cell("Users Affected"),
    ]
    MAX_TITLE_DISPLAY_LEN = 50
    table_rows = []
    for row in significant:
        title = row['title']
        if len(title) > MAX_TITLE_DISPLAY_LEN:
            title = title[:MAX_TITLE_DISPLAY_LEN] + '…'
        count_text = (
            format_count(row['count']) if humanize_counts
            else str(row['count'])
        )
        user_count_text = (
            format_count(row['user_count']) if humanize_counts
            else str(row['user_count'])
        )
        table_rows.append([
            _create_table_link_cell(
                row.get('short_id', ''), row['permalink']
            ),
            {"type": "raw_text", "text": title},
            {"type": "raw_text", "text": count_text},
            {"type": "raw_text", "text": user_count_text},
        ])

    json_data["blocks"].append({
        "type": "table",
        "rows": [header_row] + table_rows
    })
    return json_data


def main_unhandled_issues(
    csv_file: str, project: str, longform: bool = False
) -> None:
    icon = project_config.get(project).get('icon')
    product = project_config.get(project).get('product')
    now = DatetimeUtils.start_date('0')

    with open(csv_file, 'r') as f:
        rows = list(csv.DictReader(f))

    sentry_params = project_config.get(project, {}).get('sentry', {}).get('params', {})
    project_id = sentry_params.get('project', '')
    environment = sentry_params.get('environment', '')
    package = package_for(project)

    # Group by exact dot release (e.g. 151.0.1) and report the most recent
    # two, showing up to 3 significant new issues each.
    rows_by_version = {}
    for row in rows:
        version = row.get('release_version', '')
        rows_by_version.setdefault(version, []).append(row)
    versions = sorted(rows_by_version.keys(), key=Version, reverse=True)[:2]

    if longform:
        _write_longform_threaded(
            rows, project, icon, product, now,
            project_id, environment, package,
        )
        return

    json_data = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*:sentry: {icon} {product} "
                        f"Top New Sentry Issues "
                        f"({now})*"
                    )
                }
            }
        ]
    }

    if not versions:
        insert_unhandled_issues(
            json_data, [], threshold=500, humanize_counts=True
        )
    else:
        for version in versions:
            version_url = first_release_url(
                project_id, environment, package, version
            )
            insert_unhandled_issues(
                json_data,
                rows_by_version[version],
                version=version,
                version_url=version_url,
                limit=3,
                threshold=500,
                humanize_counts=True,
            )

    insert_json_footer(json_data)

    output_path = Path(f'sentry-slack-unhandled-{project}.json')
    output_path.write_text(json.dumps(json_data, indent=4))
    print(f"Slack message written to {output_path.resolve()}")


def _write_longform_threaded(
    rows, project, icon, product, now,
    project_id, environment, package,
):
    """Long-form report posted as a Slack thread.

    Writes a header payload plus one reply payload per dot version. The
    workflow posts the header with chat.postMessage, captures its `ts`, and
    posts each reply with `thread_ts` set to that value.
    """
    header_text = (
        f":sentry: {icon} {product} Top New Sentry Issues "
        f"(Detailed) ({now})"
    )
    header_block_text = (
        f"*:sentry: {icon} {product} "
        f"Top New Sentry Issues (Detailed) ({now})* "
        f":thread:"
    )
    header_data = {
        "text": header_text,
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": header_block_text,
                },
            }
        ],
    }
    header_path = Path(
        f'sentry-slack-unhandled-long-{project}-header.json'
    )
    header_path.write_text(json.dumps(header_data, indent=4))
    print(f"Slack header written to {header_path.resolve()}")

    rows_by_version = {}
    for row in rows:
        version = row.get('release_version', '')
        rows_by_version.setdefault(version, []).append(row)

    if not rows_by_version:
        return

    # Report the two most recent dot releases, newest first.
    versions = sorted(
        rows_by_version.keys(), key=Version, reverse=True
    )[:2]
    for i, version in enumerate(versions, start=1):
        version_url = first_release_url(
            project_id, environment, package, version
        )
        reply_data = {
            "text": f"v{version}",
            "blocks": [],
        }
        insert_unhandled_issues(
            reply_data,
            rows_by_version[version],
            version=version,
            version_url=version_url,
            limit=3,
            sort_by_volume=True,
            threshold=500,
            humanize_counts=True,
        )
        reply_path = Path(
            f'sentry-slack-unhandled-long-{project}-reply-{i:02d}.json'
        )
        reply_path.write_text(json.dumps(reply_data, indent=4))
        print(f"Slack reply written to {reply_path.resolve()}")


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
    parser.add_argument('--longform', action='store_true', default=False,
                        help='Generate the long-form unhandled-issues report '
                             '(top issues per sub-version)')
    parser.add_argument('--mode', default='rates',
                        choices=['rates', 'unhandled-issues'],
                        help='Report mode')

    args = parser.parse_args()
    if args.mode == 'unhandled-issues':
        main_unhandled_issues(args.file, args.project, args.longform)
    else:
        main(args.file, args.project, args.shortform)
