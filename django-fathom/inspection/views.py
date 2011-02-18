# Create your views here.

from django.shortcuts import render_to_response

from inspection import get_databases, get_database

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
    template = kwargs.get('template', INDEX_TEMPLATE)
    return render_to_response(template, {'databases': get_databases()})

@inspection_view(LIST_TABLES_TEMPLATE)
def list_tables(request, label, **kwargs):
    inspector = get_inspector(label)
    template = kwargs.get('template', LIST_TABLES_TEMPLATE)
    return render_to_response(template, {'tables': inspector.get_tables()})

@inspection_view('database.html')
def database(request, inspector, template, **kwargs):
    dictionary = {'inspector': inspector, 'database': inspector.build_scheme()}
    return render_to_response(template, dictionary)

@inspection_view('table.html')
def table(request, inspector, template, **kwargs):
    table_name = kwargs.get('table')
    columns = inspector.get_columns(table_name)
    dictionary = {'columns': columns, 'table_name': table_name}
    return render_to_response(template, dictionary)
