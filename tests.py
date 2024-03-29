#!/usr/bin/python3

'''
Preparing environment for running tests

Every DBMS requires some kind of environment to be set up, in order to run
the test suite. Here is a short description of necessary steps to setup every
environment.

1. Sqlite - No step are required. Test suite will create fathom.db file in
the current directory on wihch all operations are performed.

2. PostgreSQL - Beside having PostgreSQL server installed and running, you 
need to create database named 'fathom' and user named 'fathom':

$ sudo su postgres
$ createuser fathom
$ createdb fathom

You also need to create plpgsql language in fathom database:

$ psql fathom
fathom=# CREATE LANGUAGE plpgsql;

Furthermore you have to edit pg_hba.conf, so it will allow 'fathom' to access 
'fathom' database without a password; this requires using 'trust' setting. To 
access this DBMS from Python you need to have psycopg2 installed for python3.

3. MySQL - Beside having MySQL server installed and running, you need to create 
database named 'fathom' and user named 'fathom'. 

$ mysql -u root -p
mysql> create database fathom;
mysql> create user fathom;

Furthermore you need to grant him all privilages required to access all kinds 
of objects in 'fathom' database and possibly information_schema tables. 

mysql> grant all privileges on fathom.* to 'fathom'@'localhost'

To access this DBMS fromPython you need to have pymysql3 package installed for 
python3.

4. Oracle - Beside having Oracle server installed and running you need to
create user named 'fathom' with password 'fathom'. To access this DBMS from
Python you need to have cx_Oracle package installed for python3.
'''

from abc import ABCMeta, abstractmethod
from unittest import TestCase, main, skipUnless
from collections import namedtuple, OrderedDict

from fathom import (get_sqlite3_database, get_postgresql_database, 
                    get_mysql_database, get_oracle_database, FathomError)
from fathom.schema import Trigger, Table, Column, Database
from fathom import constants

try:
    import psycopg2
    postgres_errors = (psycopg2.OperationalError, psycopg2.ProgrammingError, 
                       psycopg2.InternalError)
    TEST_POSTGRES = True
except ImportError:
    postgres_errors = ()
    TEST_POSTGRES = False
    
try:
    import sqlite3
    TEST_SQLITE = True
except ImportError:
    TEST_SQLITE = False

TEST_MYSQL = True
try:
    import MySQLdb
    mysql_module = MySQLdb
    mysql_errors = (mysql_module.OperationalError, 
                    mysql_module.ProgrammingError)
except ImportError:
    try:
        import pymysql
        mysql_module = pymysql
        mysql_errors = (mysql_module.OperationalError, 
                        mysql_module.ProgrammingError,
                        mysql_module.err.InternalError)
    except ImportError:
        mysql_errors = ()
        TEST_MYSQL = False
        
try:
    import cx_Oracle
    oracle_errors = (cx_Oracle.DatabaseError,)
    TEST_ORACLE = True
except ImportError:
    oracle_errors = ()
    TEST_ORACLE = False

def procedure_test(procedure_name, arguments_count, returns):
    
    '''Decorator for procedure tests, that simplifies testing whether procedure
    with given name is available, whether it has given number of arguments
    and returns given value.'''
    
    def decorator(test):
        def result(self):
            procedure = self.db.procedures[self.case(procedure_name)]
            self.assertEqual(len(procedure.arguments), arguments_count)
            self.assertEqual(procedure.returns, 
                             None if returns is None else self.case(returns))
            test(self, procedure)
        # this fancy stuff is required for unittest to detect test method
        result.__name__ = test.__name__
        return result
    return decorator

