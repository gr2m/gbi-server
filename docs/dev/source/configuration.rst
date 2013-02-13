Configuration
=============

The application uses the configuration from the default configuration (``app/gbi_server/config.py``) but overwrite these values.

``python manage.py runserver`` will load the ``gbi_local_develop.conf`` file if it is present in the local directory.

You can also pass a configuration class to the ``create_app`` function for deployments. See ``app/example-config.py``.


With the configuration file it is possible to overwrite the default configuration. To overwrite the values you have to add the keyword::

    ACCEPT_LANGUAGES = ['en'] # Set accepted languages

    MAIL_SERVER = "smtp.example.org" # Set mailserver