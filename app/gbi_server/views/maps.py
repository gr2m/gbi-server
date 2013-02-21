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
import uuid

from flask import render_template, Blueprint, flash, redirect, url_for, current_app, abort, request, Response
import psycopg2

from flask.ext.babel import gettext as _
from flask.ext.login import login_required, current_user

from sqlalchemy.sql.expression import desc
from shapely.wkt import loads

from gbi_server.lib.couchdb import extend_schema_for_couchdb, CouchDBBox, CouchDBError
from gbi_server.lib.postgis import TempPGDB

from gbi_server.model import WMTS, WFSSession
from gbi_server.forms.wfs import WFSEditForm, WFSAddLayerForm

from gbi_server import signals
from gbi_server.extensions import db
from gbi_server.lib import tinyows, florlp
from gbi_server.util import ensure_dir
from gbi_server.config import SystemConfig

maps = Blueprint("maps", __name__, template_folder="../templates")

@maps.route('/maps/wmts', methods=['GET'])
@login_required
def wmts():
    couch = CouchDBBox(current_app.config.get('COUCH_DB_URL'), '%s_%s' % (SystemConfig.AREA_BOX_NAME, current_user.id))
    vector_layers = []
    couch_layers = couch.get_layer_names()
    for layer in couch_layers:
        features = [feature for feature in couch.iter_layer_features(layer) if isinstance(feature['geometry'], dict)]
        vector_layers.append({
            'name': layer,
            'features': features,
            'readonly': True if layer != current_app.config.get('USER_WORKON_LAYER') else False
        })
    wmts_layers = WMTS.query.all()
    return render_template('maps/map.html', wmts_layers=wmts_layers, vector_layers=vector_layers, user=current_user)

@maps.route('/maps/wfs', methods=['GET', 'POST'])
@login_required
def wfs_edit():
    user = current_user
    form = WFSEditForm()
    add_layer_form = WFSAddLayerForm()
    couch = CouchDBBox(current_app.config.get('COUCH_DB_URL'), '%s_%s' % (SystemConfig.AREA_BOX_NAME, user.id))

    if add_layer_form.validate_on_submit():
        layer = add_layer_form.data.get('new_layer')
        couch = CouchDBBox(current_app.config.get('COUCH_DB_URL'), '%s_%s' % (SystemConfig.AREA_BOX_NAME, user.id))
        schema = florlp.base_schema()
        if couch.layer_schema(layer):
            flash(_('Layer %(layer)s already exists', layer=layer), 'error')
        else:
            couch.store_layer_schema(layer, schema)
            flash(_('Layer %(layer)s created', layer=layer))

    form.layer.choices = [(layer, layer) for layer in couch.get_layer_names() if layer != current_app.config.get('USER_READONLY_LAYER')]

    if form.validate_on_submit():
        layer = form.data.get('layer', current_app.config.get('USER_WORKON_LAYER'))
        if not int(form.data['external_editor']):
            return redirect(url_for('.wfs_edit_layer', layer=layer))
        else:
            return redirect(url_for('.wfs_session', layer=layer))
    return render_template('maps/wfs_edit.html', form=form, add_layer_form=add_layer_form, not_removable_layer=current_app.config.get('USER_WORKON_LAYER'))

@maps.route('/maps/wfs/<layer>', methods=['GET'])
@login_required
def wfs_edit_layer(layer=None):
    user = current_user
    wfs_session = WFSSession.by_active_user_layer(layer, user)

    if wfs_session:
        flash(_('external edit in progress'))
        return redirect(url_for('.wfs_session', layer=layer))

    couch = CouchDBBox(current_app.config.get('COUCH_DB_URL'), '%s_%s' % (SystemConfig.AREA_BOX_NAME, user.id))

    try:
        wfs_layers, wfs_layer_token = create_wfs(user, [current_app.config.get('EXTERNAL_WFS_LAYER'), layer])
    except MissingSchemaError:
        flash(_('layer unknown or without schema'))
        abort(404)

    features = [feature for feature in couch.iter_layer_features(current_app.config.get('USER_READONLY_LAYER')) if isinstance(feature['geometry'], dict)]


    data_extent = couch.layer_extent(layer)

    if not data_extent:
        data_extent = couch.layer_extent(current_app.config.get('USER_READONLY_LAYER'))
    if not data_extent:
        result = db.session.query(WMTS, WMTS.view_coverage.transform(3857).wkt()).order_by(desc(WMTS.is_background_layer)).first()
        if result:
            data_extent = loads(result[1])

    return render_template(
        'maps/wfs.html',
        wfs=wfs_layers,
        layers=WMTS.query.all(),
        read_only_features=features,
        read_only_schema=couch.layer_schema(layer)['properties'],
        read_only_layer_name=current_app.config.get('USER_READONLY_LAYER'),
        editable_layer_name=layer,
        search_layer_name=current_app.config.get('EXTERNAL_WFS_NAME'),
        search_property=current_app.config.get('EXTERNAL_WFS_SEARCH_PROPERTY'),
        search_min_length=current_app.config.get('EXTERNAL_WFS_SEARCH_MIN_LENGTH'),
        search_prefix=current_app.config.get('EXTERNAL_WFS_SEARCH_PREFIX'),
        data_extent=data_extent.bounds if data_extent else None,
        user=current_user
    )

