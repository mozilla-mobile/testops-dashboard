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

PATH_IMAGES = "config/confluence/images"
PATH_YAML_FILES = "config/confluence/yaml"
PATH_XML_FILES = "config/confluence/xml"


def url_page(page_id):
    return f"{URL_WIKI_REST_API}/content/{page_id}"


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

def url_page(page_id):
    return f"{URL_WIKI_REST_API}/content/{page_id}"


def render_xml_template(template_path, params):
    with open(template_path, 'r') as file:
        template_content = file.read()
    
    template = Template(template_content)
    rendered_xml = template.render(**params)
    
    return rendered_xml



def main():
    page_id = "1663598593"
    page_title = "DEMO v2"

    # HARD-CODED PARAMS
    testrail_contacts = """ 
     <a href='mailto:csuciu@mozilla.com'>
      Catalin Suc1u
     </a>
     ,   
     <a href='mailto:amoldovan@mozilla.com'>
      Alina M0ld0van
     </a>
     ,   
     <a href='mailto:abodea@mozilla.com'>
      Andr3i Bodea
     </a>
     ,   
     <ac:link>
      <ri:user ri:userkey='712020:94a51a44-b5cc-4200-b015-b3344f6829a7'>
      </ri:user>
     </ac:link>"""

    testrail_report_summary = """
    <li>We started Full Functional test suite.</li>
    <li>We ran X sets of automated Full Functional tests on iPhone and iPad with XYZ experiment ON.</li>    
    """

    params = {
        'release_date': '2025-01-01',
        'version': 'v149',
        'testrail_report_url': 'https://mozilla.testrail.io/index.php?/runs/view/108599&group_by=cases:section_id&group_order=asc',
        'version_commit_hash': '12345',
        'testrail_report_summary': testrail_report_summary, 
        'testrail_run_1_result': 'PASS3D',
        'testrail_run_1_build_type': 'ARM64',
        'testrail_run_1_device': 'iPhone 16 Pro (iOS 18.3.2)',
        'testrail_run_2_result': 'PASS3D',
        'testrail_run_2_build_type': 'ARM64',
        'testrail_run_2_device': 'iPhone 16 Pro (iOS 18.3.2)',
        'testrail_issues_verified': 'N/A',
        'testrail_issues_new': 'N/A',
        'testrail_issues_known': '<a href="https://mozilla-hub.atlassian.net/browse/FXIOS-12650"</a>',
        'testrail_contacts': testrail_contacts,
    }
    

    TEMPLATE_PATH = f"{PATH_XML_FILES}/build-validation.xml"

    page_url = url_page(page_id)
    #page_url_storage = url_page_content_storage(page_id)
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as file:
        xml_content = file.read()
    output_xml = render_xml_template(TEMPLATE_PATH, params)

    print(f"UPDATE PAGE - page_id: {page_id}")
    page_data = page_object(page_url)
    current_version = page_data["version"]["number"]

    #new_content = page_html(page_id, page_sections)
    payload = page_payload(page_id, page_title, page_data,
                           current_version, output_xml)
    page_payload_write(page_id, payload)


if __name__ == "__main__":
    main()
