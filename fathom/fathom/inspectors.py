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
        return dict((row[0], View(row[0], inspector=self)) 
                    for row in self._select(self._VIEW_NAMES_SQL))
                                
    def get_indices(self):
        '''Return names of all indices in the database.'''
        return [Index(row[0]) for row in self._select(self._INDEX_NAMES_SQL)]
        
    @abstractmethod
    def build_columns(self, schema_object):
        pass
        
    @abstractmethod
    def build_indices(self, table):
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
    
    _COLUMN_NAMES_SQL = """pragma table_info(%s)"""
    
    _TABLE_INDICE_NAMES_SQL = """pragma index_list(%s)"""

    def __init__(self, *db_params):
        DatabaseInspector.__init__(self, *db_params)
        import sqlite3
        self._api = sqlite3

    def supports_stored_procedures(self):
        return False

    def get_stored_procedures(self):
        return []
        
    def build_columns(self, schema_object):
        sql = self._COLUMN_NAMES_SQL % schema_object.name
        schema_object.columns = dict((row[1], self.prepare_column(row)) 
                                     for row in self._select(sql))
                                     
    def build_indices(self, table):
        sql = self._TABLE_INDICE_NAMES_SQL % table.name
        table.indices = dict((row[1], Index(row[0]))
                             for row in self._select(sql))
        
    @staticmethod
    def prepare_column(row):
        not_null = bool(row[3])
        return Column(row[1], row[2], not_null=not_null)


class PostgresInspector(DatabaseInspector):
    
    _TABLE_NAMES_SQL = """
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"""
                          
    _VIEW_NAMES_SQL = """
SELECT viewname
FROM pg_views
WHERE schemaname = 'public'"""
                          
    _COLUMN_NAMES_SQL = """
SELECT column_name, data_type, character_maximum_length, is_nullable
FROM information_schema.columns
WHERE table_name = '%s'"""
                           
    _INDEX_NAMES_SQL = """
SELECT indexname
FROM pg_indexes
WHERE schemaname = 'public'"""

    _TABLE_INDICE_NAMES_SQL = """
SELECT indexname 
FROM pg_indexes 
WHERE schemaname='public' AND tablename='%s';
"""
    
    def __init__(self, *db_params):
        DatabaseInspector.__init__(self, *db_params)
        import psycopg2
        self._api = psycopg2

    def get_stored_procedures(self):
        return []

    def build_columns(self, schema_object):
        sql = self._COLUMN_NAMES_SQL % schema_object.name
        schema_object.columns = dict((row[0], self.prepare_column(row)) 
                                     for row in self._select(sql))

    def build_indices(self, table):
        sql = self._TABLE_INDICE_NAMES_SQL % table.name
        table.indices = dict((row[0], Index(row[0])) 
                             for row in self._select(sql))
    
    @staticmethod                         
    def prepare_column(row):
        # because PostgreSQL keeps varchar type as character varying, we need
        # to rename this type and get also store maximum length
        if row[1] == 'character varying':
            data_type = 'varchar(%s)' % row[2]
        else:
            data_type = row[1]
        not_null = (row[3] == 'NO')
        return Column(row[0], data_type, not_null=not_null)