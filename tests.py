#!/usr/bin/python3

from abc import ABCMeta, abstractmethod
from unittest import TestCase, main, skipUnless
from collections import namedtuple, OrderedDict

from fathom import (get_sqlite3_database, get_postgresql_database, 
                    get_mysql_database, get_oracle_database, get_database, 
                    get_database_type, FathomError)

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
    TEST_ORACLE = True
except ImportError:
    TEST_ORACLE = False

class AbstractDatabaseTestCase(metaclass=ABCMeta):
    
    DEFAULT_INTEGER_TYPE_NAME = 'integer'
    PRIMARY_KEY_IS_NOT_NULL = True
    CREATES_INDEX_FOR_PRIMARY_KEY = True
    
    TABLES = OrderedDict((
        ('one_column', '''
CREATE TABLE one_column ("column" varchar(800))'''),
        ('one_unique_column', '''
CREATE TABLE one_unique_column ("column" integer UNIQUE)'''),
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
    ref_one_column integer REFERENCES one_unique_column("column")
)'''),
    ('reference_two_tables', '''
CREATE TABLE reference_two_tables (
    ref1 integer REFERENCES one_unique_column("column"),
    ref2 integer REFERENCES primary_key_only(id)
)''')
))
    
    VIEWS = {
        'one_column_view': '''CREATE VIEW one_column_view AS SELECT "column" FROM one_column;''',
    }
    
    INDICES = {
        'one_column_index': '''CREATE INDEX one_column_index ON one_column("column")'''
    }
    
    TRIGGERS = {
        'before_insert_trigger': '''
CREATE TRIGGER before_insert_trigger BEFORE INSERT ON one_column
FOR EACH ROW BEGIN INSERT INTO one_column values(3); END'''
    }

    # TODO: this should be turned into setUpClass, when Ubuntu ships python 3.2
    def setUp(self):
        try:
            self._add_operation(self.TABLES.values())
            self._add_operation(self.VIEWS.values())
            self._add_operation(self.INDICES.values())
            self._add_triggers()
        except self.DATABASE_ERRORS as e:
            self.tearDown()
            raise
        
    # TODO: this should be turned into tearDownClass, when Ubuntu ships python 3.2
    def tearDown(self):
        self._drop_triggers()
        self._drop_operation('INDEX', self.INDICES)
        self._drop_operation('VIEW', self.VIEWS)
        self._drop_operation('TABLE', reversed(tuple(self.TABLES.keys())))

    # new assertions
    
    def assertColumns(self, table, values):
        names = set((name for name, _, _ in values))
        self.assertEqual(set(table.columns.keys()), names)
        for name, type, not_null in values:
            column = table.columns[name]
            if column.type != type:
                msg = "Table: %s, column: %s, %s != %s" % \
                      (table.name, column.name, column.type, type)
                raise AssertionError(msg)
            if column.not_null != not_null:
                msg = "Table: %s, column: %s, %s != %s" % \
                      (table.name, column.name, column.not_null, not_null)
                raise AssertionError(msg)
                
    def assertIndex(self, table, name, columns):
        index = table.indices[name]
        self.assertEqual(index.columns, columns)
        
    def assertIndices(self, table, index_names):
        names = set(index_names)
        self.assertEqual(set(table.indices.keys()), names)
        self.assertEqual(set([index.name for index in table.indices.values()]),
                         names)
                
    def assertArguments(self, procedure, values):
        for name, type in values:
            argument = procedure.arguments[name]
            if argument.type != type:
                msg = "Procedure: %s, argument: %s, %s != %s" % \
                      (procedure.name, argument.name, argument.type, type)
                raise AssertionError(msg)

    # table tests

    def test_table_names(self):
        self.assertEqual(set([table.name for table in self.db.tables.values()]), 
                         set(self.TABLES.keys()))

    def test_table_one_column(self):
        table = self.db.tables['one_column']
        self.assertEqual(set(table.columns.keys()), set(['column']))
        self.assertEqual(table.columns['column'].type, 'varchar(800)')
        self.assertEqual(table.columns['column'].not_null, False)
        self.assertEqual(set(table.indices.keys()), set(['one_column_index']))
        
    def test_table_one_unique_column(self):
        table = self.db.tables['one_unique_column']
        self.assertEqual(set(table.columns.keys()), set(['column']))
        self.assertEqual(table.columns['column'].type, 
                         self.DEFAULT_INTEGER_TYPE_NAME)
        self.assertEqual(table.columns['column'].not_null, False)
        index_names = [self.index_name('one_unique_column', 'column')]
        self.assertEqual(set(table.indices.keys()), set(index_names))
        self.assertIndex(table, index_names[0], ('column',))
        
    def test_table_column_with_default(self):
        table = self.db.tables['column_with_default']
        self.assertEqual(set(table.columns.keys()), set(['def_col']))
        self.assertEqual(table.columns['def_col'].type,
                         self.DEFAULT_INTEGER_TYPE_NAME)
        self.assertEqual(table.columns['def_col'].not_null, False)
        self.assertEqual(table.columns['def_col'].default, 5)
        
    def test_table_two_columns_unique(self):
        table = self.db.tables['two_columns_unique']
        values = (('col1', self.DEFAULT_INTEGER_TYPE_NAME, False), 
                  ('col2', 'varchar(80)', False))
        self.assertColumns(table, values)
        index_names = [self.index_name('two_columns_unique', 
                                            'col1', 'col2')]
        self.assertIndices(table, index_names)
        self.assertIndex(table, index_names[0], ('col1', 'col2'))

    def test_table_primary_key_only(self):
        table = self.db.tables['primary_key_only']
        values = (('id', self.DEFAULT_INTEGER_TYPE_NAME, 
                   self.PRIMARY_KEY_IS_NOT_NULL),)
        self.assertColumns(table, values)
        if self.CREATES_INDEX_FOR_PRIMARY_KEY:
            index_names = [self.pkey_index_name('primary_key_only', 'id')]
        else:
            index_names = []
        self.assertEqual(set(table.indices.keys()), set(index_names))
        if self.CREATES_INDEX_FOR_PRIMARY_KEY:
            self.assertIndex(table, index_names[0], ('id',))
        
    def test_table_two_double_uniques(self):
        table = self.db.tables['two_double_uniques']
        values = (('x', self.DEFAULT_INTEGER_TYPE_NAME, False),
                  ('y', self.DEFAULT_INTEGER_TYPE_NAME, False),
                  ('z', self.DEFAULT_INTEGER_TYPE_NAME, False))
        self.assertColumns(table, values)
        index_names = [self.index_name('two_double_uniques', 'x', 'y', count=1),
                       self.index_name('two_double_uniques', 'x', 'z', count=2)]
        self.assertEqual(set(table.indices.keys()), set(index_names))
    
    def test_table_reference_one_unique_column(self):
        table = self.db.tables['reference_one_unique_column']
        self.assertEqual(len(table.foreign_keys), 1)
        fk = table.foreign_keys[0]
        self.assertEqual(fk.columns, ['ref_one_column',])
        self.assertEqual(fk.referenced_table, 'one_unique_column')
        self.assertEqual(fk.referenced_columns, ['column',])
        
    def test_table_reference_two_tables(self):
        table = self.db.tables['reference_two_tables']
        self.assertEqual(len(table.foreign_keys), 2)
            
    # view tests

    def test_view_names(self):
        self.assertEqual(set([view.name for view in self.db.views.values()]), 
                         set(self.VIEWS.keys()))
        
    def test_view_one_column_view(self):
        view = self.db.views['one_column_view']
        self.assertEqual(set(view.columns.keys()), set(['column']))

    # trigger tests
    
    def test_trigger_names(self):
        self.assertEqual(set(self.db.triggers.keys()), self.TRIGGERS.keys())
        
    def test_trigger_before_insert_trigger(self):
        trigger = self.db.triggers['before_insert_trigger']
        self.assertEqual(trigger.table, 'one_column')
        
    # other tests

    def test_supports_procedures(self):
        self.assertTrue(self.db.supports_stored_procedures())
        
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
                cursor.execute(sql);
        Class._run_using_cursor(function)
        
    @classmethod    
    def _drop_operation(Class, type, names):
        def function(Class, cursor):
            for name in names:
                try:
                    cursor.execute('DROP %s %s' % (type, name));
                except Class.DATABASE_ERRORS:
                    pass # maybe it was not created, we need to try drop other
        Class._run_using_cursor(function)

    def _add_triggers(self):
        self._add_operation(self.TRIGGERS.values())
        
    def _drop_triggers(self):
        self._drop_operation('TRIGGER', self.TRIGGERS)
        
    @staticmethod
    def substitute_quote_char(string):
        return string


class DatabaseWithProceduresTestCase(AbstractDatabaseTestCase):
    
    PROCEDURES = {}

    def setUp(self):
        try:
            self._add_operation(self.TABLES.values())
            self._add_operation(self.VIEWS.values())
            self._add_operation(self.PROCEDURES.values())
            self._add_operation(self.INDICES.values())
            self._add_triggers()
        except self.DATABASE_ERRORS as e:
            self.tearDown()
            raise
            
    def tearDown(self):
        self._drop_triggers()
        self._drop_operation('INDEX', self.INDICES)
        self._drop_procedures();
        self._drop_operation('VIEW', self.VIEWS)
        self._drop_operation('TABLE', reversed(tuple(self.TABLES.keys())))
        
    # tests
    
    def test_procedure_names(self):
        self.assertEqual(set([key for key in self.db.procedures.keys()]), 
                         set(self.PROCEDURES.keys()))
        self.assertEqual(set([procedure.name 
                              for procedure in self.db.procedures.values()]), 
                         set(self.PROCEDURES.keys()))

    # protected:
        
    @classmethod
    def _drop_procedures(Class):
        def function(Class, cursor):
            for name in Class.PROCEDURES.keys():
                try:
                    cursor.execute('DROP FUNCTION %s' % name);
                except Class.DATABASE_ERRORS as e:
                    pass # maybe it was not created, we need to try drop other
        Class._run_using_cursor(function)        
            

@skipUnless(TEST_POSTGRES, 'Failed to import psycopg2 module.')
class PostgresTestCase(DatabaseWithProceduresTestCase, TestCase):
    
    DBNAME = 'fathom'
    USER = 'fathom'
    DATABASE_ERRORS = postgres_errors
    
    TABLES = AbstractDatabaseTestCase.TABLES.copy()
    TABLES['empty'] = '''CREATE TABLE empty()'''

    PROCEDURES = DatabaseWithProceduresTestCase.PROCEDURES.copy()
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
    PROCEDURES['before_insert_trigger_function()'] = '''
CREATE FUNCTION before_insert_trigger_function() RETURNS trigger AS $$
    BEGIN
        IF NEW.column < 3 THEN
        END IF;
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
    }

    def setUp(self):
        DatabaseWithProceduresTestCase.setUp(self)
        args = self.DBNAME, self.USER
        self.db = get_database('dbname=%s user=%s' % args)
            
    # postgresql specific tests
            
    def test_table_empty(self):
        table = self.db.tables['empty']
        self.assertEqual(set(table.columns.keys()), set())

    def test_fib_integer(self):
        procedure = self.db.procedures['fib(int4)']
        self.assertArguments(procedure, [('fib_for', 'int4')])
        self.assertEqual(procedure.returns, 'int4')
        self.assertEqual(procedure.sql, '''
    BEGIN
        IF fib_for < 2 THEN
            RETURN fib_for;
        END IF;
        RETURN fib(fib_for - 2) + fib(fib_for - 1);
    END;
''')

    # trigger tests
    
    def test_trigger_before_insert_trigger(self):
        trigger = self.db.triggers['before_insert_trigger(one_column)']
        self.assertEqual(trigger.table, 'one_column')
        
    # postgresql internal methods required for testing
        
    def index_name(self, table_name, *columns, count=1):
        if len(columns):
            name = '%s_%s_key' % (table_name, columns[0])
        else:
            name = '%s_column_key' % table_name
        if count > 1:
            # postgres has really strange way of indexing index names; first
            # has no suffix, the following add count suffix beginning with 1
            name += str(count - 1)
        return name
            
    def pkey_index_name(self, table_name, *columns):
        return '%s_pkey' % table_name
        
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
class MySqlTestCase(DatabaseWithProceduresTestCase, TestCase):
    
    DBNAME = 'fathom'
    USER = 'fathom'
    DATABASE_ERRORS = mysql_errors

    DEFAULT_INTEGER_TYPE_NAME = 'int'

    TABLES = DatabaseWithProceduresTestCase.TABLES.copy()
    TABLES['one_unique_column'] = '''
CREATE TABLE one_unique_column ("column" integer UNIQUE) ENGINE = INNODB'''
    TABLES['primary_key_only'] = '''
CREATE TABLE primary_key_only (id integer primary key) ENGINE = INNODB
'''
    TABLES['reference_one_unique_column'] = '''
CREATE TABLE reference_one_unique_column (
    ref_one_column integer,
    FOREIGN KEY (ref_one_column) REFERENCES one_unique_column("column")
) ENGINE = INNODB'''
    TABLES['reference_two_tables'] = '''
CREATE TABLE reference_two_tables (
    ref1 integer,
    ref2 integer,
    FOREIGN KEY (ref1) REFERENCES one_unique_column("column"),
    FOREIGN KEY (ref2) REFERENCES primary_key_only(id)
) ENGINE = INNODB'''


    PROCEDURES = DatabaseWithProceduresTestCase.PROCEDURES.copy()
    PROCEDURES['foo_double'] = '''
CREATE FUNCTION foo_double (value int4)
    RETURNS INTEGER
        RETURN 2 * value;
'''

    def setUp(self):
        DatabaseWithProceduresTestCase.setUp(self)
        args = self.DBNAME, self.USER
        self.db = get_database(user=self.USER, db=self.DBNAME)
        
    # tests
    
    def test_foo_double(self):
        procedure = self.db.procedures['foo_double']
        self.assertEqual(procedure.returns, 'integer')
        self.assertEqual(procedure.sql, 'RETURN 2 * value')
    
    # mysql internal methods required for testing

    def index_name(self, table_name, *columns, count=1):
        if count == 1:
            return '%s' % columns[0]
        else:
            return '%s_%d' % (columns[0], count)

    def pkey_index_name(self, table_name, *columns):
        return 'PRIMARY'

    @classmethod
    def _get_connection(Class):
        return mysql_module.connect(user=Class.USER, db=Class.DBNAME)

    @staticmethod
    def substitute_quote_char(string):
        return string.replace('"', '`')


