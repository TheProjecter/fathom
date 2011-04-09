#!/usr/bin/python3

import fathom
from fathom.utils import FathomArgumentParser

DESCRIPTION = 'Build graphviz ER diagrams from database schema.'

def database2graphviz(db):
    print("digraph G {")
    for table in db.tables.values():
        table_node(table)
    for table in db.tables.values():
        table_connections(table)
    print("}")

def table_node(table):
    print(' "%s"[shape=box];' % table.name)
    
def table_connections(table):
    for fk in table.foreign_keys:
        print(' "%s" -> "%s";' % (table.name, fk.referenced_table))
    
def table2django(table):
    class_name = build_class_name(table)
    fields = build_fields(table)
    result = 'class %s(model.Model):\n' % class_name
    for field in fields:
        result += '    %s' % field
    result += '''\n    class Meta:
        db_table = %s''' % table.name
    result += '\n'
    print(result)

def main():
    parser = FathomArgumentParser(description=DESCRIPTION)
    db, args = parser.parse_args()
    database2graphviz(db)

if __name__ == "__main__":
    main()
