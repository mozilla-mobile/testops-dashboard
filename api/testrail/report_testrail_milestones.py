# report_testrail_milestones.py


def fetch_testrail_milestones(*_args, **_kwargs):
    return {"status": "skipped", "reason": "temporary stub during refactor: milestones"}


def prepare_testrail_milestones(raw):
    return raw


def insert_testrail_milestones(_df, *_args, **_kwargs):
    return True


def testrail_milestones_update(*args, **kwargs):
    raw = fetch_testrail_milestones(*args, **kwargs)
    df = prepare_testrail_milestones(raw)
    return insert_testrail_milestones(df, *args, **kwargs)
