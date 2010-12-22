from django.conf import settings as project_settings

from fathom import PostgresInspector, SqliteInspector
from fathom.utils import get_postgres_connection_string

from errors import InspectionError

def _build_inspector(settings):
    if settings['type'] == 'postgresql':
        params = {'dbname': settings['name'], 'user': settings['user']}
        string = get_postgres_connection_string(**params)
        return PostgresInspector(string)
    elif settings['type'] == 'sqlite3':
        return SqliteInspector(settings['name'])
    else:
        raise InspectionError('Unsupported type of database.')
    
def get_inspectors():
    '''Build inspectors for all databases specified in settings.'''
    return [(label, _build_inspector(settings))
            for label, settings in project_settings.FATHOM.items()]
    
def get_inspector(label):
    '''Build inspector for database with given label that was specified in 
    settings.'''
    return _build_inspector(project_settings.FATHOM[label])
