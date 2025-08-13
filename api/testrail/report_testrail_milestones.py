# report_testrail_milestones.py

from .service_client import TestRailClient
from .service_db import DatabaseTestRail

def fetch_testrail_milestones(*args, **kwargs):
    client = TestRailClient()
    return client.get_milestones(*args, **kwargs)

def prepare_testrail_milestones(raw):
    # Transform raw API data into DB-friendly format
    return [
        {
            "id": m["id"],
            "name": m["name"],
            "is_completed": m.get("is_completed", False),
            "due_on": m.get("due_on"),
        }
        for m in raw
    ]

def insert_testrail_milestones(data, *args, **kwargs):
    db = DatabaseTestRail()
    return db.insert_milestones(data, *args, **kwargs)

def testrail_milestones_update(*args, **kwargs):
    raw = fetch_testrail_milestones(*args, **kwargs)
    data = prepare_testrail_milestones(raw)
    return insert_testrail_milestones(data, *args, **kwargs)