@skipUnless(TEST_ORACLE, 'Failed to import cx_Oracle module.')
class OracleTestCase(DatabaseWithProceduresTestCase, TestCase):
    
    # watch out when running those tests, cx_Oracle likes to segfault

    USER = 'fathom'
    PASSWORD = 'fathom'
    
    DATABASE_ERRORS = (cx_Oracle.DatabaseError,)
    
    TABLES = DatabaseWithProceduresTestCase.TABLES.copy()
    # oracle doesn't accept reserved words as identifiers
    TABLES.pop('one_column')
    TABLES.pop('one_unique_column')
    TABLES.pop('reference_one_unique_column')
    TABLES.pop('reference_two_tables')
    
    VIEWS = DatabaseWithProceduresTestCase.VIEWS.copy()
    VIEWS.pop('one_column_view')
    
    INDICES = DatabaseWithProceduresTestCase.INDICES.copy()
    INDICES.pop('one_column_index')
    
    TRIGGERS = DatabaseWithProceduresTestCase.TRIGGERS.copy()
    TRIGGERS.pop('before_insert_trigger')

    def setUp(self):
        DatabaseWithProceduresTestCase.setUp(self)
        self.db = get_oracle_database(user=self.USER, password=self.PASSWORD)

    def index_name(self, table_name, *columns, count=1):
        return ''
        
    def pkey_index_name(self, table_name, *columns):
        return ''

    @classmethod
    def _get_connection(Class):
        return cx_Oracle.connect('%s/%s' % (Class.USER, Class.PASSWORD))

    @staticmethod
    def substitute_quote_char(string):
        return string.replace('"', '')

