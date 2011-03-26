#!/usr/bin/python3

from os.path import exists

from .errors import FathomError

def get_database_type(*args, **kwargs):
    if len(args) > 0:
        if _try_postgres(args[0]):
            return 'PostgreSQL'
        if _try_sqlite(args[0]):
            return 'Sqlite3'
    if len(kwargs) > 0:
        if _try_mysql(kwargs):
            return 'MySQL'
    raise FathomError('Failed to determine database type;')

def _try_sqlite(path):
    try:
        import sqlite3
    except ImportError:
        return False
    if not exists(path):
        return False
    try:
        connection = sqlite3.connect(path)
        connection.execute("SELECT * FROM sqlite_master")
        connection.close()
    except Exception: # we really want to catch everything here
        return False
    return True
    
def _try_postgres(string):
    try:
        import psycopg2
    except ImportError:
        return False
    try:
        connection = psycopg2.connect(string)
        cursor = connection.cursor()
        cursor.execute("SELECT version()")
        connection.close()
    except Exception:
        return False
    return True

def _try_mysql(params):
    try:
        import pymysql
    except ImportError:
        return False
    try:
        connection = pymysql.connect(**params)
        cursor = connection.cursor()
        cursor.execute("SELECT version()")
        connection.close()
    except Exception:
        return False
    return True
