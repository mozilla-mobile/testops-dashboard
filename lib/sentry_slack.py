import json
import datetime
import csv
from pathlib import Path



def insert_crash_free_rate(json_data, csv_file):
    with open(csv_file, 'r') as file:
        rows = csv.DictReader(file)
        for row in rows:
            print(row)
            crash_free_rate_user = row['crash_free_rate_user']
            crash_free_rate_session = row['crash_free_rate_session']
            release_version = row['release_version']
            json_data["blocks"].append(
                {
			        "type": "section",
			        "text": {
				        "type": "mrkdwn",
				        "text": "*v{0}*".format(release_version)
			        }
		        }
            json_data["blocks"].append(
                {
			        "type": "section",
			        "fields": [
				        {
					        "type": "mrkdwn",
					        "text": "Crash-Free Sessions:\n{0}%".format(crash_free_rate_session)
				        },
				        {
					        "type": "mrkdwn",
					        "text": "Crash-Free Users:\n{0}%".format(crash_free_rate_user)
				        }
			        ]
		        }
            )
            json_data["blocks"].append(
                {
			       "type": "divider"
		        }
            )
            print("crash_free_rate_user: {0}, crash_free_rate_session: {1}, release_version: {2}".format(
                crash_free_rate_user, crash_free_rate_session, release_version
            ))
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
    now = datetime.datetime.now().strftime('%Y-%m-%d')
    json_data = {
        "blocks": [
		    {
			    "type": "section",
			    "text": {
				    "type": "mrkdwn",
				    "text": "*:health: iOS Health Report ({0})*".format(now)
			    }
		    },
            {			    
                "type": "divider"
		    }
        ]
    }
    return json_data


def main(csv_filename):
    json_data = init_json()
    insert_crash_free_rate(json_data, csv_filename)

    output_path = Path('sentry-slack.json')
    output_path.write_text(json.dumps(json_data, indent=4))

    print(f"Slack message written to {output_path.resolve()}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python sentry_slack.py <csv_filename>")
        sys.exit(1)
    main(sys.argv[1])