import csv
import sys
import json
from datetime import datetime, UTC


def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) != 2:
        print("Usage: python -m api.github.utils <csv_file>")
        print("   or: python api/github/utils.py <csv_file>")
        sys.exit(1)

    csv_filename = sys.argv[1]
    message = csv_to_slack_message(csv_filename)
    print(json.dumps(message, indent=2))


def csv_to_slack_message(csv_filename):
    """Read CSV file and convert to Slack message format"""
    issues = []

    try:
        with open(csv_filename, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Convert GitHub API URL to browser URL
                browser_url = row['url'].replace(
                    'api.github.com/repos/', 'github.com/'
                )
                browser_url = browser_url.replace('/issues/', '/issues/')

                issues.append({
                    'title': row['title'],
                    'url': browser_url,
                    'user': row['user'],
                    'created_at': row['created_at']
                })

    except FileNotFoundError:
        print(f"CSV file {csv_filename} not found")
        return None

    return create_slack_json_message(issues)


def csv_to_slack_text(csv_filename):
    """Read CSV file and convert to simple Slack text format"""
    try:
        with open(csv_filename, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            issues = list(reader)

        if not issues:
            return ":white_check_mark: No new GitHub issues found"

        current_date = datetime.now().strftime('%Y-%m-%d')
        message = f":github: *New GitHub Issues ({current_date})*\n\n"

        for issue in issues:
            # Convert API URL to browser URL
            browser_url = issue['url'].replace(
                'api.github.com/repos/', 'github.com/'
            )
            browser_url = browser_url.replace('/issues/', '/issues/')

            title = issue['title']
            user = issue['user']
            message += f"• <{browser_url}|{title}> (by {user})\n"

        message += f"\n_Found {len(issues)} new issues_"
        return message

    except FileNotFoundError:
        return f"Error: CSV file {csv_filename} not found"


def create_slack_json_message(issues: list) -> dict:
    current_date = datetime.now(UTC).strftime('%Y-%m-%d')

    if not issues:
        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f":white_check_mark: No New GitHub Issues ({current_date})",
                        "emoji": True
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": ":testops-notify: created by <https://mozilla-hub.atlassian.net/wiki/spaces/MTE/overview|Mobile Test Engineering>"
                        }
                    ]
                }
            ]
        }

    # Create blocks with each issue as a section
                "text": f":github: New GitHub Issues ({current_date})",
                "emoji": True
            }
        }
    ]

    # Add each issue as a separate section
    for issue in issues:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"<{issue['url']}|{issue['title']}>"
            }
        })
    
    # Add footer
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": ":testops-notify: Created by <https://mozilla-hub.atlassian.net/wiki/spaces/MTE/overview|Mobile Test Engineering>"
            }
        ]
    })

    return {
        "blocks": blocks
    }


if __name__ == "__main__":
    main()
