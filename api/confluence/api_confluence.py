#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import os
import glob
import json
import re
import requests
import sys
import yaml

from atlassian import Confluence
from bs4 import BeautifulSoup
from jinja2 import Template
from pathlib import Path
from typing import Literal, Optional

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


"""
# TODO: we should employ pathlib instead for all path declarations
PATH_CONFIG = "config/confluence"
PATH_IMAGES = f"{PATH_CONFIG}/images"
PATH_YAML_FILES = f"{PATH_CONFIG}/yaml"
PATH_XML_FILES = f"{PATH_CONFIG}/xml"
"""

"""
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
PATH_CONFIG = os.path.join(ROOT_DIR, 'config/confluence')
PATH_IMAGES = os.path.join(PATH_CONFIG, 'images')
PATH_YAML_FILES = os.path.join(PATH_CONFIG, 'yaml')
PATH_XML_FILES = os.path.join(PATH_CONFIG, 'xml')
"""

# Calculate project root (3 levels up from this file)
ROOT_DIR = Path(__file__).resolve().parents[2]

# Define paths
PATH_CONFIG = ROOT_DIR / 'config' / 'confluence'
PATH_IMAGES = PATH_CONFIG / 'images'
PATH_YAML_FILES = PATH_CONFIG / 'yaml'
PATH_XML_FILES = PATH_CONFIG / 'xml'


def _exists_status(p: Path) -> str:
    return "Exists" if p.exists() else "NOT FOUND"


# Diagnostic: Debug printouts to confirm paths
print(f"ROOT_DIR: {ROOT_DIR}")
print(f"PATH_CONFIG: {PATH_CONFIG} [{_exists_status(PATH_CONFIG)}]")
print(f"PATH_IMAGES: {PATH_IMAGES} [{_exists_status(PATH_IMAGES)}]")
print(
    f"PATH_YAML_FILES: {PATH_YAML_FILES} [{_exists_status(PATH_YAML_FILES)}]"
)
print(f"PATH_XML_FILES: {PATH_XML_FILES} [{_exists_status(PATH_XML_FILES)}]")

# Diagnostic: Fail fast if config folder is missing
if not PATH_CONFIG.exists():
    raise FileNotFoundError(f"Config path does not exist: {PATH_CONFIG}")

# ------------------------------------------------------------------
# Managed page region helpers
# ------------------------------------------------------------------

# Confluence page managed region markers (single managed region per page)
# Use a wrapper div that Confluence preserves in storage format.
MANAGED_ATTR = {"data-managed-region": "true"}
GENERATED_ATTR = {"data-generated-content": "true"}
START_MARK = '<div data-managed-region="true">'
END_MARK = "</div>"
LEGACY_BLOCK_RE = re.compile(
    r"\s*<h[1-6][^>]*>.*?</h[1-6]>\s*<table[^>]*>.*?</table>\s*",
    re.IGNORECASE | re.DOTALL,
)

# Flexible match for the spacer we insert between the heading and managed region
SPACER_RE = re.compile(
    r"<hr\b[^>]*>.*?<hr\b[^>]*>",
    re.IGNORECASE | re.DOTALL,
)


MissingMode = Literal["append", "replace_all"]


def split_heading(generated_html: str):
    # Split the first heading (H1–H6) from the rest.
    m = re.search(r"</h[1-6]>", generated_html, flags=re.I)
    if not m:
        return "", generated_html
    return generated_html[: m.end()], generated_html[m.end():]


def has_managed_block(html: str) -> bool:
    if not html:
        return False
    # Fast path substring checks (support both div wrapper and legacy comments)
    if 'data-managed-region="true"' in html:
        return True
    if "<!-- BEGIN MANAGED" in html and "<!-- END MANAGED" in html:
        return True
    # Fallback parse (handles attribute reordering/formatting)
    try:
        soup = BeautifulSoup(html, "html.parser")
        return soup.find(attrs={"data-managed-region": True}) is not None
    except Exception:
        return False


def make_managed_block(inner_html: str) -> str:
    # Build a managed wrapper with a nested generated-content region we control.
    return (
        "<!-- BEGIN MANAGED -->\n"
        f"{START_MARK}\n"
        f"  <div data-generated-content=\"true\">\n{inner_html}\n  </div>\n"
        f"{END_MARK}\n"
        "<!-- END MANAGED -->"
    )


