# report_testrail_runs.py
"""Temporary no-recursion implementation for PR4 cutover.

Avoids calling TestRailClient to prevent infinite loops with adapters.

TODO(PR4b): replace with real fetch -> prepare -> insert logic (direct DB).
"""


def fetch_testrail_runs(*_args, **_kwargs):
    return {"status": "skipped", "reason": "temporary stub during refactor: runs"}


def prepare_testrail_runs(raw):
    return raw


def insert_testrail_runs(_df, *_args, **_kwargs):
    return True


def testrail_runs_update(*args, **kwargs):
    raw = fetch_testrail_runs(*args, **kwargs)
    df = prepare_testrail_runs(raw)
    return insert_testrail_runs(df, *args, **kwargs)
