# report_testrail_coverage.py
"""
Temporary safe implementation to avoid recursion and missing DB methods during PR3A.

- fetch_testrail_coverage: returns a stub payload (no client calls)
- prepare_testrail_coverage: pass-through
- insert_testrail_coverage: no-op (returns True)
- testrail_coverage_update: orchestrator; wired so the legacy shim can call it

TODO(PR3B): Replace stubs with real logic (API fetch -> payload -> DB insert).
"""


def fetch_testrail_coverage(*_args, **_kwargs):
    # Stub payload: avoids calling TestRailClient or DatabaseTestRail.
    return {"status": "skipped", "reason": "temporary stub during refactor"}


def prepare_testrail_coverage(raw):
    # Pass-through for now; will become JSON->DataFrame later.
    return raw


def insert_testrail_coverage(_df, *_args, **_kwargs):
    # No-op insert; succeed to allow CI to proceed.
    return True


def testrail_coverage_update(*args, **kwargs):
    # Orchestrator: fetch -> prepare -> insert
    raw = fetch_testrail_coverage(*args, **kwargs)
    df = prepare_testrail_coverage(raw)
    return insert_testrail_coverage(df, *args, **kwargs)
