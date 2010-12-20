from django.conf.urls.defaults import *

from views import list_tables

urlpatterns = patterns('',
    url(r'^tables/', list_tables),
)
