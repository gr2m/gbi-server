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

from flask import Flask, g, make_response, jsonify, render_template, url_for, request, flash, redirect
from flask.ext.babel import Babel, gettext as _
from flask.ext.login import current_user

import webassets.loaders
import webassets.env

from gbi_server import authproxy
from gbi_server import logserv
from gbi_server import signals
from gbi_server.config import DefaultConfig
from gbi_server.extensions import db, login_manager, mail, assets, tileproxy, couchdbproxy
from gbi_server.lib.helper import css_alert_category, request_for_static, add_auth_to_url
from gbi_server.model import User, DummyUser


def create_app(config=None):
    app = Flask(__name__)

    configure_app(app, config)

    from . import views
    app.register_blueprint(views.user)
    app.register_blueprint(views.admin)
    app.register_blueprint(views.maps)
    app.register_blueprint(views.proxy)
    app.register_blueprint(views.context)
    app.register_blueprint(views.boxes)
    app.register_blueprint(views.pages)

    app.register_blueprint(logserv.blueprint)

    configure_jinja(app)
    configure_authproxies(app)
    configure_extensions(app)
    configure_errorhandlers(app)
    configure_before_handlers(app)

    return app


def configure_jinja(app):
    app.jinja_env.globals.update(
        css_alert_category=css_alert_category,
        add_auth_to_url=add_auth_to_url,
        config=app.config,
    )


def configure_app(app, config=None):
    app.config.from_object(DefaultConfig())

    # load config local files from currend working dir
    if app.config.get('TESTING'):
        app.config.from_pyfile(os.path.abspath('gbi_local_test.conf'), silent=True)
    else:
        app.config.from_pyfile(os.path.abspath('gbi_local_develop.conf'), silent=True)

    if config is not None:
        app.config.from_object(config)


def configure_login(app):
    login_manager.setup_app(app)

    @login_manager.user_loader
    def load_user(userid):
        if request_for_static():
            return DummyUser(userid)
        if request.blueprint == 'authproxy':
            return DummyUser(userid)
        return User.by_id(userid)

def configure_assets(app):
    assets.app = app
    assets.init_app(app)
    if not app.debug:
        assets.cache = False

    try:
        loader = webassets.loaders.YAMLLoader(app.config.get('ASSETS_BUNDLES_CONF'))
        for name, bundle in loader.load_bundles().iteritems():
            assets.register(name, bundle)
    except webassets.env.RegisterError:
        # ignore errors when registering bundles multiple times
        if not app.testing:
            raise

def configure_i18n(app):
    babel = Babel(app)

    @babel.localeselector
    def get_locale():
        accept_languages = app.config.get('ACCEPT_LANGUAGES', ['en_GB'])
        return request.accept_languages.best_match(accept_languages,
            default=accept_languages[0])

def configure_authproxies(app):

    app.register_blueprint(authproxy.blueprint)

    coverages = authproxy.TileCoverages(
        cache_dir=app.config['AUTHPROXY_CACHE_DIR'],
        couchdb_url=app.config['COUCH_DB_URL'],
        geometry_layer=app.config['USER_WORKON_LAYER'],
    )
    tileproxy.tile_coverages = coverages

    # clear authproxy cache after features where updated
    def clear_coverage_cache(user, layer):
        coverages.clear(user.authproxy_token)
    signals.features_updated.connect(clear_coverage_cache, weak=False)

    dblimit = authproxy.CouchDBLimiter(
        cache_dir=app.config['AUTHPROXY_CACHE_DIR'],
    )
    couchdbproxy.dblimit = dblimit

    # clear authproxy cache before authtoken_changes
    def clear_cache(user, authproxy_token):
        coverages.clear(user.authproxy_token)
        dblimit.clear(user.authproxy_token)
    signals.authtoken_changes.connect(clear_cache, weak=False)


def configure_extensions(app):

    mail.init_app(app)
    db.init_app(app)
    #cache.init_app(app)

    # more complicated setups
    configure_login(app)
    configure_assets(app)
    configure_i18n(app)

def configure_errorhandlers(app):

    if app.testing:
        return

    @app.errorhandler(405)
    def not_allowed(error):
        if request.is_xhr:
            return jsonify(error=_('method not allowed'))
        return make_response(render_template("errors/405.html", error=error), 405)

    @app.errorhandler(404)
    def page_not_found(error):
        if request.is_xhr:
            return jsonify(error=_('page not found'))
        return make_response(render_template("errors/404.html", error=error), 404)

    @app.errorhandler(403)
    def forbidden(error):
        if request.is_xhr:
            return jsonify(error=_('not allowed'))
        return make_response(render_template("errors/403.html", error=error), 403)

    @app.errorhandler(500)
    def server_error(error):
        if request.is_xhr:
            return jsonify(error=_('an error has occurred'))
        return make_response(render_template("errors/500.html", error=error), 500)

    @app.errorhandler(401)
    def unauthorized(error):
        if request.is_xhr:
            return jsonify(error=_("Login required"))
        flash(_("Please login to see this page"), "error")
        return redirect(url_for("user.login", next=request.url))

def configure_before_handlers(app):

    @app.before_request
    def load_project_user():
        if request_for_static():
            return
        g.user = current_user