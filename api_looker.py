import requests
import time
import re
import os

LOOKER_HOST = os.environ['LOOKER_HOST']
LOOKER_CLIENT_ID = os.environ['LOOKER_CLIENT_ID']
LOOKER_SECRET = os.environ['LOOKER_SECRET']

FOLDER_ID = 177
IMAGES_DIR = "config/confluence/images"


# Authenticate and Get Access Token
def get_looker_token():
    auth_url = f"{LOOKER_HOST}/api/4.0/login"
    payload = {"client_id": LOOKER_CLIENT_ID, "client_secret": LOOKER_SECRET}
    response = requests.post(auth_url, data=payload)
    print(response)
    response.raise_for_status()  # Raise an error for bad responses

    return response.json().get("access_token")


# Request a render task for the Look
def create_render_task(access_token, look_id, image_format="png", width=400, height=400): # noqa
    url = f"{LOOKER_HOST}/api/4.0/render_tasks/looks/{look_id}/{image_format}?width={width}&height={height}" # noqa
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"width": width, "height": height}

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    return response.json()["id"]

# Request a render task for the Dashboard
def create_render_dashboard_task(access_token, dashboard_id, image_format="png", width=400, height=200): # noqa
    url = f"{LOOKER_HOST}/api/4.0/render_tasks/dashboards/{dashboard_id}/{image_format}?width={width}&height={height}" # noqa
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"width": width, "height": height}

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    return response.json()["id"]


# Poll until the render task is complete
def wait_for_render_task(access_token, task_id, timeout=120):
    # Waits for the Looker render task to complete, with a timeout.
    url = f"{LOOKER_HOST}/api/4.0/render_tasks/{task_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    start_time = time.time()

    while True:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        task_status = response.json()

        if task_status["status"] == "success":
            return task_id  # Return the task_id to fetch the image

        elif task_status["status"] in ["failure", "expired"]:
            raise Exception(f"Render task failed or expired: {task_status}")

        elif task_status["status"] == "enqueued_for_render":
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                raise Exception(f"Render task stuck in 'enqueued_for_render' for {timeout} seconds. Aborting.") # noqa

        time.sleep(5)


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


def main():
    access_token = get_looker_token()
    # Ensure the directory exists, create if not
    os.makedirs(IMAGES_DIR, exist_ok=True)

    all_looks = get_looks_in_folder(access_token, FOLDER_ID)
    for look in all_looks:
        print(f"- ID: {look['id']}, Title: {look['title']}")
        task_id = create_render_task(access_token, look['id'])
        result_url = wait_for_render_task(access_token, task_id)
        download_image(access_token, result_url, look['title'], IMAGES_DIR)


if __name__ == "__main__":
    main()
