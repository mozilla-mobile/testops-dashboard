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
PATH_YAML_FILES = "config/confluence"


def url_page(page_id):
    return f"{URL_WIKI_REST_API}/content/{page_id}"


def url_page_content_storage(page_id):
    return f"{URL_WIKI_REST_API}/content/{page_id}?expand=body.storage"


def page_object_storage(page_url):
    """
    give page url, returns page object as JSON
    """
    response = requests.get(page_url, auth=auth, headers=headers)
    if response.status_code != 200:
        print("Failed to retrieve the page")
        print(response.text)
        exit()
    return response.json()["body"]["storage"]["value"]

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

def main():
    page_id = "1663598593"
    page_title = "DEMO v2"
    
    page_url = url_page(page_id)
    #page_url_storage = url_page_content_storage(page_id)
    with open("confluence_source.xml", "r", encoding="utf-8") as file:
        xml_content = file.read()

    print(f"UPDATE PAGE - page_id: {page_id}")
    page_data = page_object(page_url)
    current_version = page_data["version"]["number"]

    #new_content = page_html(page_id, page_sections)
    payload = page_payload(page_id, page_title, page_data,
                           current_version, xml_content)
    page_payload_write(page_id, payload)


def main_OLD():
    page_id = "1663598593"
    page_url = url_page_content_storage(page_id)
    resp = page_object(page_url)
    soup = BeautifulSoup(resp, "html.parser")
    pretty_xml = soup.prettify()
    #pretty_xml = soup.encode(formatter="minimal").decode("utf-8")
    with open("confluence_source.xml", "w", encoding="utf-8") as f:
        f.write(pretty_xml)


if __name__ == "__main__":
    main()
