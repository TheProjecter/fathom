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

TableDescription = namedtuple('TableDescription', 'sql column_names')

class AbstractDatabaseTestCase:
    
    __metaclass__ = ABCMeta
    
    TABLES = {
        'one_column': TableDescription(sql='''
CREATE TABLE one_column ("column" varchar(800))''',
                                       column_names=('column',)),
        'one_unique_column': TableDescription(sql='''
CREATE TABLE one_unique_column ("column" integer UNIQUE)''',
                                              column_names=('column',))
    }
    
    VIEWS = {
    }

    @classmethod
    def setUpClass(Class):
        try:
            Class._add_tables()
        except Class.DATABASE_ERRORS:
            self.tearDownClass()
            raise
        
    @classmethod
    def tearDownClass(Class):
        conn = Class._get_connection()
        cursor = conn.cursor()
        for name in Class.TABLES:
            try:
                cursor.execute('DROP TABLE %s' % name);
            except Class.DATABASE_ERRORS:
                pass # maybe it was not created, but we need to try drop other
        conn.commit()
        cursor.close()
        conn.close()

    # tests

    def test_table_names(self):
        self.assertEqual(set([table.name for table in self.db.tables.values()]), 
                         set(self.TABLES.keys()))
        
    def test_view_names(self):
        self.assertEqual(set([table.name for table in self.db.views]), 
                         set(self.VIEWS.keys()))
                         
    def test_column_names(self):
        for name, description in self.TABLES.items():
            table = self.db.tables[name]
            names = set(column.name for column in table.columns.values())
            self.assertEqual(names, set(description.column_names))
                
    # protected:
    
    @abstractmethod
    def _get_connection(Class):
        pass
        
    @classmethod
    def _add_tables(Class):
        conn = Class._get_connection()
        cursor = conn.cursor()
        for description in Class.TABLES.values():
            cursor.execute(description.sql);
        conn.commit()
        cursor.close()
        conn.close()

@skipUnless(TEST_POSTGRES, 'Failed to import psycopg2 module.')
class PostgresTestCase(AbstractDatabaseTestCase, TestCase):
    
    DBNAME = 'fathom'
    USER = 'fathom'
    DATABASE_ERRORS = (psycopg2.OperationalError, psycopg2.ProgrammingError)
    
    TABLES = AbstractDatabaseTestCase.TABLES.copy()
    TABLES['empty'] = TableDescription(sql='''CREATE TABLE empty()''',
                                       column_names=())

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
    
    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)
        self.db = get_sqlite3_database(self.PATH)

    @classmethod
    def _get_connection(Class):
        return sqlite3.connect(Class.PATH)


if __name__ == "__main__":
    main()
