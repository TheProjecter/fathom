from django.conf import settings

from fathom import PostgresInspector, SqliteInspector

def get_inspector():
    print settings['database']['type']
