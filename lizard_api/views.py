# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
import logging

from django.core.urlresolvers import reverse
from django.core.urlresolvers import NoReverseMatch
from django.conf import settings

from djangorestframework.views import View

from django_load.core import load_object

logger = logging.getLogger(__name__)


class RootView(View):
    """
    Startpoint for REST APIs.
    """

    def get(self, request, installed_apps=None):
        """
        Search all urls.py files in apps for an API_URL_NAME attribute.
        """
        api_entries = {}
        if installed_apps is None:
            installed_apps = settings.INSTALLED_APPS
        for app_name in installed_apps:
            try:
                api_url_name = '%s.urls.API_URL_NAME' % app_name
                api_entries[app_name] = reverse(load_object(
                    api_url_name))
            except (AttributeError, ImportError):
                # ImportError: no urls.py
                # AttributeError: no API_URL_NAME
                pass
            except NoReverseMatch:
                logger.exception('%s could not be reversed.', api_url_name)
        return api_entries
