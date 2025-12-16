import inspect
import pandas as pd

from database import (
    Database,
    ReportJiraQANeeded,
)

from api.jira.client import Jira


_DB = None
_JIRA = None


def _db() -> Database():
    global _DB
    if _DB is None:
        _DB = Database()
    return _DB


def _jira() -> Jira():
    global _JIRA
    if _JIRA is None:
        _JIRA = Jira()
    return _JIRA

# ===================================================================
# ORCHESTRATOR (BATCH)
# ===================================================================


def jira_qa_needed():
    jira = _jira()

    payload = jira.filter_qa_needed()

    df = pd.json_normalize(payload, sep='_')
    total_rows = len(df)

    # Ensure 'fields_labels' exists
    if 'fields_labels' not in df.columns:
        df['fields_labels'] = [[] for _ in range(len(df))]

    # Join list of labels into a single string
    df['fields_labels'] = df['fields_labels'].apply(
        lambda x: ','.join(x) if isinstance(x, list)
        else (x if pd.notnull(x) else '')
    )

    # Calculate Nightly Verified label
    verified_nightly_count = df['fields_labels'].str.contains(
        'verified', case=False, na=False
    ).sum()
    not_verified_count = total_rows - verified_nightly_count

    data_frame = [total_rows, not_verified_count, verified_nightly_count]
    report_jira_qa_needed_insert(data_frame)

# ===================================================================
# DB INSERT
# ===================================================================


def report_jira_qa_needed_insert(payload):
    print("--------------------------------------")
    print("Running: report_jira_qa_needed")
    print(inspect.currentframe().f_code.co_name)
    print("--------------------------------------")

    db = _db()
    report = ReportJiraQANeeded(jira_total_qa_needed=payload[0],
                                jira_qa_needed_not_verified=payload[1],
                                jira_qa_needed_verified_nightly=payload[2])

    db.session.add(report)
    db.session.commit()
