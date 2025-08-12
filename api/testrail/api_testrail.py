"""Temporary re-exports during the TestRail refactor.

These imports are intentionally unused *in this module*; they expose the
functions under the historical api.testrail.api_testrail namespace while we
migrate handlers. Flake8 is silenced with # noqa: F401.
"""

from .report_testrail_runs import fetch_testrail_runs  # noqa: F401
from .report_testrail_runs import prepare_testrail_runs  # noqa: F401
from .report_testrail_runs import insert_testrail_runs  # noqa: F401
from .report_testrail_runs import testrail_runs_update  # noqa: F401

from .report_testrail_run_counts import (  # noqa: F401
    fetch_testrail_run_counts,
    prepare_testrail_run_counts,
    insert_testrail_run_counts,
    testrail_run_counts_update,
)

from .report_testrail_coverage import (  # noqa: F401
    fetch_testrail_coverage,
    prepare_testrail_coverage,
    insert_testrail_coverage,
    testrail_coverage_update,
)
