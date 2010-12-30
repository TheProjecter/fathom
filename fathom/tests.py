#!/usr/bin/python

from unittest import TestCase, main

from _sqlite import CreateTableParser
from inspectors import PostgresInspector

class PostgresTest(TestCase):
    
    def setUp(self):
        self.inspector = PostgresInspector('dbname=django user=django')
    
    def test_table_names(self):
        tables = set(('auth_group_permissions', 'auth_group', 
                      'auth_user_user_permissions', 'auth_user_groups',
                      'auth_message', 'auth_user', 'auth_permission',
                      'django_content_type', 'django_session', 'django_site'))
        self.assertEqual(set(self.inspector._get_tables()), tables)

if __name__ == "__main__":
    main()
