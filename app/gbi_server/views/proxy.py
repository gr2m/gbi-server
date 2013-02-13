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
from flask import Blueprint, request, abort, current_app

proxy = Blueprint("proxy", __name__, template_folder="../templates")

@proxy.route('/external-wfs/', build_only=True)
@proxy.route('/external-wfs/<path:url>', methods=['GET', 'POST'])
def proxy_action(url=None):
    if not url:
        abort(400)

    allowed_hosts = [current_app.config.get('EXTERNAL_WFS_HOST')]
    found = False

    for allowed_host in allowed_hosts:
        if url.startswith('http://%s' % allowed_host) or url.startswith('https://%s' % allowed_host):
            found = True
            break
    if found:
        if request.method == 'POST':
            r = requests.post(url, data=request.data, headers={'content-type': request.headers['content-type']})
        elif request.method == 'GET':
            r = requests.get(url)
        else:
            abort(400)
        return r.content
    abort(502)
