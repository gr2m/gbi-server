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

from flask import render_template, Blueprint, flash, redirect, url_for, request, current_app, session
from flask.ext.login import current_user, login_user
from flask.ext.babel import gettext as _
from werkzeug.exceptions import Unauthorized, Forbidden
from sqlalchemy.exc import IntegrityError

from geoalchemy import WKTSpatialElement
from geoalchemy.postgis import pg_functions
from shapely.geometry import asShape

from json import loads

from gbi_server.extensions import db
from gbi_server.model import User, EmailVerification, Log, WMTS
from gbi_server.forms.admin import CreateUserForm, WMTSForm
from gbi_server.forms.user import RecoverSetForm, EditAddressForm
from gbi_server.lib.helper import send_mail
from gbi_server.lib.couchdb import init_user_boxes
from gbi_server.lib.external_wms import write_mapproxy_config


admin = Blueprint("admin", __name__, template_folder="../templates")

def assert_admin_user():
    if current_app.config.get('ADMIN_PARTY'):
        return
    if current_user.is_anonymous():
        raise Unauthorized()
    if not current_user.is_admin:
        raise Forbidden()

admin.before_request(assert_admin_user)

@admin.route('/admin')
def index():
    return render_template('admin/index.html')

@admin.route('/admin/user_list', methods=["GET"])
def user_list():
    return render_template('admin/user_list.html', users=User.query.all())

@admin.route('/admin/user_detail/<int:id>', methods=["GET", "POST"])
def user_detail(id):
    user = User.by_id(id)
    return render_template('admin/user_detail.html', user=user)

@admin.route('/admin/verify_user/<int:id>', methods=["GET"])
def verify_user(id):
    user = User.by_id(id)
    user.verified = True
    db.session.commit()
    flash(_('User verified', email=user.email), 'success')
    return redirect(url_for("admin.user_detail", id=id))


@admin.route('/admin/login_as/<int:id>', methods=["GET"])
def loging_as(id):
    user = User.by_id(id)
    login_user(user)
    session['authproxy_token'] = user.authproxy_token
    return redirect(url_for("user.home"))

@admin.route('/admin/activate_user/<int:id>', methods=["GET"])
def activate_user(id):
    user = User.by_id(id)
    user.active = True
    db.session.commit()

    send_mail(
        _("Account activated mail subject"),
        render_template("user/activated_mail.txt", user=user, _external=True),
        [user.email]
    )

    flash(_('User activated', email=user.email), 'success')
    return redirect(url_for("admin.user_detail", id=id))

@admin.route('/admin/create_user', methods=["GET", "POST"])
def create_user():
    form = CreateUserForm()
    if form.validate_on_submit():
        user = User(form.data['email'], form.data['password'])
        user.realname = form.data['realname']
        user.florlp_name = form.data['florlp_name']
        user.type = form.data.get('type')
        user.street = form.data['street']
        user.housenumber =  form.data['housenumber']
        user.zipcode = form.data['zipcode']
        user.city = form.data['city']
        if not form.data['verified']:
            verify = EmailVerification.verify(user)
            db.session.add(verify)
            send_mail(
                _("Email verification mail subject"),
                render_template("user/verify_mail.txt", user=user, verify=verify, _external=True),
                [user.email]
            )
        else:
            user.verified = True
            if form.data['activate']:
                user.active = True
        db.session.add(user)
        db.session.commit()

        init_user_boxes(user, current_app.config.get('COUCH_DB_URL'))

        flash(_('User created', email=user.email), 'success')
        return redirect(url_for('admin.user_list'))
    return render_template('admin/create_user.html', form=form)

@admin.route('/admin/edit_user/<int:id>', methods=["GET", "POST"])
def edit_user(id):
    user = User.by_id(id)
    form = EditAddressForm(request.form, user)
    if form.validate_on_submit():
        user.realname = form.data['realname']
        user.florlp_name = form.data['florlp_name']
        user.street = form.data['street']
        user.housenumber =  form.data['housenumber']
        user.zipcode = form.data['zipcode']
        user.city = form.data['city']
        db.session.commit()
        flash( _('User edited', username=user.realname), 'success')
        return redirect(url_for("admin.user_detail", id=id))
    return render_template('admin/edit_user.html', form=form)

