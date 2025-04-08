testops-dashboard
==================
The Mozilla Mobile TestOps Dashboard is data pump that collects data from diverse APIs (datasources) and aggregates it in a Cloud SQL database for display in Looker graphs. 


Overview
---------------
The following is an overview of the test-dashboard. 

The code is in this repository provides the backend which enables us to publish graphs in Looker.  

It is constructed to function as follows
1. ```__main__.py``` script invoked via github workflow cron to initiate a data extraction
2. Data 'pumped' from source API indicated
3. Data temporarily packaged into a payload
4. Payload used to update Cloud SQL database

Once the updated data is available in the database, it is made available to our Looker graphs via BigQuery views.


Description
---------------


1. Main menu

    ```
    Usage: __main__.py [-h] --project {fenix,focus-android,reference-browser,firefox-ios,focus-ios,ALL}
                       --report-type {test-case-coverage,test-run-counts,issue-regression} [--num-days NUM_DAYS]

    Retrieve and update mobile project test data

    optional arguments:
      -h, --help            show this help message and exit
      --project {fenix,focus-android,reference-browser,firefox-ios,focus-ios,ALL}
                        Indicate project
      --report-type {test-case-coverage,test-run-counts,issue-regression}
                        Indicate report type
      --num-days NUM_DAYS   Indicate number of historic days of records to include
    ```


2. API Requests

    Queries data from a given data source (see: Source APIs below).

3. Data Payload

    Repackage desired data points (usually JSON) from source API into a pandas dataframe.
    This allows for easy updates to database.

4. Database Update

    Uses SQLAlchemy to update database with pandas dataframe data payload. 
    Data reports are generated using github workflows set to specified cron
    periods:

    * Daily
    * Weekly
    * Fortnightly
    * Monthly


5. Data Retrieval

     Database is connected to a BigQuery instance.
     Corresponding views are created in BigQuery that can be directly accessed for
     generating report in Looker.

    

Connected APIs
---------------

* Testrail
* Bugzilla
* Confluence
* Looker
* Bitrise.io
* Github - TBD
* Taskcluster - TBD


Database
---------------

Data is aggregated / cached in a Cloud SQL database.  Data queries are constructed using BigQuery views.

Interactive sessions with Cloud SQL can be conducted using the following helper scripts in the db/ directory.
* db
* run-proxy

This will require setting the following 4 environment variables.
- `GCLOUD_AUTH`
- `CLOUD_SQL_CONNECTION_NAME`
- `CLOUD_SQL_DATABASE_PORT`
- `CLOUD_SQL_DATABASE_USERNAME`
- `CLOUD_SQL_DATABASE_PASSWORD`
- `CLOUD_SQL_DATABASE_NAME`

You will then need to download the Cloud SQL Auth Proxy appropriate for your OS into the db/ directory:
https://cloud.google.com/sql/docs/mysql/connect-auth-proxy#install

Open a terminal tab and run `run-proxy`
Open another terminal tab and run `./db -h`to view the options menu of the helper script:

<pre>

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

</pre>
