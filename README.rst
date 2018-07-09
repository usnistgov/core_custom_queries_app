Core Custom Queries App
=======================

Custom Queries feature for the curator core project.


Configuration
=============

1. Add "core_custom_queries_app" to your INSTALLED_APPS setting like this
-------------------------------------------------------------------------

.. code:: python

    INSTALLED_APPS = [
        ...
        "core_custom_queries_app",
    ]

2. Include the core_custom_queries_app URLconf in your project urls.py like this
--------------------------------------------------------------------------------

.. code:: python

    url(r'^', include("core_custom_queries_app.urls")),
