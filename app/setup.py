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

"""
GBI Server
----------

"""
from setuptools import setup, find_packages

setup(
    name='gbi_server',
    version='1.0',
    url='https://github.com/omniscale/gbi-server',
    license='Apache License 2.0',
    author='Oliver Tonnhofer',
    author_email='support@omniscale.de',
    description='GBI-Server application',
    long_description=__doc__,
    packages=find_packages(),
    zip_safe=False,
    install_requires=[], # see requirements.txt
    include_package_data=True,
    package_data={'': ['*.*']},
)
