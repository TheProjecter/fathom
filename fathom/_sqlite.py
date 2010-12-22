#!/usr/bin/python

from pyparsing import (Literal, CaselessLiteral, Word, Upcase, delimitedList, 
                       Optional, Combine, Group, alphas, nums, alphanums, 
                       ParseException, Forward, oneOf, quotedString, 
                       ZeroOrMore, restOfLine, Keyword, White, Suppress)

class CreateTableParser(object):
    
    identifier = Combine(Optional('"') + Word(alphanums) + 
                         ZeroOrMore('_' + Word(alphanums)) + Optional('"'))
    identifiers = ((ZeroOrMore(identifier + ",") + Optional(identifier)) | 
                   Optional(identifier))
                    
        
    create_token = Keyword("create", caseless=True)
    table_token = Keyword("table", caseless=True)    
    table_name = Combine(Optional('"') + Word(alphanums) + 
                         ZeroOrMore('_' + Word(alphanums)) + Optional('"'))
    table_name = table_name.setResultsName('table')
    
    column_name = Combine(Optional('"') + Word(alphanums) +
                          ZeroOrMore('_' + Word(alphanums)) + Optional('"'))
    column_name = column_name.setResultsName('column_names', 
                                             listAllMatches=True)
    column_type = Combine(Word(alphas, alphanums) + 
                   Optional("(" + Word(alphanums) + ")"))
    not_null = (Keyword("not", caseless=True) +
                Keyword("null", caseless=True))
    primary_key = (Keyword("primary", caseless=True) +
                   Keyword("key", caseless=True))
    references = (Keyword("references", caseless=True) + identifier.copy() +
                  Combine("(" + identifier.copy() + ")"))
    unique = Keyword("unique", caseless=True)
    
    column = (column_name + column_type + Optional(not_null) +
              Optional(primary_key) + Optional(references) + Optional(unique))
    columns = ZeroOrMore(column + ',') + Optional(column)
    
    unique = Keyword("UNIQUE", caseless=True) + "(" + identifiers.copy() + ")"
    unique = unique.setResultsName("uniques", listAllMatches=True)
    table_constraints = ZeroOrMore(unique + ",") + Optional(unique)
    
    create_stmt = Forward()
    create_stmt << (create_token + table_token + table_name + "(" + columns +
                    table_constraints + ")")
    
    def __init__(self):
        super(CreateTableParser, self).__init__()

    def parse(self, sql):
        try:
            tokens = self.create_stmt.parseString(sql)
            return tokens.column_names
        except ParseException as error:
            print error
            
if __name__ == "__main__":
    CreateTableParser().parse('''
CREATE TABLE "django_site" (
"id" integer NOT NULL PRIMARY   KEY,
"domain" varchar,
"name" varchar,
"user_id" integer NOT NULL REFERENCES "auth_user" ("id")
UNIQUE ("app_label", "model")
)''')

