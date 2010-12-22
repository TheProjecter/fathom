#!/usr/bin/python

from pyparsing import (Literal, CaselessLiteral, Word, Upcase, delimitedList, 
                       Optional, Combine, Group, alphas, nums, alphanums, 
                       ParseException, Forward, oneOf, quotedString, 
                       ZeroOrMore, restOfLine, Keyword)

class CreateTableParser(object):
    
    create_stmt = Forward()
    create_token = Keyword("create", caseless=True)
    table_token = Keyword("table", caseless=True)
    
    ident = Word(alphas, alphanums)
    
    def __init__(self):
        super(CreateTableParser, self).__init__()
