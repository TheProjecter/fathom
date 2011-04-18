#!/usr/bin/python3

from fathom.utils import FathomArgumentParser

DESCRIPTION = 'Build graphviz ER diagrams from database schema.'

def database2graphviz(db, args):
    print("digraph G {")
    for table in db.tables.values():
        table_node(table, args)
    for table in db.tables.values():
        table_connections(table)
    print("}")

def table_node(table, args):
    if not args.include_columns:
        print(' "%s"[shape=box];' % table.name)
    else:
        columns = ['<tr><td>%s: %s</td></tr>' % (column.name, column.type) 
                   for column in table.columns.values()]
        columns = ''.join(columns)
        label = '<table><tr><td bgcolor="lightgrey">%s</td></tr>%s</table>' % \
                (table.name, columns)
        print(' "%s"[shape=none,label=<%s>];' % (table.name, label))

def table_connections(table):
    for fk in table.foreign_keys:
        print(' "%s" -> "%s";' % (table.name, fk.referenced_table))

def main():
    parser = FathomArgumentParser(description=DESCRIPTION)
    parser.add_argument('--include-columns', action='store_true', default=False)
    db, args = parser.parse_args()
    database2graphviz(db, args)

if __name__ == "__main__":
    main()
