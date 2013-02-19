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

from itertools import chain
import bcrypt
import datetime

from geoalchemy import WKTSpatialElement
from shapely.geometry import asShape
from json import loads

from gbi_server import model
from gbi_server.config import SystemConfig
from gbi_server.lib.couchdb import CouchDBBox, init_user_boxes
from gbi_server.lib.florlp import (
    create_florlp_session, latest_schlag_features, remove_florlp_session,
)
from gbi_server.lib.transform import transform_geojson

def db_objects():
    users = [
        model.User(email='admin@example.org'),
        model.User(email='landwirt@example.org'),
        model.User(email='dienstleister@example.org'),
        model.User(email='berater@example.org'),
    ]

    users[0].active = True
    users[0].verified = True
    users[0].florlp_name = 'demo'
    users[0].type = 99
    users[0].password = bcrypt.hashpw('secure', bcrypt.gensalt(10))

    users[1].active = True
    users[1].verified = True
    users[1].florlp_name = 'demo'
    users[1].type = 0
    users[1].password = bcrypt.hashpw('secure', bcrypt.gensalt(10))
    users[1].authproxy_token = '12345'

    users[2].active = True
    users[2].verified = True
    users[2].florlp_name = 'demo'
    users[2].type = 1
    users[2].password = bcrypt.hashpw('secure', bcrypt.gensalt(10))

    users[3].active = True
    users[3].verified = True
    users[3].florlp_name = 'demo'
    users[3].type = 50
    users[3].password = bcrypt.hashpw('secure', bcrypt.gensalt(10))
    users[3].authproxy_token = '99999'

    wmts = [
        model.WMTS(
            name='omniscale_osm',
            url='http://igreendemo.omniscale.net/wmts/',
            title='Omniscale OSM',
            layer='omniscale_osm',
            format='png',
            srs='EPSG:3857',
            view_coverage=WKTSpatialElement(asShape(loads("""{
                "type":"Polygon",
                "coordinates":[[
                    [667916.9447596424, 5942074.072431108],
                    [1669792.3618991044, 5942074.072431108],
                    [1669792.3618991044, 7361866.113051186],
                    [667916.9447596424, 7361866.113051186],
                    [667916.9447596424, 5942074.072431108]
                ]]
                }""")).wkt, srid=3857, geometry_type='POLYGON'),
            view_level_start=7,
            view_level_end=18,
            is_background_layer=True,
            is_baselayer=True,
            is_overlay=False,
            is_transparent=False,
            is_visible=True),
    ]

    geom = WKTSpatialElement('MULTIPOLYGON(((8 49,8 50,9 50,9 49,8 49)))', srid=4326, geometry_type='MULTIPOLYGON')

    logs = [
        model.Log(user=users[1], time=datetime.datetime.now().isoformat(), action='vector_import', mapping='Schlaege Niedersachsen', source='example.shp', format='SHP'),
        model.Log(user=users[1], time=datetime.datetime.now().isoformat(), action='vector_export', mapping='Schlaege Niedersachsen', source='flaechen-box', format='SHP'),
        model.Log(user=users[1], time=datetime.datetime.now().isoformat(), action='raster_import', geometry=geom, source='http://localhost:5000/authproxy/12345/tiles', layer='omniscale_osm', zoom_level_start=8, zoom_level_end=14, refreshed=False),
        model.Log(user=users[1], time=datetime.datetime.now().isoformat(), action='raster_export', geometry=geom, format='JPEG', srs='EPSG:3857', layer='omniscale_osm', zoom_level_start=10, zoom_level_end=10, source='http://localhost:5000/authproxy/12345/tiles')
    ]

    return chain(users, wmts, logs)


def init_couchdb(config):
    user = model.User.by_email('landwirt@example.org')
    init_user_boxes(user, config.get('COUCH_DB_URL'))
    couch = CouchDBBox(config.get('COUCH_DB_URL'), '%s_%s' % (SystemConfig.AREA_BOX_NAME, user.id))
    layers = [config.get('USER_READONLY_LAYER'), config.get('USER_WORKON_LAYER')]
    florlp_session = create_florlp_session("demo", "demo")
    try:
        schema, feature_collection = latest_schlag_features(florlp_session)
    finally:
        remove_florlp_session(session)

    feature_collection = transform_geojson(from_srs=31467, to_srs=3857, geojson=feature_collection)
    for layer in layers:
        couch.clear_layer(layer)
        couch.store_layer_schema(layer, schema)
        couch.store_features(layer, feature_collection['features'])

    user = model.User.by_email('dienstleister@example.org')
    init_user_boxes(user, config.get('COUCH_DB_URL'))
