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

from geoalchemy import GeometryColumn, Polygon, GeometryDDL
from geoalchemy.postgis import PGComparator

from gbi_server.extensions import db

class WMTS(db.Model):
    __tablename__ = 'wmts'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String, nullable=False, unique=True)

    url = db.Column(db.String(256), nullable=False)
    username = db.Column(db.String(64))
    password = db.Column(db.String(64))
    title = db.Column(db.String)
    layer = db.Column(db.String(256), nullable=False)
    format = db.Column(db.String, nullable=False)
    srs = db.Column(db.String(64), default="EPSG:3857")
    matrix_set = db.Column(db.String(64), default='GoogleMapsCompatible')

    view_coverage = GeometryColumn(Polygon(), comparator=PGComparator)
    view_level_start = db.Column(db.Integer)
    view_level_end = db.Column(db.Integer)

    is_background_layer = db.Column(db.Boolean(), default=False)
    is_baselayer = db.Column(db.Boolean(), default=False)
    is_overlay = db.Column(db.Boolean(), default=True)
    is_transparent = db.Column(db.Boolean(), default=True)
    is_visible = db.Column(db.Boolean(), default=True)
    is_public = db.Column(db.Boolean(), default=False)

    @classmethod
    def by_id(cls, id):
        q = cls.query.filter(cls.id == id)
        return q.first_or_404()

    @classmethod
    def by_name(cls, name):
        q = cls.query.filter(cls.name == name)
        return q.first_or_404()

GeometryDDL(WMTS.__table__)