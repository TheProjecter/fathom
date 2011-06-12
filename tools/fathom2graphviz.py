#!/usr/bin/python3

from subprocess import Popen, PIPE

from fathom.utils import FathomArgumentParser

DESCRIPTION = 'Build graphviz ER diagrams from database schema.'

def database2graphviz(db, args):
    result = "digraph G {\n\n"
    table_nodes = [table_node(table, args) for table in db.tables.values()]
    result += '\n'.join(table_nodes) + '\n\n'
    all_table_connections = [table_connections(table) 
                             for table in db.tables.values()]
    result += '\n'.join([connection for connection in all_table_connections
                                    if connection]) + '\n\n'
    result += "}\n"
    mode = 'w'
    if args.dot is not None:
        result = run_dot(result, args.dot)
        mode += 'b'
    if args.output is not None:
        with open(args.output, mode) as file:
            file.write(result)
    else:
        print(result)

def run_dot(code, format):
    process = Popen(['dot', '-T', format], stdin=PIPE, stdout=PIPE)
    return process.communicate(input=bytes(code, 'utf-8'))[0]

def table_node(table, args):
    if not args.include_columns:
        return ' "%s"[shape=box];' % table.name
    else:
        columns = []
        for column in table.columns.values():
            args = (column.name, column.name, column.type)
            columns.append('<tr><td port="%s">%s: %s</td></tr>' % args)
        columns = ''.join(columns)
        label = '<table><tr><td bgcolor="lightgrey">%s</td></tr>%s</table>' % \
                (table.name, columns)
        return ' "%s"[shape=none,label=<%s>];' % (table.name, label)

def table_connections(table):
    result = []
    for fk in table.foreign_keys:
        args = (table.name, fk.columns[0], fk.referenced_table, 
                fk.referenced_columns[0])
        result.append(' %s:%s -> %s:%s;' % args)
    return '\n'.join(result)

def main():
    parser = FathomArgumentParser(description=DESCRIPTION)
    parser.add_argument('--include-columns', action='store_true', default=False,
                        help='shows columns in the result')
    parser.add_argument('-o', '--output', help='print output to a file')
    parser.add_argument('-d', '--dot', metavar='FORMAT',
                        help='runs dot and produces output in given format')
    db, args = parser.parse_args()
    database2graphviz(db, args)

if __name__ == "__main__":
    main()