class AbstractDatabaseTestCase(metaclass=ABCMeta):
    
    DEFAULT_INTEGER_TYPE_NAME = 'integer'
    PRIMARY_KEY_IS_NOT_NULL = True
    CREATES_INDEX_FOR_PRIMARY_KEY = True
    CREATES_INDEX_FOR_REFERENCES = False
    HAS_USABLE_INDEX_NAMES = True
    USES_CASE_SENSITIVE_IDENTIFIERS = True
    USES_PROCEDURES = True
    case = lambda Class, string: string.lower()
    
    TABLES = OrderedDict((
        ('one_column', '''
CREATE TABLE one_column (col varchar(800))'''),
        ('reserved_word_column', '''
CREATE TABLE reserved_word_column ("column" varchar(800))'''),
        ('one_unique_column', '''
CREATE TABLE one_unique_column (col integer UNIQUE)'''),
        ('column_with_default', '''
CREATE TABLE column_with_default (def_col integer default 5)'''),
        ('two_columns_unique', '''
CREATE TABLE two_columns_unique (
    col1 integer,
    col2 varchar(80),
    UNIQUE(col1, col2)
)'''),
        ('primary_key_only', '''
CREATE TABLE primary_key_only (id integer primary key)
'''),
        ('two_double_uniques', '''
CREATE TABLE two_double_uniques (
    x integer, 
    y integer, 
    z integer, 
    unique(x, y),
    unique(x, z)
)'''),
    ('reference_one_unique_column', '''
CREATE TABLE reference_one_unique_column (
    ref_one_column integer REFERENCES one_unique_column(col)
)'''),
    ('reference_two_tables', '''
CREATE TABLE reference_two_tables (
    ref1 integer REFERENCES one_unique_column(col),
    ref2 integer REFERENCES primary_key_only(id)
)'''),
    ('SoMe_TaBlE', '''
CREATE TABLE "SoMe_TaBlE" (
    col integer
)'''),
    ('some_table', 
'''CREATE TABLE some_table (col int)'''),
    ('case_sensitive_column', '''
CREATE TABLE case_sensitive_column (
    "SoMe_CoLuMn" InTeGeR
)'''))
)
    
    VIEWS = {
        'one_column_view': '''
CREATE VIEW one_column_view AS SELECT col FROM one_column''',
        'CASE_sensitive_VIEW': '''
CREATE VIEW "CASE_sensitive_VIEW" AS SELECT col FROM one_column'''
    }
    
    INDICES = {
        'one_column_index': '''CREATE INDEX one_column_index ON one_column(col)'''
    }
    
    TRIGGERS = {
        'before_insert_trigger': '''
CREATE TRIGGER before_insert_trigger BEFORE INSERT ON one_column
FOR EACH ROW BEGIN INSERT INTO one_column values(3); END''',
        'after_delete_trigger': '''
CREATE TRIGGER after_delete_trigger AFTER DELETE ON one_column
FOR EACH ROW BEGIN INSERT INTO one_column values(3); END'''
    }
    
    PROCEDURES = {}

    # TODO: this should be turned into setUpClass, when Ubuntu ships python 3.2
    def setUp(self):
        try:
            self._add_operation(self.TABLES.values())
            self._add_operation(self.VIEWS.values())
            if self.USES_PROCEDURES:
                self._add_operation(self.PROCEDURES.values())
            self._add_operation(self.INDICES.values())
            self._add_triggers()
        except self.DATABASE_ERRORS as e:
            self.tearDown()
            raise
        
    # TODO: this should be turned into tearDownClass, when Ubuntu ships python 3.2                
    def tearDown(self):
        self._drop_triggers()
        self._drop_operation('INDEX', self.INDICES)
        if self.USES_PROCEDURES:
            self._drop_procedures();
        self._drop_operation('VIEW', self.VIEWS)
        self._drop_operation('TABLE', reversed(tuple(self.TABLES.keys())))

    # new assertions
    
    def assertColumns(self, table, values):
        names = set((self.case(name) for name, _, _ in values))
        self.assertEqual(set(table.columns.keys()), names)
        for name, type, not_null in values:
            column = table.columns[self.case(name)]
            if column.type != self.case(type):
                msg = "Table: %s, column: %s, %s != %s" % \
                      (table.name, column.name, column.type, 
                       self.case(type))
                raise AssertionError(msg)
            if column.not_null != not_null:
                msg = "Table: %s, column: %s, %s != %s" % \
                      (table.name, column.name, column.not_null, not_null)
                raise AssertionError(msg)
                
    def assertIndex(self, table, name, columns):
        index = table.indices[name]
        self.assertEqual(index.columns, columns)
        
    def assertIndices(self, table, index_names):
        names = set([self.case(name) for name in index_names])
        self.assertEqual(set(table.indices.keys()), names)
        self.assertEqual(set([index.name for index in table.indices.values()]),
                         names)
                
    def assertArguments(self, procedure, values):
        for name, type in values:
            argument = procedure.arguments[self.case(name)]
            if argument.type != type:
                msg = "Procedure: %s, argument: %s, %s != %s" % \
                      (procedure.name, argument.name, argument.type, type)
                raise AssertionError(msg)

    # table tests

    def test_table_names(self):
        if self.USES_CASE_SENSITIVE_IDENTIFIERS:
            test_names = set(self.TABLES.keys())
        else:
            test_names = set([self.case(name) 
                              for name in self.TABLES.keys()])
        names = set([table.name for table in self.db.tables.values()])
        self.assertEqual(names, test_names)

    def test_table_one_column(self):
        table = self.db.tables[self.case('one_column')]
        self.assertEqual(table.database, self.db)
        column = self.case('col')
        self.assertEqual(set(table.columns.keys()), set([column]))
        self.assertEqual(table.columns[column].type, 
                         self.case('varchar(800)'))
        self.assertEqual(table.columns[column].not_null, False)
        
    def test_table_one_unique_column(self):
        # TODO: use assertColumns
        table = self.db.tables[self.case('one_unique_column')]
        self.assertEqual(set(table.columns.keys()), set([self.case('col')]))
        self.assertEqual(table.columns[self.case('col')].type, 
                         self.case(self.DEFAULT_INTEGER_TYPE_NAME))
        self.assertEqual(table.columns[self.case('col')].not_null, False)
        
    def test_table_column_with_default(self):
        # TODO: user assertColumns
        table = self.db.tables[self.case('column_with_default')]
        self.assertEqual(set(table.columns.keys()), set([self.case('def_col')]))
        self.assertEqual(table.columns[self.case('def_col')].type,
                         self.case(self.DEFAULT_INTEGER_TYPE_NAME))
        self.assertEqual(table.columns[self.case('def_col')].not_null, False)
        self.assertEqual(table.columns[self.case('def_col')].default, 5)
        
    def test_table_two_columns_unique(self):
        table = self.db.tables[self.case('two_columns_unique')]
        values = (('col1', self.DEFAULT_INTEGER_TYPE_NAME, False), 
                  ('col2', 'varchar(80)', False))
        self.assertColumns(table, values)

    def test_table_primary_key_only(self):
        table = self.db.tables[self.case('primary_key_only')]
        values = (('id', self.DEFAULT_INTEGER_TYPE_NAME, 
                   self.PRIMARY_KEY_IS_NOT_NULL),)
        self.assertColumns(table, values)
        
    def test_table_two_double_uniques(self):
        table = self.db.tables[self.case('two_double_uniques')]
        values = (('x', self.DEFAULT_INTEGER_TYPE_NAME, False),
                  ('y', self.DEFAULT_INTEGER_TYPE_NAME, False),
                  ('z', self.DEFAULT_INTEGER_TYPE_NAME, False))
        self.assertColumns(table, values)
    
    def test_table_reference_one_unique_column(self):
        table = self.db.tables[self.case('reference_one_unique_column')]
        self.assertEqual(len(table.foreign_keys), 1)
        fk = table.foreign_keys[0]
        self.assertEqual(fk.columns, [self.case('ref_one_column')])
        self.assertEqual(fk.referenced_table, self.case('one_unique_column'))
        self.assertEqual(fk.referenced_columns, [self.case('col')])
        
    def test_table_reference_two_tables(self):
        table = self.db.tables[self.case('reference_two_tables')]
        self.assertEqual(len(table.foreign_keys), 2)
        
    def test_table_SoMe_TaBlE(self):
        if self.USES_CASE_SENSITIVE_IDENTIFIERS:
            table = self.db.tables['SoMe_TaBlE']
        else:
            table = self.db.tables[self.case('some_table')]
    
    def test_table_case_sensitive_column(self):
        table = self.db.tables[self.case('case_sensitive_column')]
        if self.USES_CASE_SENSITIVE_IDENTIFIERS:
            column = table.columns['SoMe_CoLuMn']
            self.assertEqual(column.name, 'SoMe_CoLuMn')
        else:
            column = table.columns[self.case('some_column')]
            self.assertEqual(column.name, self.case('some_column'))
        self.assertEqual(column.type, self.DEFAULT_INTEGER_TYPE_NAME)
        
    def test_drop(self):
        name = self.case('two_columns_unique')
        table = self.db.tables[name]
        table.drop()
        self.assertTrue(name not in self.db.tables)
        self.db.refresh()
        self.assertTrue(name not in self.db.tables)
            
    # view tests

    def test_view_names(self):
        self.assertEqual(set([view.name for view in self.db.views.values()]), 
                         set(self.VIEWS.keys()))
        
    def test_view_one_column_view(self):
        view = self.db.views[self.case('one_column_view')]
        self.assertEqual(view.database, self.db)
        self.assertEqual(set(view.columns.keys()), set([self.case('col')]))
                         
    def test_view_case_sensitive_view(self):
        view = self.db.views['CASE_sensitive_VIEW']
        self.assertEqual(set(view.columns.keys()), set([self.case('col')]))

    # trigger tests
    
    def test_trigger_names(self):
        self.assertEqual(set(self.db.triggers.keys()), self.TRIGGERS.keys())
        
    def test_trigger_before_insert_trigger(self):
        trigger = self.db.triggers[self.case('before_insert_trigger')]
        self.assertEqual(trigger.database, self.db)        
        self.assertEqual(trigger.table, self.case('one_column'))
        self.assertEqual(trigger.when, Trigger.BEFORE)
        self.assertEqual(trigger.event, Trigger.INSERT)

    # index tests
    
    def test_index_names(self):
        indices = {self.case('one_column: one_column_index'), 
                   self.index_name('two_double_uniques', 'x', 'y', count=1),
                   self.index_name('two_double_uniques', 'x', 'z', count=2),
                   self.index_name('one_unique_column', 'col'),
                   self.index_name('two_columns_unique', 'col1', 'col2')}
        if self.CREATES_INDEX_FOR_PRIMARY_KEY:
            indices.add(self.pkey_index_name('primary_key_only', 'id'))
        if self.HAS_USABLE_INDEX_NAMES:
            self.assertEqual(set(self.db.indices.keys()), indices)
        else:
            self.assertEqual(len(self.db.indices.keys()), len(indices))
            
    def test_index_one_unique_column(self):
        if not self.HAS_USABLE_INDEX_NAMES:
            return
        index = self.db.indices[self.index_name('one_unique_column', 'col')]
        self.assertTrue(index.is_unique)
        
    def test_index_one_column_index(self):
        index = self.db.indices[self.case('one_column: one_column_index')]
        self.assertEqual(index.database, self.db)
        self.assertEqual(index.columns, ('col',))
        self.assertFalse(index.is_unique)
        
    # procedure tests
    
    def test_procedure_names(self):
        self.assertEqual(set([key for key in self.db.procedures.keys()]), 
                         set(self.PROCEDURES.keys()))
        self.assertEqual(set([procedure.name 
                              for procedure in self.db.procedures.values()]), 
                         set(self.PROCEDURES.keys()))        

    # other tests

    def test_supports_procedures(self):
        self.assertTrue(self.db.supports_stored_procedures())

    def test_case_sensitivity(self):
        self.assertEqual(self.db.case_sensitivity, 
                         constants.CASE_SENSITIVE_QUOTED)
        
    @abstractmethod
    def index_name(self, table_name, *columns, count=None):
        pass
    
    @abstractmethod
    def pkey_index_name(self, table_name, *columns):
        pass
                         
    # protected:
    
    @abstractmethod
    def _get_connection(Class):
        pass
    
    @classmethod
    def _run_using_cursor(Class, function):
        conn = Class._get_connection()
        cursor = conn.cursor()
        function(Class, cursor)
        conn.commit()
        cursor.close()
        conn.close()
    
    @classmethod
    def _add_operation(Class, sqls):
        def function(Class, cursor):
            for sql in sqls:
                sql = Class.substitute_quote_char(sql)
                cursor.execute(sql)
        Class._run_using_cursor(function)
        
    @classmethod    
    def _drop_operation(Class, type, names):
        conn = Class._get_connection()
        cursor = conn.cursor()
        for name in names:
            sql = Class.substitute_quote_char('DROP %s "%s"' % (type, name))
            try:
                cursor.execute(sql);
                conn.commit()
            except Class.DATABASE_ERRORS as e:
                # maybe it was dropped on not created, we need to try drop other
                conn = Class._get_connection()
                cursor = conn.cursor()
        cursor.close()
        conn.close()
        
    @classmethod
    def _drop_procedures(Class):
        def function(Class, cursor):
            for name in Class.PROCEDURES.keys():
                try:
                    cursor.execute('DROP FUNCTION %s' % name);
                except Class.DATABASE_ERRORS as e:
                    # maybe it is a PROCEDURE, not a function
                    try:
                        cursor.execute('DROP PROCEDURE %s' % name)
                    except Class.DATABASE_ERRORS as e:
                        # maybe it was not created, we need to try drop other
                        pass 
        Class._run_using_cursor(function)              

    def _add_triggers(self):
        self._add_operation(self.TRIGGERS.values())
        
    def _drop_triggers(self):
        self._drop_operation('TRIGGER', self.TRIGGERS)
        
    @staticmethod
    def substitute_quote_char(string):
        return string

    @classmethod
    def case(Class, string):
        return string.lower()


