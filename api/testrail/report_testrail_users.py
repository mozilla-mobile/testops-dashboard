# report_testrail_users.py
import pandas as pd
from api.testrail.client import TestRailClient
from db import Database, ReportTestRailUsers

def fetch_testrail_users(*_args, **_kwargs):
    client = TestRailClient()
    projects = client.get_projects()
    print(f"[users] fetched {len(projects)} projects")
    all_users = []
    for proj in projects:
        pid = proj.get("id")
        users = client.get(f"get_users/{pid}")
        print(f"[users] project_id={pid}: fetched {len(users)} users")
        all_users.extend(users)
    return all_users

def prepare_testrail_users(raw):
    if not raw:
        return pd.DataFrame()
    df = pd.DataFrame(raw)
    if "email" in df.columns:
        df = df.drop_duplicates(subset=["email"])
    print(f"[users] prepare: df rows={len(df)} cols={list(df.columns)}")
    return df

def insert_testrail_users(df, *_args, **_kwargs):
    if df.empty:
        print("[users] insert: no data")
        return 0
    db = Database()
    session = db.session
    rows_inserted = 0
    for _, row in df.iterrows():
        rec = ReportTestRailUsers(
            name=row.get("name"),
            email=row.get("email"),
            status=row.get("is_active"),
            role=row.get("role_id"),
            created_at=row.get("created_on")
        )
        session.add(rec)
        rows_inserted += 1
    session.commit()
    print(f"[users] insert: committed {rows_inserted} rows")
    return rows_inserted

def testrail_users_update(*args, **kwargs):
    raw = fetch_testrail_users(*args, **kwargs)
    df = prepare_testrail_users(raw)
    inserted = insert_testrail_users(df, *args, **kwargs)
    print(f"[users] finished: inserted {inserted} rows")
    return inserted
