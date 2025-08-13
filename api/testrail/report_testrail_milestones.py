"""TestRail milestones report (functional, flake8-clean, with diagnostics)."""
import os
from typing import Iterable, List, Tuple

import numpy as np
import pandas as pd

from lib.testrail_conn import APIClient
from database import Database, Projects, ReportTestRailMilestones
from utils.payload_utils import PayloadUtils as pl


def _api_client() -> APIClient:
    host = os.environ.get('TESTRAIL_HOST')
    user = os.environ.get('TESTRAIL_USERNAME')
    pwd = os.environ.get('TESTRAIL_PASSWORD')
    if not host or not user or not pwd:
        raise RuntimeError('Missing TESTRAIL_* environment variables')
    client = APIClient(host)
    client.user = user
    client.password = pwd
    return client


def _project_id_pairs(
    db: Database,
    project: Iterable[str] | str,
) -> List[Tuple[int, int]]:
    """Return [(projects.id, projects.testrail_project_id), ...]."""
    session = db.session
    if isinstance(project, list):
        q = session.query(Projects).filter(
            Projects.project_name_abbrev.in_(project)
        )
    else:
        q = session.query(Projects).filter(
            Projects.project_name_abbrev == project
        )
    results = q.all()
    return [[p.id, p.testrail_project_id] for p in results]


# ---- original-style names for fetch/prepare/insert ---------------------
def fetch_testrail_milestones(client: APIClient, testrail_project_id: int) -> list:
    path = f"get_milestones/{testrail_project_id}"
    payload = client.send_get(path)
    print(
        "[milestones] fetched {} items for tr_project_id={}".format(
            len(payload or []), testrail_project_id
        )
    )
    return payload


def prepare_testrail_milestones(payload: list) -> pd.DataFrame:
    if not payload:
        print("[milestones] prepare: empty payload -> empty DataFrame")
        return pd.DataFrame()

    df_all = pd.json_normalize(payload)
    print(
        "[milestones] prepare: normalized {} rows, {} columns".format(
            len(df_all.index), len(df_all.columns)
        )
    )

    # Keep only known columns if present and rename to DB schema names
    colmap = {
        'id': 'testrail_milestone_id',
        'name': 'name',
        'started_on': 'started_on',
        'is_completed': 'is_completed',
        'description': 'description',
        'completed_on': 'completed_on',
        'url': 'url',
    }
    existing = [k for k in colmap.keys() if k in df_all.columns]
    if not existing:
        print("[milestones] prepare: expected columns missing -> empty DataFrame")
        return pd.DataFrame()

    rename_map = {k: v for k, v in colmap.items() if k in existing}
    df = df_all[existing].rename(columns=rename_map)

    # Epoch seconds -> pandas datetime; replace NaN with None
    if 'started_on' in df.columns:
        df['started_on'] = pd.to_datetime(
            df['started_on'], unit='s', errors='coerce'
        )
        df['started_on'] = df['started_on'].replace({np.nan: None})
    if 'completed_on' in df.columns:
        df['completed_on'] = pd.to_datetime(
            df['completed_on'], unit='s', errors='coerce'
        )
        df['completed_on'] = df['completed_on'].replace({np.nan: None})

    # Derivations from description/name if available
    if 'description' in df.columns:
        df['testing_status'] = df['description'].apply(
            pl.extract_testing_status
        )
        df['testing_recommendation'] = df['description'].apply(
            pl.extract_testing_recommendation
        )

    if 'name' in df.columns:
        df['build_name'] = df['name'].apply(pl.extract_build_name)
        df['build_version'] = df['build_name'].apply(pl.extract_build_version)

    print(
        "[milestones] prepare: final df rows={}, cols={}".format(
            len(df.index), len(df.columns)
        )
    )
    return df


def insert_testrail_milestones(
    db: Database,
    projects_id: int,
    df: pd.DataFrame,
) -> int:
    if df.empty:
        print(
            "[milestones] insert: 0 rows for projects_id={}".format(
                projects_id
            )
        )
        return 0

    session = db.session
    count = 0
    for _, row in df.iterrows():
        rec = ReportTestRailMilestones(
            testrail_milestone_id=row.get('testrail_milestone_id'),
            projects_id=projects_id,
            name=row.get('name'),
            started_on=row.get('started_on'),
            is_completed=row.get('is_completed'),
            completed_on=row.get('completed_on'),
            description=row.get('description'),
            url=row.get('url'),
            testing_status=row.get('testing_status'),
            testing_recommendation=row.get('testing_recommendation'),
            build_name=row.get('build_name'),
            build_version=row.get('build_version'),
        )
        session.add(rec)
        count += 1
    session.commit()
    print(
        "[milestones] insert: committed {} rows for projects_id={}".format(
            count, projects_id
        )
    )
    return count


# ---- public orchestrator (original name kept) --------------------------
def testrail_milestones_update(project: Iterable[str] | str) -> None:
    """End-to-end update for milestones for a given project filter (or ALL)."""
    db = Database()
    client = _api_client()

    # Special-case 'ALL': expand to all project abbrevs from DB
    proj_filter = project
    if isinstance(project, str) and project.upper() == 'ALL':
        all_abbrevs = [
            p.project_name_abbrev for p in db.session.query(Projects).all()
        ]
        proj_filter = all_abbrevs

    total = 0
    pairs = _project_id_pairs(db, proj_filter)
    print("[milestones] projects: {}".format(pairs))
    for projects_id, testrail_project_id in pairs:
        payload = fetch_testrail_milestones(client, testrail_project_id)
        df = prepare_testrail_milestones(payload)
        total += insert_testrail_milestones(db, projects_id, df)
    print("[milestones] finished; total inserted={}".format(total))
