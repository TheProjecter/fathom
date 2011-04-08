#!/usr/bin/python3

import argparse

import fathom

DESCRIPTION = 'Build django models from database schema.'

def database2django(db):
    for table in db.tables.values():
        table2django(table)

def table2django(table):
    class_name = build_class_name(table)
    result = '''class %s(model.Model):
    pass'''
    print(result % class_name)

def build_class_name(table):
    return ''.join([part.title() for part in table.name.split('_')])

def _get_mysql_database(args):
    kwargs = {}
    for label, name in (('db', 'db'), ('user', 'user'), ('host', 'host'),
                        ('password', 'passwd'), ('port', 'port')):
        if args[label] is not None:
            kwargs[name] = args[label]
    return fathom.get_mysql_database(**kwargs)

def fathom2django(args):
    assert args['database_type'] in ('postgresql', 'sqlite3', 'mysql'), \
           'Unknown database type.'
            
    if args['database_type'] == 'sqlite3':
        db = fathom.get_sqlite3_database(args['path'])
    elif args['database_type'] == 'postgresql':
        db = fathom.get_postgresql_database(args['string'])
    elif args['database_type'] == 'mysql':
        db = _get_mysql_database(args)
    database2django(db)

def add_postgres_subparser(subparsers):
    postgres = subparsers.add_parser('postgresql')
    postgres.add_argument('string', type=str, help='connection string')

def add_sqlite_subparser(subparsers):
    sqlite = subparsers.add_parser('sqlite3')
    sqlite.add_argument('path', type=str, help='database path')

def add_mysql_subparser(subparsers):
    mysql = subparsers.add_parser('mysql')
    mysql.add_argument('db', type=str, help='database name')
    mysql.add_argument('-u', '--user', type=str, help='database user')
    mysql.add_argument('-p', '--password', type=str, help='database password')
    mysql.add_argument('-H', '--host', type=str, help='database host')
    mysql.add_argument('-P', '--port', type=str, help='database port')
    
def add_database_subparsers(parser):
    subparsers = parser.add_subparsers(dest="database_type")
    for name in ('postgres', 'sqlite', 'mysql'):
        globals()['add_%s_subparser' % name](subparsers)

def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    add_database_subparsers(parser)
    args = vars(parser.parse_args())
    fathom2django(args)

if __name__ == "__main__":
    main()
