"""Re-export hub for functional report entry points (compat shim).

TODO(PR5): remove after handlers import report modules directly.
"""
from .report_testrail_runs import testrail_runs_update  # noqa: F401
from .report_testrail_runs import fetch_testrail_runs  # noqa: F401
from .report_testrail_runs import prepare_testrail_runs  # noqa: F401
from .report_testrail_runs import insert_testrail_runs  # noqa: F401

from .report_testrail_run_counts import testrail_run_counts_update  # noqa: F401
from .report_testrail_run_counts import fetch_testrail_run_counts  # noqa: F401
from .report_testrail_run_counts import prepare_testrail_run_counts  # noqa: F401
from .report_testrail_run_counts import insert_testrail_run_counts  # noqa: F401

from .report_testrail_coverage import testrail_coverage_update  # noqa: F401
from .report_testrail_coverage import fetch_testrail_coverage  # noqa: F401
from .report_testrail_coverage import prepare_testrail_coverage  # noqa: F401
from .report_testrail_coverage import insert_testrail_coverage  # noqa: F401

from .report_testrail_users import testrail_users_update  # noqa: F401
from .report_testrail_users import fetch_testrail_users  # noqa: F401
from .report_testrail_users import prepare_testrail_users  # noqa: F401
from .report_testrail_users import insert_testrail_users  # noqa: F401

from .report_testrail_milestones import testrail_milestones_update  # noqa: F401
from .report_testrail_milestones import fetch_testrail_milestones  # noqa: F401
from .report_testrail_milestones import prepare_testrail_milestones  # noqa: F401
from .report_testrail_milestones import insert_testrail_milestones  # noqa: F401

from .report_testrail_testplans import testrail_testplans_update  # noqa: F401
from .report_testrail_testplans import fetch_testrail_testplans  # noqa: F401
from .report_testrail_testplans import prepare_testrail_testplans  # noqa: F401
from .report_testrail_testplans import insert_testrail_testplans  # noqa: F401
