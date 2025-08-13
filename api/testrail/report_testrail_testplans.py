"""TestRail test plans (and runs) — production logic with diagnostics."""
from __future__ import annotations

import os
from typing import Dict, Iterable, List, Tuple

from lib.testrail_conn import APIClient
from database import Database, Projects, ReportTestRailTestPlans
from utils.datetime_utils import DatetimeUtils as dt
from utils.payload_utils import PayloadUtils as pl
from .report_testrail_runs import testrail_runs_update


def _api_client() -> APIClient:
    host = os.environ.get("TESTRAIL_HOST")
    user = os.environ.get("TESTRAIL_USERNAME")
    pwd = os.environ.get("TESTRAIL_PASSWORD")
    if not host or not user or not pwd:
        raise RuntimeError("Missing TESTRAIL_* environment variables")
    client = APIClient(host)
    client.user = user
    client.password = pwd
    return client


def _project_id_pairs(
    db: Database, project: Iterable[str] | str
) -> List[Tuple[int, int]]:
    session = db.session
    if isinstance(project, list):
        q = session.query(Projects).filter(
            Projects.project_name_abbrev.in_(project)
        )
    else:
        q = session.query(Projects).filter(
            Projects.project_name_abbrev == project
        )
    rows = q.all()
    return [[p.id, p.testrail_project_id] for p in rows]


def _insert_test_plans(
    db: Database, project_id: int, totals_by_name: Dict[str, dict]
) -> int:
    session = db.session
    count = 0
    for total in totals_by_name.values():
        created_on = dt.convert_epoch_to_datetime(total.get("created_on"))
        comp_val = total.get("completed_on")
        completed_on = (
            dt.convert_epoch_to_datetime(comp_val) if comp_val else None
        )

        rec = ReportTestRailTestPlans(
            projects_id=project_id,
            testrail_plan_id=total.get("plan_id"),
            name=total.get("name"),
            test_case_passed_count=total.get("passed_count", 0),
            test_case_retest_count=total.get("retest_count", 0),
            test_case_failed_count=total.get("failed_count", 0),
            test_case_blocked_count=total.get("blocked_count", 0),
            test_case_total_count=total.get("total_count", 0),
            testrail_created_on=created_on,
            testrail_completed_on=completed_on,
        )
        session.add(rec)
        session.commit()
        total["id"] = rec.id  # used by runs updater
        count += 1
    print(f"[plans] insert: committed {count} rows for project_id={project_id}")
    return count


def testrail_test_plans_and_runs(
    project: Iterable[str] | str, num_days: str
) -> None:
    client = _api_client()
    db = Database()

    start_date = dt.start_date(num_days)
    after = (
        dt.convert_datetime_to_epoch(start_date) if start_date else None
    )

    pairs = _project_id_pairs(db, project)
    print(f"[plans] projects: {pairs}")

    for projects_id, tr_project_id in pairs:
        date_range = f"&created_after={after}" if after else ""
        payload = client.send_get(f"/get_plans/{tr_project_id}{date_range}")
        plans = (payload or {}).get("plans", [])

        full_plans = {
            plan["name"]: pl.extract_plan_info(plan)
            for plan in plans
            if "Automated testing" in plan.get("name", "")
        }

        print(
            f"[plans] {tr_project_id}: filtered plans="
            f"{len(full_plans)}"
        )

        _insert_test_plans(db, projects_id, full_plans)

        # Also update runs for these plans
        testrail_runs_update(num_days, full_plans)


def testrail_testplans_update(
    project: Iterable[str] | str, num_days: str
) -> None:
    return testrail_test_plans_and_runs(project, num_days)