@skipUnless(TEST_POSTGRES, 'Failed to import psycopg2 module.')
class PostgresTestCase(AbstractDatabaseTestCase, TestCase):
    
    DBNAME = 'fathom'
    USER = 'fathom'
    DATABASE_ERRORS = postgres_errors
    
    TABLES = AbstractDatabaseTestCase.TABLES.copy()
    TABLES['empty'] = '''CREATE TABLE empty()'''

    PROCEDURES = AbstractDatabaseTestCase.PROCEDURES.copy()
    PROCEDURES['fib(int4)'] = '''
CREATE OR REPLACE FUNCTION fib (fib_for integer) RETURNS integer AS $$
    BEGIN
        IF fib_for < 2 THEN
            RETURN fib_for;
        END IF;
        RETURN fib(fib_for - 2) + fib(fib_for - 1);
    END;
$$ LANGUAGE plpgsql;'''
    PROCEDURES['fib(int2)'] = '''
CREATE OR REPLACE FUNCTION fib (fib_for int2) RETURNS integer AS $$
    BEGIN
        IF fib_for < 2 THEN
            RETURN fib_for;
        END IF;
        RETURN fib(fib_for - 2) + fib(fib_for - 1);
    END;
$$ LANGUAGE plpgsql;'''
    PROCEDURES['void_function()'] = '''
CREATE OR REPLACE FUNCTION void_function () RETURNS VOID AS $$
    BEGIN
    END;
$$ LANGUAGE plpgsql;'''
    PROCEDURES['before_insert_trigger_function()'] = '''
CREATE FUNCTION before_insert_trigger_function() RETURNS trigger AS $$
    BEGIN
        IF NEW.column < 3 THEN
        END IF;
    END;
$$ LANGUAGE plpgsql'''
    PROCEDURES['after_delete_trigger_function()'] = '''
CREATE FUNCTION after_delete_trigger_function() RETURNS trigger AS $$
    BEGIN
        IF NEW.column < 3 THEN
        END IF;
    END;
$$ LANGUAGE plpgsql'''
    PROCEDURES['before_update_trigger_function()'] = '''
CREATE FUNCTION before_update_trigger_function() RETURNS trigger AS $$
    BEGIN
        IF NEW.column < 3 THEN
        END IF;
    END;
$$ LANGUAGE plpgsql'''

    # tests for get_accessing_procedures
    
    PROCEDURES['get_accessing_procedures_1()'] = '''
CREATE FUNCTION get_accessing_procedures_1() RETURNS VOID AS $$
    BEGIN
        SELECT * FROM one_column;
    END;
$$ LANGUAGE plpgsql'''

    PROCEDURES['get_accessing_procedures_2()'] = '''
CREATE FUNCTION get_accessing_procedures_2() RETURNS VOID AS $$
    BEGIN
        SELECT * FROM some_table;
    END;
$$ LANGUAGE plpgsql'''

    PROCEDURES['get_accessing_procedures_3()'] = '''
CREATE FUNCTION get_accessing_procedures_3() RETURNS VOID AS $$
    BEGIN
        SELECT * FROM soMe_TABLE;
    END;    
$$ LANGUAGE plpgsql'''

    PROCEDURES['get_accessing_procedures_4()'] = '''
CREATE FUNCTION get_accessing_procedures_4() RETURNS VOID AS $$
    BEGIN
        SELECT * FROM "SoMe_TaBlE";
    END;
$$ LANGUAGE plpgsql'''

    PROCEDURES['get_accessing_procedures_5()'] = '''
CREATE FUNCTION get_accessing_procedures_5() RETURNS VOID AS $$
    BEGIN
        SELECT * FROM "some_TABLE";
    END;
$$ LANGUAGE plpgsql'''

    # postgresql defines only subset of sql CREATE TRIGGER statement, that's
    # why keep separate dictionary of trigger fixtures and also must keep
    # table names to drop trigger properly
    # also postgres identifies a trigger by a pair <trigger_name>, <table>
    # that's why we must hold postgres trigger names differently
    TRIGGERS = {'before_insert_trigger(one_column)': ('''
CREATE TRIGGER before_insert_trigger BEFORE INSERT ON one_column
EXECUTE PROCEDURE before_insert_trigger_function()''', 'one_column'),
                'before_insert_trigger(one_unique_column)': ('''
CREATE TRIGGER before_insert_trigger BEFORE INSERT ON one_unique_column
EXECUTE PROCEDURE before_insert_trigger_function()''', 'one_unique_column'),
                'after_delete_trigger(one_unique_column)': ('''
CREATE TRIGGER after_delete_trigger AFTER DELETE ON one_unique_column
EXECUTE PROCEDURE after_delete_trigger_function()''', 'one_unique_column'),
                'before_update_trigger(one_unique_column)': ('''
CREATE TRIGGER before_update_trigger BEFORE UPDATE ON one_unique_column
EXECUTE PROCEDURE before_update_trigger_function()''', 'one_unique_column')
    }

    def setUp(self):
        AbstractDatabaseTestCase.setUp(self)
        args = self.DBNAME, self.USER
        self.db = get_postgresql_database('dbname=%s user=%s' % args)
            
    # postgresql specific tests
            
    def test_table_empty(self):
        table = self.db.tables['empty']
        self.assertEqual(set(table.columns.keys()), set())

    @procedure_test('fib(int4)', 1, 'int4')
    def test_fib_integer(self, procedure):
        self.assertEqual(procedure.database, self.db)
        self.assertArguments(procedure, [('fib_for', 'int4')])
        self.assertEqual(procedure.sql, '''
    BEGIN
        IF fib_for < 2 THEN
            RETURN fib_for;
        END IF;
        RETURN fib(fib_for - 2) + fib(fib_for - 1);
    END;
''')

    @procedure_test('void_function()', 0, None)
    def test_void_function(self, procedure):
        self.assertArguments(procedure, [])

    # trigger tests
    
    def test_trigger_before_insert_trigger(self):
        trigger = self.db.triggers['before_insert_trigger(one_column)']
        self.assertEqual(trigger.table, 'one_column')
        self.assertEqual(trigger.when, Trigger.BEFORE)
        self.assertEqual(trigger.event, Trigger.INSERT)
        
    def test_trigger_after_delete_trigger(self):
        trigger = self.db.triggers['after_delete_trigger(one_unique_column)']
        self.assertEqual(trigger.table, 'one_unique_column')
        self.assertEqual(trigger.when, Trigger.AFTER)
        self.assertEqual(trigger.event, Trigger.DELETE)

    def test_trigger_before_update_trigger(self):
        trigger = self.db.triggers['before_update_trigger(one_unique_column)']
        self.assertEqual(trigger.table, 'one_unique_column')
        self.assertEqual(trigger.when, Trigger.BEFORE)
        self.assertEqual(trigger.event, Trigger.UPDATE)

    # postgresql internal methods required for testing
            
    def index_name(self, table_name, *columns, count=1):
        # different versions of postgres use different kinds of index names
        if self.db.version >= (9, 0, 0):
            return self.index_name9(table_name, *columns)
        else:
            return self.index_name8(table_name, *columns, count=count)
            
    def index_name9(self, table_name, *columns, count=1):
        if len(columns):
            columns = '_'.join((column for column in columns))
            name = '%s: %s_%s_key' % (table_name, table_name, columns)
        else:
            name = '%s: %s_column_key' % (table_name, table_name)
        return name
                    
    def index_name8(self, table_name, *columns, count=1):
        if len(columns):
            name = '%s: %s_%s_key' % (table_name, table_name, columns[0])
        else:
            name = '%s: %s_column_key' % (table_name, table_name)
        if count > 1:
            # postgres 8.* has curios way of indexing index names; first
            # has no suffix, the following add count suffix beginning with 1
            name += str(count - 1)
        return name
            
    def pkey_index_name(self, table_name, *columns):
        return '%s: %s_pkey' % (table_name, table_name)
        
    @classmethod
    def _get_connection(Class):
        args = Class.DBNAME, Class.USER
        return psycopg2.connect('dbname=%s user=%s' % args)
        
    def _add_triggers(self):
        sqls = [trigger for trigger, _ in self.TRIGGERS.values()]
        self._add_operation(sqls)

    def _drop_triggers(self):
        def function(Class, cursor):
            for name, (_, table) in Class.TRIGGERS.items():
                name = name.split('(')[0]
                try:
                    cursor.execute('DROP TRIGGER %s ON %s' % (name, table));
                except Class.DATABASE_ERRORS as e:
                    pass # maybe it was not created, we need to try drop other
        self._run_using_cursor(function)


