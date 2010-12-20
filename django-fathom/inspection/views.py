# Create your views here.

from django.shortcuts import render_to_response

from inspection import get_inspector

LIST_TABLES_TEMPLATE = 'list_tables.html'

def list_tables(request, **kwargs):
    inspector = get_inspector()
    template = kwargs.get('template', LIST_TABLES_TEMPLATE)
    return render_to_response(template, {'tables': inspector.get_tables()})
