#!/usr/bin/python

from pyparsing import (Literal, CaselessLiteral, Word, Upcase, delimitedList, 
                       Optional, Combine, Group, alphas, nums, alphanums, 
                       ParseException, Forward, oneOf, quotedString, 
                       ZeroOrMore, restOfLine, Keyword, White, Suppress,
                       OneOrMore, StringEnd, ParseResults, NotAny, And)
                       
from schema import Column

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
    PRIMARY = Keyword('PRIMARY', caseless=True)
    KEY = Keyword('KEY', caseless=True)
    UNIQUE = Keyword('UNIQUE', caseless=True)
    NULL = Keyword('NULL', caseless=True)
    REFERENCES = Keyword('REFERENCES', caseless=True)
    keywords_set = (CREATE | TEMP | TEMPORARY | TABLE | IF | NOT | EXISTS | 
                    AS | PRIMARY | KEY | UNIQUE | NULL | REFERENCES)
        
    # different types of identifier objects
    identifier = (~keywords_set + (Optional('"') + Word(alphanums) + 
                          ZeroOrMore('_' + Word(alphanums)) + 
                          Optional('"')))
    identifier_coma = delimitedList(identifier.copy())
    identifier_white = OneOrMore(identifier.copy())
        
    # statements used in sqlite 'CREATE TABLE' reference
    create_table_stmt = Forward()
    select_stmt = Forward()
    column_def = Forward().setResultsName('columns', listAllMatches=True)
    type_name = Forward().setResultsName('column_types', listAllMatches=True)
    column_constraint = Forward()

    # special statements for multiple occurance of certain statement
    multi_column_def = Forward()
    multi_table_constraint = Forward()
    multi_column_constraint = Forward()

    # identifiers
    database_name = identifier.setResultsName('database_name')
    table_name = identifier.setResultsName('table_name')
    column_name = identifier.setResultsName('column_name', 
                                            listAllMatches=True)
                                                
    # building statement as described in sqlite 'CREATE TABLE' reference        
    create_table_stmt << (CREATE + Optional(TEMP | TEMPORARY) + TABLE + 
                          Optional(IF + NOT + EXISTS) + 
                          Optional(database_name + '.') + table_name +
                          ((AS + select_stmt) | 
                           ('(' + multi_column_def + 
                            Optional(multi_table_constraint) + ')')) + 
                           StringEnd())
    multi_column_def << delimitedList(column_def)
    column_def << column_name + Optional(type_name) + multi_column_constraint
    type_name << (identifier_white.copy() + 
                  Optional('(' + Word(nums) + 
                           (')' | (',' + Word(nums) + ')'))))
    multi_column_constraint << ZeroOrMore(column_constraint)
    column_constraint << (UNIQUE | (NOT + NULL) | (PRIMARY + KEY) | 
                          (REFERENCES + identifier  + "(" + identifier + ")"))
            
    def __init__(self):
        super(CreateTableParser, self).__init__()
        
    def parse(self, sql, table):
        self.tokens = self.create_table_stmt.parseString(sql)
        columns = {}
        for column in self.tokens.columns:
            column_name = clear_identifier(''.join(column.column_name[0]))
            column_type = join_type(column.column_types[0])
            columns[column_name] = Column(column_name, column_type)
        table.columns = columns

def join_type(parts):
    brackets = ('(', ')')
    separated = []
    previous = None
    for part in parts:
        if (previous is not None and 
            previous not in brackets and part not in brackets):
            separated.append(' ')
        separated.append(part)
        previous = part
    return ''.join(separated)

def clear_identifier(identifier):
    if identifier[0] == '"' and identifier[-1] == '"':
        identifier = identifier[1:-1]
    return identifier

def parse_table(sql, table):
    CreateTableParser().parse(sql, table)

if __name__ == "__main__":
    sql = '''
CREATE TABLE "django_admin_log" (
    "id" integer NOT NULL PRIMARY KEY,
    "action_time" datetime NOT NULL,
    "user_id" integer NOT NULL REFERENCES "auth_user" ("id"),
    "content_type_id" integer REFERENCES "django_content_type" ("id"),
    "object_id" text,
    "object_repr" varchar(200) NOT NULL,
    "action_flag" smallint unsigned NOT NULL,
    "change_message" text NOT NULL
)'''
    CreateTableParser().parse(sql, None)
    
