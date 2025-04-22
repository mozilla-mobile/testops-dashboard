import requests
from requests_toolbelt.utils.links import parse_link_header


class APIClient:
    def __init__(self, base_url):
        self.api_token = ''
        self.project_slug = ''
        if not base_url.endswith('/'):
            base_url += '/'
        self.__url = (
                '{0}api/0/'
            ).format(base_url)

    def get(self, uri):
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }

        url = self.__url + uri
        all_results = []

        while url:
            print(f"Fetching: {url}")
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()
            if isinstance(data, list):
                all_results.extend(data)
            else:
                return data  # For non-list endpoints

            link_header = response.headers.get("Link")
            links = parse_link_header(link_header) if link_header else {}
            next_link = links.get("next")

            url = next_link["url"] if next_link and next_link.get("results", "false").lower() == "true" else None

        return all_results