@skipUnless(TEST_MYSQL, 'Failed to import MySQLDb or PyMySQL module.')
class MySqlTestCase(AbstractDatabaseTestCase, TestCase):
    
    DBNAME = 'fathom'
    USER = 'fathom'
    DATABASE_ERRORS = mysql_errors

    DEFAULT_INTEGER_TYPE_NAME = 'int'
    CREATES_INDEX_FOR_REFERENCES = True

    TABLES = AbstractDatabaseTestCase.TABLES.copy()
    TABLES['one_unique_column'] = '''
CREATE TABLE one_unique_column (col integer UNIQUE) ENGINE = INNODB'''
    TABLES['primary_key_only'] = '''
CREATE TABLE primary_key_only (id integer primary key) ENGINE = INNODB
'''
    TABLES['reference_one_unique_column'] = '''
CREATE TABLE reference_one_unique_column (
    ref_one_column integer,
    FOREIGN KEY (ref_one_column) REFERENCES one_unique_column(col)
) ENGINE = INNODB'''
    TABLES['reference_two_tables'] = '''
CREATE TABLE reference_two_tables (
    ref1 integer,
    ref2 integer,
    FOREIGN KEY (ref1) REFERENCES one_unique_column(col),
    FOREIGN KEY (ref2) REFERENCES primary_key_only(id)
) ENGINE = INNODB'''

    PROCEDURES = AbstractDatabaseTestCase.PROCEDURES.copy()
    PROCEDURES['foo_double'] = '''
CREATE FUNCTION foo_double (value int4)
    RETURNS INTEGER
        RETURN 2 * value;
'''
    PROCEDURES['simple_proc'] = '''
CREATE PROCEDURE simple_proc()
BEGIN
END;
'''
    PROCEDURES['get_accessing_procedures_1'] = '''
CREATE PROCEDURE get_accessing_procedures_1()
    BEGIN
        SELECT * FROM one_column;
    END'''
    
    PROCEDURES['get_accessing_procedures_2'] = '''
CREATE PROCEDURE get_accessing_procedures_2()
    BEGIN
        SELECT * FROM ONE_column;
    END'''
    
    def setUp(self):
        AbstractDatabaseTestCase.setUp(self)
        args = self.DBNAME, self.USER
        self.db = get_mysql_database(user=self.USER, db=self.DBNAME)
        
    # tests
    
    def test_case_sensitivity(self):
        self.assertEqual(self.db.case_sensitivity, constants.CASE_SENSITIVE)
    
    def test_foo_double(self):
        procedure = self.db.procedures[self.case('foo_double')]
        if self.db.version >= (5, 5):
            self.assertEqual(len(procedure.arguments), 1)
            self.assertArguments(procedure, [('value', 'int')])
        else:
            self.assertEqual(len(procedure.arguments), 0)
        self.assertEqual(procedure.returns, 'integer')
        self.assertEqual(procedure.database, self.db)
        self.assertEqual(procedure.sql, 'RETURN 2 * value')

    @procedure_test('simple_proc', 0, None)
    def test_simple_proc(self, procedure):
        self.assertEqual(procedure.database, self.db)
        self.assertEqual(procedure.sql, 'BEGIN\nEND')

    def test_index_names(self):
        indices = {self.case('one_column: one_column_index'), 
                   self.index_name('two_double_uniques', 'x', 'y', count=1),
                   self.index_name('two_double_uniques', 'x', 'z', count=2),
                   self.index_name('one_unique_column', 'col'),
                   self.index_name('two_columns_unique', 'col1', 'col2')}
        if self.CREATES_INDEX_FOR_PRIMARY_KEY:
            indices.add(self.pkey_index_name('primary_key_only', 'id'))
        indices.add(self.ref_index_name('reference_one_unique_column',
                                        "ref_one_column"))
        indices.add(self.ref_index_name('reference_two_tables', 'ref1'))
        indices.add(self.ref_index_name('reference_two_tables', 'ref2'))
        self.assertEqual(set(self.db.indices.keys()), indices)
    
    # mysql internal methods required for testing

    def index_name(self, table_name, *columns, count=1):
        if count == 1:
            return '%s: %s' % (table_name, columns[0])
        else:
            return '%s: %s_%d' % (table_name, columns[0], count)

    def pkey_index_name(self, table_name, *columns):
        return '%s: PRIMARY' % table_name
        
    def ref_index_name(self, table_name, column, *columns):
        return '%s: %s' % (table_name, column)
        
    @classmethod
    def _get_connection(Class):
        return mysql_module.connect(user=Class.USER, db=Class.DBNAME)

    @classmethod
    def substitute_quote_char(Class, string):
        return string.replace('"', '`')