@maps.route('/maps/wfs/remove/<layer>', methods=['GET'])
@login_required
def wfs_remove_layer(layer=None):
    user = current_user
    if layer in [current_app.config.get('USER_READONLY_LAYER'), current_app.config.get('USER_WORKON_LAYER')]:
        flash(_('not allowed to remove this layer'))
        return redirect(url_for('.wfs_edit'))

    wfs_session = WFSSession.by_active_user_layer(layer, user)
    if wfs_session:
        flash(_('external edit in progress'))
        return redirect(url_for('.wfs_session', layer=layer))

    couch = CouchDBBox(current_app.config.get('COUCH_DB_URL'), '%s_%s' % (SystemConfig.AREA_BOX_NAME, user.id))
    try:
        couch.clear_layer(layer)
        flash(_('Layer %(layer)s removed', layer=layer))
    except CouchDBError:
        flash(_('Could not remove layer %(layer)s', layer=layer), 'error')

    return redirect(url_for('.wfs_edit'))

@maps.route('/maps/wfs/external/<layer>', methods=['GET'])
@login_required
def wfs_session(layer=None):
    user = current_user
    wfs_session = WFSSession.by_active_user_layer(layer, user)

    if not wfs_session:
        try:
            wfs_layers, wfs_layer_token = create_wfs(user, [layer])
        except MissingSchemaError:
            flash(_('layer unknown or without schema'))
            abort(404)
        wfs_session = WFSSession(user=user, layer=layer, url=url_for('.tinyows_wfs', token=wfs_layer_token, _external=True))
        db.session.add(wfs_session)
        db.session.commit()
    return render_template('maps/wfs_session.html', wfs_session=wfs_session)


@maps.route('/maps/wfs/cancel_changes/<layer>', methods=['GET'])
@login_required
def cancel_changes(layer=None):
    user = current_user

    wfs_session = WFSSession.by_active_user_layer(layer, user)
    wfs_session.active=False
    wfs_session.update()

    db.session.commit()

    flash(_('wfs changes discarded'))

    return redirect(url_for('.wfs_edit'))

@maps.route('/maps/wfs/write_back/<layer>')
@login_required
def write_back(layer=None, ajax=True):
    user = current_user

    connection = psycopg2.connect(
        database=current_app.config.get('TEMP_PG_DB'),
        host=current_app.config.get('TEMP_PG_HOST'),
        user=current_app.config.get('TEMP_PG_USER'),
        password=current_app.config.get('TEMP_PG_PASSWORD'),
        sslmode='allow',
    )

    couch = CouchDBBox(current_app.config.get('COUCH_DB_URL'), '%s_%s' % (SystemConfig.AREA_BOX_NAME, user.id))
    schema = couch.layer_schema(layer)
    extend_schema_for_couchdb(schema)
    tablename = 'tmp%s%s' % (user.id, layer)
    tmp_db = TempPGDB(connection=connection, tablename=tablename, schema=schema)
    couch.store_features(layer, tmp_db.load_features(), delete_missing=tmp_db.imported_feature_ids())
    connection.close()

    signals.features_updated.send(user, layer=layer)

    if ajax:
        return Response(response='success', status=200, headers=None, mimetype='application/json', content_type=None)

@maps.route('/maps/wfs/save_changes/<layer>')
@login_required
def save_changes(layer=None):
    user = current_user
    write_back(layer, False)
    wfs_session = WFSSession.query.filter_by(user=user, active=True, layer=layer).first()
    if wfs_session:
        wfs_session.active = False
        wfs_session.update()
        db.session.commit()
    flash(_('wfs changes saved'))
    return redirect(url_for('.wfs_edit'))

