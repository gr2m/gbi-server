Development
===========

.. _manage_script:

Manage Script
-------------

The application includes a small commandline tool that is helpful when working with web application of the GBI-Server. This commandline tool includes running a development server, scripts to set up the database and scripts to create and update the translation files.

::

    # create a clear db
    python manage.py init_db

::

    # start the testserver
    python manage.py runserver

.. note::

    For running from your :ref:`virtual environment <virtual_env>`  use ``venv/bin/python manage.py`` instead of just ``python``.
