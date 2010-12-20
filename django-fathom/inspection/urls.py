from django.conf.urls.defaults import *

from views import (index, list_tables)

urlpatterns = patterns('',
    url(r'^$', index),
    url(r'^(?P<label>\w+)/tables/', list_tables),
)