class MissingSchemaError(Exception):
    pass

def create_wfs(user=None, layers=None):
    connection = psycopg2.connect(
        database=current_app.config.get('TEMP_PG_DB'),
        host=current_app.config.get('TEMP_PG_HOST'),
        user=current_app.config.get('TEMP_PG_USER'),
        password=current_app.config.get('TEMP_PG_PASSWORD'),
        sslmode='allow',
    )
    couch = CouchDBBox(current_app.config.get('COUCH_DB_URL'), '%s_%s' % (SystemConfig.AREA_BOX_NAME, user.id))

    wfs_layer_token = uuid.uuid4().hex

    wfs = []
    tinyows_layers = []

    for id, layer in enumerate(layers):
        wfs_layer = {
            'id': id,
            'name': layer,
            'url': url_for('.tinyows_wfs', token=wfs_layer_token, _external=True) + '?',
            'srs': 'EPSG:3857',
            'geometry_field': 'geometry',
            'wfs_version': '1.1.0',
            'feature_ns': current_app.config.get('TINYOWS_NS_URI'),
            'typename': current_app.config.get('TINYOWS_NS_PREFIX'),
            'writable': False,
            'display_in_layerswitcher': True,
        }
        if layer == current_app.config.get('EXTERNAL_WFS_LAYER'):
            wfs_layer['name'] = current_app.config.get('EXTERNAL_WFS_NAME')
            wfs_layer['url'] = current_app.config.get('EXTERNAL_WFS_URL')
            wfs_layer['layer'] = current_app.config.get('EXTERNAL_WFS_LAYER')
            wfs_layer['srs'] = current_app.config.get('EXTERNAL_WFS_SRS')
            wfs_layer['geometry_field'] = current_app.config.get('EXTERNAL_WFS_GEOMETRY')
            wfs_layer['feature_ns'] = current_app.config.get('EXTERNAL_WFS_NS_URI')
            wfs_layer['typename'] = current_app.config.get('EXTERNAL_WFS_NS_PREFIX')
            wfs_layer['max_features'] = current_app.config.get('EXTERNAL_WFS_MAX_FEATURES')
            wfs_layer['display_in_layerswitcher'] = False
        else:
            schema = couch.layer_schema(layer)
            if not schema or 'properties' not in schema:
                raise MissingSchemaError('no schema found for layer %s' % layer)
            extend_schema_for_couchdb(schema)
            # tinyows layername must not contain underscores
            tablename = 'tmp%s%s' % (user.id, layer)
            tmp_db = TempPGDB(connection=connection, tablename=tablename, schema=schema)
            tmp_db.create_table()
            tmp_db.insert_features(couch.iter_layer_features(layer))
            # TODO remember created table in new model, store wfs_layer_token
            # and remove old tinyows configs on update
            wfs_layer['layer'] = tablename
            wfs_layer['writable'] = current_app.config.get('USER_READONLY_LAYER') != layer
            tinyows_layers.append({
                'name': tablename,
                'title': wfs_layer['name'],
                'writable': '1' if wfs_layer['writable'] else '0',
            })
        wfs.append(wfs_layer)
    connection.commit()
    connection.close()

    ensure_dir(current_app.config.get('TINYOWS_TMP_CONFIG_DIR'))

    tinyows_config = os.path.join(
        current_app.config.get('TINYOWS_TMP_CONFIG_DIR'),
        wfs_layer_token + '.xml')

    tinyows.build_config(current_app, tinyows_layers, wfs_layer_token, tinyows_config)

    return wfs, wfs_layer_token

@maps.route('/maps/wfs/<token>/service', methods=['GET', 'POST'])
def tinyows_wfs(token):
    tinyows_config = os.path.join(
        current_app.config.get('TINYOWS_TMP_CONFIG_DIR'),
        token + '.xml')
    tows = tinyows.TinyOWSCGI(
        script=current_app.config.get('TINYOWS_BIN'),
        tinyows_config=tinyows_config,
        content_type=request.content_type)
    try:
        result = tows.open(url='/?' + request.query_string, data=request.data)
        return Response(result.read(), status=result.status_code,
            content_type=result.headers.get('Content-type', 'text/xml'))
    except tinyows.CGIError, ex:
        current_app.logger.error(ex)
        abort(502)
