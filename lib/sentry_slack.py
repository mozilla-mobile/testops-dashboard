import json
from pathlib import Path

def all_available_versions():
    versions = []
    csv_files = Path('.').glob('*.csv')
    for file in csv_files:
        print(f"File: {file.name}, Suffix: {file.stem}")
        version = file.name.split('sentry_issues_')
        versions.append(version)
    return versions

def insert_json_content(json_data, versions):
    pass

def init_json():
    json_data = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": ":health: :sentry: Sentry Health Report (${{ env.TODAY_DATE }})",
                    "emoji": True
                }
            }
        ]
      }
    return json_data

def main():
    versions = all_available_versions()
    json_data = init_json()
    with open('sentry_slack.json', 'w') as json_file:
        json.dump(json_data, json_file, indent=4)
    

if __name__ == '__main__':
    main()