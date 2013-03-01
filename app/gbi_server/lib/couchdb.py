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

import requests
import json
import urllib
import datetime

from flask import current_app
import shapely.geometry
from gbi_server.config import SystemConfig

class CouchDBError(Exception):
    pass


def geojson_feature_to_geocouch(feature):
    """
    Convert GeoJSON to GeoCouch feature:
    {'type': 'Feature', 'properties': {'foo': 'bar'}, 'geometry': {...}}
    -> {'foo': 'bar', 'geometry': {...}}

    This function reuses and modifies the `feature['properties']` dictionary.
    """
    result = feature['properties']
    result['geometry'] = feature['geometry']
    return result

def geocouch_feature_to_geojson(feature):
    """
    Convert GeoCouch to GeoJON feature:
    {'foo': 'bar', 'geometry': {...}}
    ->
    {'type': 'Feature', 'properties': {'foo': 'bar'}, 'geometry': {...}}

    This function reuses and modifies the `feature` dictionary.
    """
    geometry = feature.pop('geometry')
    feature.pop('layer')
    result = {
        'type': 'Feature',
        'geometry': geometry,
        'properties': feature,
    }
    return result


class CouchDB(object):
    def __init__(self, url, dbname, auth=None):
        self.url = url
        self.dbname = dbname
        self.couchdb_url = url + '/' + dbname
        self.session = requests.Session()
        if auth:
            self.session.auth = auth
        else:
            self.session.auth = (
                current_app.config['COUCH_DB_ADMIN_USER'],
                current_app.config['COUCH_DB_ADMIN_PASSWORD'],
            )

    def drop(self):
        self.session.delete(self.couchdb_url)

    def create(self):
        self.session.put(self.couchdb_url)

    def clear(self):
        self.drop()
        self.create()

    def delete(self, doc_id, rev):
        doc_url = self.couchdb_url + '/' + doc_id
        resp = self.session.delete(doc_url, params={'rev': rev})
        if resp.status_code not in (200, 404):
            raise CouchDBError(
                'got unexpected resp (%d) from CouchDB for %s: %s'
                % (resp.status_code, doc_url, resp.content)
            )

    def get(self, doc_id):
        doc_url = self.couchdb_url + '/' + doc_id
        resp = self.session.get(doc_url)
        if resp.ok:
            return resp.json()
        elif resp.status_code != 404:
            raise CouchDBError(
                'got unexpected resp (%d) from CouchDB for %s: %s'
                % (resp.status_code, doc_url, resp.content)
            )

    def put(self, doc_id, doc):
        doc_url = self.couchdb_url + '/' + doc_id
        resp = self.session.put(doc_url,
            headers={'Accept': 'application/json'},
            data=json.dumps(doc),
        )
        if resp.status_code != 201:
            raise CouchDBError(
                'got unexpected resp (%d) from CouchDB for %s: %s'
                % (resp.status_code, doc_url, resp.content)
            )

    def put_bulk(self, docs):
        doc = {'docs': docs}
        data = json.dumps(doc)
        resp = self.session.post(self.couchdb_url + '/_bulk_docs',
            data=data, headers={'Content-type': 'application/json'}
        )
        if resp.status_code != 201:
            raise CouchDBError(
                'got unexpected resp (%d) from CouchDB for %s: %s'
                % (resp.status_code, self.couchdb_url + '/_bulk_docs', resp.content)
            )

        errors = {}
        for row in resp.json():
            if 'error' in row:
                errors[row['id']] = row['error']
        return errors

    def update_user(self, user_id, password):
        user_doc = {
            'name': user_id,
            'password': password,
            'type': 'user',
            'roles': [],
        }
        resp = self.session.get(self.url + '/_users/org.couchdb.user:' + user_id)
        if resp.status_code == 200:
            user_doc['_rev'] = resp.json()['_rev']
        resp = self.session.put(self.url + '/_users/org.couchdb.user:' + user_id,
            data=json.dumps(user_doc),
            headers={'Content-type': 'application/json'},
        )
        if resp.status_code != 201:
            raise CouchDBError(
                'got unexpected resp (%d) from CouchDB for %s: %s'
                % (resp.status_code, self.couchdb_url + '/_bulk_docs', resp.content)
            )

    def update_auth_doc(self, user, writable=True, read_roles=[], write_roles=[]):
        auth_doc = {
          "_id":"_design/auth",
          "language": "javascript",
        }

        validate_func = """function(new_doc, old_doc, userCtx) {\n"""
        if writable:
            validate_func += """    if (userCtx.name == '%s') { return; }\n""" % user
        for role in write_roles:
            validate_func += """    if (userCtx.roles.indexOf('%s') >= 0) { return; }\n""" % role

        # allways permit _admin (for replication)
        validate_func += """    if (userCtx.roles.indexOf('_admin') >= 0) { return; }"""
        validate_func += """    throw({forbidden: "User " + userCtx.name + " not authorized"});\n}"""

        auth_doc['validate_doc_update'] = validate_func

        existing_auth_doc = self.get('_design/auth')
        if existing_auth_doc:
            auth_doc['_rev'] = existing_auth_doc['_rev']
        self.put('_design/auth', auth_doc)


        # PUT /_security returns 200 not 201, so we don't use
        # self.put but self.session.put
        resp = self.session.put(self.couchdb_url + '/_security',
            data=json.dumps({
                'members': {
                    'names': [user],
                    'roles': read_roles + ['_admin'],
                }
            }),
            headers=(('Content-type', 'application/json'),),
        )

        if resp.status_code != 200:
            raise CouchDBError(
                'got unexpected resp (%d) from CouchDB for %s: %s'
                % (resp.status_code, self.couchdb_url + '/_security', resp.content)
            )

