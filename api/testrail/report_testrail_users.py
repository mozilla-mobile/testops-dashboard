# report_testrail_users.py
"""Temporary no-recursion implementation for PR4 cutover.

Avoids calling TestRailClient to prevent infinite loops with adapters.
TODO(PR4b): replace with real fetch -> prepare -> insert logic (direct DB).
"""

def fetch_testrail_users(*_args, **_kwargs):
    return {"status": "skipped", "reason": "temporary stub during refactor: users"}

def prepare_testrail_users(raw):
    return raw

def insert_testrail_users(_df, *_args, **_kwargs):
    return True

def testrail_users_update(*args, **kwargs):
    raw = fetch_testrail_users(*args, **kwargs)
    df = prepare_testrail_users(raw)
    return insert_testrail_users(df, *args, **kwargs)
