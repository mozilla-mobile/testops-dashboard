"""Shim: re-export runs functional API during refactor."""

from .report_testrail_runs import fetch_testrail_runs  # noqa: F401
from .report_testrail_runs import prepare_testrail_runs  # noqa: F401
from .report_testrail_runs import insert_testrail_runs  # noqa: F401
from .report_testrail_runs import testrail_runs_update  # noqa: F401
