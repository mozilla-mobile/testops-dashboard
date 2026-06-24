#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Base database connector module
https://github.com/swaathi/sqlalchemy"""

import os
import re

from sqlalchemy import create_engine, engine, event, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# MySQL utf8 columns only support 3-byte UTF-8. Characters in the
# supplementary planes (emoji, rare CJK, etc.) are 4 bytes and cause
# DataError on insert. Strip them at the session level so every model
# is protected regardless of which API the data came from.
_FOUR_BYTE_UTF8 = re.compile('[\U00010000-\U0010ffff]', flags=re.UNICODE)


db_username = os.environ['CLOUD_SQL_DATABASE_USERNAME']
db_password = os.environ['CLOUD_SQL_DATABASE_PASSWORD']
db_name = os.environ['CLOUD_SQL_DATABASE_NAME']
db_host = os.environ.get('CLOUD_SQL_DATABASE_HOST', 'localhost')

# SQLAlchemy 2.0+ requires an integer port
db_port = os.environ.get('CLOUD_SQL_DATABASE_PORT', 3307)
db_port = int(db_port) if str(db_port).strip() else 3307

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


@event.listens_for(Session, 'before_flush')
def _sanitize_string_values(session, flush_context, instances):
    for obj in session.new | session.dirty:
        mapper = getattr(obj.__class__, '__mapper__', None)
        if mapper is None:
            continue
        for col in mapper.columns:
            if isinstance(col.type, String):
                val = getattr(obj, col.key, None)
                if isinstance(val, str) and _FOUR_BYTE_UTF8.search(val):
                    setattr(obj, col.key, _FOUR_BYTE_UTF8.sub('', val))