def upsert_managed_block(
    existing_html: Optional[str],
    inner_html: str,
    on_missing: MissingMode = "append",
) -> str:
    """
    Merge the auto-generated fragment (inner_html) into the existing page HTML:
    - If the managed markers already exist, replace ONLY the content between them.
    - If markers are missing:
        - append: append a new managed block to the end of the page
        - replace_all: replace the entire page body with just the managed block
    Params:
      existing_html: full Confluence storage HTML for the page
                     (can be None on first run)
      inner_html: the auto-generated fragment (tables + Looker images),
                  NOT the whole page
    Returns:
      A full HTML string ready to PUT back to Confluence.
    """
    # 1) Normalize input
    existing_html = existing_html or ""

    # 2) If a managed block exists, replace its inner HTML using BeautifulSoup
    try:
        soup = BeautifulSoup(existing_html, "html.parser")
    except Exception:
        soup = None

    if soup is not None:
        container = soup.find(attrs={"data-managed-region": True})
        if container is not None:
            # Find or create the generated-content child
            gen = container.find(attrs={"data-generated-content": True})
            if gen is None:
                gen = soup.new_tag("div")
                gen.attrs.update(GENERATED_ATTR)
                # Put generated-content at top of the managed region
                container.insert(0, gen)
            # Replace inner content of the generated block
            gen.clear()
            inner_soup = BeautifulSoup(inner_html, "html.parser")
            for child in list(inner_soup.contents):
                gen.append(child)
            return str(soup)

    # Fallback: legacy comment markers present? Replace them with div wrapper
    legacy_pattern = re.compile(
        r"<!-- BEGIN MANAGED(?::[^>]*)? -->.*?<!-- END MANAGED(?::[^>]*)? -->",
        re.DOTALL,
    )
    replacement = make_managed_block(inner_html)
    if legacy_pattern.search(existing_html):
        # Try to preserve non-table user edits when migrating from legacy block
        def migrate_legacy_to_managed(match: re.Match) -> str:
            legacy_inner = match.group(0)
            # Extract the inner part between the comments
            inner = re.sub(
                r"^<!-- BEGIN MANAGED.*?-->\\s*|\\s*<!-- END MANAGED.*?-->$",
                "",
                legacy_inner,
                flags=re.DOTALL,
            )

            try:
                legacy_soup = BeautifulSoup(inner, "html.parser")
                preserved = []
                for node in list(legacy_soup.contents):
                    if getattr(node, "name", None) == "table":
                        # skip old generated tables
                        continue
                    preserved.append(node)
                # Build new managed wrapper with fresh generated content
                new_soup = BeautifulSoup(make_managed_block(inner_html), "html.parser")
                container = new_soup.find(attrs={"data-managed-region": True})
                # Append preserved nodes after the generated-content block
                for node in preserved:
                    container.append(node)
                return str(new_soup)
            except Exception:
                # Fallback: no migration, just replace
                return replacement

        return legacy_pattern.sub(migrate_legacy_to_managed, existing_html, count=1)

    # 3) If missing, choose first-run behavior
    replacement = make_managed_block(inner_html)
    if on_missing == "replace_all":
        return replacement
    return f"{existing_html}\n{replacement}" if existing_html else replacement

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
    return f"{path}?status=current&expand=body.storage,version,space"


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
        sys.exit(1)


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

            delete_response = requests.delete(
                delete_url,
                headers=headers,
                auth=auth,
            )
            if delete_response.status_code == 204:
                print(f"Attachment {attachment_id} deleted successfully.")
            else:
                print(f"Failed to delete attachment {attachment_id}.")
    else:
        print(
            f"Failed to fetch attachments: {response.status_code}"
        )
        print(response.text)


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
        if filename.lower().endswith(
            (
                '.png',
                '.jpg',
                '.jpeg',
                '.gif',
                '.bmp',
                '.webp',
            )
        ):
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
    return (
        f"""
            <row>
        <td><b>{report_title}</b></td>
        <td>{report_description}</td>
        <td>
        <a href="{looker_graph_url}"><ac:image>
            <ri:attachment ri:filename="{attachment_filename}"/>
        </ac:image></a></td>
        </row>
        """
    )


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

            print(f"PROCESS ATTACHMENTS - page_id: {page_id}")
            image_attachments_list(page_id)
            image_attachments_delete(page_id)
            image_attachments_list(page_id)
            image_attachments_upload(page_id)

            print(f"UPDATE PAGE - page_id: {page_id}")
            page_data = page_object(url_page_content_storage(page_id))
            existing_storage_html = page_data["body"]["storage"]["value"]
            current_version = page_data["version"]["number"]

            # Generate only the managed fragment (tables + images)
            full_generated = page_html(page_id, page_sections)
            heading_html, table_html = split_heading(full_generated)

            if not has_managed_block(existing_storage_html):
                # If the spacer exists, treat as already-seeded
                # and replace content after it
                spacer_match = SPACER_RE.search(existing_storage_html)
                if spacer_match:
                    prefix_html = existing_storage_html[: spacer_match.end()]
                    # Preserve everything after the spacer (including existing Notes)
                    remaining_html = existing_storage_html[spacer_match.end():]
                    # Just insert the managed block and keep the rest
                    merged_html = (
                        prefix_html
                        + make_managed_block(table_html)
                        + remaining_html
                    )
                else:
                    # One-time cleanup: remove legacy heading+table blocks if present
                    cleaned_html = LEGACY_BLOCK_RE.sub("", existing_storage_html)

                    # First run: insert title and a persistent gap above
                    # the managed region
                    extra_html = (
                        "\n<hr />\n<p><br/></p>\n"
                        "<hr />\n"
                    )

                    # Build the full page body with a managed wrapper so we
                    # don't append repeatedly
                    notes_html = (
                        "<hr />\n"
                        "<p><em>Notes</em></p>\n"
                        "<hr />\n"
                        "<div data-notes-region=\"true\"><p><br/></p></div>\n"
                    )
                    merged_html = "".join([
                        f"{cleaned_html}{heading_html}{extra_html}",
                        make_managed_block(table_html),
                        notes_html,
                    ])
            else:
                # Managed wrapper exists; replace its contents only
                merged_html = upsert_managed_block(
                    existing_storage_html,
                    table_html
                )

            payload = page_payload(
                page_id,
                page_title,
                page_data,
                current_version,
                merged_html
            )

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

    payload = page_payload(
        page_id,
        page_data["title"],
        page_data,
        current_version,
        output_xml,
    )
    page_payload_write(page_id, payload)


