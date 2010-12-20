from django.conf import settings as project_settings

from fathom import PostgresInspector, SqliteInspector
from fathom.utils import get_postgres_connection_string

from errors import InspectionError

def get_inspectors():
    result = []
    for label, settings in project_settings.FATHOM.items():
        if settings['type'] == 'postgresql':
            params = {'dbname': settings['name'], 'user': settings['user']}
            string = get_postgres_connection_string(**params)
            result.append((label, PostgresInspector(string)))
        elif settings['type'] == 'sqlite3':
            inspector = SqliteInspector(settings['name'])
            result.append((label, inspector))
        else:
            raise InspectionError('Unsupported type of database.')
    return result
    