class CouchDBBox(CouchDB):
    def layer_schema(self, layer):
        resp = self.session.get(self.couchdb_url + '/schema_%s' % layer)
        if resp.ok:
            return resp.json()

    def layer_url(self, layer, include_docs=False):
        url = self.couchdb_url + '/_design/layers/_view/all?key=' + urllib.quote('"%s"' % layer.encode('utf8'))
        if include_docs:
            url += '&include_docs=true'
        return url

    def update_layer_view_doc(self):
        design_doc = {
          "_id":"_design/layers",
          "language": "javascript",
          "views":
          {
            "all": {
              "map": "function(doc) { if (doc.layer) emit(doc.layer, {'_rev': doc._rev}) }"
            },
            "distinct": {
              "map": "function(doc) { if (doc._id.indexOf('schema_') == 0 && doc.title) { emit(doc.layer, doc.title); } else if (doc._id.indexOf('schema_') == 0) { emit(doc.layer, doc.layer); } }"
            }
          }
        }
        existing_design_doc = self.get('_design/layers')
        if existing_design_doc:
            design_doc['_rev'] = existing_design_doc['_rev']
        self.put('_design/layers', design_doc)

    def store_layer_schema(self, layer, schema, extend_schema=True, title=None):
        title = title if title else layer
        existing_doc = self.get('schema_' + layer)

        if extend_schema and existing_doc:
            existing_doc.update(schema)
            new_doc = existing_doc
        elif existing_doc:
            new_doc = schema
            new_doc['_rev'] = existing_doc['_rev']
        else:
            new_doc = schema

        new_doc['layer'] = layer
        new_doc['title'] = title
        self.put('schema_' + layer, new_doc)

    def iter_layer_features(self, layer):
        resp = self.session.get(self.layer_url(layer, include_docs=True))
        data = resp.json()

        for row in data.get('rows', []):
            feature = row['doc']
            if feature.get('layer') == layer and 'geometry' in feature:
                yield geocouch_feature_to_geojson(feature)

    def get_layer_names(self):
        resp = self.session.get(self.couchdb_url + '/_design/layers/_view/distinct')
        data = resp.json()
        for row in data.get('rows', []):
            yield (row['key'], row['value'])

    def layer_extent(self, layer=None):
        """
        Retrun MultiPolygon of all layer geometries.
        If `layer` is None it returns a MultiPolygon of _all_ geometries.
        """
        if layer:
            resp = self.session.get(self.layer_url(layer, include_docs=True))
        else:
            resp = self.session.get(self.couchdb_url + '/_all_docs?include_docs=true')

        data = resp.json()

        geometries = []
        for row in data.get('rows', []):
            geom = row['doc'].get('geometry')
            if not geom:
                continue
            try:
                geom = shapely.geometry.asShape(geom)
            except ValueError:
                continue # not a GeoJSON geometry

            if geom.type == 'MultiPolygon':
                geometries.extend(geom)
            elif geom.type == 'Polygon':
                geometries.append(geom)
            else:
                # use boundary of non polygon geometries
                geometries.append(shapely.geometry.box(geom.bounds))


        if geometries:
            return shapely.geometry.MultiPolygon(geometries)

    def store_features(self, layer, features, update_unmodified=False, delete_missing=None):
        """
        :param update_unmodified: when true, overwrite features even when
            they where not modified
        :param delete_missing: delete these features IDs if they are not in `features`.

        :returns: dict with all feature ids that could not be saved
        """
        docs = []
        feature_ids = set()
        for feature in features:
            feature_ids.add(feature['properties'].get('_id'))
            if not update_unmodified and feature.get('modified') == False:
                continue
            feature = geojson_feature_to_geocouch(feature)
            feature['layer'] = layer
            docs.append(feature)

        if delete_missing:
            delete_missing = set(delete_missing)
            deleted_feature_ids = delete_missing.difference(feature_ids)
            self._delete(layer, deleted_feature_ids)

        return self.put_bulk(docs)

    def _delete(self, layer, ids):
        resp = self.session.get(self.layer_url(layer))
        data = resp.json()
        for row in data.get('rows', []):
            if row['id'] in ids:
                self.delete(row['id'], row['value']['_rev'])

    def clear_layer(self, layer):
        resp = self.session.get(self.layer_url(layer, include_docs=True))
        if resp.status_code != 200:
            raise CouchDBError('could not read layer from %s: %s' % (resp.url, resp.content))
        data = resp.json()

        for row in data.get('rows', []):
            feature = row['doc']
            if feature.get('layer') == layer:
                self.delete(feature['_id'], feature['_rev'])

