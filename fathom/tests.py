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
        self.assertEqual(self.parser.parse(sql), ('', 'table', [], []))
        
if __name__ == "__main__":
    main()
