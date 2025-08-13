"""TestRail test case coverage — production logic with diagnostics."""
from __future__ import annotations

import os
from typing import Iterable, List, Tuple

import pandas as pd

from lib.testrail_conn import APIClient
from database import Database, Projects, ReportTestCaseCoverage
from utils.payload_utils import PayloadUtils as pl


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


def _coverage_payload(cases: list) -> pd.DataFrame:
    rows = []
    for case in cases:
        suit = case.get("suite_id")
        sub = (
            pl.extract_subsuite_id(case)
            if hasattr(pl, "extract_subsuite_id")
            else case.get("section_id")
        )
        status = (
            pl.extract_automation_status_id(case)
            if hasattr(pl, "extract_automation_status_id")
            else case.get("custom_automation_status_id")
        )
        cov = (
            pl.extract_coverage_id(case)
            if hasattr(pl, "extract_coverage_id")
            else case.get("custom_coverage_id")
        )
        rows.append(
            {"suit": suit, "sub": sub, "status": status, "cov": cov, "tally": 1}
        )
    df = pd.DataFrame(
        rows, columns=["suit", "sub", "status", "cov", "tally"]
    )
    df = (
        df.groupby(["suit", "sub", "status", "cov"])["tally"]
        .sum()
        .reset_index()
    )
    return df


def testrail_coverage_update(project: Iterable[str] | str) -> int:
    client = _api_client()
    db = Database()

    total_rows = 0
    pairs = _project_id_pairs(db, project)
    print(f"[coverage] projects: {pairs}")

    for projects_id, tr_project_id in pairs:
        payload = client.send_get(f"/get_cases/{tr_project_id}")
        cases = payload or []
        df = _coverage_payload(cases)
        print(
            f"[coverage] project_id={projects_id} grouped rows="
            f"{len(df.index)}"
        )

        session = db.session
        rows = 0
        for _, row in df.iterrows():
            rec = ReportTestCaseCoverage(
                projects_id=projects_id,
                testrail_test_suites_id=row["suit"],
                test_automation_status_id=row["status"],
                test_automation_coverage_id=row["cov"],
                test_sub_suites_id=row["sub"],
                test_count=row["tally"],
            )
            session.add(rec)
            rows += 1
        session.commit()
        print(
            f"[coverage] insert: committed {rows} rows for "
            f"projects_id={projects_id}"
        )
        total_rows += rows

    print(f"[coverage] finished; total inserted={total_rows}")
    return total_rows
