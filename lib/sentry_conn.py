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
        print(url)
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json()
