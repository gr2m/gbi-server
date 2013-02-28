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

import uuid

from contextlib import contextmanager

import shapely.geometry
import shapely.wkb
import psycopg2

PG_TYPES = {
    'str': 'VARCHAR',
    'float': 'DOUBLE PRECISION',
    'int': 'INTEGER',
}

def json_schema_to_pg_columns(schema):
    table_statements = []
    for key, prop_type in schema['properties'].iteritems():
        table_statements.append('%s %s' % (key, PG_TYPES[prop_type]))

    return ',\n'.join(table_statements)

class TempPGDB(object):
    def __init__(self, connection, tablename, schema=None):
        self.connection = connection
        self.tablename = tablename
        self.schema = schema

    @contextmanager
    def savepoint(self, cur, raise_errors=False):
        savepoint_name = 'savepoint' + uuid.uuid4().get_hex()
        try:
            cur.execute('SAVEPOINT %s' % savepoint_name)
            yield
        except psycopg2.ProgrammingError:
            cur.execute('ROLLBACK TO SAVEPOINT %s' % savepoint_name)
            if raise_errors:
                raise

    def drop_table_or_view(self, cur, name):
        with self.savepoint(cur):
            cur.execute('DROP TABLE "' + name + '" CASCADE')
        with self.savepoint(cur):
            cur.execute('DROP VIEW "' + name + '" CASCADE')

    def ensure_metadata_table(self, cur):
        with self.savepoint(cur):
            create_table_stmt = """
            CREATE TABLE table_metadata (
                tablename VARCHAR PRIMARY KEY,
                feature_ids VARCHAR[]
            );
            """
            cur.execute(create_table_stmt)

    def create_table(self):
        cur = self.connection.cursor()

        self.ensure_metadata_table(cur)
        # remove old metadata entry for tablename
        cur.execute("DELETE FROM table_metadata WHERE tablename = %s", [self.tablename])

        self.drop_table_or_view(cur, self.tablename)

        if not self.schema:
            raise ValueError('schema of data not set')

        properties = json_schema_to_pg_columns(self.schema)
        if properties:
            properties = ',\n' + properties

        create_table_stmt = """
        CREATE TABLE %(tablename)s (
            __id SERIAL PRIMARY KEY,
            __modified BOOL DEFAULT true
            %(properties)s
        );
        """ % {
            'tablename': self.tablename,
            'properties': properties,
        }
        cur.execute(create_table_stmt)

        update_trigger = """
        CREATE OR REPLACE FUNCTION update_modified_column()
        RETURNS TRIGGER AS $$
        BEGIN
           NEW.__modified = true;
           RETURN NEW;
        END;
        $$ language 'plpgsql';
        CREATE TRIGGER update_%(tablename)s_modified BEFORE UPDATE
        ON %(tablename)s FOR EACH ROW EXECUTE PROCEDURE
        update_modified_column();
        """ % {'tablename': self.tablename}
        cur.execute(update_trigger)

        add_geometry_stmt = """
        SELECT AddGeometryColumn ('', '%(tablename)s', 'geometry',
                                      %(srid)s, '%(pg_geometry_type)s', 2);
        """ % {
            'tablename': self.tablename,
            'srid': 3857,
            'pg_geometry_type': 'POLYGON'
        }
        cur.execute(add_geometry_stmt)

    def store_feature_ids(self, cur, feature_ids):
        if not feature_ids:
            return

        insert_statement = """
        INSERT INTO table_metadata (tablename, feature_ids)
        VALUES (%s, %s);
        """

        update_statement = """
        UPDATE table_metadata
        SET feature_ids = feature_ids || %s
        WHERE tablename = %s;
        """

        cur.execute("SELECT 1 FROM table_metadata WHERE tablename = %s", [self.tablename])
        if cur.rowcount == 1:
            cur.execute(update_statement, [feature_ids, self.tablename])
        else:
            cur.execute(insert_statement, [self.tablename, feature_ids])

    def imported_feature_ids(self):
        cur = self.connection.cursor()
        cur.execute("SELECT feature_ids FROM table_metadata WHERE tablename = %s", [self.tablename])
        results = cur.fetchone()
        return results[0] if results else None

    def insert_features(self, features):
        cur = self.connection.cursor()

        feature_ids = []
        schema_properties = set(self.schema.keys())
        for feature in features:
            feature_id = feature['properties'].get('_id')

            extra_arg_names = [n for n in feature['properties'].iterkeys() if n in schema_properties]
            extra_args = ', %s' * len(extra_arg_names)
            extra_arg_names_list = ', ' + ', '.join('"' + name.lower() + '"' for name in extra_arg_names)
            insert_statement = """
            INSERT INTO %(tablename)s (geometry, __modified %(extra_arg_names)s)
                VALUES (ST_GeomFromWKB(%%s, 3857), false %(extra_args)s);
            """ % {
                'tablename': self.tablename,
                'extra_arg_names': extra_arg_names_list,
                'extra_args': extra_args,
            }
            try:
                geometry = shapely.geometry.asShape(feature['geometry'])
            except ValueError:
                # feature is not a geometry
                continue
            if geometry.type not in ('Polygon', ):
                # skip non polygons
                continue

            cur.execute(insert_statement,
                [psycopg2.Binary(geometry.wkb)]
                + [feature['properties'][n] for n in extra_arg_names])

            if feature_id:
                feature_ids.append(feature_id)

        self.store_feature_ids(cur, feature_ids)

    def load_features(self):
        cur = self.connection.cursor()

        property_keys = self.schema['properties'].keys()
        extra_arg_names = ', ' + ', '.join('"' + name.lower() + '"' for name in property_keys)
        select_stmt = """
        SELECT ST_AsBinary(geometry), __modified %(extra_arg_names)s FROM %(tablename)s;
        """ % {
            'extra_arg_names': extra_arg_names,
            'tablename': self.tablename,
        }
        cur.execute(select_stmt)

        for row in cur:
            # filter out emtpy properties
            properties = dict((k, v) for k, v in zip(property_keys, row[2:]) if v is not None)
            feature = {
                'geometry': shapely.geometry.mapping(shapely.wkb.loads(str(row[0]))),
                'properties': properties,
                'modified': row[1],
            }
            yield feature