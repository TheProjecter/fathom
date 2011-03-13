#!/usr/bin/python

from abc import ABCMeta, abstractmethod

from .errors import FathomError
from .schema import (Database, Table, Column, View, Index, Procedure, Argument)

class DatabaseInspector(metaclass=ABCMeta):
    
    '''Abstract base class for database system inspectors.'''
    
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

    def build_columns(self, schema_object):
        sql = self._COLUMN_NAMES_SQL % schema_object.name
        schema_object.columns = dict((row[0], self.prepare_column(row)) 
                                     for row in self._select(sql))

    def build_indices(self, table):
        sql = self._TABLE_INDICE_NAMES_SQL % table.name
        table.indices = dict((row[0], Index(row[0])) 
                             for row in self._select(sql))

    def prepare_default(self, data_type, value):
        if data_type in self.INTEGER_TYPES:
            try:
                return int(value)
            except (ValueError, TypeError):
                return value
        elif data_type in self.FLOAT_TYPES:
            try:
                return float(value)
            except (ValueError, TypeError):
                return value
        return value

    def supports_stored_procedures(self):
        return True
        
    def supports_routine_parametres(self):
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
    
    INTEGER_TYPES = ('integer', 'smallint')
    FLOAT_TYPES = ('float',)

    def __init__(self, *db_params):
        DatabaseInspector.__init__(self, *db_params)
        import sqlite3
        self._api = sqlite3

    def supports_stored_procedures(self):
        return False

    def supports_routine_parametres(self):
        return False

    def get_procedures(self):
        return {}
        
    def build_columns(self, schema_object):
        sql = self._COLUMN_NAMES_SQL % schema_object.name
        schema_object.columns = dict((row[1], self.prepare_column(row)) 
                                     for row in self._select(sql))
                                     
    def build_indices(self, table):
        sql = self._TABLE_INDICE_NAMES_SQL % table.name
        table.indices = dict((row[1], Index(row[0]))
                             for row in self._select(sql))
        
    def prepare_column(self, row):
        not_null = bool(row[3])
        default = self.prepare_default(row[2], row[4]) if row[4] else None
        return Column(row[1], row[2], not_null=not_null, default=default)


class PostgresInspector(DatabaseInspector):

    INTEGER_TYPES = ('integer', 'int4', 'int2')
    FLOAT_TYPES = ('float',)
    
    _TABLE_NAMES_SQL = """
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"""
                          
    _VIEW_NAMES_SQL = """
SELECT viewname
FROM pg_views
WHERE schemaname = 'public'"""
                          
    _COLUMN_NAMES_SQL = """
SELECT column_name, data_type, character_maximum_length, is_nullable,
       column_default
FROM information_schema.columns
WHERE table_name = '%s'"""
                           
    _INDEX_NAMES_SQL = """
SELECT indexname
FROM pg_indexes
WHERE schemaname = 'public'"""

    _TABLE_INDICE_NAMES_SQL = """
SELECT indexname 
FROM pg_indexes 
WHERE schemaname='public' AND tablename='%s'
"""

    _PROCEDURE_NAMES_SQL = """
SELECT proname, proargtypes
FROM pg_proc JOIN pg_language ON pg_proc.prolang = pg_language.oid
WHERE pg_language.lanname = 'plpgsql'
"""

    _PROCEDURE_ARGUMENTS_SQL = """
SELECT proargnames, proargtypes
FROM pg_proc JOIN pg_language ON pg_proc.prolang = pg_language.oid
WHERE pg_language.lanname = 'plpgsql' AND proname = '%s' AND proargtypes='%s'
"""

    _PROCEDURE_RETURN_TYPE_SQL = """
SELECT prorettype
FROM pg_proc JOIN pg_language ON pg_proc.prolang = pg_language.oid
WHERE pg_language.lanname = 'plpgsql' AND proname = '%s' AND proargtypes='%s'
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
                             
    def build_procedure(self, procedure):
        arg_type_oids = procedure._private['arg_type_oids']
        name = procedure.name.split('(')[0]
        sql = self._PROCEDURE_ARGUMENTS_SQL % (name, arg_type_oids)
        result = self._select(sql)[0]
        names, oids = result[0], result[1].split(' ')
        types = self.types_from_oids(oids)
        procedure.arguments = dict((name, Argument(name, type)) 
                                   for name, type in zip(result[0], types))
        
        sql = self._PROCEDURE_RETURN_TYPE_SQL % (name, arg_type_oids)
        oid = self._select(sql)[0][0]
        procedure.returns = self.types_from_oids([oid])[0]

    def get_procedures(self):
        return dict(self.prepare_procedure(row)
                    for row in self._select(self._PROCEDURE_NAMES_SQL))
            
    def prepare_column(self, row):
        # because PostgreSQL keeps varchar type as character varying, we need
        # to rename this type and get also store maximum length
        if row[1] == 'character varying':
            data_type = 'varchar(%s)' % row[2]
        else:
            data_type = row[1]
        not_null = (row[3] == 'NO')
        default = self.prepare_default(data_type, row[4])        
        return Column(row[0], data_type, not_null=not_null, default=default)
        
    def prepare_procedure(self, row):
        # because PostgreSQL identifies procedure by <proc_name>(<proc_args>)
        # we need to name it the same way; also table with procedure names
        # use oids rather than actual type names, so we need decipher them
        oids = row[1].split(' ')
        type_string = ', '.join(type for type in self.types_from_oids(oids))
        name = '%s(%s)' % (row[0], type_string)
        procedure = Procedure(name, inspector=self)
        procedure._private['arg_type_oids'] = row[1]
        return name, procedure
        
    def types_from_oids(self, oids):
        return [self._select(self._TYPE_SQL % oid)[0][0] for oid in oids]


class MySqlInspector(DatabaseInspector):

    INTEGER_TYPES = ('int',)
    FLOAT_TYPES = ('float',)

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

    _COLUMN_NAMES_SQL = """
SELECT column_name, data_type, character_maximum_length, is_nullable, 
       column_default
FROM information_schema.columns
WHERE table_name = '%s'
"""

    _TABLE_INDICE_NAMES_SQL = """
SELECT index_name 
FROM information_schema.statistics
WHERE table_name='%s';
"""

    _VERSION_SQL = """
    SELECT version()
"""
    
    def __init__(self, *args, **kwargs):
        DatabaseInspector.__init__(self, *args, **kwargs)
        try:
            import MySQLdb
            self._api = MySQLdb
        except ImportError:
            try:
                import pymysql
                self._api = pymysql
            except ImportError:
                raise FathomError('Either MySQLdb or pymsql package is '
                                  'required to access MySQL database.')
        self.set_version()
        
    def set_version(self):
        try:
            version = self._select(self._VERSION_SQL)[0][0].split('.')[0:2]
            self.version = tuple([int(step) for step in version])
        except Exception as e:
            print('Warning: failed to obtain MySQL version; assuming 5.0')
            self.version = (5, 0)
        
    def get_procedures(self):
        return dict((row[0], Procedure(row[0], inspector=self))
                    for row in self._select(self._PROCEDURE_NAMES_SQL))
        
    def build_procedure(self, procedure):
        if self.supports_routine_parametres():
            pass
        else:
            procedure.arguments = {}

    def prepare_column(self, row):
        if row[1] == 'varchar':
            data_type = 'varchar(%s)' % row[2]
        else:
            data_type = row[1]
        not_null = (row[3] == 'NO')
        default = self.prepare_default(data_type, row[4])
        return Column(row[0], data_type, not_null=not_null, default=default)

    def supports_routine_parametres(self):
        return self.version >= (5, 5)
