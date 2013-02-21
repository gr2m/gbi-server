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

from sqlalchemy.orm import backref
from geoalchemy import GeometryColumn, MultiPolygon, GeometryDDL
from geoalchemy.postgis import PGComparator

from gbi_server.extensions import db

class Log(db.Model):
    __tablename__ = 'logs'

    id = db.Column(db.Integer, primary_key=True)

    time = db.Column(db.DateTime, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref=backref('logs', cascade="all,delete,delete-orphan"))

    action = db.Column(db.String(24), nullable=False)

    geometry = GeometryColumn(MultiPolygon(), comparator=PGComparator)
    format = db.Column(db.String)
    srs = db.Column(db.String)
    mapping = db.Column(db.String)
    source = db.Column(db.String)
    layer = db.Column(db.String)
    zoom_level_start = db.Column(db.Integer)
    zoom_level_end = db.Column(db.Integer)
    refreshed = db.Column(db.Boolean)


GeometryDDL(Log.__table__)