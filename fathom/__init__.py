#!/usr/bin/python3

from .schema import Database
from .inspectors import (PostgresInspector, SqliteInspector, MySqlInspector,
                         OracleInspector)
from .errors import FathomError

def get_sqlite3_database(path):
    return Database(name=path, inspector=SqliteInspector(path))
    
def get_postgresql_database(args):
    return Database(name=args, inspector=PostgresInspector(args))

def get_mysql_database(**kwargs):
    return Database(name=kwargs['db'], inspector=MySqlInspector(**kwargs))
    
def get_oracle_database(*args, **kwargs):
    return Database(inspector=OracleInspector(*args, **kwargs))

TYPE_TO_FUNCTION = {
    'Sqlite3': get_sqlite3_database,
    'PostgreSQL': get_postgresql_database,
    'MySQL': get_mysql_database,
    'Oracle': get_oracle_database
}
