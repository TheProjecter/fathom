#!/usr/bin/python

from abc import ABCMeta, abstractmethod

from errors import FathomError
from schema import Database, Table, Column, View, Index

class DatabaseInspector:
    
    '''Abstract base class for database system inspectors. This class defines
    interface for class inspecting database and creating image.'''
    
    __metaclass__ = ABCMeta
    
    def __init__(self, *db_params):
        self._db_params = db_params
        
    def get_tables(self):
        '''Return names of all tables in the database.'''
        return dict((row[0], Table(row[0], inspector=self)) 
                    for row in self._select(self._TABLE_NAMES_SQL))
        
    def get_views(self):
        '''Return names of all views in the database.'''
        return [View(row[0]) for row in self._select(self._VIEW_NAMES_SQL)]
                                
    def get_indices(self):
        '''Return names of all indices in the database.'''
        return [Index(row[0]) for row in self._select(self._INDEX_NAMES_SQL)]
        
    @abstractmethod
    def fill_table(self, table):
        pass
        
    @abstractmethod
    def get_stored_procedures(self):
        pass
        
    def supports_stored_procedures(self):
        return True
                    
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
        from sqlite import parse_table
        self.parse_table = parse_table

    def supports_stored_procedures(self):
        return False

    def get_stored_procedures(self):
        return []
        
    def fill_table(self, table):
        sql = self._COLUMN_NAMES_SQL % table
        # only one row should be returned with only one value
        table_sql = self._select(sql)[0][0]
        self.parse_table(table_sql, table)


class PostgresInspector(DatabaseInspector):
    
    _TABLE_NAMES_SQL = """SELECT table_name 
                          FROM information_schema.tables 
                          WHERE table_schema = 'public' AND 
                                table_type = 'BASE TABLE'"""
                          
    _VIEW_NAMES_SQL = """SELECT viewname
                         FROM pg_views
                         WHERE schemaname = 'public'"""
                          
    _COLUMN_NAMES_SQL = """SELECT column_name 
                           FROM information_schema.columns
                           WHERE table_name = '%s'"""
                           
    _INDEX_NAMES_SQL = """SELECT indexname
                          FROM pg_indexes
                          WHERE schemaname = 'public'"""
    
    def __init__(self, *db_params):
        DatabaseInspector.__init__(self, *db_params)
        import psycopg2
        self._api = psycopg2

    def get_stored_procedures(self):
        return []

    def fill_table(self, table):
        sql = self._COLUMN_NAMES_SQL % table.name
        table.columns = [Column(row[0]) for row in self._select(sql)]

