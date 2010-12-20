from django.conf import settings

from fathom import PostgresInspector, SqliteInspector

def get_inspector():
    dbsettings = settings.FATHOM['DATABASE']
    if dbsettings['type'] == 'postgresql':
        return PostgresInspector('dbname=%s user=%s' % 
                                 (dbsettings['name'], dbsettings['user']))
    return None
