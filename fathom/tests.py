#!/usr/bin/python

from abc import ABCMeta, abstractmethod
try:
    from unittest import TestCase, main, skipUnless
except ImportError:
    from unittest2 import TestCase, main, skipUnless
from collections import namedtuple

from inspectors import PostgresInspector, SqliteInspector

try:
    import psycopg2
    TEST_POSTGRES = True
except ImportError:
    # print('Failed to import psycopg2; skipping postgres tests.')
    TEST_POSTGRES = False
    
try:
    import sqlite3
    TEST_SQLITE = True
except:
    # print('Failed to import sqlite3; skipping sqlite tests.')
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

    def setUp(self):
        # should be moved to setUpClass when python 2.7 is more popular
        try:
            self._add_tables()
        except self.DatabaseErrors:
            self.tearDown()
            raise
        
    def tearDown(self):
        self._drop_tables()

    def test_table_names(self):
        tables = set(self.TABLES.keys())
        self.assertEqual(set(self.inspector._get_tables()), tables)
        
    def test_view_names(self):
        views = set()
        self.assertEqual(set(self.inspector._get_views()), views)

    def test_column_names(self):
        for table, description in self.TABLES.items():
            self.assertEqual(set(self.inspector._get_columns(table)),
                             set(description.column_names))
        
    # protected:
    
    @abstractmethod
    def _get_connection(self):
        pass
        
    def _add_tables(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        for description in self.TABLES.values():
            cursor.execute(description.sql);
        conn.commit()
        cursor.close()
        conn.close()

    def _drop_tables(self):
        # should be moved to setUpClass when python 2.7 is more popular
        conn = self._get_connection()
        cursor = conn.cursor()
        for name in self.TABLES:
            try:
                cursor.execute('DROP TABLE %s' % name);
            except self.DatabaseErrors:
                pass # maybe it was not created, but we need to try drop other
        conn.commit()
        cursor.close()
        conn.close()


@skipUnless(TEST_POSTGRES, 'Failed to import psycopg2 module.')
class PostgresTestCase(AbstractDatabaseTestCase, TestCase):
    
    DBNAME = 'fathom'
    USER = 'fathom'
    
    TABLES = AbstractDatabaseTestCase.TABLES.copy()
    TABLES['empty'] = TableDescription(sql='''CREATE TABLE empty()''',
                                       column_names=())

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)
        args = self.DBNAME, self.USER
        self.inspector = PostgresInspector('dbname=%s user=%s' % args)
        self.DatabaseErrors = (psycopg2.ProgrammingError,
                               psycopg2.OperationalError)
        
    def _get_connection(self):
        args = self.DBNAME, self.USER
        return psycopg2.connect('dbname=%s user=%s' % args)


@skipUnless(TEST_SQLITE, 'Failed to import sqlite3 module.')
class SqliteTestCase(AbstractDatabaseTestCase, TestCase):
    
    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)
        self.inspector = SqliteInspector('fathom.db3')
        self.DatabaseErrors = (sqlite3.OperationalError, 
                               sqlite3.ProgrammingError)

    def _get_connection(self):
        return sqlite3.connect('fathom.db3')


if __name__ == "__main__":
    main()
