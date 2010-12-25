#!/usr/bin/python

from unittest import TestCase, main

from _sqlite import CreateTableParser

class SqliteCreateTableParseTestCase(TestCase):
    
    def setUp(self):
        self.parser = CreateTableParser()
    
    def test_empty_table(self):
        sql = '''
CREATE TABLE "table" (
)'''
        self.assertEqual(self.parser.parse(sql), 
                         {'database_name': '', 'table_name': ['"table"'], 
                          'column_names': '', 'column_types': ''})
                                                  
    def test_empty_table_with_database(self):
        sql = '''
CREATE TABLE "database"."table" (
)'''
        self.assertEqual(self.parser.parse(sql), {'database_name': ['"database"'], 
                                                  'table_name': ['"table"'], 
                                                  'column_names': '', 
                                                  'column_types': ''})
                                            
    def test_no_type_column(self):
        sql = '''CREATE TABLE "database".one_column_table (column)'''
        result = {'database_name': ['"database"'], 
                  'table_name': ['one_column_table'], 
                  'column_names': [['column']], 'column_types': ''}
        self.assertEqual(self.parser.parse(sql), result)
                                                  
    def test_single_typed_column(self):
        sql = '''CREATE TABLE "database".one_column_table (column integer)'''
        self.assertEqual(self.parser.parse(sql), 
                         {'database_name': ['"database"'], 
                          'table_name': ['one_column_table'], 
                          'column_names': [['column']], 
                          'column_types': [['integer']]})
        sql = '''CREATE TABLE "database".one_column_table 
                 (column varchar(800))'''
        self.assertEqual(self.parser.parse(sql), 
                         {'database_name': ['"database"'], 
                          'table_name': ['one_column_table'], 
                          'column_names': [['column']], 
                          'column_types': [['varchar', '(', '800', ')']]})
        sql = '''CREATE TABLE one_column_table (column varchar(100, 200))'''     
        result = {'database_name': '',  'table_name': ['one_column_table'], 
                  'column_names': [['column']], 
                  'column_types': [['varchar', '(', '100', ',', '200', ')']]}
        self.assertEqual(self.parser.parse(sql), result) 
    
    def test_multi_untyped_column(self):
        sql = '''CREATE TABLE some_name (x, y, "z", tytww_wer, rew)'''
        result = {'database_name': '', 'table_name': ['some_name'], 
                  'column_names': [['x'], ['y'], ['"z"'], ['tytww_wer'], 
                                   ['rew']], 
                  'column_types': ''}
        self.assertEqual(self.parser.parse(sql), result)
        
    def test_multi_typed_column(self):
        sql ='''CREATE TABLE "django_site7" (
                    "id" integer,
                    "domain" varchar(2000),
                    "name" varchar(100, 500),
                    "user_id" integer)'''
        result = {'database_name': '', 'table_name': ['"django_site7"'], 
                  'column_names': [['"id"'], ['"domain"'], ['"name"'], 
                                   ['"user_id"']],
                  'column_types': [['integer'], ['varchar', '(', '2000', ')'],
                                   ['varchar', '(', '100', ',', '500', ')'],
                                   ['integer']]}
        self.assertEqual(self.parser.parse(sql), result)
        
if __name__ == "__main__":
    main()
