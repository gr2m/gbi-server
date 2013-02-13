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

import yaml
import os

from mapproxy.grid import TileGrid
from mapproxy.srs import SRS

from shapely.wkt import loads

from flask.ext.babel import gettext as _

from gbi_server.extensions import db
from gbi_server.model import WMTS

class MapProxyConfiguration(object):
    def __init__(self, srs, target_dir):
        self.service_srs = srs
        self.sources = {}
        self.caches = {}
        self.layers = []
        self.yaml_file = os.path.join(target_dir, 'mapproxy.yaml')
        self.grid = TileGrid(SRS(3857))

    def _load_sources(self):
        public_wmts = db.session.query(WMTS, WMTS.view_coverage.transform(3857).wkt()).filter_by(is_public=True).group_by(WMTS).all()
        for wmts, view_coverage in public_wmts:
            self.sources['%s_source' % wmts.name] = {
                'type': 'tile',
                'url': wmts.url + wmts.layer + '/GoogleMapsCompatible-%(z)s-%(x)s-%(y)s/tile' ,
                'grid': 'GoogleMapsCompatible',
                'coverage': {
                    'srs': 'EPSG:3857',
                    'bbox': list(loads(view_coverage).bounds)
                }
            }
            self.caches['%s_cache' % wmts.name] = {
                'sources': ['%s_source' % wmts.name],
                'grids': [wmts.matrix_set],
                'disable_storage': True
            }
            self.layers.append({
                'name': '%s_layer' % wmts.name,
                'title': wmts.title,
                'sources': ['%s_cache' % wmts.name],
                'min_res': self.grid.resolution(wmts.view_level_start),
                # increase max_res to allow a bit of oversampling
                'max_res': self.grid.resolution(wmts.view_level_end) / 2,
            })

    def _write_mapproxy_yaml(self):
        grids = {
            'GoogleMapsCompatible': {
                'base': 'GLOBAL_MERCATOR',
                'srs': 'EPSG:3857',
                'num_levels': 19,
                'origin': 'nw'
            }
        }

        services = {
            'demo': None,
            'wms': {
                'srs': self.service_srs,
                'md': {'title': _('external_wms_title')}
            },
        }

        globals_ = {
            'image': {
                'paletted': True,
            },
            'cache': {
                'meta_size': [8, 8],
                'meta_buffer': 50,
            },
            'http': {
                'client_timeout': 120,
            },
        }

        config = {}

        if globals_: config['globals'] = globals_
        if grids: config['grids'] = grids
        if self.layers:
            config['layers'] = self.layers
            config['services'] = services
        if self.caches: config['caches'] = self.caches
        if self.sources: config['sources'] = self.sources


        # safe_dump does not output !!python/unicode, etc.
        mapproxy_yaml = yaml.safe_dump(config, default_flow_style=False)
        f = open(self.yaml_file, 'w')
        f.write(mapproxy_yaml)
        f.close()

def write_mapproxy_config(app):
    mpc = MapProxyConfiguration(app.config.get('MAPPROXY_SRS'), app.config.get('MAPPROXY_YAML_DIR'))
    mpc._load_sources()
    mpc._write_mapproxy_yaml()