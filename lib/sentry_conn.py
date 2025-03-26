import base64
import json

import requests

class APIClient:
    def __init__(self, base_url):
        self.api_token = ''
        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        if not base_url.endswith('/'):
            base_url += '/'
        self.__url = base_url + 'api/0/organizations' + self.organization_slug + '/'
        
    def get(self, url):
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json()