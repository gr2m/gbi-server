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

from flask.ext.wtf import TextField, TextAreaField, validators, PasswordField, BooleanField, SelectField
from flask.ext.babel import lazy_gettext as _l

from .base import Form

from gbi_server.model import User
from user import NewUserForm

class CreateUserForm(NewUserForm):
    type = SelectField(_l('type'), coerce=int, choices=[
        (User.Type.CUSTOMER, _l('customer')),
        (User.Type.SERVICE_PROVIDER, _l('service_provider')),
        (User.Type.CONSULTANT, _l('consultant')),
        (User.Type.ADMIN, _l('admin'))]
    )
    verified = BooleanField(_l('verified'), default=False)
    activate = BooleanField(_l('active'), default=False)
    terms_of_use = BooleanField(_l('terms of use'), default=True)

class WMTSForm(Form):
    url = TextField(_l('wmts_url'), [validators.Required()])
    username = TextField(_l('wmts_username'))
    password = PasswordField(_l('wmts_password'))
    name = TextField(_l('wmts_name'), [validators.Required(), validators.Regexp('[a-zA-Z0-9_-]+$')])
    title = TextField(_l('wmts_title'), [validators.Required()])
    layer = TextField(_l('wmts_layer'), [validators.Required()])
    format = SelectField(_l('wmts_format'), [validators.Required()], choices=[('png', 'png'), ('jpeg', 'jpeg')])
    srs = TextField(_l('wmts_srs'), [validators.Required()])
    matrix_set = TextField(_l('wmts_matrix_set'), [validators.Required()], default='GoogleMapsCompatible')

    view_coverage = TextAreaField(_l('wmts_view_coverage'), [validators.Required()]) #XXX kai: geojson validator?
    view_level_start = SelectField(_l('wmts_view_level_start'), coerce=int, choices=[(x, x) for x in range(21)])
    view_level_end = SelectField(_l('wmts_view_level_end'), coerce=int, choices=[(x, x) for x in range(21)])

    is_background_layer = BooleanField(_l('wmts_background_layer'))
    is_transparent = BooleanField(_l('wmts_transparent'))
    is_visible = BooleanField(_l('wmts_visibility'))
    is_public = BooleanField(_l('wmts_public'))

    def validate_view_level_end(form, field):
        if form.data['view_level_start'] > field.data:
            raise validators.ValidationError(_l('level needs to be bigger or equal to start level'))
