"""Shim: re-export coverage functions (with noqa) so handlers work."""

from .report_testrail_coverage import fetch_testrail_coverage  # noqa: F401
from .report_testrail_coverage import prepare_testrail_coverage  # noqa: F401
from .report_testrail_coverage import insert_testrail_coverage  # noqa: F401
from .report_testrail_coverage import testrail_coverage_update  # noqa: F401
