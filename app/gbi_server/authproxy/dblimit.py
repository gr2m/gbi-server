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

from gbi_server.authproxy.limiter import LimiterCache, InvalidUserToken
from gbi_server.config import SystemConfig

class CouchDBLimiter(LimiterCache):
    def cache_file(self, user_token, name):
        return os.path.join(self.cache_path(user_token), name)

    def is_permitted(self, user_token, dbname, method):
        permissions = self.load(user_token, dbname)
        if method in ('GET', 'HEAD', 'OPTIONS'):
            return permissions in ('r', 'rw')
        else:
            return permissions == 'rw'

    def create(self, user_token, dbname):
        from gbi_server.model import User

        user = User.by_authproxy_token(user_token)
        if not user:
            raise InvalidUserToken()

        if user.is_customer or user.is_service_provider:
            if dbname in (
                '%s_%s' % (SystemConfig.AREA_BOX_NAME, user.id),
                '%s_%s' % (SystemConfig.CUSTOMER_BOX_NAME, user.id),
            ):
                return 'rw'
            if dbname in (
                '%s_%s' % (SystemConfig.CONSULTANT_BOX_NAME, user.id),
            ):
                return 'r'
        elif user.is_admin or user.is_consultant:
            if dbname.startswith('%s_' % (SystemConfig.CONSULTANT_BOX_NAME, )):
                return 'rw'
            elif dbname.startswith('%s_' % (SystemConfig.CUSTOMER_BOX_NAME, )):
                return 'r'

        return 'no'

    def serialize(self, data):
        return data

    def deserialize(self, data):
        return data
