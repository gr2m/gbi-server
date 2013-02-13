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

from flask.ext.wtf import Form as BaseForm
from flask.ext.babel import gettext, ngettext

class BabelTranslations(object):
    def gettext(self, string):
        return gettext(string)

    def ngettext(self, singular, pluaral, n):
        return ngettext(singular, pluaral, n)

babel = BabelTranslations()

class Form(BaseForm):
    def _get_translations(self):
        return babel

    @property
    def csrf(self):
        # csrf was renamed to csrf_token in 0.6
        return self.csrf_token
