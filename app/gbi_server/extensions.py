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

from flask.ext.mail import Mail
from flask.ext.sqlalchemy import SQLAlchemy
#from flask.ext.cache import Cache
from flask.ext.assets import Environment
from flask.ext.login import LoginManager

from gbi_server.authproxy import proxy

__all__ = ['mail', 'db', 'assets', 'tileproxy', 'couchdbproxy']

mail = Mail()
db = SQLAlchemy()
#cache = Cache()
assets = Environment()
login_manager = LoginManager()

couchdbproxy = proxy.CouchDBProxy()
tileproxy = proxy.TileProxy()
