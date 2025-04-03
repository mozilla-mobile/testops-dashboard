import os
import glob
import sys
import json
import yaml
from atlassian import Confluence
import requests


# Confluence ENV vars
# URL_WIKI_REST_API = "https://your-confluence-instance.atlassian.net/wiki/rest/api"
ATLASSIAN_API_TOKEN = os.environ['ATLASSIAN_API_TOKEN']
ATLASSIAN_USERNAME = os.environ['ATLASSIAN_USERNAME']
ATLASSIAN_HOST = f"https://{os.environ['ATLASSIAN_HOST']}"
URL_WIKI_REST_API = f"{ATLASSIAN_HOST}/wiki/rest/api"

auth = (ATLASSIAN_USERNAME, ATLASSIAN_API_TOKEN)
headers = {"Accept": "application/json"}
confluence = Confluence(
    url=ATLASSIAN_HOST,
    username=ATLASSIAN_USERNAME,
    password=ATLASSIAN_API_TOKEN
)

PATH_IMAGES = "config/confluence/images"
PATH_YAML_FILES = "config/confluence"


def url_page(page_id):
    return f"{URL_WIKI_REST_API}/content/{page_id}"

def url_attachments(page_id):
    return f"{URL_WIKI_REST_API}/content/{page_id}/child/attachment"

def image_attachments_delete(page_id):
    # get list of attachments for page
    url = url_attachments(page_id)
    response = requests.get(url, headers=headers, auth=auth)

    if response.status_code == 200:
        attachments = response.json()['results']

        # delete each attachment
        for attachment in attachments:
            attachment_id = attachment['id']
            delete_url = f"{URL_WIKI_REST_API}/content/{attachment_id}"

            delete_response = requests.delete(delete_url, headers=headers, auth=auth) # noqa
            if delete_response.status_code == 204:
                print(f"Attachment {attachment_id} deleted successfully.")
            else:
                print(f"Failed to delete attachment {attachment_id}.")
    else:
        print(f"Failed to fetch attachments: {response.status_code}, {response.text}") # noqa


def image_attachments_list(page_id):
    # fetch all page attachments
    url = url_attachments(page_id)
    response = requests.get(f"{url}", auth=auth, headers=headers)

    if response.status_code == 200:
        attachments = response.json()["results"]
        for att in attachments:
            print(f"Filename: {att['title']} - ID: {att['id']}")
        return response
    else:
        print("❌ Failed to retrieve attachments")
        print(response.text)


def image_attachments_upload(page_id):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    image_dir = os.path.join(script_dir, PATH_IMAGES)

    # upload image files 1 by 1
    for filename in os.listdir(image_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')): # noqa
            file_path = os.path.join(image_dir, filename)
            print(f"Uploading: {filename}...")

            with open(file_path, "rb"):
                response = confluence.attach_file(
                    filename=file_path,
                    page_id=page_id
                )

            if response:
                print(f"Successfully uploaded: {filename}")
            else:
                print(f"Failed to upload: {filename}")

    print("Upload process completed!")


def page_object(page_url):
    """
    give page url, returns page object as JSON 
    """
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


# def page_html(image_name, page_id):
def page_html(page_id, sections):
    yaml_page_name = f"page-id-{page_id}.yaml"
    yaml_page_path = f"{PATH_YAML_FILES}/{yaml_page_name}"
    
    html_content = ""

    section = ""
    for section in sections:
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


def page_payload(page_id, page_title, page_data, current_version, new_content):
    # Update the page with new content
    update_payload = {
        "id": page_id,
        "type": "page",
        "title": page_title,
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


def page_payload_write(page_id, update_payload):
    update_url = f"{URL_WIKI_REST_API}/content/{page_id}"
    headers.update({"Content-Type": "application/json"})

    update_response = requests.put(update_url, auth=auth, headers=headers,
                                   data=json.dumps(update_payload))

    if update_response.status_code == 200:
        print("Page updated successfully!")
    else:
        print("Failed to update the page")
        print(update_response.text)


def pages():
    """
    iterates over confluence YAML files and generates pages 
    """
    for filepath in glob.glob(f"{PATH_YAML_FILES}/*.yaml"):  # Only YAML files
        with open(filepath, 'r', encoding='utf-8') as file:
            print(f"LOAD CONFIG FILE - {filepath}")
            config = yaml.safe_load(file)

            page_title = config["wiki_page"].get("page_title")
            page_id = config["wiki_page"].get("page_id")
            page_sections = config["wiki_page"]["sections"]

            url = url_page(page_id)

            print(f"PROCESS ATTACHMENTS - page_id: {page_id}")
            image_attachments_list(page_id)
            image_attachments_delete(page_id)
            image_attachments_list(page_id)
            image_attachments_upload(page_id)

            print(f"UPDATE PAGE - page_id: {page_id}")
            page_data = page_object(url)
            current_version = page_data["version"]["number"]
            new_content = page_html(page_id, page_sections)
            payload = page_payload(page_id, page_title, page_data, current_version, new_content)
            page_payload_write(page_id, payload)


def main():
    pages()


if __name__ == "__main__":
    main()
