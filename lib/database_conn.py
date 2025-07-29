#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Base database connector module
https://github.com/swaathi/sqlalchemy"""

import os

from sqlalchemy import create_engine, engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


db_username = os.environ['CLOUD_SQL_DATABASE_USERNAME']
db_password = os.environ['CLOUD_SQL_DATABASE_PASSWORD']
db_name = os.environ['CLOUD_SQL_DATABASE_NAME']
db_host = os.environ.get('CLOUD_SQL_DATABASE_HOST', 'localhost')
db_port = os.environ.get('CLOUD_SQL_DATABASE_PORT', '3307')
db_config = {
    "pool_size": 5,
    "max_overflow": 2,
    "pool_timeout": 30,  # 30 seconds
    "pool_recycle": 1800,  # 30 minutes
}

Base = declarative_base()

pool = create_engine(
    engine.url.URL(
        drivername="mysql+pymysql",
        username=db_username,
        password=db_password,
        host=db_host,
        port=db_port,
        database=db_name,
        query={}
    ),
    **db_config
)

Session = sessionmaker(bind=pool)
Base.metadata.bind = pool
