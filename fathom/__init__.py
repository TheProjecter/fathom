#!/usr/bin/python

from schema import Database
from inspectors import PostgresInspector, SqliteInspector

def get_sqlite3_database(path):
    return Database(inspector=SqliteInspector(path))
    
def get_postgresql_database(args):
    return Database(inspector=PostgresInspector(args))
