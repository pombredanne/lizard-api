lizard-api
==========================================

Introduction
------------

Create a single REST API entrypoint for all available api's in your
installed apps.

And a base class for rich api's used for grids and forms with the Ext-js javascript framework


Usage
-----

1) In the urls.py of your app, add
API_URL_NAME. i.e. 'lizard-area:api:root'

2) Put lizard-api in your INSTALLED_APPS.

3) Mount lizard-api in the main urls.py. i.e.::


    (r'^api/', include(
      'lizard_api.urls',
      namespace='api',
      app_name='lizard-api')),


