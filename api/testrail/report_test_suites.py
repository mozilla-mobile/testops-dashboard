# report_test_suites.py
# Thin wrapper that preserves signature by delegating to DatabaseTestRail.test_suites_update
from .service_db import DatabaseTestRail


def test_suites_update(*args, **kwargs):
    """Delegate to DatabaseTestRail.test_suites_update.
    Accepts the same parameters as the original method.
    """
    _svc = DatabaseTestRail()
    return _svc.test_suites_update(*args, **kwargs)
