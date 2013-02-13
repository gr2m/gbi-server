Installation
============

Source
------

GBI-Server uses `Git`_ as a source control management tool. If you are new to distributed SCMs or Git we recommend to read `Pro Git <http://git-scm.com/book>`_.

The main (authoritative) repository is hosted at http://github.com/omniscale/gbi-server

To get a copy of the repository call::

  git clone https://github.com/omniscale/gbi-server

.. _`Git`: http://git-scm.com/

Dependencies
------------

GBI-Server runs with Python 2.7 and is tested on Linux and Mac OS X.

Other dependencies are:

    - `Tinyows 1.1.0 <http://mapserver.org/trunk/tinyows/>`_: WFS Server
    - `Apache CouchDB 1.2 <http://couchdb.apache.org/>`_: Database using JSON documents

TinyOWS itself requires a recent version of libxml:

    - `libxml2 2.8.0 <http://xmlsoft.org/index.html>`_: XML parser


GBI-Server also requires the following system packages:

    - postgresql-9.1-postgis
    - postgresql-contrib-9.1
    - postgresql-client-9.1
    - libgdal1-dev
    - libgeos-dev
    - gdal-bin
    - libproj0
    - build-essential
    - erlang-dev
    - erlang-manpages
    - erlang-base-hipe
    - erlang-eunit
    - erlang-nox
    - erlang-xmerl
    - erlang-inets
    - libmozjs185-dev
    - libicu-dev
    - libcurl4-gnutls-dev
    - libtool
    - python-dev
    - python-yaml
    - python-imaging
    - python-psycopg2
    - flex

To install all requirements on Ubuntu::

    sudo aptitude install libgdal1-dev libgeos-dev gdal-bin libproj0 build-essential \
                          postgresql-9.1-postgis postgresql-contrib-9.1 postgresql-client-9.1 \
                          postgresql-server-dev-9.1 erlang-dev erlang-manpages \
                          erlang-base-hipe erlang-eunit erlang-nox erlang-xmerl erlang-inets \
                          libmozjs185-dev libicu-dev libcurl4-gnutls-dev libtool \
                          python-dev python-yaml python-imaging python-psycopg2 flex

GBI-Server requires Python packages listed in `requirements.txt`

These Python packages will be installed by running::

    pip install -r requirements.txt

.. note::

    The `requirements.txt` is located in ``server/requirements.txt``


virtualenv
----------

.. _virtual_env:

It is recommended to install GBI-Server into a `virtual Python environment <http://www.virtualenv.org/en/latest/>`_, especially if you are also running other Python based software.

On Ubuntu::

    sudo aptitude install python-pip python-virtualenv
    virtualenv venv
    venv/bin/pip install -r requirements.txt