@skipUnless(TEST_ORACLE, 'Failed to import cx_Oracle module.')
class OracleTestCase(AbstractDatabaseTestCase, TestCase):
    
    # watch out when running those tests, cx_Oracle likes to segfault

    USER = 'fathom'
    PASSWORD = 'fathom'
    
    DATABASE_ERRORS = oracle_errors
    DEFAULT_INTEGER_TYPE_NAME = 'NUMBER'
    HAS_USABLE_INDEX_NAMES = False
    
    TABLES = {}
    for key, value in AbstractDatabaseTestCase.TABLES.items():
        name = key.upper() if key.lower() == key else key
        TABLES[name] = value
    # oracle doesn't accept reserved words as identifiers at all
    TABLES.pop('reserved_word_column'.upper())
        
    TRIGGERS = {}
    for key, value in AbstractDatabaseTestCase.TRIGGERS.items():
        name = key.upper() if key.lower() == key else key
        TRIGGERS[name] = value
        
    INDICES = {}
    for key, value in AbstractDatabaseTestCase.INDICES.items():
        name = key.upper() if key.lower() == key else key
        INDICES[name] = value
    
    VIEWS = {}
    for key, value in AbstractDatabaseTestCase.VIEWS.items():
        name = key.upper() if key.lower() == key else key
        VIEWS[name] = value
                
    PROCEDURES = {}
    PROCEDURES['FOO_DOUBLE'] = '''
CREATE FUNCTION foo_double 
    RETURN VARCHAR2 IS
    BEGIN 
        RETURN 'dd'; 
    END;
'''
    PROCEDURES['SIMPLE_PROC'] = '''
CREATE PROCEDURE simple_proc(suchar IN OUT VARCHAR2) IS
    BEGIN
        suchar := 'f';
    END;
'''

    def setUp(self):
        AbstractDatabaseTestCase.setUp(self)
        self.db = get_oracle_database(self.USER, self.PASSWORD)

    def test_case_sensitivity(self):
        self.assertEqual(self.db.case_sensitivity, 
                         constants.CASE_SENSITIVE_QUOTED)
        
    # procedure tests
    
    @procedure_test('foo_double', 0, 'varchar2')
    def test_procedure_foo_double(self, procedure):
        self.assertEqual(procedure.database, self.db)

    @procedure_test('simple_proc', 1, None)
    def test_procedure_simple_proc(self, procedure):
        self.assertEqual(procedure.database, self.db)

    def index_name(self, table_name, *columns, count=1):
        # these index names are not generated this way, but we need to keep 
        # those names somehow
        return 'index_%s_' % table_name + '_'.join(columns)
        
    def pkey_index_name(self, table_name, *columns):
        return self.index_name(table_name, *columns)
        

    def case(self, string):
        return string.upper()

    @classmethod
    def _get_connection(Class):
        return cx_Oracle.connect('%s/%s' % (Class.USER, Class.PASSWORD))


