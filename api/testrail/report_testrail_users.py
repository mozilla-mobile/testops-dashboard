"""TestRail users report (real inserts + diagnostics, flake8-clean)."""
import os
from typing import Dict, List

import pandas as pd

from lib.testrail_conn import APIClient
from database import Database, ReportTestRailUsers


# ---- API helpers --------------------------------------------------------
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


def _get_projects(client: APIClient) -> List[dict]:
    resp = client.send_get('get_projects')
    projects = resp.get('projects') if isinstance(resp, dict) else resp
    if not isinstance(projects, list):
        projects = []
    print(f"[users] fetched {len(projects)} projects")
    return projects


def _get_users_for_project(client: APIClient, project_id: int) -> List[dict]:
    path = f'get_users/{project_id}'
    resp = client.send_get(path)
    users = resp.get('users') if isinstance(resp, dict) else resp
    if not isinstance(users, list):
        users = []
    print(f"[users] project_id={project_id}: fetched {len(users)} users")
    return users


# ---- Transform ----------------------------------------------------------
def _unique_by_email(users: List[dict]) -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    for u in users:
        email = u.get('email')
        if email:
            out[email] = u
    return out


def _users_to_dataframe(unique_email_map: Dict[str, dict]) -> pd.DataFrame:
    rows = []
    for user in unique_email_map.values():
        created_on = user.get('created_on')
        created_at = (
            pd.to_datetime(created_on, unit='s', errors='coerce')
            if created_on else None
        )
        rows.append({
            'name': user.get('name'),
            'email': user.get('email'),
            'status': 'active' if user.get('is_active') else 'inactive',
            'role': user.get('role'),
            'created_at': created_at,
        })
    df = pd.DataFrame(rows)
    print(
        f"[users] prepare: df rows={len(df.index)} "
        f"cols={len(df.columns)}"
    )
    return df


# ---- Insert (direct via SQLAlchemy model) ------------------------------
def _insert_users(db: Database, df: pd.DataFrame) -> int:
    if df.empty:
        print("[users] insert: 0 rows (empty DataFrame)")
        return 0

    session = db.session
    count = 0
    for _, row in df.iterrows():
        rec = ReportTestRailUsers(
            name=row.get('name'),
            email=row.get('email'),
            status=row.get('status'),
            role=row.get('role'),
            created_at=row.get('created_at'),
        )
        session.add(rec)
        count += 1
    session.commit()
    print(f"[users] insert: committed {count} rows")
    return count


# ---- Public orchestrator (original handler name) ------------------------
def testrail_users_update() -> None:
    """Fetch all TestRail users across projects and insert unique by email."""
    client = _api_client()
    db = Database()

    projects = _get_projects(client)

    all_users: List[dict] = []
    seen_ids = set()
    for proj in projects:
        pid = proj.get('id')
        if pid in seen_ids or pid is None:
            continue
        seen_ids.add(pid)
        try:
            users = _get_users_for_project(client, pid)
            all_users.extend(users)
        except Exception as exc:
            print(f"[users] error fetching users for project {pid}: {exc}")

    unique_map = _unique_by_email(all_users)
    df = _users_to_dataframe(unique_map)
    _insert_users(db, df)
    print("[users] finished")
