# testops-dashboard

The Mozilla Mobile TestOps Dashboard is a data pump that collects data from diverse APIs and aggregates it in a Cloud SQL database for display in Looker graphs.

## Overview

This repository contains the backend which enables data collection and processing for visualization in Looker.

### High-Level Workflow

1. `__main__.py` script is invoked via GitHub workflow cron job to initiate data extraction.
2. Data is pulled from the source API.
3. The data is transformed into a payload (usually a pandas dataframe).
4. The payload is used to update a Cloud SQL database.

Once the data is in the database, it's accessed via BigQuery views for use in Looker dashboards.

## Usage

Run the following to retrieve and update mobile project test data:

```
Usage: __main__.py [-h] --project {fenix,focus-android,reference-browser,firefox-ios,focus-ios,ALL}
                   --report-type {test-case-coverage,test-run-counts,issue-regression} [--num-days NUM_DAYS]
```

**Arguments:**
- `--project`: Choose which project to pull data for.
- `--report-type`: Select type of report.
- `--num-days`: Optional number of historical days to include.

## Connected APIs

- Testrail
- Bugzilla
- Confluence
- Looker
- Bitrise.io
- GitHub (TBD)
- Taskcluster (TBD)

## Database

Data is stored in a Cloud SQL database and made available through BigQuery views.

> See [`DB/README.md`](db/README.md) for more details on working with the database, environment variables, and helper scripts.