# REPORT: Build Validation

def page_report_build_validation(
    page_id,
    projects_id,
    testrail_milestone_id,
    testrail_milestone_title,
    testrail_report_url,
    build_version,
    signoff_date,
    test_status,
    test_summary,
    ship_recommend,
    ship_recommend_verbose,
    contacts,
):
    """
    Applies params to jinja/mustache-style XML template and inserts into page
    """

    # TODO: hard-coded params for now...
    params = {
        'release_date': signoff_date,
        'build_version': build_version,
        'build_version_commit_hash': '12345',
        'testrail_report_url': (
            'https://mozilla.testrail.io/index.php?/runs/view/108599'
            '&group_by=cases:section_id&group_order=asc'
        ),
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
    payload = page_payload(
        page_id,
        page_data["title"],
        page_data,
        current_version,
        output_xml,
    )
    page_payload_write(page_id, payload)


def main():
    # TODO: phase 2 PR - instead of invoking this directly from main,
    # invoke it from __main__.py --report-type looker-graphs
    pages_looker_graphs()

    # TODO: design approach for custom (XML-config) reports
    """
    page_id = "1663598593"
    page_title = "DEMO v2"
    projects_id = 14 # Firefox for iOS
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

    page_report_build_validation(
        page_id=page_id,
        projects_id=projects_id,
        testrail_milestone_id,
        testrail_milestone_title=release,
        testrail_report_url=testrail_report_url,
        build_version=build_version,
        signoff_date=release_date,
        test_status=testing_status,
        test_summary=testing_summary,
        ship_recommend=qa_recommendation,
        ship_recommend_verbose=qa_recommendation_verbose,
        contacts=qa_contacts,
    )
    """


if __name__ == "__main__":
    main()
