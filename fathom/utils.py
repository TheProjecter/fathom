#!/usr/bin/python3

from os.path import exists
from argparse import ArgumentParser

from .errors import FathomError

class FathomArgumentParser(ArgumentParser):
    
    def __init__(self, *args, **kwargs):
        ArgumentParser.__init__(self, *args, **kwargs)
        self.add_database_subparsers()
    
    def parse_args(self, *args, **kwargs):
        arguments = ArgumentParser.parse_args(self, *args, **kwargs)
        return self.get_database(vars(arguments)), arguments

    def add_database_subparsers(self):
        subparsers = self.add_subparsers(dest="database_type",
                                         parser_class=ArgumentParser)
        for name in ('postgres', 'sqlite', 'mysql'):
            getattr(self, 'add_%s_subparser' % name)(subparsers)

    def add_postgres_subparser(self, subparsers):
        postgres = subparsers.add_parser('postgresql')
        postgres.add_argument('string', type=str, help='connection string')
    
    def add_sqlite_subparser(self, subparsers):
        sqlite = subparsers.add_parser('sqlite3')
        sqlite.add_argument('path', type=str, help='database path')
    
    def add_mysql_subparser(self, subparsers):
        mysql = subparsers.add_parser('mysql')
        mysql.add_argument('db', type=str, help='database name')
        mysql.add_argument('-u', '--user', type=str, help='database user')
        mysql.add_argument('-p', '--password', type=str, help='database password')
        mysql.add_argument('-H', '--host', type=str, help='database host')
        mysql.add_argument('-P', '--port', type=str, help='database port')

    def get_database(self, args):
        assert args['database_type'] in ('postgresql', 'sqlite3', 'mysql'), \
               'Unknown database type.'
        if args['database_type'] == 'sqlite3':
            from . import get_sqlite3_database
            return get_sqlite3_database(args['path'])
        elif args['database_type'] == 'postgresql':
            from . import get_postgresql_database
            return get_postgresql_database(args['string'])
        elif args['database_type'] == 'mysql':
            return self.get_mysql_database(args)
            
    def _get_mysql_database(self, args):
        kwargs = {}
        for label, name in (('db', 'db'), ('user', 'user'), ('host', 'host'),
                            ('password', 'passwd'), ('port', 'port')):
            if args[label] is not None:
                kwargs[name] = args[label]
        from . import get_mysql_database
        return get_mysql_database(**kwargs)



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
