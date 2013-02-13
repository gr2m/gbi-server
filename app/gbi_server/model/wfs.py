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

from datetime import datetime

from gbi_server.extensions import db

class WFSSession(db.Model):
    __tablename__ = 'wfs_sessions'

    id = db.Column(db.Integer, primary_key=True)
    active = db.Column(db.Boolean, default=True)
    layer = db.Column(db.String, nullable=False)
    url = db.Column(db.String, nullable=False)
    start_edit = db.Column(db.DateTime, default=datetime.utcnow)
    last_update = db.Column(db.DateTime, default=None)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref='wfs_sessions')

    @classmethod
    def by_active_user_layer(cls, layer, user):
        q = WFSSession.query.filter_by(user=user, active=True, layer=layer)
        return q.first()

    def update(self):
        self.last_update = datetime.utcnow()
