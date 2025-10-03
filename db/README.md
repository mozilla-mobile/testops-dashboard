# Database Configuration

The dashboard stores and processes its data using a Cloud SQL database. This directory contains helper scripts and configurations to interact with that database.

## BigQuery Integration

Once data is processed and stored in the Cloud SQL database, corresponding views are created in BigQuery. These views are then accessed by Looker for reporting and dashboarding.

## Local Database Access

You can use the scripts in this directory (`db`, `run-proxy`) to connect and interact with the Cloud SQL instance locally.

`db` depends on `mysql` v8.

### Setup Instructions

1. Open `Cloud SQL auth credentials / config` from 1Password's team vault. Save the following variables in 
   your shell's `rc` file (or a file that your `rc` file imports)
   * `CLOUD_SQL_DATABASE_USERNAME`
   * `CLOUD_SQL_DATABASE_PASSWORD`
   * `CLOUD_SQL_DATABASE_NAME` (use `preflight`)
   * `CLOUD_SQL_DATABASE_HOST`
   * `CLOUD_SQL_DATABASE_PORT`
2. Download `cloud-sql-proxy.json` from 1Password. Save the file somewhere under your home directory. Note the path.
3. Add `CLOUD_SQL_CREDENTIALS` to the `rc` file. The value the path of `cloud-sql-proxy.json`.
4. Download the dependencies: Google Cloud CLI and MySQL v8.
   ```
   brew install gcloud-cli
   brew install mysql@8.4
   ```
5. Log in to Google Cloud and configure the project name.
   ```
   gcloud auth login
   gcloud config set project [GCP project name]
   ```
6. Download the [Cloud SQL Auth Proxy](https://cloud.google.com/sql/docs/mysql/connect-auth-proxy#install) appropriate for your OS.
7. Place the binary in this `DB/` directory.
8. Open a terminal tab and run:
   ```
   ./run-proxy
   ```
9. In another terminal tab, run:
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
