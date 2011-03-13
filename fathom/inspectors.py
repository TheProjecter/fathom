#!/usr/bin/python

from abc import ABCMeta, abstractmethod

from .errors import FathomError
from .schema import (Database, Table, Column, View, Index, Procedure, Argument)

class DatabaseInspector(metaclass=ABCMeta):
    
    '''Abstract base class for database system inspectors. This class defines
    interface for class inspecting database and creating image.'''
    
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        
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
        return dict((row[0], Index(row[0])) 
                    for row in self._select(self._INDEX_NAMES_SQL))
        
    @abstractmethod
    def get_procedures(self): 
        '''Return names of all stored procedures in the database.'''
        pass
        
    @abstractmethod
    def build_columns(self, schema_object): pass
        
    @abstractmethod
    def build_indices(self, table): pass
                        
    def supports_stored_procedures(self):
        return True
                    
    def _select(self, sql):
        connection = self._api.connect(*self._args, **self._kwargs)
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

    def get_procedures(self):
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

    _PROCEDURE_NAMES_SQL = """
SELECT proname, proargtypes
FROM pg_proc JOIN pg_language ON pg_proc.prolang = pg_language.oid
WHERE pg_language.lanname = 'plpgsql';    
"""

    _PROCEDURE_ARGUMENTS_SQL = """
SELECT proargnames, proargtypes
FROM pg_proc JOIN pg_language ON pg_proc.prolang = pg_language.oid
WHERE pg_language.lanname = 'plpgsql' AND proname = '%s' AND proargtypes='%s';
"""

    _TYPE_SQL = """
SELECT typname
FROM pg_type
WHERE oid = %s;
"""
    
    def __init__(self, *db_params):
        DatabaseInspector.__init__(self, *db_params)
        import psycopg2
        self._api = psycopg2

    def build_columns(self, schema_object):
        sql = self._COLUMN_NAMES_SQL % schema_object.name
        schema_object.columns = dict((row[0], self.prepare_column(row)) 
                                     for row in self._select(sql))

    def build_indices(self, table):
        sql = self._TABLE_INDICE_NAMES_SQL % table.name
        table.indices = dict((row[0], Index(row[0])) 
                             for row in self._select(sql))
                             
    def build_procedure(self, procedure):
        arg_type_oids = procedure._private['arg_type_oids']
        sql = self._PROCEDURE_ARGUMENTS_SQL % (procedure.get_base_name(),
                                               arg_type_oids)
        result = self._select(sql)[0]
        names, oids = result[0], result[1].split(' ')
        types = self.types_from_oids(oids)
        procedure.arguments = dict((name, Argument(name, type)) 
                                   for name, type in zip(result[0], types))

    def get_procedures(self):
        return dict(self.prepare_procedure(row)
                    for row in self._select(self._PROCEDURE_NAMES_SQL))
            
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
        
    def prepare_procedure(self, row):
        procedure = Procedure(row[0], inspector=self)
        # because PostgreSQL identifies procedure by <proc_name>(<proc_args>)
        # we need to name it the same way; also table with procedure names
        # use oids rather than actual type names, so we need decipher them
        procedure._private['arg_type_oids'] = row[1]
        oids = row[1].split(' ')
        type_string = ', '.join(type for type in self.types_from_oids(oids))
        name = '%s(%s)' % (row[0], type_string)
        return name, procedure
        
    def types_from_oids(self, oids):
        return [self._select(self._TYPE_SQL % oid)[0][0] for oid in oids]


class MySqlInspector(DatabaseInspector):

    _TABLE_NAMES_SQL = """
SELECT TABLE_NAME
FROM information_schema.tables
WHERE TABLE_TYPE = 'BASE TABLE';
"""

    _VIEW_NAMES_SQL = """
SELECT TABLE_NAME 
FROM information_schema.views"""

    _PROCEDURE_NAMES_SQL = """
SELECT routine_name
FROM information_schema.routines
"""
    
    def __init__(self, *args, **kwargs):
        DatabaseInspector.__init__(self, *args, **kwargs)
        import MySQLdb
        self._api = MySQLdb
        
    def get_procedures(self):
        return dict((row[0], Procedure(row[0], inspector=self))
                    for row in self._select(self._PROCEDURE_NAMES_SQL))

    def build_columns(self, schema_object): 
        pass
        
    def build_indices(self, table): 
        pass
