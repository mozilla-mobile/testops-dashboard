import csv
import sys
import json


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
        with open(csv_filename, 'r', encoding='utf-8', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            print(f"CSV headers: {reader.fieldnames}", file=sys.stderr)
            row_count = 0
            for i, row in enumerate(reader):
                print(f"Row {i}: {row}", file=sys.stderr)
                issues.append({
                    'title': row['github_title'],
                    'url': row['github_url'],
                    'user': row['github_user']
                })
                row_count += 1

        print(f"Total issues found: {len(issues)}", file=sys.stderr)

        if row_count == 0:
            print("No data rows found after headers")

    except FileNotFoundError:
        print(f"CSV file {csv_filename} not found", file=sys.stderr)
        issues = []
    except UnicodeDecodeError as e:
        print(f"Encoding error reading CSV: {e}", file=sys.stderr)
        issues = []

    return create_slack_json_message(issues)


def create_slack_json_message(issues: list) -> dict:
    GITHUB_URL = "https://github.com/mozilla-mobile/firefox-ios/issues?q=is%3Aopen%20is%3Aissue%20no%3Aassignee%20-author%3Adata-sync-user"
    if not issues:
        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": ":white_check_mark: No New GitHub Issues",
                        "emoji": True
                    }
                }
            ]
        }

    # Create blocks with each issue as a section
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "<{0}|:github: GitHub>".format(GITHUB_URL)
            }
        }
    ]

    # Add all issues as bullet points in a single section
    issue_text = ""
    for issue in issues:
        issue_text += f"• <{issue['url']}|{issue['title']}> ({issue['user']})\n"

    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": issue_text.rstrip()
        }
    })

    return {
        "blocks": blocks
    }


if __name__ == "__main__":
    main()
