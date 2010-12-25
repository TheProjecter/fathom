#!/usr/bin/python

from abc import ABCMeta, abstractmethod
from re import compile as re_compile, search as re_search

from _sqlite import CreateTableParser

class FathomError(Exception):
    pass


class DatabaseInspector:
    
    '''Abstract base class for database system inspectors. This class defines
    interface for class inspecting database and creating image.'''
    
    __metaclass__ = ABCMeta
    
    def __init__(self, *db_params):
        self._db_params = db_params
        
    def get_tables(self):
        return [row[0] for row in self._select(self._TABLE_NAMES_SQL)]
        
    @abstractmethod
    def get_columns(self, table):
        pass
        
    def _get_views(self):
        return [row[0] for row in self._select(self._VIEW_NAMES_SQL)]
        
    @abstractmethod
    def get_stored_procedures(self):
        pass
        
    def supports_stored_procedures(self):
        return True
        
    def build_scheme(self):
        database = Database()
        for table_name in self.get_tables():
            table = database.add_table(table_name)
            for column_name in self.get_columns(table_name):
                column = table.add_column(column_name)
        for view_name in self._get_views():
            view = database.add_view(view_name)
        return database
    
    def _select(self, sql):
        connection = self._api.connect(*self._db_params)
        cursor = connection.cursor()
        cursor.execute(sql)
        rows = list(cursor)
        connection.close()
        return rows


class SqliteInspector(DatabaseInspector):
    
    _TABLE_NAMES_SQL = """SELECT name 
                          FROM sqlite_master
                          WHERE type = 'table'"""
                          
    _VIEW_NAMES_SQL = """SELECT name
                          FROM sqlite_master
                          WHERE type= 'view'"""
    
    _COLUMN_NAMES_SQL = """SELECT sql
                           FROM sqlite_master
                           WHERE name = '%s'"""

    def __init__(self, *db_params):
        DatabaseInspector.__init__(self, *db_params)
        import sqlite3
        self._api = sqlite3

    def supports_stored_procedures(self):
        return False

    def get_stored_procedures(self):
        return []
        
    def get_columns(self, table):
        sql = self._COLUMN_NAMES_SQL % table
        # only one row should be returned with only one value
        table_sql = self._select(sql)[0][0]
        return self._parse_table_sql(table_sql)
        
    def _parse_table_sql(self, sql):
        def strip(column):
            if column[0] == column[-1] == '"':
                return column[1:-1]
            else:
                return column
        return [strip(column) for column in CreateTableParser().parse(sql)]


class PostgresInspector(DatabaseInspector):
    
    _TABLE_NAMES_SQL = """SELECT table_name 
                          FROM information_schema.tables 
                          WHERE table_schema = 'public'"""
                          
    _VIEW_NAMES_SQL = """SELECT viewname
                         FROM pg_views
                         WHERE schemaname = 'public'"""
                          
    _COLUMN_NAMES_SQL = """SELECT column_name 
                           FROM information_schema.columns
                           WHERE table_name = '%s'"""
    
    def __init__(self, *db_params):
        DatabaseInspector.__init__(self, *db_params)
        import psycopg2
        self._api = psycopg2
        
    def get_stored_procedures(self):
        pass
        
    def get_columns(self, table):
        sql = self._COLUMN_NAMES_SQL % table
        return [row[0] for row in self._select(sql)]


class Database(object):
    
    def __init__(self, name=''):
        # TODO: somehow database name should be set too, maybe inspector should
        # get it too
        super(Database, self).__init__()
        self.name = name
        self.tables = dict()
        self.views = dict()
        self.stored_procedures = dict()
        
    def add_table(self, name):
        self.tables[name] = Table(name)
        return self.tables[name]
        
    def add_view(self, name):
        self.views[name] = View(name)
        return self.views[name]
        
    def add_stored_procedure(self, name):
        self.stored_procedures[name] = StoredProcedure(name)
        return self.stored_procedures[name]


class Table(object):
    
    def __init__(self, name):
        super(Table, self).__init__()
        self.name = name
        self.columns = dict()
        
    def add_column(self, name):
        self.columns[name] = Column(name)
        return self.columns[name]
        

class View(object):
    
    def __init__(self, name):
        super(View, self).__init__()
        self.name = name
        

class StoredProcedure(object):
    
    def __init__(self, name):
        super(Table, self).__init__()
        self.name = name
        self.parametres = dict()
        

class Column(object):
    
    def __init__(self, name):
        super(Column, self).__init__()
        self.name = name
        

if __name__ == "__main__":
    print 'sqlite3'
    sqlite = SqliteInspector("test.db3")
    for table in sqlite.get_tables():
        print table, sqlite.get_columns(table)
    sqlite.build_scheme()
    pgsql = PostgresInspector("dbname=django user=django")
    print 'postgresql'
    for table in pgsql.get_tables():
        print table, pgsql.get_columns(table)
    pgsql.build_scheme()
