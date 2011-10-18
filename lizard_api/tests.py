# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from django.test import TestCase

from lizard_api.views import RootView


class ApiTest(TestCase):

    def test_smoke(self):
        root_view = RootView.as_view()
        self.assertTrue(root_view)

    def test_get(self):
        installed_apps = [
            'dummy',
            'lizard-api',]
        RootView().get(None, installed_apps)
