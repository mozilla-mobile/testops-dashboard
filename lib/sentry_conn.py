import requests


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
                print(f"Received {len(all_results)} items")
            else:
                return data  # For non-list endpoints

            link_header = response.headers.get("Link", "")
            links = requests.utils.parse_header_links(link_header.rstrip('>').replace('>,<', ',<'))

            next_url = None
            for link in links:
                if link.get("rel") == "next" and link.get("url") and link.get("results") == "true":
                    next_url = link["url"]

            url = next_url

        return all_results
