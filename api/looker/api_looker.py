#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import requests
import time
import re
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

LOOKER_HOST = os.environ['LOOKER_HOST']
LOOKER_CLIENT_ID = os.environ['LOOKER_CLIENT_ID']
LOOKER_SECRET = os.environ['LOOKER_SECRET']

FOLDER_ID = 1820
MAX_CONCURRENT_REQUESTS = 100

project_root = Path.cwd()
IMAGES_DIR = project_root / "config" / "confluence" / "images"


# Authenticate and Get Access Token
def get_looker_token():
    auth_url = f"{LOOKER_HOST}/api/4.0/login"
    payload = {"client_id": LOOKER_CLIENT_ID, "client_secret": LOOKER_SECRET}
    response = requests.post(auth_url, data=payload)
    print(response)
    response.raise_for_status()  # Raise an error for bad responses

    return response.json().get("access_token")


# Request a render task for the Look
def create_render_task(token, look_id, fmt="png", width=400, height=400):
    url = (f"{LOOKER_HOST}/api/4.0/render_tasks/looks/"
           f"{look_id}/{fmt}?width={width}&height={height}")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"width": width, "height": height}

    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()["id"]


# Poll until the render task is complete
def wait_for_render_task(token, task_id, timeout=120):
    """Waits for the Looker render task to complete, with a timeout."""
    url = f"{LOOKER_HOST}/api/4.0/render_tasks/{task_id}"
    headers = {"Authorization": f"Bearer {token}"}
    start = time.time()

    while True:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        status = resp.json()

        if status["status"] == "success":
            return task_id

        if status["status"] in ["failure", "expired"]:
            raise Exception(f"Render task failed or expired: {status}")

        if status["status"] == "enqueued_for_render":
            elapsed = time.time() - start
            if elapsed > timeout:
                raise Exception(
                    f"Task stuck in 'enqueued_for_render' > {timeout}s. Aborting."
                )

        time.sleep(2)


# Download the rendered image and save it as a PNG file
def download_image(access_token, task_id, look_name, images_dir):
    """Fetch the rendered Looker image after the task completes."""
    url = f"{LOOKER_HOST}/api/4.0/render_tasks/{task_id}/results"
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    # Change the name to graph-name.png
    look_name = look_name.lower().strip()
    look_name = re.sub(r'[^a-z0-9\s-]', '', look_name)
    look_name = re.sub(r'[-\s]+', '-', look_name)

    # Define the path to save the image
    save_path = os.path.join(images_dir, f"{look_name}.png")

    with open(save_path, "wb") as f:
        f.write(response.content)

    print(f"Graph image saved as {save_path}")


def get_looks_in_folder(access_token, FOLDER_ID):
    url = f"{LOOKER_HOST}/api/4.0/folders/{FOLDER_ID}/looks"
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    looks = response.json()
    return looks


def process_single_look(access_token, look, images_dir):
    """Process a single look: create task, wait for completion, download image"""
    try:
        print(f"Processing - ID: {look['id']}, Title: {look['title']}")
        task_id = create_render_task(access_token, look['id'])
        result_url = wait_for_render_task(access_token, task_id)
        download_image(access_token, result_url, look['title'], images_dir)
        return f"Successfully processed look {look['id']}: {look['title']}"
    except Exception as e:
        return f"Failed to process look {look['id']}: {look['title']} - Error: {str(e)}"


def main():
    access_token = get_looker_token()
    # Ensure the directory exists, create if not
    os.makedirs(IMAGES_DIR, exist_ok=True)

    all_looks = get_looks_in_folder(access_token, FOLDER_ID)

    print(f"Found {len(all_looks)} looks to process")

    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
        # Submit all tasks
        future_to_look = {
            executor.submit(process_single_look, access_token, look, IMAGES_DIR): look
            for look in all_looks
        }

        for future in as_completed(future_to_look):
            look = future_to_look[future]
            try:
                result = future.result()
                print(result)
            except Exception as exc:
                print(f'Look {look["id"]} generated an exception: {exc}')


if __name__ == "__main__":
    main()