@admin.route('/admin/reset_user_password/<int:id>', methods=["GET", "POST"])
def reset_user_password(id):
    form = RecoverSetForm()
    if form.validate_on_submit():
        user = User.by_id(id)
        user.update_password(form.password.data)
        db.session.commit()
        flash( _('Password reset', username=user.realname), 'success')
        return redirect(url_for('admin.user_detail', id=id))
    return render_template('admin/reset_user_password.html', form=form)

@admin.route('/admin/remove_user/<int:id>', methods=["GET", "POST"])
def remove_user(id):
    user = User.by_id(id)
    if request.method == 'POST':
        email = user.email
        db.session.delete(user)
        db.session.commit()
        flash( _('User removed', username=email), "success")
        return redirect(url_for('admin.user_list'))
    return render_template('admin/remove_user.html', user=user)

@admin.route('/admin/user_log/<int:id>', methods=["GET"])
def user_log(id):
    user = User.by_id(id)
    result = db.session.query(Log, Log.geometry.envelope().wkt).filter_by(user=user).all()
    return render_template('admin/user_log.html', logs=result)

@admin.route('/admin/wmts/list', methods=["GET"])
def wmts_list():
    return render_template('admin/wmts_list.html', wmts=WMTS.query.all())

@admin.route('/admin/wmts/edit', methods=["GET", "POST"])
@admin.route('/admin/wmts/edit/<int:id>', methods=["GET", "POST"])
def wmts_edit(id=None):

    wmts = db.session.query(WMTS, pg_functions.geojson(WMTS.view_coverage.transform(3857))).filter_by(id=id).first() if id else None
    if wmts:
        wmts[0].view_coverage = wmts[1]
        wmts = wmts[0]
        form = WMTSForm(request.form, wmts)
    else:
        form = WMTSForm(request.form)

    if form.validate_on_submit():
        if not wmts:
            wmts = WMTS()
            db.session.add(wmts)
        if form.data['is_background_layer']:
            old_background_layer = WMTS.query.filter_by(is_background_layer=True).first()
            if old_background_layer:
                old_background_layer.is_background_layer = False
        wmts.url = form.data['url']
        wmts.username = form.data['username']
        wmts.password = form.data['password']
        wmts.name = form.data['name']
        wmts.title = form.data['title']
        wmts.layer = form.data['layer']
        wmts.format = form.data['format']
        wmts.srs = form.data['srs']
        wmts.matrix_set = form.data['matrix_set']
        geom = asShape(loads(form.data['view_coverage']))
        wmts.view_coverage = WKTSpatialElement(geom.wkt, srid=3857, geometry_type='POLYGON')

        wmts.view_level_start = form.data['view_level_start']
        wmts.view_level_end = form.data['view_level_end']
        wmts.is_background_layer = form.data['is_background_layer']
        wmts.is_baselayer = not form.data['is_transparent']
        wmts.is_overlay = form.data['is_transparent']
        wmts.is_transparent = form.data['is_transparent']
        wmts.is_visible = form.data['is_visible']
        wmts.is_public = form.data['is_public']
        try:
            db.session.commit()
            write_mapproxy_config(current_app)
            flash( _('Saved WMTS'), 'success')
            return redirect(url_for('admin.wmts_list'))
        except IntegrityError:
            db.session.rollback()
            flash(_('WMTS with this name already exist'), 'error')
    return render_template('admin/wmts_edit.html', form=form, id=id)

@admin.route('/admin/wmts/remove/<int:id>', methods=["GET"])
def wmts_remove(id):
    wmts = WMTS.by_id(id)
    if wmts:
        db.session.delete(wmts)
        db.session.commit()
        flash( _('WMTS removed'), 'success')
    return redirect(url_for('admin.wmts_list'))
