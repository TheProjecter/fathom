#!/usr/bin/python

from pyparsing import (Literal, CaselessLiteral, Word, Upcase, delimitedList, 
                       Optional, Combine, Group, alphas, nums, alphanums, 
                       ParseException, Forward, oneOf, quotedString, 
                       ZeroOrMore, restOfLine, Keyword, White)

class CreateTableParser(object):
    
    
    create_token = Keyword("create", caseless=True)
    table_token = Keyword("table", caseless=True)    
    table_name = Word(alphas, alphanums).setResultsName('table')
    column_name = Word(alphas, alphanums).setResultsName('columns')
    column_type = Word(alphas, alphanums)
    
    create_stmt = Forward()
    create_stmt << (create_token + table_token + table_name + '(' + 
					ZeroOrMore(column_name + column_type) + ')' )
    
    def __init__(self):
        super(CreateTableParser, self).__init__()

    def parse(self, sql):
        try:
            tokens = self.create_stmt.parseString(sql)
            print tokens.table, tokens.columns
        except ParseException as error:
            print error
            
if __name__ == "__main__":
    CreateTableParser().parse('create table dupa (x int z varchar)')
