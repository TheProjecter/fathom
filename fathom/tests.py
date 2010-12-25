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
        self.assertEqual(self.parser.parse(sql), {'database_name': '', 
                                                  'table_name': ['"table"'], 
                                                  'column_names': '', 
                                                  'column_types': ''})
                                                  
    def test_empty_table_with_database(self):
        sql = '''
CREATE TABLE "database"."table" (
)'''
        self.assertEqual(self.parser.parse(sql), {'database_name': ['"database"'], 
                                                  'table_name': ['"table"'], 
                                                  'column_names': '', 
                                                  'column_types': ''})
                                            
    def test_no_type_column(self):
        sql = '''
CREATE TABLE "database".one_column_table (
        column
)'''
        self.assertEqual(self.parser.parse(sql), {'database_name': ['"database"'], 
                                                  'table_name': ['one_column_table'], 
                                                  'column_names': [['column']], 
                                                  'column_types': ''})
                                                  
    def test_typed_column(self):
        sql = '''
CREATE TABLE "database".one_column_table (
        column integer
)'''
        self.assertEqual(self.parser.parse(sql), {'database_name': ['"database"'], 
                                                  'table_name': ['one_column_table'], 
                                                  'column_names': [['column']], 
                                                  'column_types': [['integer']]})
        sql = '''
CREATE TABLE "database".one_column_table (
        column varchar(800)
)'''
        self.assertEqual(self.parser.parse(sql), 
                         {'database_name': ['"database"'], 
                          'table_name': ['one_column_table'], 
                          'column_names': [['column']], 
                          'column_types': [['varchar', '(', '800', ')']]})
        
        
        
if __name__ == "__main__":
    main()
