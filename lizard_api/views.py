# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from django.core.urlresolvers import reverse
from django.conf import settings

from djangorestframework.views import View

from django_load.core import load_object


class RootView(View):
    """
    Startpoint for REST APIs.
    """

    def get(self, request):
        """
        Search all urls.py files in apps for an API_URL_NAME attribute.
        """
        api_entries = {}
        for app_name in settings.INSTALLED_APPS:
            try:
                api_entries[app_name] = reverse(load_object(
                    '%s.urls.API_URL_NAME' % app_name))
            except (AttributeError, ImportError):
                # ImportError: no urls.py
                # AttributeError: no API_URL_NAME
                pass
        return api_entries
