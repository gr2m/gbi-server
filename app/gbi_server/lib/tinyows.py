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

import errno
import os
import re
import subprocess

from flask import url_for

from StringIO import StringIO
from urlparse import urlparse

from xml.etree import ElementTree as ET

# layers must be list of dict
# layer dict must contain:
#   writable <string [1||0]>
#   name <string>
#   title <string>
def build_config(app, layers, token, destination):
    tinyows_cfg = {
        'tinyows': {
            'check_schema': "1",
            'online_resource': url_for('maps.tinyows_wfs', token=token, _external=True),
            'schema_dir': app.config.get('TINYOWS_SCHEMA_DIR'),
            'log': app.config.get('TINYOWS_LOG_FILE'),
            'log_level': app.config.get('TINYOWS_LOG_LEVEL'),
        },
        'pg': {
            'dbname': app.config.get('TEMP_PG_DB'),
            'host': app.config.get('TEMP_PG_HOST'),
            'user': app.config.get('TEMP_PG_USER'),
            'password': app.config.get('TEMP_PG_PASSWORD'),
            'port': app.config.get('TEMP_PG_PORT'),
        },
        'metadata': {
            'name': app.config.get('TINYOWS_NAME'),
            'title': app.config.get('TINYOWS_TITLE'),
        },

    }

    tinyows = ET.Element('tinyows', attrib=tinyows_cfg['tinyows'])
    ET.SubElement(tinyows, 'pg', attrib=tinyows_cfg['pg'])
    ET.SubElement(tinyows, 'metadata', attrib=tinyows_cfg['metadata'])
    for layer in layers:
        layer['ns_prefix'] = app.config.get('TINYOWS_NS_PREFIX')
        layer['ns_uri'] = app.config.get('TINYOWS_NS_URI')
        layer['retrievable'] = "1"
        layer['exclude_items'] = '__id,__modified,_id,_rev'
        ET.SubElement(tinyows, 'layer', attrib=layer)

    dest_file = open(destination, 'w')
    dest_file.write(ET.tostring(tinyows, "UTF-8"))
    dest_file.close()

def split_cgi_response(data):
    headers = []
    prev_n = 0
    while True:
        next_n = data.find('\n', prev_n)
        if next_n < 0:
            break
        next_line_begin = data[next_n+1:next_n+3]
        headers.append(data[prev_n:next_n].rstrip('\r'))
        if next_line_begin[0] == '\n':
            return headers_dict(headers), data[next_n+2:]
        elif next_line_begin == '\r\n':
            return headers_dict(headers), data[next_n+3:]
        prev_n = next_n+1
    return {}, data

def headers_dict(header_lines):
    headers = {}
    for line in header_lines:
        if ':' in line:
            key, value = line.split(':', 1)
            value = value.strip()
        else:
            key = line
            value = None
        key = key[0].upper() + key[1:].lower()
        headers[key] = value
    return headers

class CGIError(Exception):
    pass

class CGIClient(object):
    def __init__(self, script, no_headers=False, working_directory=None):
        self.script = script
        self.working_directory = working_directory
        self.no_headers = no_headers

    def prepare_environ(self, url, environ):
        return environ

    def open(self, url, data=None):
        method = 'GET'
        if data:
            method = 'POST'

        parsed_url = urlparse(url)
        environ = os.environ.copy()
        environ.update({
            'QUERY_STRING': parsed_url.query,
            'REQUEST_METHOD': method,
            'GATEWAY_INTERFACE': 'CGI/1.1',
            'SERVER_ADDR': '127.0.0.1',
            'SERVER_NAME': 'localhost',
            'SERVER_PROTOCOL': 'HTTP/1.0',
            'SERVER_SOFTWARE': 'MapProxy',
        })

        if method == 'POST':
            environ['CONTENT_LENGTH'] = str(len(data))

        environ = self.prepare_environ(url, environ)

        try:
            p = subprocess.Popen([self.script], env=environ,
                stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                cwd=self.working_directory or os.path.dirname(self.script)
            )
        except OSError, ex:
            if ex.errno == errno.ENOENT:
                raise CGIError('CGI script not found (%s)' % (self.script,))
            elif ex.errno == errno.EACCES:
                raise CGIError('No permission for CGI script (%s)' % (self.script,))
            else:
                raise

        stdout = p.communicate(data)[0]
        ret = p.wait()
        if ret != 0:
            raise CGIError('Error during CGI call (exit code: %d)'
                                              % (ret, ))

        if self.no_headers:
            content = stdout
            headers = dict()
        else:
            headers, content = split_cgi_response(stdout)

        status_match = re.match('(\d\d\d) ', headers.get('Status', ''))
        if status_match:
            status_code = status_match.group(1)
        else:
            status_code = '200'

        content = StringIO(content)
        content.headers = headers
        content.status_code = int(status_code)

        return content


class TinyOWSCGI(CGIClient):
    def __init__(self, tinyows_config, content_type='text/xml', **kw):
        CGIClient.__init__(self, **kw)
        self.tinyows_config = tinyows_config
        self.content_type = content_type
    def prepare_environ(self, url, environ):
        environ['TINYOWS_CONFIG_FILE'] = self.tinyows_config
        environ['CONTENT_TYPE'] = 'text/xml'
        return environ
