# report_testrail_testplans.py
"""Temporary no-recursion implementation for PR4 cutover.

Breaks the mutual recursion between TestRailClient <-> report module by
avoiding any call back into TestRailClient. This is a safe no-op version
that preserves the function signatures.

TODO(PR4b): replace with real fetch -> prepare -> insert logic (direct DB).
"""


def fetch_testrail_testplans(*_args, **_kwargs):
    # Stub payload to keep CI green during cutover.
    return {"status": "skipped", "reason": "temporary stub during refactor: testplans"}


def prepare_testrail_testplans(raw):
    return raw


def insert_testrail_testplans(_df, *_args, **_kwargs):
    return True


def testrail_testplans_update(*args, **kwargs):
    raw = fetch_testrail_testplans(*args, **kwargs)
    df = prepare_testrail_testplans(raw)
    return insert_testrail_testplans(df, *args, **kwargs)
