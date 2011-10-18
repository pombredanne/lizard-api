# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from django.conf.urls.defaults import include
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url
from django.contrib import admin

from lizard_api.views import RootView

admin.autodiscover()

urlpatterns = patterns(
    '',
    # (r'^admin/', include(admin.site.urls)),
    url(r'^$',
        RootView.as_view(),
        name="root"),
    )
