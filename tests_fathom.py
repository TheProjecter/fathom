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

TableDescription = namedtuple('TableDescription', 
                              'sql column_names column_types')
ViewDescription = namedtuple('ViewDescription', 'sql columns tables')

class AbstractDatabaseTestCase:
    
    __metaclass__ = ABCMeta
    
    TABLES = {
        'one_column': TableDescription(sql='''
CREATE TABLE one_column ("column" varchar(800))''',
                                       column_names=('column',),
                                       column_types=('varchar(800)',)),
        'one_unique_column': TableDescription(sql='''
CREATE TABLE one_unique_column ("column" integer UNIQUE)''',
                                              column_names=('column',),
                                              column_types=('integer',)),                                              
    }
    
    VIEWS = {
        'one_column_view': ViewDescription(sql='''
CREATE VIEW one_column_view AS SELECT "column" FROM one_column;''',
                                           columns=('column',),
                                           tables=('one_column',))
    }

    @classmethod
    def setUpClass(Class):
        try:
            Class._add_tables()
            Class._add_views()
        except Class.DATABASE_ERRORS as e:
            print e
            Class.tearDownClass()
            raise
        
    @classmethod
    def tearDownClass(Class):
        Class._drop_views()
        Class._drop_tables()

    # tests

    def test_table_names(self):
        self.assertEqual(set([table.name for table in self.db.tables.values()]), 
                         set(self.TABLES.keys()))
        
    def test_view_names(self):
        self.assertEqual(set([view.name for view in self.db.views]), 
                         set(self.VIEWS.keys()))
                         
    def test_column_names(self):
        for name, description in self.TABLES.items():
            table = self.db.tables[name]
            names = set(column.name for column in table.columns.values())
            self.assertEqual(names, set(description.column_names))

    def test_column_types(self):
        for name, description in self.TABLES.items():
            table = self.db.tables[name]
            types = set(column.type for column in table.columns.values())
            self.assertEqual(types, set(description.column_types))

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
    def _add_tables(Class):
        def function(Class, cursor):
            for description in Class.TABLES.values():
                cursor.execute(description.sql);
        Class._run_using_cursor(function)
        
    @classmethod    
    def _drop_tables(Class):
        def function(Class, cursor):
            for name in Class.TABLES:
                try:
                    cursor.execute('DROP TABLE %s' % name);
                except Class.DATABASE_ERRORS:
                    pass # maybe it was not created, we need to try drop other
        Class._run_using_cursor(function)

    @classmethod
    def _add_views(Class):
        def function(Class, cursor):
            for description in Class.VIEWS.values():
                cursor.execute(description.sql)
        Class._run_using_cursor(function)
        
    @classmethod
    def _drop_views(Class):
        def function(Class, cursor):
            for name in Class.VIEWS:
                try:
                    cursor.execute('DROP VIEW %s' % name)
                except Class.DATABASE_ERRORS:
                    pass # maybe it was not created, we need to try drop other
        Class._run_using_cursor(function)


@skipUnless(TEST_POSTGRES, 'Failed to import psycopg2 module.')
class PostgresTestCase(AbstractDatabaseTestCase, TestCase):
    
    DBNAME = 'fathom'
    USER = 'fathom'
    DATABASE_ERRORS = (psycopg2.OperationalError, psycopg2.ProgrammingError)
    
    TABLES = AbstractDatabaseTestCase.TABLES.copy()
    TABLES['empty'] = TableDescription(sql='''CREATE TABLE empty()''',
                                       column_names=(), column_types=())

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)
        args = self.DBNAME, self.USER
        self.db = get_postgresql_database('dbname=%s user=%s' % args)

    @classmethod
    def _get_connection(Class):
        args = Class.DBNAME, Class.USER
        return psycopg2.connect('dbname=%s user=%s' % args)


@skipUnless(TEST_SQLITE, 'Failed to import sqlite3 module.')
class SqliteTestCase(AbstractDatabaseTestCase, TestCase):
    
    PATH = 'fathom.db3'
    DATABASE_ERRORS = (sqlite3.OperationalError, sqlite3.ProgrammingError)
    
    TABLES = AbstractDatabaseTestCase.TABLES.copy()
    TABLES['django_admin_log'] = TableDescription(sql='''
CREATE TABLE "django_admin_log" (
    "id" integer NOT NULL PRIMARY KEY,
    "action_time" datetime NOT NULL,
    "user_id" integer NOT NULL REFERENCES "auth_user" ("id"),
    "content_type_id" integer REFERENCES "django_content_type" ("id"),
    "object_id" text,
    "object_repr" varchar(200) NOT NULL,
    "action_flag" smallint unsigned NOT NULL,
    "change_message" text NOT NULL
)''',
column_names=('id', 'action_time', 'user_id', 'content_type_id', 'object_id',
              'object_repr', 'action_flag', 'change_message'),
column_types=('integer', 'datetime', 'integer', 'integer', 'text', 
              'varchar(200)', 'smallint unsigned', 'text'))
    TABLES['auth_permission'] = TableDescription(sql='''
CREATE TABLE "auth_permission" (
    "id" integer NOT NULL PRIMARY KEY,
    "name" varchar(50) NOT NULL,
    "content_type_id" integer NOT NULL,
    "codename" varchar(100) NOT NULL,
    UNIQUE ("content_type_id", "codename")
)''',
column_names=('id', 'name', 'content_type_id', 'codename'),
column_types=('integer', 'varchar(50)', 'integer', 'varchar(100)'))

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)
        self.db = get_sqlite3_database(self.PATH)

    @classmethod
    def _get_connection(Class):
        return sqlite3.connect(Class.PATH)


if __name__ == "__main__":
    main()
