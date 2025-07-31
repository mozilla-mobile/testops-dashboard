#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import os
import glob
import json
import yaml
from atlassian import Confluence
import requests
from bs4 import BeautifulSoup
from jinja2 import Template
from api_testrail import TestRailClient


# Confluence ENV vars
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

PATH_CONFIG = "config/confluence"
PATH_IMAGES = f"{PATH_CONFIG}/images"
PATH_YAML_FILES = f"{PATH_CONFIG}/yaml"
PATH_XML_FILES = f"{PATH_CONFIG}/xml"


# ------------------------------------------------------------------
# URL string builders
# ------------------------------------------------------------------


def url_page(page_id):
    return f"{URL_WIKI_REST_API}/content/{page_id}"


def url_attachments(page_id):
    # return f"{URL_WIKI_REST_API}/content/{page_id}/child/attachment"
    path = url_page(page_id)
    return f"{path}/child/attachment"


def url_page_content_storage(page_id):
    path = url_page(page_id)
    return f"{path}?expand=body.storage"


# ------------------------------------------------------------------
# Page handlers
# ------------------------------------------------------------------


def page_object(page_url):
    """give page url, returns page object as JSON
    """

    response = requests.get(page_url, auth=auth, headers=headers)
    if response.status_code != 200:
        print("Failed to retrieve the page")
        print(response.text)
        exit()
    return response.json()


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


# ------------------------------------------------------------------
# Attachment processing
# ------------------------------------------------------------------


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

# ------------------------------------------------------------------
# Page rendering: Looker Reports (YAML)
# ------------------------------------------------------------------


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


def page_html(page_id, sections):

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


def pages_looker_graphs():
    """iterates over confluence YAML config files and generates
    looker graph pages in bulk (all have same format)
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
            payload = page_payload(page_id, page_title, page_data,
                                   current_version, new_content)
            page_payload_write(page_id, payload)


# ------------------------------------------------------------------
# Page rendering: Custom pages (XML)
# ------------------------------------------------------------------


def render_xml_template(template_path, params):
    """ 1. open Mustache-style (jinja compatible) XML template
        2. parameterize template with params """

    with open(template_path, 'r') as file:
        template_content = file.read()

    template = Template(template_content)
    rendered_xml = template.render(**params)

    return rendered_xml


# UTILITY FUNCTIONS

def page_content_retrieve_xml(page_id):
    """Utility function only

    Given page_id, write XML content to a local XML template file
    """
    page_url = url_page_content_storage(page_id)
    resp = page_object(page_url)

    soup = BeautifulSoup(resp, "html.parser")
    pretty_xml = soup.prettify()
    with open("confluence_page_content.xml", "w", encoding="utf-8") as f:
        f.write(pretty_xml)


def page_content_insert_xml(page_id, params):
    """Utility function only

    NOTE: Confluence API returns page content in XML format.

    Use this function as a stand-alone utility / example for pulling page
    content for rewriting pages or creating new XML template configs.
    """

    TEMPLATE_PATH = f"{PATH_XML_FILES}/build-validation.xml"

    # XML template
    # with open(TEMPLATE_PATH, "r", encoding="utf-8") as file:
    #     xml_content = file.read()
    output_xml = render_xml_template(TEMPLATE_PATH, params)

    # Confluence page (for updating)
    page_url = url_page(page_id)

    # Write output_xml to page
    print(f"UPDATING PAGE - page_id: {page_id}")
    page_data = page_object(page_url)
    current_version = page_data["version"]["number"]

    payload = page_payload(page_id, page_title, page_data, current_version, output_xml) # noqa
    page_payload_write(page_id, payload)


# REPORT: Build Validation

def page_report_build_validation():
    page_id = "1663598593"
    page_title = "DEMO v2"
    #  projects_id = 14 # Firefox for iOS
    testrail_project_id = "59" # Fenix
    testrail_milestone_id = "1066" # Manual functional testing sign-off - Firefox v120 (36024) RC1 # noqa
    testrail_report_url = "http://mozilla.org"
    release = "Manual functional testing sign-off - Firefox v120 (36024) RC1"
    build_version = "v149"
    testing_status = "green"
    testing_summary = '''
    <li>We started Full Functional test suite.</li>
    <li>We ran X sets of automated Full Functional tests on iPhone and iPad with XYZ experiment ON.</li> # noqa
    '''
    release_tag_url = "https://archive.mozilla.org/pub/fenix/releases/"
    qa_contacts = '''
     <a href='mailto:csuciu@mozilla.com'>Catalin Suc1u</a>,
     <a href='mailto:amoldovan@mozilla.com'>Alina M0ld0van</a>,
     <a href='mailto:abodea@mozilla.com'>Andr3i Bodea</a>
     '''
    client = TestRailClient()
    client.get_milestones(testrail_project_id)
    lastest_milestone = sorted(
        milestones,
        key=lambda m: m.get('start_on', m.get('created_on', 0)),
        reverse=True
    )[0]

    print(f"latest milestone: {latest_milestone['name']} (ID: {latest_milestone['id']})")
    print(f"latest milestone: {latest_milestone['description']}")
    sys.exit()



    """
    Applies params to jinja/mustache-style XML template and inserts into page
    """

    # TODO: hard-coded params for now...
    params = {
        'release_date': signoff_date,
        'build_version': build_version,
        'build_version_commit_hash': '12345',
        'testrail_report_url': 'https://mozilla.testrail.io/index.php?/runs/view/108599&group_by=cases:section_id&group_order=asc', # noqa
        'testrail_report_summary': test_summary,
        'testrail_run_1_result': 'PASS3D',
        'testrail_run_1_build_type': 'ARM64',
        'testrail_run_1_device': 'iPhone 16 Pro (iOS 18.3.2)',
        'testrail_run_2_result': 'PASS3D',
        'testrail_run_2_build_type': 'ARM64',
        'testrail_run_2_device': 'iPhone 16 Pro (iOS 18.3.2)',
        'testrail_issues_verified': 'N/A',
        'testrail_issues_new': 'N/A',
        'testrail_issues_known': '<a href="https://mozilla-hub.atlassian.net/browse/FXIOS-12650"</a>', # noqa
        'testrail_contacts': contacts,
    }

    params = {
        **locals()
    }

    TEMPLATE_PATH = f"{PATH_XML_FILES}/build-validation.xml"

    page_url = url_page(page_id)
    # page_url_storage = url_page_content_storage(page_id)
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as file:
        xml_content = file.read()
    output_xml = render_xml_template(TEMPLATE_PATH, params)

    print(f"UPDATE PAGE - page_id: {page_id}")
    page_data = page_object(page_url)
    current_version = page_data["version"]["number"]

    # new_content = page_html(page_id, page_sections)
    payload = page_payload(page_id, page_title, page_data, current_version, output_xml) # noqa
    page_payload_write(page_id, payload)


def main():
    # TODO: phase 2 PR - instead of invoking this directly from main,
    # invoke it from __main__.py --report-type looker-graphs
    pages_looker_graphs()


def main_2():
    # TODO: phase 2 PR - instead of invoking this directly from main,
    # invoke it from __main__.py --report-type looker-graphs
    page_report_build_validation()


if __name__ == "__main__":
    main()
