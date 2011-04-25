#!/usr/bin/python3

from os.path import exists
try:
    from argparse import ArgumentParser
except ImportError: 
    # falling back to local argparse module for user convenience
    from ._argparse import ArgumentParser

from .errors import FathomError
from . import constants

class FathomArgumentParser(ArgumentParser):
    
    '''ArgumentParser which provides subcommand for each supported database
    type and arguments for connecting to the database. It is supposed to
    ease building of new tools that are based on fathom library.'''
    
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
    
    '''Based on argument that should be passed to the database this function
    tries to guess the type of the database it should connect to.'''
    
    if len(args) > 0:
        if _try_postgres(args[0]):
            return 'PostgreSQL'
        if _try_sqlite(args[0]):
            return 'Sqlite3'
    if len(args) > 1:
        if _try_oracle(args[0], args[1]):
            return 'Oracle'
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
    
def _try_oracle(username, password):
    try:
        import cx_Oracle
    except ImportError:
        return False
    try:
        connection = cx_Oracle.connect(username, password)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM v$version")
        connection.close()
    except Exception as e:
        return False
    return True

def find_accessing_procedures(table):
    '''Provides list of procedure names that access in some way the given
    table.'''
    
    case_sensitivity = table.database.case_sensitivity
    assert case_sensitivity in constants.CASE_SENSITIVITY, \
            'Unknown type of case sensitivity!'
    procedures = table.database.procedures
    if case_sensitivity == constants.CASE_SENSITIVE:
        return [procedure.name for procedure in procedures.values()
                               if table.name in procedure.sql]        
    elif case_sensitivity == constants.CASE_SENSITIVE_QUOTED:
        return _find_accessing_procedures_quoted(table, procedures)
    else: # case_sensitivity == constants.CASE_INSENSITIVE:
        return [procedure.name for procedure in table.database.procedures.values()
                               if case(table.name) in case(procedure.sql)]

def _find_accessing_procedures_quoted(table, procedures):
    result = []
    lower_name = table.name.lower()
    for procedure in procedures.values():
        indices = find_occurances(procedure.sql.lower(), lower_name)
        for index in indices:
            if _check_name_quoted(table.name, procedure.sql, index):
                result.append(procedure.name)
                break
    return result

_SEPARATING_CHARS = [' ', ';', '\n']

def _check_name_quoted(name, sql, index):
    if index == 0:
        return True
    if (name == name.lower() and
        sql[index - 1] in _SEPARATING_CHARS and 
        sql[index + len(name)] in _SEPARATING_CHARS):
        return True
    if (sql[index - 1] == '"' and sql[index + len(name)] == '"' and 
        name == sql[index:index + len(name)]):
        return True
    return False

def find_occurances(string, sub):
    result = []
    while True:
        index = string.find(sub)
        if index == -1:
            return result
        result.append(index)
        string = string[index + len(sub):]