@skipUnless(TEST_SQLITE, 'Failed to import sqlite3 module.')
class SqliteTestCase(AbstractDatabaseTestCase, TestCase):
    
    PATH = 'fathom.db3'
    DATABASE_ERRORS = (sqlite3.OperationalError, sqlite3.ProgrammingError)

    PRIMARY_KEY_IS_NOT_NULL = False
    CREATES_INDEX_FOR_PRIMARY_KEY = False
    
    TABLES = AbstractDatabaseTestCase.TABLES.copy()
    TABLES['django_admin_log'] = '''
        CREATE TABLE "django_admin_log" (
            "id" integer NOT NULL PRIMARY KEY,
            "action_time" datetime NOT NULL,
            "user_id" integer NOT NULL REFERENCES "auth_user" ("id"),
            "content_type_id" integer REFERENCES "django_content_type" ("id"),
            "object_id" text,
            "object_repr" varchar(200) NOT NULL,
            "action_flag" smallint unsigned NOT NULL,
            "change_message" text NOT NULL
        )'''
    TABLES['auth_permission'] = '''
        CREATE TABLE "auth_permission" (
            "id" integer NOT NULL PRIMARY KEY,
            "name" varchar(50) NOT NULL,
            "content_type_id" integer NOT NULL,
            "codename" varchar(100) NOT NULL,
            UNIQUE ("content_type_id", "codename")
        )'''

    def setUp(self):
        AbstractDatabaseTestCase.setUp(self)
        self.db = get_database(self.PATH)

    # sqlite specific tests

    def test_supports_procedures(self):
        self.assertFalse(self.db.supports_stored_procedures())
    
    def test_sqlite_table_django_admin_log(self):
        table = self.db.tables['django_admin_log']
        values = (('id', 'integer', True), ('action_time', 'datetime', True),
                  ('user_id', 'integer', True), 
                  ('content_type_id', 'integer', False),
                  ('object_id', 'text', False), 
                  ('object_repr', 'varchar(200)', True),
                  ('action_flag', 'smallint unsigned', True),
                  ('change_message', 'text', True))
        self.assertColumns(table, values)

    def test_sqlite_table_auth_permission(self):
        table = self.db.tables['auth_permission']
        values = (('id', 'integer', True), ('name', 'varchar(50)', True),
                  ('content_type_id', 'integer', True),
                  ('codename', 'varchar(100)', True))
        self.assertColumns(table, values)
        
        self.assertEqual(set(table.indices.keys()), 
                         set([self.index_name('auth_permission')]))

    # sqlite internal methods required for testing

    def index_name(self, table_name, *columns, count=1):
        return 'sqlite_autoindex_%s_%d' % (table_name, count)
    
    def pkey_index_name(self, table_name, *columns):
        return self.index_name(table_name, columns)

    @classmethod
    def _get_connection(Class):
        return sqlite3.connect(Class.PATH)


class DatabaseTypeTestCase(TestCase):
    
    def test_sqlite(self):
        self.assertEqual(get_database_type('fathom.db3'), 'Sqlite3')
        
    def test_mysql(self):
        self.assertEqual(get_database_type(user='fathom', db='fathom'), 'MySQL')
        
    def test_postgres(self):
        self.assertEqual(get_database_type('dbname=fathom user=fathom'),
                         'PostgreSQL')
    
    def test_exception(self):
        self.assertRaises(FathomError, get_database_type, 
                          'non_existing_file.db')
        self.assertRaises(FathomError, get_database_type, user='fathom', 
                          db='non_existing_database')
        self.assertRaises(FathomError, get_database_type, 
                          'dbname=not_existing_database user=fathom')

if __name__ == "__main__":
    main()
