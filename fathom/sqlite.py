#!/usr/bin/python

from pyparsing import (Literal, CaselessLiteral, Word, Upcase, delimitedList, 
                       Optional, Combine, Group, alphas, nums, alphanums, 
                       ParseException, Forward, oneOf, quotedString, 
                       ZeroOrMore, restOfLine, Keyword, White, Suppress,
                       OneOrMore, StringEnd, ParseResults)

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
    keywords_set = (CREATE | TEMP | TEMPORARY | TABLE | IF | NOT | EXISTS | 
                    AS | PRIMARY | KEY)
    
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
    multi_column_def << ((OneOrMore(column_def + ',') + column_def) |
                         Optional(column_def))
    column_def << column_name + Optional(type_name) + multi_column_constraint
    type_name << (identifier_white.copy() + 
                  Optional('(' + Word(nums) + 
                           (')' | (',' + Word(nums) + ')'))))
    multi_column_constraint << ZeroOrMore(column_constraint)
    #column_constraint << 
            
    def __init__(self, sql):
        super(CreateTableParser, self).__init__()
        self.tokens = self.create_table_stmt.parseString(sql)

    def column_names(self):
        result = []
        for column in self.tokens.columns:
            result.append(clear_identifier(column[0]))
        return result

def clear_identifier(identifier):
    if identifier[0] == '"' and identifier[-1] == '"':
        identifier = identifier[1:-1]
    return identifier
