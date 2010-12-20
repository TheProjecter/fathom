# Create your views here.

from django.shortcuts import render_to_response

from fathomapp import 

LIST_TABLES_TEMPLATE = 'fathom/templates/list_tables.html'

def list_tables(request, **kwargs):
    inspector = 
    template = kwargs.get('template', LIST_TABLES_TEMPLATE)
