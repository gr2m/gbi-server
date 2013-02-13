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

import re
import requests
from collections import namedtuple

from werkzeug import exceptions
from werkzeug.routing import Map, Rule
from werkzeug.wrappers import Request, Response

from gbi_server.authproxy.limiter import InvalidUserToken

ProxyTile = namedtuple('ProxyTile', ['url', 'layer', 'tile_coord'])
ProxyCouch = namedtuple('ProxyCouch', ['url', 'dbname'])

tile_proxy_urls = [
    (
        re.compile('^GoogleMapsCompatible-(?P<z>[^/]+)-(?P<x>[^/]+)-(?P<y>[^/]+)/tile$'),
        'http://igreendemo.omniscale.net/wmts/%(layer)s/GoogleMapsCompatible-%(z)s-%(x)s-%(y)s/tile'
        # 'http://localhost:8099/%(layer)s/GoogleMapsCompatible-%(z)s-%(x)s-%(y)s/tile'
    ),
]
couch_proxy_urls = [
    (
        re.compile('(?P<dbname>[^/]+)(?P<req>.*)'),
        # 'http://igreendemo.omniscale.net/wmts/%(layer)s/GoogleMapsCompatible-%(z)s-%(x)s-%(y)s/tile'
        'http://localhost:5984/%(dbname)s%(req)s'
    ),
]

# headers to remove as of HTTP 1.1 RFC2616
# http://www.w3.org/Protocols/rfc2616/rfc2616-sec13.html
hop_by_hop_headers = set([
    'connection',
    'keep-alive',
    'proxy-authenticate',
    'proxy-authorization',
    'te',
    'trailers',
    'transfer-encoding',
    'upgrade',
])

def end_to_end_headers(headers):
    """
    Create a copy of `headers` while removing all
    hop-by-hop headers (see HTTP1.1 RFC2616).

    >>> end_to_end_headers({'CoNNecTION': 'close', 'X-Foo': 'bar'})
    [('X-Foo', 'bar')]
    """
    result = []
    for key, value in headers.iteritems():
        if key.lower() in hop_by_hop_headers:
            continue
        if not value:
            continue
        result.append((key.title(), value))
    return result

def response_iterator(resp, chunk_size=16*1024):
    for chunk in resp.iter_content(chunk_size=chunk_size):
        yield chunk

def chunked_response_iterator(resp, native_chunk_support, line_based):
    """
    Return stream with chunked encoding if native_chunk_support is True.
    """
    if line_based:
        for chunk in resp.iter_lines(1):
            chunk += '\n'
            if native_chunk_support:
                yield chunk
            else:
                yield hex(len(chunk))[2:] + '\r\n' + chunk + '\r\n'
        if not native_chunk_support:
            yield '0\r\n\r\n'
    else:
        for chunk in resp.iter_content(16*1024):
            if native_chunk_support:
                yield chunk
            else:
                yield hex(len(chunk))[2:] + '\r\n' + chunk + '\r\n'
        if not native_chunk_support:
            yield '0\r\n\r\n'

class LimitedStream(object):
    """
    Wraps an existing ``werkzeug.wsgi.LimitedStream`` and adds
    __len__ method, required by requests.
    """
    def __init__(self, limited_stream, limit=None):
        self.limited_stream = limited_stream
        self.limit = limit

    def __getattr__(self, name):
        return getattr(self.limited_stream, name)

    def __len__(self):
        if self.limit is not None:
            return self.limit
        return self.limited_stream.limit

