from django.conf import settings as project_settings

from fathom import get_postgresql_database, get_sqlite3_database
from fathom.utils import get_postgres_connection_string

from errors import InspectionError

def _get_database(settings):
    if settings['type'] == 'postgresql':
        params = {'dbname': settings['name'], 'user': settings['user']}
        string = get_postgres_connection_string(**params)
        return get_postgresql_database(string)
    elif settings['type'] == 'sqlite3':
        return get_sqlite3_database(settings['name'])
    else:
        raise InspectionError('Unsupported type of database.')
    
def get_databases():
    '''Retrieve all databases specified in settings.'''
    return [(label, _get_database(settings))
            for label, settings in project_settings.FATHOM.items()]
    
def get_database(label):
    '''Retrieve database with given label that was specified in settings.'''
    return _build_inspector(project_settings.FATHOM[label])
