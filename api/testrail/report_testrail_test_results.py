"""TestRail test results — production logic with diagnostics."""
from __future__ import annotations

import os
from typing import Iterable, List, Tuple

from lib.testrail_conn import APIClient
from database import (
    Database,
    Projects,
    ReportTestRailTestRuns,
    ReportTestRailTestResults,
)
from utils.datetime_utils import DatetimeUtils as dt


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


def _elapsed_to_seconds(elapsed) -> float:
    # Handles forms like "3m 10s", "5m", "42s" or numeric seconds
    try:
        if isinstance(elapsed, str):
            parts = elapsed.split()
            if len(parts) == 2 and parts[0].endswith("m") and parts[1].endswith("s"):
                return int(parts[0][:-1]) * 60 + int(parts[1][:-1])
            if elapsed.endswith("m"):
                return int(elapsed[:-1]) * 60
            if elapsed.endswith("s"):
                return int(elapsed[:-1])
        return float(str(elapsed).rstrip("s"))
    except Exception:
        return 0.0


def _insert_results(
    db: Database, db_run_id: int, results: List[dict], kind: str
) -> int:
    session = db.session
    count = 0
    for res in results:
        # Mirror monolith: only automated user id 976
        if res.get("created_by") != 976:
            continue

        created_on = dt.convert_epoch_to_datetime(res.get("created_on"))
        comp_val = res.get("completed_on")
        completed_on = (
            dt.convert_epoch_to_datetime(comp_val) if comp_val else None
        )

        rec = ReportTestRailTestResults(
            testrail_result_id=res.get("id"),
            run_id=db_run_id,
            test_id=res.get("test_id"),
            elapsed=float(_elapsed_to_seconds(res.get("elapsed"))),
            status_id=res.get("status_id"),
            testrail_created_on=created_on,
            testrail_completed_on=completed_on,
            type=kind,
        )
        session.add(rec)
        count += 1
    session.commit()
    print(
        f"[results] insert: committed {count} rows "
        f"for run_id={db_run_id}, type={kind}"
    )
    return count


def testrail_test_results_update(project: Iterable[str] | str) -> int:
    client = _api_client()
    db = Database()

    total = 0
    pairs = _project_id_pairs(db, project)
    for _projects_id, tr_project_id in pairs:

        plans = client.send_get(
            f"get_plans/{tr_project_id}",
            data_type="plans",
        ) or []


        beta_plan_id = None
        l10n_plan_id = None
        for p in sorted(plans, key=lambda x: x.get("id", 0), reverse=True):
            name = p.get("name", "")
            if beta_plan_id is None and "Beta" in name:
                beta_plan_id = p.get("id")
            if l10n_plan_id is None and "L10N" in name:
                l10n_plan_id = p.get("id")
            if beta_plan_id and l10n_plan_id:
                break

        for kind, pid in (("beta", beta_plan_id), ("l10n", l10n_plan_id)):
            if not pid:
                continue
            plan_payload = client.send_get(f"/get_plan/{pid}")
            entries = (plan_payload or {}).get("entries", [])
            for entry in entries:
                for run in entry.get("runs", []):
                    tr_run_id = run.get("id")
                    run_row = db.session.query(
                        ReportTestRailTestRuns
                    ).filter_by(
                        testrail_run_id=tr_run_id
                    ).first()
                    if not run_row:
                        continue
                    results_payload = client.send_get(
                        f"/get_results_for_run/{tr_run_id}"
                    )
                    results = results_payload or []
                    total += _insert_results(db, run_row.id, results, kind)

    print(f"[results] finished; total inserted={total}")
    return total
