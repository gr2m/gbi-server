# This file is part of the GBI project.
# Copyright (C) 2013 Omniscale GmbH & Co. KG <http://omniscale.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Example deployment file for GBI-Server.

Includes local configuration, logging configuration and
the setup of the GBI-Server ``application`` itself for the use
with gunicorn.
"""

class GBIConfig(object):
    SQLALCHEMY_ECHO = False

    SQLALCHEMY_DATABASE_URI = 'postgresql://gbi:gbi@localhost/gbi'

    TINYOWS_SCHEMA_DIR = "/opt/gbi/local/share/tinyows/schema/"
    TINYOWS_BIN = "/opt/gbi/bin/tinyows"

    TEMP_PG_HOST = "localhost"
    TEMP_PG_DB = "gbi_wfs"
    TEMP_PG_USER = "gbi"
    TEMP_PG_PASSWORD = "gbi"

    SESSION_COOKIE_NAME = 'gbi_server_session'
    SECRET_KEY = 'INSERT RANDOM STRING HERE!!!'

    COUCH_DB_ADMIN_USER = 'admin'
    COUCH_DB_ADMIN_PASSWORD = 'INSERT COUCHDB ADMIN PASSWORD HERE'

    MAIL_SERVER = "smtp.example.org"
    MAIL_USERNAME = 'gbi-admin@example.org'
    MAIL_PASSWORD = 'XXXXX'
    DEFAULT_MAIL_SENDER = "GBI Server <gbi-admin@example.org>"

    COUCH_DB_URL = "http://gbiserver.omniscale.net/couchdb"

    GBI_CLIENT_DOWNLOAD_URL = "http://download.omniscale.de/geobox/dist/setup-geobox-0.2.8.exe"


from gbi_server import create_app
application = create_app(config=GBIConfig)

# logging configuration

import logging
from logging import Formatter, handlers

formatter = Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s [@%(pathname)s:%(lineno)s]')
file_handler = handlers.RotatingFileHandler('/var/log/gbi/gbi-server.log', maxBytes=100000, backupCount=10)

file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
application.logger.addHandler(file_handler)

gbi_server_logger = logging.getLogger('gbi_server')
gbi_server_logger.setLevel(logging.INFO)
gbi_server_logger.addHandler(file_handler)

root_logger = logging.getLogger()
root_logger.setLevel(logging.WARN)
root_logger.addHandler(file_handler)