def extend_schema_for_couchdb(schema):
    schema['properties']['_id'] = 'str'
    schema['properties']['_rev'] = 'str'


class CouchFileBox(CouchDB):

    def _file_doc(self, data):
        file_id = data['filename']
        file_doc = {}
        file_doc['_id'] = file_id
        file_doc['datetime'] = datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S ')
        file_doc['_attachments'] = {
            'file': {
                'content_type': data['content-type'],
                'data':  data['file'].encode('base64').replace('\n', ''),
            }
        }
        return file_id, file_doc

    def _store_bulk(self, files, overwrite=False):
        file_docs = {}
        for file in files:
            file_id, file_doc = self._file_doc(file)
            file_docs[file_id] = file_doc

            existing_doc = self.get(file_id)
            if existing_doc:
                file_docs[file_id]['_rev'] = existing_doc['_rev']

            self.put(file_id, file_doc)
        return True

    def store_file(self, file, overwrite=False):
        return self._store_bulk([file], overwrite)

    def store_files(self, files, overwrite=False):
        files = [f for f in files]
        return self._store_bulk(files, overwrite)

    def all_files(self):
        resp = self.session.get(self.file_url(include_docs=True))
        data = resp.json()
        files = []
        for row in data.get('rows', []):
            if row['id'] and '_attachments' in row['doc']:
                files.append({
                    'id': row['id'],
                    'rev': row['value']['rev'],
                    'size':  row['doc']['_attachments']['file']['length'],
                    'date': row['doc']['datetime'],
                    'content_type': row['doc']['_attachments']['file']['content_type'],
                })
        return files

    def file_url(self, include_docs=False):
        url = self.couchdb_url + '/_all_docs?'
        if include_docs:
            url += '&include_docs=true'
        return url


def init_user_boxes(user, couchdb_url):
    """
    Init or update area/document boxes for user.
    Updates user's password and authorization docs.
    """
    username = 'user_%d' % user.id
    password = user.authproxy_token

    couch = CouchDBBox(couchdb_url, '%s_%s' % (SystemConfig.AREA_BOX_NAME, user.id))
    couch.create()
    couch.update_layer_view_doc()
    couch.update_user(username, password)
    couch.update_auth_doc(username, writable=True, read_roles=['consultants'])

    customer_couch = CouchFileBox(couchdb_url, '%s_%s' % (SystemConfig.CUSTOMER_BOX_NAME, user.id))
    customer_couch.create()
    customer_couch.update_auth_doc(username, writable=True, read_roles=[])

    consultant_couch = CouchFileBox(couchdb_url, '%s_%s' % (SystemConfig.CONSULTANT_BOX_NAME, user.id))
    consultant_couch.create()
    consultant_couch.update_auth_doc(username, writable=False, read_roles=['consultants'], write_roles=['consultants'])
