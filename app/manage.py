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

import os
import sys
import scriptine
from scriptine.shell import sh

from gbi_server import create_app
from gbi_server.model import fixtures
from gbi_server.extensions import db

def babel_init_lang_command(lang):
    "Initialize new language."
    sh('pybabel init -i gbi_server/translations/messages.pot -d gbi_server/translations -l %s' % (lang,))

def babel_refresh_command():
    "Extract messages and update translation files."

    # get directory of all extension that also use translations
    import wtforms
    wtforms_dir = os.path.dirname(wtforms.__file__)
    extensions = ' '.join([wtforms_dir])

    sh('pybabel extract -F babel.cfg -k lazy_gettext -k _l -o gbi_server/translations/messages.pot gbi_server gbi_server/model gbi_server/lib ' + extensions)
    sh('pybabel update -i gbi_server/translations/messages.pot -d gbi_server/translations')

def babel_compile_command():
    "Compile translations."
    sh('pybabel compile -d gbi_server/translations')


def init_db_command(app=None):
    if not app:
        app = create_app()
    db.app = app
    db.drop_all()
    db.create_all()

def fixtures_command():
    app = create_app()
    init_db_command(app)
    db.session.add_all(fixtures.db_objects())
    db.session.commit()
    with app.test_request_context():
        fixtures.init_couchdb(app.config)

def runserver_command(host='127.0.0.1', port=5000):
    app = create_app()

    # scriptine removed sub-command from argv,
    # but Flask reloader needs complete sys.argv
    sys.argv[1:1] = ['runserver']

    from werkzeug.serving import run_simple, WSGIRequestHandler
    # use custom request handler to force HTTP/1.1
    # needed for chunked encoding in CouchDB AuthProxy
    class HTTP11WSGIRequestHandler(WSGIRequestHandler):
        protocol_version = 'HTTP/1.1'
    run_simple(application=app, hostname=host, port=port, threaded=True,
        request_handler=HTTP11WSGIRequestHandler, use_reloader=True)

if __name__ == '__main__':
    scriptine.run()