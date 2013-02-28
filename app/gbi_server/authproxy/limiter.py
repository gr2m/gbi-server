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
import time
from glob import glob

import errno

from mapproxy.platform.lock import FileLock

import logging
log = logging.getLogger(__name__)

class InvalidUserToken(ValueError):
    pass

class LimiterCache(object):
    def __init__(self, cache_dir, file_pattern='*'):
        self.cache_dir = cache_dir
        self.file_pattern = file_pattern
        self.max_cache_time = 60*60 # 60min

    def cache_path(self, user_token):
        return os.path.join(self.cache_dir, user_token[:2], user_token)

    def cache_file(self, user_token, filename):
        return os.path.join(self.cache_path(user_token))

    def clear(self, user_token, file_pattern=None):
        if file_pattern is None:
            file_pattern = self.file_pattern
        for f in glob(os.path.join(self.cache_path(user_token), file_pattern)):
            try:
                os.remove(f)
            except EnvironmentError, ex:
                if ex.errno != errno.EEXIST:
                    raise

    def load(self, user_token, name):
        cache_file = self.cache_file(user_token, name)
        try:
            mtime = os.path.getmtime(cache_file)
            if (time.time() - mtime) > self.max_cache_time:
                log.debug('removing cached tilelimit for %s %s', user_token, name)
                os.unlink(cache_file)
        except EnvironmentError, ex:
            if ex.errno != errno.ENOENT:
                raise

        try:
            with open(cache_file, 'rb') as f:
                return self.deserialize(f.read())
        except EnvironmentError, ex:
            if ex.errno != errno.ENOENT:
                raise

        with FileLock(cache_file + '.lck', remove_on_unlock=True):
            if os.path.exists(cache_file):
                # created while we were waiting for the lock
                return self.load(user_token, name)
            data = self.create(user_token, name)
            self.cache(user_token, name, data)

        return data

    def create(self, user_token, name):
        raise NotImplementedError

    def serialize(self, date):
        raise NotImplementedError

    def deserialize(self, date):
        raise NotImplementedError

    def cache(self, user_token, name, data):
        try:
            os.makedirs(self.cache_path(user_token))
        except OSError, ex:
            if ex.errno != errno.EEXIST:
                # ignore error when path already exists
                pass

        with open(self.cache_file(user_token, name), 'wb') as f:
            f.write(self.serialize(data))
