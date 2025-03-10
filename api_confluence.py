import os
import json
import yaml
from atlassian import Confluence
import requests


# Confluence env vars
# BASE_URL = "https://your-confluence-instance.atlassian.net/wiki/rest/api"
ATLASSIAN_API_TOKEN = os.environ['ATLASSIAN_API_TOKEN']
ATLASSIAN_USERNAME = os.environ['ATLASSIAN_USERNAME']
ATLASSIAN_HOST = os.environ['ATLASSIAN_HOST']

BASE_URL = f"https://{ATLASSIAN_HOST}/wiki/rest/api"
auth = (ATLASSIAN_USERNAME, ATLASSIAN_API_TOKEN)
headers = {"Accept": "application/json"}
# Confluence connection
ATLASSIAN_HOST = f"https://{ATLASSIAN_HOST}"
confluence = Confluence(
    url=ATLASSIAN_HOST,
    username=ATLASSIAN_USERNAME,
    password=ATLASSIAN_API_TOKEN
)

# PAGE_ID = "419954941"
PAGE_ID = "1346961433"
page_url = f"{BASE_URL}/content/{PAGE_ID}"
YAML_FILE_PATH = "confluence-reports.yaml"
IMAGE_PATH = "looker_images"


def image_attachments_delete():
    # get list of attachments for page
    attachments_url = f"{BASE_URL}/content/{PAGE_ID}/child/attachment"
    response = requests.get(attachments_url, headers=headers, auth=auth)

    if response.status_code == 200:
        attachments = response.json()['results']

        # delete each attachment
        for attachment in attachments:
            attachment_id = attachment['id']
            delete_url = f"{BASE_URL}/content/{attachment_id}"

            delete_response = requests.delete(delete_url, headers=headers, auth=auth) # noqa
            if delete_response.status_code == 204:
                print(f"Attachment {attachment_id} deleted successfully.")
            else:
                print(f"Failed to delete attachment {attachment_id}.")
    else:
        print(f"Failed to fetch attachments: {response.status_code}, {response.text}") # noqa


def image_attachments_list():
    # fetch all attachments on page
    response = requests.get(f"{BASE_URL}/content/{PAGE_ID}/child/attachment",
                            auth=auth, headers=headers)

    if response.status_code == 200:
        attachments = response.json()["results"]
        for att in attachments:
            print(f"Filename: {att['title']} - ID: {att['id']}")
        return response
    else:
        print("❌ Failed to retrieve attachments")
        print(response.text)


def image_attachments_upload():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    image_dir = os.path.join(script_dir, IMAGE_PATH)

    # upload image files 1 by 1
    for filename in os.listdir(image_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')): # noqa
            file_path = os.path.join(image_dir, filename)
            print(f"Uploading: {filename}...")

            with open(file_path, "rb"):
                response = confluence.attach_file(
                    filename=file_path,
                    page_id=PAGE_ID
                )

            if response:
                print(f"Successfully uploaded: {filename}")
            else:
                print(f"Failed to upload: {filename}")

    print("Upload process completed!")


def page():
    response = requests.get(page_url, auth=auth, headers=headers)
    if response.status_code != 200:
        print("Failed to retrieve the page")
        print(response.text)
        exit()
    return response.json()


def table_row_write(report_title, report_description,
                    attachment_filename, looker_graph_url):
    return f"""
            <row>
        <td><b>{report_title}</b></td>
        <td>{report_description}</td>
        <td>
        <a href="{looker_graph_url}"><ac:image><ri:attachment ri:filename="{attachment_filename}"/></ac:image></a></td>
        </row>
        """ # noqa


def page_html(image_name):
    html_content = ""

    with open(YAML_FILE_PATH, "r") as file:
        config = yaml.safe_load(file)

    section = ""
    for section in config["wiki_page"]["sections"]:
        print(f"Section: {section['name']}")
        rows = ""
        for report in section["reports"]:
            row = table_row_write(report["report-title"],
                                  report["report-description"],
                                  report["attachment-filename"],
                                  report["looker-graph-url"])
            rows += row

        html_content += f"""
        <h1>{section['name']}</h1>
        <table>
        {rows}
        </table>"""
    return html_content


def page_payload(page_data, current_version, new_content):
    # Update the page with new content
    update_payload = {
        "id": PAGE_ID,
        "type": "page",
        "title": page_data["title"],
        "space": {"key": page_data["space"]["key"]},
        "body": {
            "storage": {
                "value": new_content,
                "representation": "storage"
            }
        },
        "version": {"number": current_version + 1}  # Increment version
    }
    return update_payload


def page_payload_write(update_payload):
    update_url = f"{BASE_URL}/content/{PAGE_ID}"
    headers.update({"Content-Type": "application/json"})

    update_response = requests.put(update_url, auth=auth, headers=headers,
                                   data=json.dumps(update_payload))

    if update_response.status_code == 200:
        print("Page updated successfully!")
    else:
        print("Failed to update the page")
        print(update_response.text)


def main():
    image_attachments_list()
    image_attachments_delete()
    image_attachments_list()
    image_name = image_attachments_upload()
    page_data = page()
    current_version = page_data["version"]["number"]
    new_content = page_html(image_name)
    payload = page_payload(page_data, current_version, new_content)
    page_payload_write(payload)


if __name__ == "__main__":
    main()
