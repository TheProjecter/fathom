#!/usr/bin/python

from .schema import Database
from .inspectors import PostgresInspector, SqliteInspector, MySqlInspector
from .errors import FathomError

def get_sqlite3_database(path):
    return Database(inspector=SqliteInspector(path))
    
def get_postgresql_database(args):
    return Database(inspector=PostgresInspector(args))

def get_mysql_database(**kwargs):
    return Database(inspector=MySqlInspector(**kwargs))

def get_database_type(*args, **kwargs):
    pass
