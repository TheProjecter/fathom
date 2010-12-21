# Create your views here.

from django.shortcuts import render_to_response

from inspection import get_inspectors, get_inspector

INDEX_TEMPLATE = 'index.html'
LIST_TABLES_TEMPLATE = 'list_tables.html'

def inspection_view(default_template):
    def _decorator(function):
        def result(request, label, **kwargs):
            inspector = get_inspector(label)
            template = kwargs.pop('template', default_template)
            return function(request, inspector, template, **kwargs)
        return result
    return _decorator

def index(request, **kwargs):
    inspectors = get_inspectors()
    template = kwargs.get('template', INDEX_TEMPLATE)
    return render_to_response(template, {'inspectors': inspectors})

@inspection_view(LIST_TABLES_TEMPLATE)
def list_tables(request, label, **kwargs):
    inspector = get_inspector(label)
    template = kwargs.get('template', LIST_TABLES_TEMPLATE)
    return render_to_response(template, {'tables': inspector.get_tables()})

@inspection_view('database.html')
def database(request, inspector, template, **kwargs):
    dictionary = {'inspector': inspector, 'database': inspector.build_scheme()}
    return render_to_response(template, dictionary)
