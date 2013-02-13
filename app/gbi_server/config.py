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

# -:- encoding: utf8 -:-
from os import path as p

class DefaultConfig(object):
    """
    Default configuration
    """

    TESTING = False

    DEBUG = True

    SESSION_COOKIE_NAME = 'gbi_server_session'

    # allow access to admin URLs without authentication
    # (e.g. for testing with curl)
    ADMIN_PARTY = False

    # change this in your production settings !!!

    SECRET_KEY = "verysecret"

    # keys for localhost. Change as appropriate.

    SQLALCHEMY_DATABASE_URI = 'postgresql://igreen:igreen@127.0.0.1:5432/igreen'

    SQLALCHEMY_ECHO = False

    ACCEPT_LANGUAGES = ['de']

    ASSETS_DEBUG = True
    ASSETS_BUNDLES_CONF = p.join(p.dirname(__file__), 'asset_bundles.yaml')

    LOG_DIR = p.abspath(p.join(p.dirname(__file__), '../../var/log'))
    DEBUG_LOG = 'debug.log'
    ERROR_LOG = 'error.log'

    CACHE_TYPE = "simple"
    CACHE_DEFAULT_TIMEOUT = 300

    BCRYPT_LOG_ROUNDS = 10

    MAIL_SERVER = "smtp.example.org"
    MAIL_USERNAME = 'gbi_server@example.org'
    MAIL_PASSWORD = 'XXXXX'
    MAIL_DEBUG = DEBUG
    DEFAULT_MAIL_SENDER = "GBI Server <gbi_server@example.org>"

    TINYOWS_NAME = "TinyOWS Server"
    TINYOWS_TITLE = "TinyOWS Server - Demo Service"
    TINYOWS_BIN = "/usr/local/bin/tinyows"
    TINYOWS_SCHEMA_DIR = "/usr/local/share/tinyows/schema/"
    TINYOWS_LOG_FILE = "/tmp/tinyows.log"
    TINYOWS_LOG_LEVEL = "7"
    TINYOWS_NS_PREFIX = "tows"
    TINYOWS_NS_URI = "http://www.tinyows.org/"

    TINYOWS_TMP_CONFIG_DIR = "/tmp/tinyows"
    TEMP_PG_HOST = "127.0.0.1"
    TEMP_PG_DB = "wfs_tmp"
    TEMP_PG_USER = "igreen"
    TEMP_PG_PASSWORD = "igreen"
    TEMP_PG_PORT = "5432"

    USER_READONLY_LAYER = "florlp"
    USER_WORKON_LAYER = "baselayer"

    COUCH_DB_URL = "http://127.0.0.1:5984"
    # user name and password for db admin that is allowed to
    # create new user boxes
    COUCH_DB_ADMIN_USER = 'gbi'
    COUCH_DB_ADMIN_PASSWORD = 'secure'

    AUTHPROXY_CACHE_DIR = "/tmp/authproxy"

    EXTERNAL_WFS_HOST = "www.ks.rlp.de"
    EXTERNAL_WFS_URL = "https://www.ks.rlp.de/fc_wfs/wfs.php?user=XXXXX&password=XXXXX&"
    EXTERNAL_WFS_GEOMETRY = "geom"
    EXTERNAL_WFS_LAYER = 'kataster'
    EXTERNAL_WFS_SRS = 'EPSG:3857'
    EXTERNAL_WFS_NAME = 'GeoServer Web Feature Service'
    EXTERNAL_WFS_NS_PREFIX = "MWKEL"
    EXTERNAL_WFS_NS_URI = ""
    EXTERNAL_WFS_SEARCH_PROPERTY = "flurstueckskennzeichen"
    EXTERNAL_WFS_SEARCH_MIN_LENGTH = 7
    EXTERNAL_WFS_SEARCH_PREFIX = '07'
    EXTERNAL_WFS_MAX_FEATURES = 500

    MAPPROXY_SRS = ['EPSG:25832']
    MAPPROXY_YAML_DIR = "/tmp/"

    GBI_CLIENT_DOWNLOAD_URL = "http://download.omniscale.de/geobox/dist/setup-geobox-0.2.7.exe"

    STATIC_PAGES_DIR = p.join(p.dirname(__file__), '..', 'pages')

class SystemConfig(object):
    # name of the databases on the server
    # will be suffixed by the user id
    AREA_BOX_NAME = 'gbi_flaechenbox'
    CUSTOMER_BOX_NAME = 'gbi_customerbox'
    CONSULTANT_BOX_NAME = 'gbi_consultantbox'

    # name of the databases on the client
    AREA_BOX_NAME_LOCAL = 'flaechen-box'
    CUSTOMER_BOX_NAME_LOCAL = 'beratungs-inbox'
    CONSULTANT_BOX_NAME_LOCAL = 'beratungs-outbox'
