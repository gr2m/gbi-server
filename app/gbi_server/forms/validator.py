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

from flask.ext.wtf import ValidationError
from flask.ext.babel import lazy_gettext as _l
from gbi_server.model import User

def username_unique(form, field):
    if User.by_email(field.data):
    	raise ValidationError(_l('email already exists.'))

def username_exists(form, field):
    if not User.by_email(field.data):
    	raise ValidationError(_l('email does not exist.'))

def check_password_length(form, field):
    if len(field.data) < 5:
        raise ValidationError(_l('Password must at least 6 characters'))