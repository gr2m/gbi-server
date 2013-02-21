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

from flask import request
from flask.ext.wtf import SelectField, HiddenField, TextField, validators
from flask.ext.babel import lazy_gettext as _l
from .base import Form

class WFSEditForm(Form):
    def is_submitted(self):
        return request and request.method in ("PUT", "POST") and request.form.get('edit_form')

    layer = SelectField(_l('wfs_layer'))
    external_editor = HiddenField()
    edit_form = HiddenField()

class WFSAddLayerForm(Form):
    def is_submitted(self):
        return request and request.method in ("PUT", "POST") and request.form.get('add_form')

    new_layer = TextField(_l('wfs_new_layer_name'), validators=[
        validators.Regexp(regex='^[a-z0-9]+$', message=_l('Only alphanummeric lowercase characters are allowed!')),
    ])
    add_form = HiddenField()