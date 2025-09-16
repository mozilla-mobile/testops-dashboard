#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import os
import glob
import json
import logging
import re
import requests
import sys
import yaml

from atlassian import Confluence
from bs4 import BeautifulSoup
from jinja2 import Template
from pathlib import Path
from typing import Literal, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

# Match the Notes section marker (heading + div + HR separator)
# The data-notes-region attribute is optional in case Confluence strips it
# Use non-greedy match and require HR immediately after the div
SPACER_RE = re.compile(
    r"<h3>Notes</h3>\s*<div[^>]*>.*?</div>\s*<hr\s*/?>",
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
    # Layer 1: Fast path substring checks (data attributes)
    if 'data-managed-region="true"' in html:
        logger.info("Managed block detected via Layer 1: data-managed-region")
        return True
    # Layer 2: HTML comments (rarely stripped by Confluence)
    if "<!-- BEGIN MANAGED" in html and "<!-- END MANAGED" in html:
        logger.info("Managed block detected via Layer 2: HTML comments")
        return True
    # Layer 3: Confluence anchor macros (never stripped)
    if "managed-region-start" in html and "managed-region-end" in html:
        logger.info("Managed block detected via Layer 3: anchor macros")
        return True
    # Layer 4: CSS class (always preserved)
    if "auto-managed-region" in html or "auto-generated-content" in html:
        logger.info("Managed block detected via Layer 4: CSS classes")
        return True
    # Layer 5: BeautifulSoup parse (handles attribute variations)
    try:
        soup = BeautifulSoup(html, "html.parser")
        # Check for any of our markers
        if soup.find(attrs={"data-managed-region": True}):
            logger.info("Managed block detected via Layer 5: data-managed-region")
            return True
        if soup.find(attrs={"class": "auto-managed-region"}):
            logger.info("Managed block detected via Layer 5: auto-managed-region")
            return True
        if soup.find("ac:parameter", string="managed-region-start"):
            logger.info("Managed block detected via Layer 5: anchor macro")
            return True
    except Exception as e:
        logger.warning(f"Layer 5 BeautifulSoup detection failed: {e}")
    logger.info("Managed block NOT detected - all 5 layers failed")
    return False


def make_managed_block(inner_html: str) -> str:
    # Build a managed wrapper with a nested generated-content region we control.
    # Multiple markers ensure detection even if Confluence strips some:
    # 1. HTML comments (most reliable)
    # 2. data-* attributes (standard HTML5)
    # 3. class attribute (always preserved by Confluence)
    # 4. ac:parameter macro (Confluence-native, never stripped)
    return (
        "<!-- BEGIN MANAGED -->\n"
        '<ac:structured-macro ac:name="anchor" ac:schema-version="1">'
        '<ac:parameter ac:name="id">managed-region-start</ac:parameter>'
        '</ac:structured-macro>\n'
        f'<div data-managed-region="true" class="auto-managed-region">\n'
        f'  <div data-generated-content="true" class="auto-generated-content">'
        f'\n{inner_html}\n  </div>\n'
        f"</div>\n"
        '<ac:structured-macro ac:name="anchor" ac:schema-version="1">'
        '<ac:parameter ac:name="id">managed-region-end</ac:parameter>'
        '</ac:structured-macro>\n'
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
    logger.info("upsert_managed_block called")
    # 1) Normalize input
    existing_html = existing_html or ""

    # 2) If a managed block exists, replace its inner HTML using BeautifulSoup
    try:
        soup = BeautifulSoup(existing_html, "html.parser")
        logger.info("BeautifulSoup parsing successful")
    except Exception as e:
        logger.warning(f"BeautifulSoup parsing failed: {e}")
        soup = None

    if soup is not None:
        # Try multiple detection methods (same 5-layer approach as has_managed_block)
        container = None

        # DIAGNOSTIC: Log what we're searching in
        logger.info(
            f"Searching for container in HTML with length: "
            f"{len(existing_html)}"
        )
        logger.info(
            f"HTML contains 'auto-managed-region': "
            f"{'auto-managed-region' in existing_html}"
        )
        logger.info(
            f"HTML contains 'managed-region-start': "
            f"{'managed-region-start' in existing_html}"
        )

        # Layer 1: data-managed-region attribute
        container = soup.find(attrs={"data-managed-region": True})
        if container:
            logger.info("Container found via Layer 1: data-managed-region")
        # Layer 2: CSS class (search for class containing the string)
        if container is None:
            logger.info("Layer 1 failed, trying Layer 2: CSS class")
            # BeautifulSoup class_ accepts a function for flexible matching

            def has_managed_class(class_list):
                if class_list is None:
                    return False
                # class_list can be a string or list
                if isinstance(class_list, str):
                    return "auto-managed-region" in class_list
                return "auto-managed-region" in class_list

            container = soup.find("div", class_=has_managed_class)
            if container:
                logger.info("Container found via Layer 2: CSS class")
            else:
                logger.warning(
                    "Layer 2 failed: No element with "
                    "class='auto-managed-region'"
                )
        # Layer 3: Look for div near HTML comments (siblings or contained)
        if container is None:
            # First try: comments as siblings (preferred structure)
            html_str = str(soup)
            if "<!-- BEGIN MANAGED" in html_str:
                # Find all comments
                def is_begin_comment(text):
                    is_comment = isinstance(text, type(soup))
                    has_marker = "BEGIN MANAGED" in str(text)
                    return is_comment and has_marker
                comments = soup.find_all(string=is_begin_comment)
                for comment in comments:
                    # Check next sibling after comment
                    next_elem = comment.find_next_sibling()
                    if next_elem and next_elem.name == "div":
                        container = next_elem
                        logger.info(
                            "Container found via Layer 3: "
                            "HTML comment sibling"
                        )
                        break
            # Fallback: div containing comments (legacy)
            if container is None:
                for div in soup.find_all("div"):
                    div_str = str(div)
                    if "<!-- BEGIN MANAGED" in div_str:
                        container = div
                        logger.info(
                            "Container found via Layer 3: "
                            "HTML comments (legacy)"
                        )
                        break
        # Layer 4: Robust search between anchor macros
        if container is None:
            logger.info(
                "Layer 3 failed, trying Layer 4: "
                "search between anchor macros"
            )
            # Find BOTH anchor macros
            start_param = soup.find(
                "ac:parameter",
                string="managed-region-start"
            )
            end_param = soup.find(
                "ac:parameter",
                string="managed-region-end"
            )
            if start_param and end_param:
                logger.info("Found both anchor macros")
                start_macro = start_param.find_parent("ac:structured-macro")
                end_macro = end_param.find_parent("ac:structured-macro")
                if start_macro and end_macro:
                    logger.info("Found parent macros for both anchors")
                    # Find the parent containers (might be <p> tags)
                    start_container = start_macro.find_parent()
                    end_container = end_macro.find_parent()
                    logger.info(
                        f"Start container: <{start_container.name}>, "
                        f"End container: <{end_container.name}>"
                    )
                    # Collect ALL content between the two anchor containers
                    content_between = []
                    current = start_container.find_next_sibling()
                    while current and current != end_container:
                        content_between.append(current)
                        current = current.find_next_sibling()
                    if content_between:
                        logger.info(
                            f"Found {len(content_between)} elements "
                            f"between anchors"
                        )
                        # Create a new managed div wrapper
                        container = soup.new_tag("div")
                        container.attrs["data-managed-region"] = "true"
                        container.attrs["class"] = "auto-managed-region"
                        # Create generated-content child
                        gen = soup.new_tag("div")
                        gen.attrs["data-generated-content"] = "true"
                        gen.attrs["class"] = "auto-generated-content"
                        # Move all content into the generated div
                        for element in content_between:
                            gen.append(element.extract())
                        container.append(gen)
                        # Insert the new container after start_container
                        start_container.insert_after(container)
                        # Now container has the managed structure
                        logger.info(
                            "Container found via Layer 4: "
                            "reconstructed from content between anchors"
                        )
                        # CRITICAL FIX: Update the reconstructed container
                        # immediately and return to prevent fallthrough
                        gen.clear()
                        logger.info(
                            f"Cleared generated-content div, inserting "
                            f"{len(inner_html)} chars"
                        )
                        inner_soup = BeautifulSoup(inner_html, "html.parser")
                        for child in list(inner_soup.contents):
                            gen.append(child)
                        logger.info(
                            "Successfully updated managed block content "
                            "in Layer 4"
                        )
                        # Return immediately - don't fall through to append!
                        return str(soup)
                    else:
                        logger.warning(
                            "Layer 4: No content found between anchor macros"
                        )
                        container = None
                else:
                    logger.warning(
                        "Could not find parent ac:structured-macro "
                        "for anchors"
                    )
            else:
                logger.warning(
                    "Layer 4 failed: Could not find both anchor macros"
                )
        # Layer 5: Look for div containing auto-generated-content child
        if container is None:
            for div in soup.find_all("div", recursive=True):
                if div.find(attrs={"data-generated-content": True}):
                    container = div
                    logger.info(
                        "Container found via Layer 5: "
                        "parent of generated-content"
                    )
                    break
                if div.find(attrs={"class": "auto-generated-content"}):
                    container = div
                    logger.info(
                        "Container found via Layer 5: "
                        "parent of auto-generated-content class"
                    )
                    break
        if container is not None:
            logger.info(
                "Container found in upsert_managed_block, "
                "updating content"
            )
            # Find or create the generated-content child
            gen = container.find(attrs={"data-generated-content": True})
            if gen is None:
                gen = container.find(attrs={"class": "auto-generated-content"})
            if gen is None:
                gen = soup.new_tag("div")
                gen.attrs.update(GENERATED_ATTR)
                gen.attrs["class"] = "auto-generated-content"
                # Put generated-content at top of the managed region
                container.insert(0, gen)
            # Ensure attributes are present (restore if stripped)
            if "data-managed-region" not in container.attrs:
                container.attrs["data-managed-region"] = "true"
            has_class = "class" in container.attrs
            has_managed_class = (
                "auto-managed-region" in container.attrs.get("class", "")
            )
            if not has_class or not has_managed_class:
                container.attrs["class"] = "auto-managed-region"
            if "data-generated-content" not in gen.attrs:
                gen.attrs["data-generated-content"] = "true"
            has_gen_class = "class" in gen.attrs
            has_gen_content_class = (
                "auto-generated-content" in gen.attrs.get("class", "")
            )
            if not has_gen_class or not has_gen_content_class:
                gen.attrs["class"] = "auto-generated-content"
            # Replace inner content of the generated block
            gen.clear()
            logger.info(
                f"Cleared generated-content div, inserting "
                f"{len(inner_html)} chars"
            )
            inner_soup = BeautifulSoup(inner_html, "html.parser")
            for child in list(inner_soup.contents):
                gen.append(child)
            logger.info("Successfully updated managed block content")
            return str(soup)
        else:
            logger.warning(
                "Container NOT found in upsert_managed_block, "
                "falling through to legacy/append path"
            )

    # Fallback: legacy comment markers present? Replace them with div wrapper
    legacy_pattern = re.compile(
        r"<!-- BEGIN MANAGED(?::[^>]*)? -->.*?<!-- END MANAGED(?::[^>]*)? -->",
        re.DOTALL,
    )
    replacement = make_managed_block(inner_html)
    logger.info("Checking for legacy comment markers")
    if legacy_pattern.search(existing_html):
        logger.info("Legacy pattern found, migrating to managed block")
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
    logger.warning(
        f"Reached fallback path with on_missing={on_missing}, "
        f"APPENDING new managed block"
    )
    replacement = make_managed_block(inner_html)
    if on_missing == "replace_all":
        logger.info("on_missing=replace_all, returning only replacement")
        return replacement
    logger.warning(
        "APPENDING managed block to existing HTML - "
        "THIS CAUSES DUPLICATES"
    )
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

            # For multi-section pages, put everything in managed region
            # For single-section pages, keep first heading outside
            if len(page_sections) > 1:
                heading_html = ""
                table_html = full_generated
            else:
                heading_html, table_html = split_heading(full_generated)

            if not has_managed_block(existing_storage_html):
                logger.info(
                    f"Page {page_id}: Managed block NOT detected, "
                    f"checking for spacer"
                )
                # If the spacer exists, check if there's already content after it
                spacer_match = SPACER_RE.search(existing_storage_html)
                if spacer_match:
                    logger.info(
                        f"Page {page_id}: Spacer found, "
                        f"checking content after spacer"
                    )
                    # Self-heal: Restore data-notes-region attribute if stripped
                    spacer_html = spacer_match.group(0)
                    if 'data-notes-region' not in spacer_html:
                        # Fix the Notes div to include the attribute
                        healed_spacer = spacer_html.replace(
                            '<div>',
                            '<div data-notes-region="true">',
                            1
                        )
                        # Also handle case where div has other attributes
                        if healed_spacer == spacer_html:  # No replacement made
                            healed_spacer = spacer_html.replace(
                                '<div ',
                                '<div data-notes-region="true" ',
                                1
                            )
                        # Update the HTML with healed spacer
                        prefix = existing_storage_html[:spacer_match.start()]
                        suffix = existing_storage_html[spacer_match.end():]
                        existing_storage_html = prefix + healed_spacer + suffix
                    # Check if there's already managed content after the spacer
                    content_after_spacer = existing_storage_html[spacer_match.end():]

                    # If there's substantial content after spacer, treat it as managed
                    # and use upsert logic instead of inserting new content
                    has_tables = "<table" in content_after_spacer
                    has_h1 = "<h1>" in content_after_spacer
                    has_h2 = "<h2>" in content_after_spacer
                    has_headings = has_h1 or has_h2
                    has_content = content_after_spacer.strip()
                    if has_content and (has_tables or has_headings):
                        logger.warning(
                            f"Page {page_id}: Content detected after spacer "
                            f"(tables={has_tables}, headings={has_headings}), "
                            f"REPLACING"
                        )
                        # Content exists after spacer - REPLACE it
                        prefix_html = existing_storage_html[: spacer_match.end()]

                        # Use the same multi-section logic as the first-run path
                        if len(page_sections) > 1:
                            content_to_insert = make_managed_block(full_generated)
                        else:
                            content_to_insert = make_managed_block(table_html)

                        merged_html = prefix_html + content_to_insert
                    else:
                        logger.info(
                            f"Page {page_id}: Spacer exists but no content after, "
                            f"first-time setup"
                        )
                        # Spacer exists but no content after - first-time setup
                        prefix_html = existing_storage_html[: spacer_match.end()]
                        # Use the same multi-section logic as the first-run path
                        if len(page_sections) > 1:
                            content_to_insert = make_managed_block(full_generated)
                        else:
                            content_to_insert = make_managed_block(table_html)

                        merged_html = prefix_html + content_to_insert
                else:
                    logger.info(
                        f"Page {page_id}: No spacer found, "
                        f"creating new Notes section and managed block"
                    )
                    # One-time cleanup: remove legacy heading+table blocks if present
                    cleaned_html = LEGACY_BLOCK_RE.sub("", existing_storage_html)

                    # Create a single editable Notes region at the top with guidance
                    notes_html = (
                        "<ac:structured-macro ac:name=\"info\">\n"
                        "  <ac:rich-text-body>\n"
                        "    <p><strong>📝 Editable Section:</strong> "
                        "Add your notes, updates, and comments below. "
                        "The generated content (tables and charts) will be "
                        "automatically updated while preserving your notes.</p>\n"
                        "    <p><strong>⚠️ Important:</strong> "
                        "Do not modify the \"Notes\" heading or remove the "
                        "horizontal line separator. "
                        "Use H4-H6 headings for subsections.</p>\n"
                        "  </ac:rich-text-body>\n"
                        "</ac:structured-macro>\n"
                        "<h3>Notes</h3>\n"
                        "<div data-notes-region=\"true\">\n"
                        "  <p><em>Add notes, updates, & comments here.</em></p>\n"
                        "  <p><br/></p>\n"
                        "</div>\n"
                        "<hr />\n"
                    )

                    # Build the full page body with Notes at top, then managed content
                    merged_html = "".join([
                        cleaned_html,
                        heading_html,
                        notes_html,
                        make_managed_block(table_html),
                    ])
            else:
                logger.info(
                    f"Page {page_id}: Managed block DETECTED, "
                    f"using upsert to update content"
                )
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
