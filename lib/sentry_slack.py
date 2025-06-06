import json
from pathlib import Path


def all_available_versions():
    versions = []
    csv_files = Path('.').glob('*.csv')
    for file in csv_files:
        try:
            print(f"File: {file.name}, Suffix: {file.stem}")
            version = file.name.split('sentry_issues_')[-1].split('.csv')[0]
            versions.append(version)
        except IndexError:
            print(
                f"Skipped file: {file.name} "
                "(unexpected naming format, or file doesn't exist)"
            )
    return versions


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
    json_data = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": (
                        ":health: :sentry: Sentry Health Report "
                        "(${{ env.TODAY_DATE }})"
                    ),
                    "emoji": True
                }
            }
        ]
    }
    return json_data


def main():
    versions = all_available_versions()

    if not versions:
        print("No versions found in CSV filenames. Exiting.")
        return

    print(f"Discovered versions: {', '.join(versions)}")

    json_data = init_json()
    insert_json_content(json_data, versions)

    output_path = Path('sentry_slack.json')
    output_path.write_text(json.dumps(json_data, indent=4))

    print(f"Slack message written to {output_path.resolve()}")


if __name__ == '__main__':
    main()