#!/usr/bin/python

from pyparsing import (Literal, CaselessLiteral, Word, Upcase, delimitedList, 
                       Optional, Combine, Group, alphas, nums, alphanums, 
                       ParseException, Forward, oneOf, quotedString, 
                       ZeroOrMore, restOfLine, Keyword, White, Suppress,
                       OneOrMore, StringEnd)

class CreateTableParser(object):

    # keywords:
    CREATE = Keyword('CREATE', caseless=True)
    TEMP = Keyword('TEMP', caseless=True)
    TEMPORARY = Keyword('TEMPORARY', caseless=True)
    TABLE = Keyword('TABLE', caseless=True)
    IF = Keyword('IF', caseless=True)
    NOT = Keyword('NOT', caseless=True)
    EXISTS = Keyword('EXISTS', caseless=True)
    AS = Keyword('AS', caseless=True)
    keywords_set = (CREATE | TEMP | TEMPORARY | TABLE | IF | NOT | EXISTS | AS)
    
    # different types of identifier objects
    identifier = (Combine(Optional('"') + Word(alphanums) + 
                          ZeroOrMore('_' + Word(alphanums)) + 
                          Optional('"')) & ~keywords_set)
    identifier_coma = ((ZeroOrMore(identifier.copy() + ",") + Optional(identifier.copy())) | 
                      Optional(identifier.copy()))
    identifier_white = OneOrMore(identifier.copy())
        
    # statements used in sqlite 'CREATE TABLE' reference
    create_table_stmt = Forward()
    select_stmt = Forward()
    column_def = Forward()
    type_name = Forward()

    # special statements for multiple occurance of certain statement
    multi_column_def = Forward()
    multi_table_constraint = Forward()
    multi_column_constraint = Forward()

    # identifiers
    database_name = identifier.setResultsName('database_name', 
                                              listAllMatches=True)
    table_name = identifier.setResultsName('table_name', listAllMatches=True)
    column_name = identifier.setResultsName('column_names', 
                                            listAllMatches=True)
    
    # building statement as described in sqlite 'CREATE TABLE' reference        
    create_table_stmt << (CREATE + Optional(TEMP | TEMPORARY) + TABLE + 
                          Optional(IF + NOT + EXISTS) + 
                          Optional(database_name + '.') + table_name +
                          ((AS + select_stmt) | 
                           ('(' + multi_column_def + 
                            Optional(multi_table_constraint) + ')')) + 
                           StringEnd())
    multi_column_def << ((OneOrMore(column_def + ',') + column_def) |
                         Optional(column_def))
                                   
    column_def << column_name + Optional(type_name)
        
    def __init__(self):
        super(CreateTableParser, self).__init__()

    def parse(self, sql):
        try:
            tokens = self.create_table_stmt.parseString(sql)
            print tokens.database_name, tokens.table_name, tokens.column_names
            return tokens.column_names
        except ParseException as error:
            print error
            
if __name__ == "__main__":
    CreateTableParser().parse('''
CREATE TABLE "django"."django_site" (
)''')
    CreateTableParser().parse('''
CREATE TABLE "django"."django_site" (
)''')
    CreateTableParser().parse('''
CREATE TABLE "django"."django_site" (
x
)''')
    CreateTableParser().parse('''
CREATE TABLE "django"."django_site" (
x, y,
z,
tytww_wer,
rew
)''')

    CreateTableParser().parse('''
CREATE TABLE "django_site" (
"id" integer NOT NULL PRIMARY   KEY,
"domain" varchar,
"name" varchar,
"user_id" integer NOT NULL REFERENCES "auth_user" ("id")
UNIQUE ("app_label", "model")
)''')

