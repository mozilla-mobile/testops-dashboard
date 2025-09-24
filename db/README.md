# Database Configuration

The dashboard stores and processes its data using a Cloud SQL database. This directory contains helper scripts and configurations to interact with that database.

## BigQuery Integration

Once data is processed and stored in the Cloud SQL database, corresponding views are created in BigQuery. These views are then accessed by Looker for reporting and dashboarding.

## Local Database Access

You can use the scripts in this directory (`db`, `run-proxy`) to connect and interact with the Cloud SQL instance locally.

`db` depends on `mysql` v8.

### Required Environment Variables

Before starting, ensure you have set the following environment variables. The credentials and the cloud SQL database info are available from 1Password's team vault.

- `GCLOUD_AUTH`
- `CLOUD_SQL_CONNECTION_NAME`
- `CLOUD_SQL_DATABASE_PORT`
- `CLOUD_SQL_DATABASE_USERNAME`
- `CLOUD_SQL_DATABASE_PASSWORD`
- `CLOUD_SQL_DATABASE_NAME`: The name of the database to use currently. Example: `preflight`.
- `CLOUD_SQL_CREDENTIALS`: The location of cloud-sql-proxy.json file, which is available from 1Password.

### Setup Instructions

1. Download the dependencies: Google Cloud CLI and MySQL v8.
   ```
   brew install gcloud
   brew install mysql@8.4
   ```
2. Log in to Google Cloud and configure the project name.
   ```
   gcloud auth login
   gcloud config set project [GCP project name]
   ```
3. Download the [Cloud SQL Auth Proxy](https://cloud.google.com/sql/docs/mysql/connect-auth-proxy#install) appropriate for your OS.
4. Place the binary in this `DB/` directory.
5. Open a terminal tab and run:
   ```
   ./run-proxy
   ```
6. In another terminal tab, run:
   ```
   ./db -h
   ```

### `db` Script Options

```
$ ./db -h

==============================
Cloud SQL DB
==============================

Syntax: db [--help|--sql|--copy-db|--import|--dump|--dump-data|*]

options:
--sql           Run SQL command, then quit.   Ex: db -s 'SHOW DATABASES'
--copy-db       Copy database to new          Ex. db -c <source-db> <target-db>
--import        Import SQL data file          Ex. db -i <input.sql>
--dump          Dump SQL schema + data file   Ex. db -d <source-db>
--dump-data     Dump SQL data file            Ex. db -d <source-db>
--migrate-data  Migrate SQL data file         Ex. db -d <source-db> <target-db>
*               Open mysql CLI client         Ex. db
```