class CouchDBProxy(object):
    def __init__(self, dblimit=None):
        self.dblimit = dblimit

    def on_proxy(self, request, user_token, url):
        proxy_couch = self.proxy_url_and_db(url)
        if not proxy_couch:
            raise exceptions.BadRequest('unknown proxy url')

        headers = end_to_end_headers(request.headers)

        content_length = request.headers.get('content-length')
        if not content_length:
            data = None
        else:
            data = LimitedStream(request.stream)

        dbname = url.split('/', 1)[0]

        try:
            if not self.dblimit.is_permitted(user_token, dbname, request.method):
                raise exceptions.Forbidden()
        except InvalidUserToken:
            raise exceptions.Unauthorized()


        try:
            resp = requests.request(request.method, proxy_couch.url,
                data=data, headers=headers,
                params=request.args, stream=True)

            chunked_response = resp.headers.get('Transfer-Encoding') == 'chunked'
            line_based = resp.headers.get('Content-type', '').startswith(('text/plain', 'application/json'))

        except requests.exceptions.RequestException, ex:
            raise exceptions.BadGateway('source returned: %s' % ex)

        headers = end_to_end_headers(resp.headers)

        if chunked_response:
            # gunicorn supports chunked encoding, no need to
            # encode it manually
            native_chunk_support = 'gunicorn' in request.environ['SERVER_SOFTWARE']
            if not native_chunk_support:
                headers.append(('Transfer-Encoding', 'chunked'))

            resp_iter = chunked_response_iterator(resp, native_chunk_support,
                line_based)
        else:
            resp_iter = response_iterator(resp)
        return Response(resp_iter, direct_passthrough=True,
            headers=headers, status=resp.status_code)

    def proxy_url_and_db(self, req_url):
        for req_url_re, target_url_template in couch_proxy_urls:
            match = req_url_re.match(req_url)
            if match:
                params = match.groupdict()
                target_url = target_url_template % params
                return ProxyCouch(target_url, params['dbname'])
        return None

class TileProxy(object):
    def __init__(self, tile_coverages=None):
        self.tile_coverages = tile_coverages

    def on_proxy(self, request, user_token, layer, url):
        proxy_tile = self.proxy_url_and_coords(url, layer)
        if not proxy_tile:
            raise exceptions.BadRequest('unknown proxy url')

        if request.method not in ('GET', 'HEAD'):
            raise exceptions.MethodNotAllowed(valid_methods=['GET', 'HEAD'])

        try:
            if not self.tile_coverages.is_permitted(user_token, layer, proxy_tile.tile_coord):
                raise exceptions.Forbidden()

        except InvalidUserToken:
            raise exceptions.Unauthorized()

        headers = end_to_end_headers(request.headers)

        try:
            resp = requests.request(request.method, proxy_tile.url, headers=headers, stream=True)
        except requests.exceptions.RequestException, ex:
            raise exceptions.BadGateway('source returned: %s' % ex)

        headers = end_to_end_headers(resp.headers)
        return Response(response_iterator(resp), headers=headers, status=resp.status_code)

    def proxy_url_and_coords(self, req_url, layer):
        for req_url_re, target_url_template in tile_proxy_urls:
            match = req_url_re.match(req_url)
            if match:
                params = match.groupdict()
                params['layer'] = layer
                target_url = target_url_template % params
                tile_coord = int(params['x']), int(params['y']), int(params['z'])
                return ProxyTile(target_url, params['layer'], tile_coord)
        return None


class AuthProxy(object):
    def __init__(self, backends={}, url_map=None):
        self.backends = backends
        self.url_map = Map([
            Rule('/proxy/<string:user_token>/tiles/<path:url>', endpoint='tile.proxy'),
            Rule('/proxy/<string:user_token>/couchdb/<path:url>', endpoint='couchdb.proxy'),
        ])

    def dispatch_request(self, request):
        # return self.on_proxy_couchdb(request, None, None)
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()

            if '.' in endpoint:
                backend, endpoint = endpoint.split('.')
                return getattr(self.backends[backend], 'on_' + endpoint)(request, **values)

            return getattr(self, 'on_' + endpoint)(request, **values)

        except exceptions.HTTPException, e:
            return e

    def __call__(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

def make_profile_app(application):
    from repoze.profile.profiler import AccumulatingProfileMiddleware
    application = AccumulatingProfileMiddleware(
                    application,
                    log_filename='/tmp/profile.log',
                    discard_first_request=True,
                    flush_at_shutdown=True,
                    path='/__profile__'
                   )
    return application

if __name__ == '__main__':
    from limiter import TileCoverages
    from mapproxy.grid import tile_grid
    DEFAULT_GRID = tile_grid(3857, origin='nw')

    tile_coverages = TileCoverages(cache_dir='./cache_coverages', tile_grid=DEFAULT_GRID)
    backends = {
        'tile': TileProxy(tile_coverages),
        'couchdb': CouchDBProxy(),
    }

    application = AuthProxy(backends=backends)
    from werkzeug.serving import run_simple
    run_simple('localhost', 8000, application, use_reloader=True, threaded=True)
