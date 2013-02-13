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
Example script for database initalization for GBI-Server.

Creates all necessary tables and inserts initial admin user.
"""

import bcrypt
from gbi_server import model
from gbi_server.application import create_app
from gbi_server.extensions import db

def init_db(app):
    db.app = app
    # db.drop_app() # uncomment to clear database
    db.create_all()

    admin = model.User(
        email='admin@example.org',
        active=True,
        verified=True,
        type=model.User.Type.ADMIN,
        passwort=bcrypt.hashpw('changeme', bcrypt.gensalt(10))
    )
    db.session.add(admin)
    db.session.commit()

if __name__ == '__main__':
    import config
    app = create_app(config.GBIConfig)
    init_db(app)