#!/usr/bin/python3

from .schema import Database
from .inspectors import PostgresInspector, SqliteInspector, MySqlInspector
from .errors import FathomError
from .utils import get_database_type

def get_sqlite3_database(path):
    return Database(inspector=SqliteInspector(path))
    
def get_postgresql_database(args):
    return Database(inspector=PostgresInspector(args))

def get_mysql_database(**kwargs):
    return Database(inspector=MySqlInspector(**kwargs))

TYPE_TO_FUNCTION = {
    'Sqlite3': get_sqlite3_database,
    'PostgreSQL': get_postgresql_database,
    'MySQL': get_mysql_database
}

def get_database(*args, **kwargs):
    function = TYPE_TO_FUNCTION[get_database_type(*args, **kwargs)]
    return function(*args, **kwargs)
