from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^inspection/', include('inspection.urls')),
    (r'^admin/', include(admin.site.urls)),
)
