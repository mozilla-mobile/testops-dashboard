#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import inspect

from database import (
    Database,
)
from sqlalchemy.exc import OperationalError

_DB = None


def _db() -> Database():
    global _DB
    if _DB is None:
        _DB = Database()
    return _DB


def jira_delete(table):
    # DIAGNOSTIC
    print("--------------------------------------")
    print("DIAGNOSTIC: helpers")
    print("--------------------------------------")
    print(inspect.currentframe().f_code.co_name)

    db = _db()
    # Check if there is at least one row
    has_rows = db.session.query(table).first() is not None
    if not has_rows:
        print("Table is empty, skipping delete()")
        return

    try:
        db.session.query(table).delete()
        db.session.commit()
    except OperationalError as e:
        db.session.rollback()
        print(f"Delete failed with OperationalError: {e}")
