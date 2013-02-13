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

# -*- coding: utf-8 -*-
"""
    setup.py
    ~~~~~~~~

    :copyright: (c) 2012 by Omniscale GmbH & Co. KG.
"""

""""""""""
GBI Server
----------

"""
from setuptools import setup, find_packages

setup(
    name='gbi_server',
    version='0.1',
    url='<enter URL here>',
    license='BSD',
    author='Oliver Tonnhofer',
    author_email='support@omniscale.de',
    description='<enter short description here>',
    long_description=__doc__,
    packages=find_packages(),
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Babel==0.9.6',
        'cssmin==0.1.4',
        'Flask-Assets==0.7',
        'Flask-Babel==0.8',
        'Flask-Login==0.1.3',
        'Flask-Mail==0.7.3',
        'Flask-SQLAlchemy==0.16',
        'Flask-WTF==0.8',
        'Flask==0.9',
        'py-bcrypt==0.2',
        'PyYAML==3.10',
        'requests==1.0.4',
        'SQLAlchemy==0.7.9',
        'GeoAlchemy==0.7.1',
        'Werkzeug==0.8.3',
        'WTForms==1.0.2',
        'Fiona==0.8',
        'Shapely==1.2.16',
        'scriptine==0.2.0a4',
        'MapProxy==1.5.0',
    ],
    include_package_data=True,
    package_data={'': ['*.*']},
)
