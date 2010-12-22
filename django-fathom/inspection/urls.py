from django.conf.urls.defaults import *

from views import (index, list_tables, database, table)

urlpatterns = patterns('',
    url(r'^(?P<label>\w+)/$', database),
    url(r'^(?P<label>\w+)/table/(?P<table>\w+)/$', table),
)
