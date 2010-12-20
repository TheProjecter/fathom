# Create your views here.

from django.shortcuts import render_to_response

from inspection import get_inspectors, get_inspector

INDEX_TEMPLATE = 'index.html'
LIST_TABLES_TEMPLATE = 'list_tables.html'

def index(request, **kwargs):
    inspectors = get_inspectors()
    template = kwargs.get('template', INDEX_TEMPLATE)
    return render_to_response(template, {'inspectors': inspectors})

def list_tables(request, label, **kwargs):
    inspector = get_inspector(label)
    template = kwargs.get('template', LIST_TABLES_TEMPLATE)
    return render_to_response(template, {'tables': inspector.get_tables()})
