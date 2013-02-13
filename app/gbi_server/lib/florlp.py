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
import json
import requests
import re
from zipfile import ZipFile
import fiona
import tempfile
import shutil


from urlparse import urlparse
from werkzeug.urls import url_decode
from cStringIO import StringIO

import logging
log = logging.getLogger(__name__)

# URLs for all "API" end-points
FLORLP_BASE_URL = "http://demo.flo.rlp.de/demo/"
FLORLP_LOGIN_URL = FLORLP_BASE_URL + 'frames/login.php'
FLORLP_MAPPHP_URL = FLORLP_BASE_URL + 'javascripts/map.php?gui_id=FLOrlp_DEMO&&mb_myBBOX='
FLORLP_SHAPE_SCHLAG_URL = FLORLP_BASE_URL + 'florlp/mod_wfsrequest_iframe_shape.php'
FLORLP_SHAPE_FLURSTUECK_URL = FLORLP_BASE_URL + 'florlp/mod_wfsrequest_iframe_flstk_shape.php'

# regular expressions to detect available years and bboxes
FLORLP_SCHLAG_BOX_RE = re.compile(r'mod_schlag_bbox\s=\s\'([0-9.,|]+)\'')
FLORLP_SCHLAG_YEAR_RE = re.compile(r'mod_schlag_jahr\s=\s\'([0-9,]+)\'')

class FLOrlpError(Exception):
    pass

class FLOrlpUnauthenticated(FLOrlpError):
    pass

def create_florlp_session(username, password):
    """
    Try to login into FLOrlp with username and password.

    Returns all session cookies required to authenticate further requests.
    Raises FLOrlpUnauthenticated if username/password did not match.
    """
    try:
        resp = requests.post(FLORLP_LOGIN_URL, data={'name': username, 'password': password})
    except requests.exceptions.RequestError, ex:
        raise FLOrlpError('unable to login: %s' % ex)

    # session as cookie
    if 'PHPSESSID' in resp.cookies:
        return {'PHPSESSID': resp.cookies['PHPSESSID']}

    # session in URL
    url = urlparse(resp.url)
    url_query = url_decode(url.query)
    if 'PHPSESSID' in url_query:
        return {'PHPSESSID': url_query['PHPSESSID']}

    raise FLOrlpUnauthenticated()

def authed_get(url, session, *args, **kw):
    """
    Request `url` with requests. Passes session cookies to the server.
    Raises ``FLOrlpUnauthenticated`` if the request was not accepted by the server.
    """
    kw['cookies'] = session
    resp = requests.get(url, *args, **kw)
    if resp.url != url:
        # got redirected to login because session cookie is invalid/expired
        raise FLOrlpUnauthenticated()
    return resp

def load_year_bboxes(session):
    resp = authed_get(FLORLP_MAPPHP_URL, session)
    return parse_schlag_bboxes(resp.content)

def parse_schlag_bboxes(content):
    """
    Parse bbox and years from javascript content like:
        mod_schlag_bbox = '3438800,5507400,3441425.31,5508822.31';mod_schlag_jahr = '2010';

    Returns a dictionary with a bbox for each year.
    """
    bboxs = FLORLP_SCHLAG_BOX_RE.search(content)
    years = FLORLP_SCHLAG_YEAR_RE.search(content)
    if not bboxs or not years:
        raise ValueError('bbox ando/or years not not found')

    bboxs = bboxs.group(1).split('|')
    years = years.group(1).split(',')

    if len(bboxs) != len(years):
        raise ValueError('number of bbox and years does not match')

    year_bbox = dict(zip(map(int, years), bboxs))

    return year_bbox

def download_schlag_shape(session, bbox, year, dest_dir):
    return _download_shape(FLORLP_SHAPE_SCHLAG_URL, session, bbox, year, dest_dir)

def download_flurstueck_shape(session, bbox, year, dest_dir):
    return _download_shape(FLORLP_SHAPE_FLURSTUECK_URL, session, bbox, year, dest_dir)

def _download_shape(url, session, bbox, year, dest_dir):
    params = {
        'REQUEST': 'GetFeature',
        'VERSION': '1.0.0',
        'SERVICE': 'WFS',
        'TYPENAME': 'schlag_box',
        'BBOX': bbox,
        'JAHR': str(year)
    }
    resp = authed_get(FLORLP_SHAPE_SCHLAG_URL, session, data=params)
    zipfile = ZipFile(StringIO(resp.content), mode='r')
    shapename = None
    for zipinfo in zipfile.infolist():
        zipfile.extract(zipinfo, dest_dir)
        if zipinfo.filename.lower().endswith('.shp'):
            shapename = os.path.basename(zipinfo.filename)

    return shapename

def shape_to_geojson(path, epsg_code=None):
    feature_collection = {
        'type': 'FeatureCollection',
        'features': [],
    }

    if epsg_code:
        feature_collection['crs'] = {
            'type': 'name',
            'properties': {
                'name': 'urn:ogc:def:crs:EPSG:6.3:%d' % epsg_code
            }
        }

    schema = None
    with fiona.collection(path) as source:
        schema = source.schema
        schema['properties'] = dict((k.lower(), v) for k, v in schema['properties'].items())
        for feature in source:
            feature['type'] = 'Feature'
            feature['properties'] = dict((k.lower(), v) for k, v in feature['properties'].items())
            feature_collection['features'].append(feature)

    return schema, feature_collection


def base_schema():
    return {
        "properties": {
            "nuar": "str",
            "slfl": "float",
            "slnr": "str",
            "jahr": "float",
            "styp": "str",
            "sung": "float",
            "bena": "str",
            "exte": "str",
            "suna": "float",
            "id": "float",
            "btnr": "str",
        }
    }


def latest_flursteuck_features(session):
    return _latest_features(session, download_function=download_flurstueck_shape)

def latest_schlag_features(session):
    return _latest_features(session, download_function=download_schlag_shape)

def _latest_features(session, download_function):
    year_bboxes = load_year_bboxes(session)
    latest_year = max(year_bboxes.keys())
    latest_bbox = year_bboxes[latest_year]
    try:
        dest_dir = tempfile.mkdtemp()
        shapefile_name = download_function(session, bbox=latest_bbox, year=latest_year, dest_dir=dest_dir)

        schema, feature_collection = shape_to_geojson(os.path.join(dest_dir, shapefile_name), epsg_code=31467)
        return schema, feature_collection
    finally:
        try:
            shutil.rmtree(dest_dir)
        except OSError, ex:
            log.warning('unable to remove temp dir:', ex)

if __name__ == '__main__':
    # print create_florlp_session('demo', 'demo')
    session = {'PHPSESSID': u'7kuci16jivqutou9vho76dg124'}

    print json.dumps(latest_schlag_features(session)[1], indent=4)