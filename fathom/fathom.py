#!/usr/bin/python

from abc import ABCMeta, abstractmethod
from re import compile as re_compile, search as re_search

class InspectError(Exception):
    pass

class DatabaseInspector:
    __metaclass__ = ABCMeta
    
    def __init__(self, *db_params):
        self._db_params = db_params
        
    def get_tables(self):
        return [row[0] for row in self._select(self._TABLE_NAMES_SQL)]
        
    @abstractmethod
    def get_columns(self, table):
        pass
    
    def _select(self, sql):
        connection = self._api.connect(*self._db_params)
        cursor = connection.cursor()
        cursor.execute(sql)
        rows = list(cursor)
        connection.close()
        return rows


class SqliteInspector(DatabaseInspector):
    
    _TABLE_NAMES_SQL = """SELECT name 
                          FROM sqlite_master"""
    
    _COLUMN_NAMES_SQL = """SELECT sql
                           FROM sqlite_master
                           WHERE name = '%s'"""

    def __init__(self, *db_params):
        DatabaseInspector.__init__(self, *db_params)
        import sqlite3
        self._api = sqlite3
        
    def get_columns(self, table):
        sql = self._COLUMN_NAMES_SQL % table
        # only one row should be returned with only one value
        table_sql = self._select(sql)[0][0]
        return self._parse_table_sql(table_sql)
        
    def _parse_table_sql(self, sql):
        start = sql.find('(')
        end = sql.rfind(')')
        if start == -1 or end == -1:
            raise InspectError("Failed to parse table sql.")
        columns = [col.strip() for col in sql[start + 1:end].split(',')]
        columns = [column.split(' ')[0] for column in columns]
        print columns


class PostgresInspector(DatabaseInspector):
    
    _TABLE_NAMES_SQL = """SELECT table_name 
                          FROM information_schema.tables 
                          WHERE table_schema = 'public'"""
    _COLUMN_NAMES_SQL = """SELECT column_name 
                           FROM information_schema.columns
                           WHERE table_name = '%s'"""
    
    def __init__(self, *db_params):
        DatabaseInspector.__init__(self, *db_params)
        import psycopg2
        self._api = psycopg2
        
    def get_columns(self, table):
        sql = self._COLUMN_NAMES_SQL % table
        return [row[0] for row in self._select(sql)]
        

if __name__ == "__main__":
    print 'sqlite3'
    sqlite = SqliteInspector("test.db3")
    for table in sqlite.get_tables():
        print table, sqlite.get_columns(table)
    pgsql = PostgresInspector("dbname=django user=django")
    print 'postgresql'
    for table in pgsql.get_tables():
        print table, pgsql.get_columns(table)
    