@skipUnless(TEST_SQLITE, 'Failed to import sqlite3 module.')
class SqliteTestCase(AbstractDatabaseTestCase, TestCase):
    
    PATH = 'fathom.db3'
    DATABASE_ERRORS = (sqlite3.OperationalError, sqlite3.ProgrammingError)

    PRIMARY_KEY_IS_NOT_NULL = False
    CREATES_INDEX_FOR_PRIMARY_KEY = False
    USES_CASE_SENSITIVE_IDENTIFIERS = False
    USES_PROCEDURES = False
    
    TABLES = AbstractDatabaseTestCase.TABLES.copy()
    del TABLES['some_table']
    
    def setUp(self):
        AbstractDatabaseTestCase.setUp(self)
        self.db = get_sqlite3_database(self.PATH)

    # sqlite specific tests

    def test_supports_procedures(self):
        self.assertFalse(self.db.supports_stored_procedures())
        
    def test_case_sensitivity(self):
        self.assertEqual(self.db.case_sensitivity, constants.CASE_INSENSITIVE)

    def test_index_names(self):
        indices = {self.case('one_column_index'), 
                   self.index_name('two_double_uniques', 'x', 'y', count=1),
                   self.index_name('two_double_uniques', 'x', 'z', count=2),
                   self.index_name('one_unique_column', 'col'),
                   self.index_name('two_columns_unique', 'col1', 'col2')}
        if self.CREATES_INDEX_FOR_PRIMARY_KEY:
            indices.add(self.pkey_index_name('primary_key_only', 'id'))
        if self.HAS_USABLE_INDEX_NAMES:
            self.assertEqual(set(self.db.indices.keys()), indices)
        else:
            self.assertEqual(len(self.db.indices.keys()), len(indices))

    def test_index_one_column_index(self):
        index = self.db.indices[self.case('one_column_index')]
        self.assertFalse(index.is_unique)
        
    # sqlite internal methods required for testing

    def index_name(self, table_name, *columns, count=1):
        return 'sqlite_autoindex_%s_%d' % (table_name, count)
    
    def pkey_index_name(self, table_name, *columns):
        return self.index_name(table_name, columns)

    @classmethod
    def _get_connection(Class):
        return sqlite3.connect(Class.PATH)


if __name__ == "__main__":
    main()
