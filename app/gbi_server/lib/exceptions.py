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

from werkzeug.exceptions import HTTPException
import json

class JSONHTTPException(HTTPException):
    description = "error"
    def get_headers(self, environ):
        return [('Content-Type', 'application/json')]

    def get_body(self, environ):
        return json.dumps({
            'error': self.get_description(environ)
        }, indent=4)


def json_abort(code, description=None):
    code_ = code
    class WrappedException(JSONHTTPException):
        code = code_

    raise WrappedException(description=description)
