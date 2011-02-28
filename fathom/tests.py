#!/usr/bin/python

from abc import ABCMeta, abstractmethod
try:
    from unittest import TestCase, main, skipUnless
except ImportError:
    from unittest2 import TestCase, main, skipUnless
from collections import namedtuple

from fathom import get_sqlite3_database, get_postgresql_database

try:
    import psycopg2
    TEST_POSTGRES = True
except ImportError:
    TEST_POSTGRES = False
    
try:
    import sqlite3
    TEST_SQLITE = True
except:
    TEST_SQLITE = False

class AbstractDatabaseTestCase:
    
    __metaclass__ = ABCMeta
    
    TABLES = {
        'one_column': '''CREATE TABLE one_column ("column" varchar(800))''',
        'one_unique_column': '''CREATE TABLE one_unique_column ("column" integer UNIQUE)''',
    }
    
    VIEWS = {
        'one_column_view': '''CREATE VIEW one_column_view AS SELECT "column" FROM one_column;''',
    }

    @classmethod
    def setUpClass(Class):
        try:
            Class._add_operation(Class.TABLES.values())
            Class._add_operation(Class.VIEWS.values())
        except Class.DATABASE_ERRORS as e:
            Class.tearDownClass()
            raise
        
    @classmethod
    def tearDownClass(Class):
        Class._drop_operation('VIEW', Class.VIEWS)
        Class._drop_operation('TABLE', Class.TABLES)

    # new assertions
    
    def assertColumns(self, table, values):
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

    # tests

    def test_table_names(self):
        self.assertEqual(set([table.name for table in self.db.tables.values()]), 
                         set(self.TABLES.keys()))
        
    def test_view_names(self):
        self.assertEqual(set([view.name for view in self.db.views.values()]), 
                         set(self.VIEWS.keys()))
                         
    def test_table_one_column(self):
        table = self.db.tables['one_column']
        self.assertEqual(set(table.columns.keys()), set(['column']))
        self.assertEqual(table.columns['column'].type, 'varchar(800)')
        self.assertEqual(table.columns['column'].not_null, False)
        self.assertEqual(set(table.indices.keys()), set())
        
    def test_table_one_unique_column(self):
        table = self.db.tables['one_unique_column']
        self.assertEqual(set(table.columns.keys()), set(['column']))
        self.assertEqual(table.columns['column'].type, 'integer')
        self.assertEqual(table.columns['column'].not_null, False)
        self.assertEqual(set(table.indices.keys()), 
                         set([self.auto_index_name('one_unique_column')]))
        
    def test_view_one_column_view(self):
        view = self.db.views['one_column_view']
        self.assertEqual(set(view.columns.keys()), set(['column']))
        
    @abstractmethod
    def auto_index_name(self, table_name):
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


class DatabaseWithProceduresTestCase(AbstractDatabaseTestCase):
    
    PROCEDURES = {
        'fib': '''
CREATE OR REPLACE FUNCTION fib (fib_for integer) RETURNS integer AS $$
    BEGIN
        IF fib_for < 2 THEN
            RETURN fib_for;
        END IF;
        RETURN fib(fib_for - 2) + fib(fib_for - 1);
    END;
$$ LANGUAGE plpgsql;'''
    }

    @classmethod
    def setUpClass(Class):
        try:
            Class._add_operation(Class.TABLES.values())
            Class._add_operation(Class.VIEWS.values())
            Class._add_operation(Class.PROCEDURES.values())
        except Class.DATABASE_ERRORS as e:
            print e
            Class.tearDownClass()
            raise

    @classmethod
    def tearDownClass(Class):
        Class._drop_operation('FUNCTION', Class.PROCEDURES)
        Class._drop_operation('VIEW', Class.VIEWS)
        Class._drop_operation('TABLE', Class.TABLES)
            

@skipUnless(TEST_POSTGRES, 'Failed to import psycopg2 module.')
class PostgresTestCase(DatabaseWithProceduresTestCase, TestCase):
    
    DBNAME = 'fathom'
    USER = 'fathom'
    DATABASE_ERRORS = (psycopg2.OperationalError, psycopg2.ProgrammingError)
    
    TABLES = AbstractDatabaseTestCase.TABLES.copy()
    TABLES['empty'] = '''CREATE TABLE empty()'''

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)
        args = self.DBNAME, self.USER
        self.db = get_postgresql_database('dbname=%s user=%s' % args)
    
    # postgresql specific tests
        
    def test_table_empty(self):
        table = self.db.tables['empty']
        self.assertEqual(set(table.columns.keys()), set())
    
    # postgresql internal methods required for testing
        
    def auto_index_name(self, table_name):
        return '%s_column_key' % table_name
        
    @classmethod
    def _get_connection(Class):
        args = Class.DBNAME, Class.USER
        return psycopg2.connect('dbname=%s user=%s' % args)


@skipUnless(TEST_SQLITE, 'Failed to import sqlite3 module.')
class SqliteTestCase(AbstractDatabaseTestCase, TestCase):
    
    PATH = 'fathom.db3'
    DATABASE_ERRORS = (sqlite3.OperationalError, sqlite3.ProgrammingError)
    
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

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)
        self.db = get_sqlite3_database(self.PATH)

    # sqlite specific tests
    
    def test_sqlite_table_django_admin_log(self):
        table = self.db.tables['django_admin_log']
        column_names = ('id', 'action_time', 'user_id', 'content_type_id', 
                        'object_id', 'object_repr', 'action_flag', 
                        'change_message')
        self.assertEqual(set(table.columns.keys()), set(column_names))
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
        column_names = 'id', 'name', 'content_type_id', 'codename'
        self.assertEqual(set(table.columns.keys()), set(column_names))
        values = (('id', 'integer', True), ('name', 'varchar(50)', True),
                  ('content_type_id', 'integer', True),
                  ('codename', 'varchar(100)', True))
        self.assertColumns(table, values)
        self.assertEqual(set(table.indices.keys()), 
                         set([self.auto_index_name('auth_permission')]))

    # sqlite internal methods required for testing

    def auto_index_name(self, table_name):
        return 'sqlite_autoindex_%s_1' % table_name

    @classmethod
    def _get_connection(Class):
        return sqlite3.connect(Class.PATH)


if __name__ == "__main__":
    main()
