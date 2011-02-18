# Create your views here.

from django.http import Http404
from django.shortcuts import render_to_response
from django.template import RequestContext

from inspection import get_databases, get_database

INDEX_TEMPLATE = 'index.html'
LIST_TABLES_TEMPLATE = 'list_tables.html'
TABLE_TEMPLATE = 'table.html'

def inspection_view(default_template):
    def _decorator(function):
        def result(request, label, **kwargs):
            database = get_database(label)
            template = kwargs.pop('template', default_template)
            return function(request, database, template, **kwargs)
        return result
    return _decorator

def index(request, **kwargs):
    template = kwargs.get('template', INDEX_TEMPLATE)
    return render_to_response(template, {'databases': get_databases()})

@inspection_view(LIST_TABLES_TEMPLATE)
def list_tables(request, database, template, **kwargs):
    return render_to_response(template, {'database': database})

@inspection_view('database.html')
def database(request, inspector, template, **kwargs):
    dictionary = {'inspector': inspector, 'database': inspector.build_scheme()}
    return render_to_response(template, dictionary)

@inspection_view(TABLE_TEMPLATE)
def table(request, database, template, **kwargs):
    table_name = kwargs.get('table')
    try:
        table = database.tables[table_name]
    except KeyError:
        raise Http404
    dictionary = {'table': table}
    return render_to_response(template, dictionary,
                              context_instance=RequestContext(request))
