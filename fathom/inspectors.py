#!/usr/bin/python3

from abc import ABCMeta, abstractmethod

from .errors import FathomError, FathomParsingError
from .schema import (Database, Table, Column, View, Index, Procedure, Argument,
                     Trigger, ForeignKey)
from . import constants

TRIGGER_WHEN_NAMES = {'AFTER': Trigger.AFTER, 'BEFORE': Trigger.BEFORE}
TRIGGER_EVENT_NAMES = {'INSERT': Trigger.INSERT, 'UPDATE': Trigger.UPDATE,
                       'DELETE': Trigger.DELETE}

class DatabaseInspector(metaclass=ABCMeta):
    
    '''Abstract base class for database system inspectors.'''

    # in most databases aaa, AaA and aAa is turned into "aaa" and you can
    # get case sensitive names by quoting, so "AaA" keeps capital letters    
    CASE_SENSITIVITY = constants.CASE_SENSITIVE_QUOTED
        
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        
    def get_tables(self):
        '''Return names of all tables in the database.'''
        return {self.case(row[0]): Table(self.case(row[0]), inspector=self)
                for row in self._select(self._TABLE_NAMES_SQL)}
        
    def get_views(self):
        '''Return names of all views in the database.'''
        return dict((row[0], View(row[0], inspector=self)) 
                    for row in self._select(self._VIEW_NAMES_SQL))
                                
    def get_indices(self):
        '''Return names of all indices in the database.'''
        return dict((row[0], Index(row[0])) 
                    for row in self._select(self._INDEX_NAMES_SQL))
        
    def get_procedures(self): 
        '''Return names of all stored procedures in the database.'''
        
    def get_triggers(self):
        '''Returns names of all triggers in the database.'''
        return dict((row[0], Trigger(row[0], inspector=self))
                    for row in self._select(self._TRIGGER_NAMES_SQL))

    def get_procedures(self):
        return dict(self.prepare_procedure(row)
                    for row in self._select(self._PROCEDURE_NAMES_SQL))

    def get_index_columns(self, index):
        sql = self._INDEX_COLUMNS_SQL % index.name
        return tuple(row[0] for row in self._select(sql))        

    def build_columns(self, schema_object):
        sql = self._COLUMN_NAMES_SQL % schema_object.name
        columns = {}
        for row in self._select(sql):
            case_sensitve = self.CASE_SENSITIVITY != constants.CASE_INSENSITIVE
            name = (row[0] if case_sensitve else row[0].lower())
            columns[name] = self.prepare_column(row)
        schema_object.columns = columns

    def build_indices(self, table):
        sql = self._TABLE_INDEX_NAMES_SQL % table.name
        table.indices = dict((row[0], Index(row[0], inspector=self)) 
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
        
    def case(self, string):
        if self.CASE_SENSITIVITY != constants.CASE_INSENSITIVE:
            return string
        return string.lower()


class SqliteInspector(DatabaseInspector):

    # Sqlite3 doesn't give a flying fuck about case sensitivity, so 
    # "AaA" == "aaa"
    CASE_SENSITIVITY = constants.CASE_INSENSITIVE

    _TABLE_NAMES_SQL = """SELECT name 
                          FROM sqlite_master
                          WHERE type = 'table'"""
                          
    _VIEW_NAMES_SQL = """SELECT name
                         FROM sqlite_master
                         WHERE type= 'view'"""
                         
    _TRIGGER_NAMES_SQL = """
SELECT name
FROM sqlite_master
WHERE type = 'trigger'"""
    
    _COLUMN_NAMES_SQL = """pragma table_info(%s)"""
    
    _TABLE_INDEX_NAMES_SQL = """pragma index_list(%s)"""
    
    _INDEX_COLUMNS_SQL = """pragma index_info(%s)"""
    
    _FOREIGN_KEYS_SQL = """pragma foreign_key_list(%s)"""
    
    _TRIGGER_SQL = """
SELECT sql FROM sqlite_master 
WHERE type='trigger' AND name = '%s'"""
    
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
        schema_object.columns = dict((row[1].lower(), self.prepare_column(row)) 
                                     for row in self._select(sql))
                                     
    def build_indices(self, table):
        sql = self._TABLE_INDEX_NAMES_SQL % table.name
        table.indices = dict((row[1], Index(row[1], inspector=self))
                             for row in self._select(sql))
                             
    def build_trigger(self, trigger):
        sql = self._TRIGGER_SQL % trigger.name
        source_sql = self._select(sql)[0][0]
        sql = source_sql.replace('\n', ' ').replace('\r', ' ').split(' ')
        sql = [part for part in sql if part]
        index = sql.index('ON')
        if index == -1 or index + 1 == len(sql):
            raise FathomParsingError('CREATE TRIGGER statement', source_sql)
        trigger.table = sql[index + 1]
        self._build_trigger_event(trigger, sql[:index], source_sql)
        self._build_trigger_when(trigger, sql[:index], source_sql)
        
    def _build_trigger_event(self, trigger, sql, source_sql):
        for part in sql:
            if part.upper() in TRIGGER_EVENT_NAMES:
                trigger.event = TRIGGER_EVENT_NAMES[part.upper()]
                return
        raise FathomParsingError('CREATE TRIGGER statement', source_sql)
        
    def _build_trigger_when(self, trigger, sql, source_sql):
        for part in sql:
            if part.upper() in TRIGGER_WHEN_NAMES:
                trigger.when = TRIGGER_WHEN_NAMES[part.upper()]
                return
        raise FathomParsingError('CREATE TRIGGER statement', source_sql)
        
    def prepare_column(self, row):
        not_null = bool(row[3])
        default = self.prepare_default(row[2], row[4]) if row[4] else None
        return Column(row[1].lower(), row[2].lower(), not_null=not_null, 
                      default=default)
        
    def get_index_columns(self, index):
        sql = self._INDEX_COLUMNS_SQL % index.name
        return tuple(row[2] for row in self._select(sql))

    def build_foreign_keys(self, table):
        sql = self._FOREIGN_KEYS_SQL % table.name
        rows = self._select(sql)
        foreign_keys = {}
        for row in rows:
            fk = foreign_keys.setdefault(row[0], ForeignKey())
            fk.referenced_table = row[2]
            fk.columns.append(row[3])
            fk.referenced_columns.append(row[4])
        table.foreign_keys = tuple(foreign_keys.values())


class PostgresInspector(DatabaseInspector):

    INTEGER_TYPES = ('integer', 'int4', 'int2')
    FLOAT_TYPES = ('float',)
    
    CASE_SENSITIVITY = constants.CASE_SENSITIVE_QUOTED
    
    _TABLE_NAMES_SQL = """
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"""
                          
    _VIEW_NAMES_SQL = """
SELECT viewname
FROM pg_views
WHERE schemaname = 'public'"""

    _TRIGGER_NAMES_SQL = """
SELECT tgname, class.relname, tgrelid, tgtype
FROM pg_catalog.pg_trigger, pg_catalog.pg_class class
WHERE tgname NOT IN ('pg_sync_pg_database', 'pg_sync_pg_authid', 
                     'pg_sync_pg_auth_members') AND
      tgname NOT LIKE 'RI_ConstraintTrigger_%' AND
      class.oid = tgrelid
"""
                          
    _COLUMN_NAMES_SQL = """
SELECT column_name, data_type, character_maximum_length, is_nullable,
       column_default
FROM information_schema.columns
WHERE table_name = '%s'"""
                           
    _INDEX_NAMES_SQL = """
SELECT indexname
FROM pg_indexes
WHERE schemaname = 'public'"""

    _TABLE_INDEX_NAMES_SQL = """
SELECT indexname 
FROM pg_indexes 
WHERE schemaname='public' AND tablename='%s'
"""

    _PROCEDURE_NAMES_SQL = """
SELECT proname, proargtypes, prosrc, prorettype
FROM pg_proc JOIN pg_language ON pg_proc.prolang = pg_language.oid
WHERE pg_language.lanname = 'plpgsql'
"""

    _PROCEDURE_ARGUMENTS_SQL = """
SELECT proargnames, proargtypes
FROM pg_proc JOIN pg_language ON pg_proc.prolang = pg_language.oid
WHERE pg_language.lanname = 'plpgsql' AND proname = '%s' AND proargtypes='%s'
"""

    _TYPE_SQL = """
SELECT typname
FROM pg_type
WHERE oid = %s;
"""

    _INDEX_COLUMNS_SQL = """
SELECT attname 
FROM pg_catalog.pg_class, pg_catalog.pg_attribute 
WHERE relname='%s' AND attrelid=oid;
"""

    _FOREIGN_KEYS_SQL = """
SELECT ref.relname, conkey, confkey
FROM pg_catalog.pg_constraint, pg_catalog.pg_class tab, 
     pg_catalog.pg_class ref
WHERE contype = 'f' AND confrelid = ref.oid AND conrelid = tab.oid AND 
      tab.relname = '%s'"""
      
    _COLUMNS_FROM_POSITIONS_SQL = """
SELECT column_name
FROM information_schema.columns
WHERE table_name = '%s' AND ordinal_position IN ('%s')"""

    _BEFORE_BIT = 2
    _INSERT_BIT, _DELETE_BIT, _UPDATE_BIT = 4, 8, 16
    
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
        if oids != ['']:
            types = self.types_from_oids(oids)
            procedure.arguments = dict((name, Argument(name, type)) 
                                       for name, type in zip(result[0], types))
        else:
            procedure.arguments = {}

    def build_foreign_keys(self, table):
        sql = self._FOREIGN_KEYS_SQL % table.name
        rows = self._select(sql)
        foreign_keys = []
        for row in rows:
            fk = ForeignKey()
            fk.referenced_table = row[0]
            fk.columns = self.get_table_columns(table.name, row[1])
            fk.referenced_columns = self.get_table_columns(row[0], row[2])
            foreign_keys.append(fk)
        table.foreign_keys = foreign_keys

    def get_triggers(self):
        '''Returns names of all triggers in the database.'''
        triggers = {}
        for row in self._select(self._TRIGGER_NAMES_SQL):
            name = '%s(%s)' % (row[0], row[1])
            trigger = Trigger(row[0], inspector=self)
            trigger.table = row[1]
            self._build_trigger_event(trigger, row[3])
            self._build_trigger_when(trigger, row[3])
            triggers[name] = trigger
        return triggers
        
    def _build_trigger_event(self, trigger, bitmask):
        if bitmask & self._INSERT_BIT:
            trigger.event = Trigger.INSERT
        elif bitmask & self._DELETE_BIT:
            trigger.event = Trigger.DELETE
        elif bitmask & self._UPDATE_BIT:
            trigger.event = Trigger.UPDATE
        else:
            raise FathomError('Unknown bitmask %d in trigger event type.' % 
                              bitmask)
        
    def _build_trigger_when(self, trigger, bitmask):
        if bitmask & self._BEFORE_BIT:
            trigger.when = Trigger.BEFORE
        else:
            trigger.when = Trigger.AFTER
            
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
        if row[1]:
            oids = row[1].split(' ')
            type_string = ', '.join(type for type in self.types_from_oids(oids))
            name = '%s(%s)' % (row[0], type_string)
        else:
            name = '%s()' % row[0]
        procedure = Procedure(name, inspector=self)
        procedure.sql = row[2]
        if row[3]:
            return_type = self.types_from_oids([row[3]])[0]
            if return_type.lower() != 'void':
                procedure.returns = return_type
        procedure._private['arg_type_oids'] = row[1]
        return name, procedure
        
    def types_from_oids(self, oids):
        return [self._select(self._TYPE_SQL % oid)[0][0] for oid in oids]
    
    def get_table_columns(self, table, positions):
        positions = ', '.join([str(position) for position in positions])
        sql = self._COLUMNS_FROM_POSITIONS_SQL % (table, positions)
        return [row[0] for row in self._select(sql)]


class MySqlInspector(DatabaseInspector):

    INTEGER_TYPES = ('int',)
    FLOAT_TYPES = ('float',)

    CASE_SENSITIVITY = constants.CASE_SENSITIVE

    _TABLE_NAMES_SQL = """
SELECT TABLE_NAME
FROM information_schema.tables
WHERE TABLE_TYPE = 'BASE TABLE';
"""

    _VIEW_NAMES_SQL = """
SELECT TABLE_NAME 
FROM information_schema.views"""

    _PROCEDURE_NAMES_SQL = """
SELECT routine_name, dtd_identifier, routine_definition
FROM information_schema.routines
"""

    _TRIGGER_NAMES_SQL = """
SELECT trigger_name, event_object_table, event_manipulation, action_timing
FROM information_schema.triggers
"""

    _COLUMN_NAMES_SQL = """
SELECT column_name, data_type, character_maximum_length, is_nullable, 
       column_default
FROM information_schema.columns
WHERE table_name = '%s'
"""

    _TABLE_INDEX_NAMES_SQL = """
SELECT index_name 
FROM information_schema.statistics
WHERE table_name = '%s'
"""

    _INDEX_COLUMNS_SQL = """
SELECT column_name
FROM information_schema.statistics
WHERE index_name = '%s'
"""

    _VERSION_SQL = """
    SELECT version()
"""

    _FOREIGN_KEYS_SQL = """
SELECT constraint_name, column_name, referenced_table_name, 
       referenced_column_name
FROM information_schema.key_column_usage
WHERE table_name = '%s'
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

    def prepare_procedure(self, row):
        procedure = Procedure(row[0], inspector=self)
        if row[1] is None:
            procedure.returns = None
        elif row[1].startswith('int'):
            procedure.returns = 'integer'
        else:
            procedure.returns = row[1]
        procedure.sql = row[2]
        procedure._private['arg_type_oids'] = row[1]
        return row[0], procedure
        
    def get_triggers(self):
        '''Returns names of all triggers in the database.'''
        triggers = {}
        for row in self._select(self._TRIGGER_NAMES_SQL):
            trigger = Trigger(row[0], inspector=self)
            trigger.when = TRIGGER_WHEN_NAMES[row[3].upper()]
            trigger.event = TRIGGER_EVENT_NAMES[row[2].upper()]
            trigger.table = row[1]
            triggers[row[0]] = trigger
        return triggers
        
    def build_procedure(self, procedure):
        if self.supports_routine_parametres():
            procedure.arguments = {} # i need mysql 5.5 for this
        else:
            procedure.arguments = {}

    def build_foreign_keys(self, table):
        sql = self._FOREIGN_KEYS_SQL % table.name
        rows = self._select(sql)
        foreign_keys = {}
        for row in rows:
            fk = foreign_keys.setdefault(row[0], ForeignKey())
            fk.referenced_table = row[2]
            fk.columns.append(row[1])
            fk.referenced_columns.append(row[3])
        table.foreign_keys = list(foreign_keys.values())

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


class OracleInspector(DatabaseInspector):

    INTEGER_TYPES = ('NUMBER',)
    FLOAT_TYPES = ('FLOAT',)

    _TABLE_NAMES_SQL = """
SELECT object_name
FROM user_objects 
WHERE object_type = 'TABLE' AND object_name NOT LIKE 'BIN%'
"""
    
    _VIEW_NAMES_SQL = """
SELECT object_name
FROM user_objects
WHERE object_type = 'VIEW'
"""

    _TRIGGER_NAMES_SQL = """
SELECT object_name
FROM user_objects
WHERE object_type = 'TRIGGER'
"""

    _PROCEDURE_NAMES_SQL = """
SELECT object_name
FROM user_objects
WHERE object_type = 'PROCEDURE'
"""

    _FUNCTION_NAMES_SQL = """
SELECT objects.object_name, arguments.data_type
FROM user_objects objects, user_arguments arguments
WHERE objects.object_type = 'FUNCTION' AND 
      objects.object_name = arguments.object_name AND
      arguments.argument_name IS NULL
"""

    _ARGUMENTS_SQL = """
SELECT argument_name, data_type
FROM user_arguments
WHERE argument_name IS NOT NULL AND object_name = upper('%s')
"""
    
    _COLUMN_NAMES_SQL = """
SELECT column_name, data_type, data_length, data_default, 
       upper(nullable)
FROM all_tab_columns
WHERE table_name = '%s'
"""
    
    _TABLE_INDEX_NAMES_SQL = """
SELECT index_name
FROM user_indexes
WHERE table_name = upper('%s')
"""

    _TRIGGER_INFO_SQL = """
SELECT table_name, trigger_type, triggering_event
FROM user_triggers
WHERE trigger_name = upper('%s')
"""
    
    _FOREIGN_KEY_NAMES_SQL = """
SELECT first.constraint_name, first.r_constraint_name, second.table_name
FROM user_constraints first, user_constraints second
WHERE first.constraint_type = 'R' AND 
      first.r_constraint_name = second.constraint_name AND
      first.table_name = upper('%s')
"""
    
    _FOREIGN_KEY_SQL = """
SELECT column_name
FROM all_cons_columns
WHERE constraint_name = upper('%s')
ORDER BY position
"""

    def __init__(self, *db_params):
        DatabaseInspector.__init__(self, *db_params)
        import cx_Oracle
        self._api = cx_Oracle
        
    def prepare_column(self, row):
        if row[1].startswith('VARCHAR'):
            data_type = 'VARCHAR(%s)' % row[2]
        else:
            data_type = row[1]
        not_null = (row[4] == 'N')
        default = self.prepare_default(data_type, row[3])                    
        return Column(row[0], data_type, default=default, not_null=not_null)

    def get_procedures(self):
        procedures =  dict(self.prepare_procedure(row)
                           for row in self._select(self._PROCEDURE_NAMES_SQL))
        functions = dict(self.prepare_procedure(row)
                         for row in self._select(self._FUNCTION_NAMES_SQL))
        procedures.update(functions)
        return procedures
        
    def prepare_procedure(self, row):
        procedure = Procedure(row[0], inspector=self)
        procedure.returns = row[1] if len(row) > 1 else None
        return row[0], procedure
        
    def build_procedure(self, procedure):
        sql = self._ARGUMENTS_SQL % procedure.name
        procedure.arguments = {row[0]: Argument(row[0], row[1]) 
                               for row in self._select(sql)}
                
    def build_foreign_keys(self, table):
        table.foreign_keys = []
        
    def build_trigger(self, trigger):
        sql = self._TRIGGER_INFO_SQL % trigger.name
        row = self._select(sql)[0]
        trigger.table = row[0]
        # should return something like BEFORE EACH ROW, we need first word
        when = row[1].split(' ')[0]
        trigger.when = TRIGGER_WHEN_NAMES[when]
        trigger.event = TRIGGER_EVENT_NAMES[row[2]]

    def build_foreign_keys(self, table):
        sql = self._FOREIGN_KEY_NAMES_SQL % table.name
        rows = self._select(sql)
        foreign_keys = {}
        for row in rows:
            fk = foreign_keys.setdefault(row[0], ForeignKey())
            sql = self._FOREIGN_KEY_SQL % row[0]
            for column_row in self._select(sql):
                fk.columns.append(column_row[0])
            sql = self._FOREIGN_KEY_SQL % row[1]
            for column_row in self._select(sql):
                fk.referenced_columns.append(column_row[0])
            fk.referenced_table = row[2]
        table.foreign_keys = list(foreign_keys.values())
