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
    
def get_oracle_database(user, password):
    return Database(inspector=OracleInspector(user, password))
