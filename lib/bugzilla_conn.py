#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

import bugzilla

from constants import BUGZILLA_URL


class BugzillaAPIClient:

    @property
    def URL(self) -> str:
        return BUGZILLA_URL

    @property
    def bz_client(self) -> bugzilla.Bugzilla:
        return self._bz_client

    @bz_client.setter
    def bz_client(self, client: bugzilla.Bugzilla) -> None:
        self._bz_client = client

    def __init__(self) -> None:
        self.key = os.environ.get("BUGZILLA_API_KEY")
        if not self.key:
            raise Exception("Missing BUGZILLA_API_KEY")
        if self.key:
            self.bz_client = bugzilla.Bugzilla(self.URL, api_key=self.key)
