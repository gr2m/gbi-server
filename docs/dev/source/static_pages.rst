Static pages
============

GBI-Server is not a CMS, but you can add contant as static files (e.g. for terms of use, etc).
You need to configure ``STATIC_PAGES_DIR`` to point to a directory with HTML files.

The URL ``/page/<lang>/<name>`` will return the file ``STATIC_PAGES_DIR/<lang>/<name>``.

The files will be rendered as a Jinja template and you can inherit from the base template::


    {% extends "base.html" %}

    {% block title %} Title {% endblock %}

    {% block content_head %}<h1> Title </h1>{% endblock %}

    {% block content %}

    <div class="row">
        Content
    </div>

    {% endblock %}
