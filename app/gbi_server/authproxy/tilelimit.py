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

from shapely.geometry import box
from shapely import wkb, wkt

from mapproxy.grid import tile_grid

from gbi_server.extensions import db
from gbi_server.model import WMTS
from gbi_server.authproxy.limiter import LimiterCache, InvalidUserToken
from gbi_server.lib.geometry import optimize_geometry
from gbi_server.lib.couchdb import CouchDBBox
from gbi_server.config import SystemConfig

DEFAULT_GRID = tile_grid(3857, origin='nw')

class TileCoverages(LimiterCache):
    def __init__(self, cache_dir, couchdb_url, geometry_layer, tile_grid=DEFAULT_GRID):
        LimiterCache.__init__(self, cache_dir=cache_dir)
        self.cache_dir = cache_dir
        self.couchdb_url = couchdb_url
        self.geometry_layer = geometry_layer
        self.tile_grid = tile_grid

    def cache_file(self, user_token, name):
        return os.path.join(self.cache_path(user_token), name + '.wkb')

    def is_permitted(self, user_token, layer, tile_coord):
        geometry = self.load(user_token, layer)
        if not geometry:
            return False
        bbox = self.tile_grid.tile_bbox(tile_coord)
        return geometry.intersects(box(*bbox))

    def create(self, user_token, layer):
        from gbi_server.model import User

        user = User.by_authproxy_token(user_token)
        if not user:
            raise InvalidUserToken()

        result = db.session.query(WMTS, WMTS.view_coverage.transform(3857).wkt()).filter_by(name=layer).first()
        if result:
            wmts, view_coverage = result
            if wmts and wmts.is_public:
                return wkt.loads(view_coverage)

        if user.is_customer:
            couch_url = self.couchdb_url
            couchdb = CouchDBBox(couch_url, '%s_%s' % (SystemConfig.AREA_BOX_NAME, user.id))
            geom = couchdb.layer_extent(self.geometry_layer)
            return optimize_geometry(geom) if geom else None
        elif user.is_service_provider:
            couch_url = self.couchdb_url
            couchdb = CouchDBBox(couch_url, '%s_%s' % (SystemConfig.AREA_BOX_NAME, user.id))
            geom = couchdb.layer_extent()
            return optimize_geometry(geom) if geom else None
        elif user.is_admin or user.is_consultant:
            # permit access to everything
            return box(-20037508.3428, -20037508.3428, 20037508.3428, 20037508.3428)

        return None

    def serialize(self, data):
        if data:
            return data.wkb
        else:
            return ''

    def deserialize(self, data):
        if data:
            return wkb.loads(data)
        else:
            return None
