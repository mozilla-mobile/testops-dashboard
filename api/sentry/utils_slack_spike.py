import json
import csv
import argparse
from pathlib import Path
import requests
import yaml
from .utils import insert_json_footer, project_config, _create_table_header_cell, get_all_future_versions
from utils.datetime_utils import DatetimeUtils


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
                                "*{0} Spike Issues Alert: {1} "
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

        # Create table headers
        header_row = [
            _create_table_header_cell("Issue"),
            _create_table_header_cell("Version")
        ]

        # Create table rows for each issue
        table_rows = []
        for issue in issues:
            title = issue['title']
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


def main(file_csv: str, project: str) -> None:
    """Generate Slack message for spike issues."""
    # Check if there are any spike issues before generating the JSON
    try:
        with open(file_csv, 'r') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            issues = list(csv_reader)

        if not issues:
            print("ℹ️ No spike issues found. Skipping JSON generation.")
            return

    except FileNotFoundError:
        print(f"⚠️ CSV file {file_csv} not found. Skipping JSON generation.")
        return
    except Exception as e:
        print(f"⚠️ Error reading CSV file: {str(e)}. Skipping JSON generation.")
        return

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

    args = parser.parse_args()

    main(args.file, args.project)
