#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# flake8: noqa
import os
import sys
import json
from prettytable import PrettyTable
import requests

BASE_URL = 'https://api.github.com'
GITHUB_ORG = 'mozilla-mobile'


try:
    API_TOKEN = os.environ['GITHUB_TOKEN']
    API_HEADER = {'Authorization': API_TOKEN, 'accept': 'application/json'}
except KeyError:
    print("ERROR: GITHUB_TOKEN env var not set")
    sys.exit()

project  = 'reference-browser'
EXCLUDED = ['MickeyMoz', 'mozilla-l10n-automation-bot', 'mergify[bot]', 'github-actions[bot]']

table = PrettyTable()
table.field_names = ["count", "title", "merged_at","user"]
table.align['count'] = "l"
table.align['title'] = "l"
table.align['merged_at'] = "l"
table.align['user'] = "l"

def url_pulls_base(project):
    return  '{0}/repos/{1}/{2}/pulls?state=closed'.format(BASE_URL, GITHUB_ORG, project)

def page_response(api):
    print(api)
    response = requests.get(api, headers=API_HEADER)
    return response.json()

def add_rows(data, row_count):
    for repository in data:
        title = repository["title"]
        merged_at = repository["merged_at"]
        user= repository["user"]["login"]
     
        if user not in EXCLUDED:
            if merged_at:
                table.add_row([row_count, title, merged_at, user])
                row_count += 1

    return table, row_count 

params = {'page': 1, 'per_page':100}
another_page = True
api = url_pulls_base(project)
count = 1
row_count = 1
while another_page: #the list of teams is paginated
    params = {'page': count, 'per_page':100}
    response = requests.get(api, params=params, headers=API_HEADER)
    print(response)
    r = response.json()
    
    if 'next' in response.links: #check if there is another page of organisations
        api = response.links['next']['url']
        print(api)
        table, row_count = add_rows(r, row_count)
        count += 1
        another_page=True
    else:
        another_page=False

print(table)
