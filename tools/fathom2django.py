#!/usr/bin/python3

from re import match

from fathom.utils import FathomArgumentParser

DESCRIPTION = 'Build django models from database schema.'

class DjangoExporter:
    
    def __init__(self, db, filter=None, output=None):
        self.db = db
        self.filter = filter
        self.output = output
        
    def run(self):
        self.filter_tables()
        result = ''.join([self.table2django(table) 
                          for table in self.tables.values()])
        if self.output is not None:
            with open(self.args.output, 'w') as file:
                file.write(result)
        else:
            print(result)
    
    def filter_tables(self):
        if self.filter is not None:
            self.tables = {key: value for key, value in self.db.tables.items() 
                                      if match(self.filter, key)}
        else:
            self.tables = self.db.tables

        
    def table2django(self, table):
        class_name = self.build_class_name(table)
        fields = self.build_fields(table)
        result = 'class %s(model.Model):\n' % class_name
        for field in fields:
            result += '    %s' % field
        result += '''\n    class Meta:
            db_table = %s''' % table.name
        result += '\n\n'
        return result

    def build_class_name(self, table):
        if not isinstance(table, str):
            table = table.name
        return ''.join([part.title() for part in table.split('_')])
    
    def build_fields(self, table):
        result = []
        for column in table.columns.values():
            if column.type == 'integer':
                if column.name == 'id':
                    pass # django implictly creates id field
                else:
                    value = self.try_foreign_key(table, column)
                    if value:
                        result.append(value)
                    else:
                        result.append('%s = models.IntegerField()\n' % column.name)
            elif column.type == 'smallint':
                result.append('%s = models.PositiveSmallIntegerField()\n' % 
                              column.name)
            elif column.type == 'float' or column.type.startswith('double'):
                result.append('%s = models.FloatField()\n' % column.name)
            elif column.type == 'bool' or column.type == 'boolean':
                result.append('%s = models.BooleanField()\n' % column.name)
            elif column.type == 'date':
                result.append('%s = models.DateField()\n' % column.name)
            elif column.type == 'datetime' or column.type.startswith('timestamp'):
                result.append('%s = models.DateTimeField()\n' % column.name)
            elif column.type == 'text':
                result.append('%s = models.TextField()\n' % column.name)
            elif column.type.startswith('varchar'):
                result.append(self.build_varchar_field(column))
            else:
                # can't determine type, adding warning
                comment = '# failed to build field for column %s: %s\n' % \
                          (column.name, column.type)
                result.append(comment)
        return result
        
    def try_foreign_key(self, table, column):
        for fk in table.foreign_keys:
            if len(fk.columns) == 1 and column.name == fk.columns[0]:
                class_name = self.build_class_name(fk.referenced_table)
                args = column.name.split('_')[0], class_name
                return '%s = models.ForeignKey(%s)\n' % args
    
    def build_varchar_field(self, column):
        length = int(column.type.split('(')[1][:-1])
        return '%s = model.CharField(max_length=%d)\n' % (column.name, length)
        
def main():
    parser = FathomArgumentParser(description=DESCRIPTION)
    parser.add_argument('-o', '--output', help='print output to a file')
    parser.add_argument('--filter', help='regular expression by which tables '
                                         'will be filtered')
    db, args = parser.parse_args()
    DjangoExporter(db, filter=args.filter, output=args.output).run()

if __name__ == "__main__":
    main()
