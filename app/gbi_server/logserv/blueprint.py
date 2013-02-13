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

import json

from flask import Blueprint, request, current_app, jsonify
from geoalchemy import WKTSpatialElement
from sqlalchemy.exc import SQLAlchemyError, DataError
from shapely.geometry import asShape

from gbi_server.lib.exceptions import json_abort
from gbi_server.model import User, Log
from gbi_server.extensions import db

logserv = Blueprint("logserv", __name__)

for code in [401, 403, 404, 405]:
    @logserv.errorhandler(code)
    def on_error(error):
        return error

@logserv.route("/log/<string:user_token>", methods=['POST'])
def log(user_token):
    if request.headers['content-type'] != 'application/json':
        json_abort(406, "request content-type not application/json")

    try:
        log_record = json.loads(request.data)
    except (TypeError, ValueError):
        json_abort(400, 'invalid JSON')

    try:
        user = User.by_authproxy_token(user_token)
        if not user:
            json_abort(401, 'unknown user token')

        if user.email != log_record['user']:
            json_abort(401, 'user token does not match user email')

        time = log_record['time']
        action = log_record['action']
    except KeyError, ex:
        json_abort(400, 'missing %s in log record' % ex)
    log = Log(user=user, time=time, action=action)

    if 'geometry' in log_record:
        if log_record['geometry']['type'] != 'MultiPolygon':
            json_abort(400, "geometry not a MultiPolygon")
        geom =  asShape(log_record['geometry'])
        log.geometry = WKTSpatialElement(geom.wkt, srid=3857, geometry_type='MULTIPOLYGON')

    log.source = log_record.get('source')
    log.layer = log_record.get('layer')
    log.zoom_level_start = log_record.get('zoom_level_start')
    log.zoom_level_end = log_record.get('zoom_level_end')
    log.refreshed = log_record.get('refreshed')
    log.mapping = log_record.get('mapping')
    log.format = log_record.get('format')
    log.srs = log_record.get('srs')

    try:
        db.session.add(log)
        db.session.commit()
    except DataError, ex:
        # invalid datatype, e.g. string instead of integer
        json_abort(400, ex.args[0])
    except SQLAlchemyError, ex:
        current_app.logger.error(ex)
        json_abort(500)

    return jsonify({'sucess': True})
