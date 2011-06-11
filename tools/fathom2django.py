#!/usr/bin/python3

from re import match

from fathom.utils import FathomArgumentParser

DESCRIPTION = 'Build django models from database schema.'

class DjangoExporter:
    
    def __init__(self, db, filter=None, output=None):
        self.tables = db.tables
        self.filter = filter
        self.output = output
        
    def run(self):
        self.gather_through_tables()
        self.filter_tables()
        result = ''.join([self.table2django(table) 
                          for table in self.tables.values()])
        if self.output is not None:
            with open(self.args.output, 'w') as file:
                file.write(result)
        else:
            print(result)

    def gather_through_tables(self):
        tables = {}
        self.through_tables = {}
        for name, table in self.tables.items():
            through, explicit = self.is_through_table(table)
            if through:
                self.through_tables[name] = table
            if not through or explicit:
                tables[name] = table
        self.tables = tables

    @staticmethod
    def is_through_table(table):
        return len(table.foreign_keys) == 2, len(table.columns) > 3
    
    def filter_tables(self):
        if self.filter is not None:
            self.tables = {key: value for key, value in self.tables.items() 
                                      if match(self.filter, key)}

    def table2django(self, table):
        class_name = self.build_class_name(table)
        result = 'class %s(model.Model):\n' % class_name
        for field in self.build_fields(table):
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
        return result + self.build_many_to_many_fields(table)
        
    def build_many_to_many_fields(self, table):
        deleted = []
        result = []
        for through_table in self.through_tables.values():
            if self.needs_many_to_many(table, through_table):
                deleted.append(through_table.name)
                fks = through_table.foreign_keys
                index = 1 if fks[0].referenced_table == table.name else 0
                args = (fks[index].referenced_table, 
                        self.build_class_name(fks[index].referenced_table))
                result.append("%s = models.ManyToManyField('%s')\n" % args)
        for name in deleted:
            del self.through_tables[name]
        return result
            
    def needs_many_to_many(self, table, through_table):
        return table.name in self.referenced_tables(through_table)

    def try_foreign_key(self, table, column):
        for fk in table.foreign_keys:
            if len(fk.columns) == 1 and column.name == fk.columns[0]:
                class_name = self.build_class_name(fk.referenced_table)
                args = column.name.split('_')[0], class_name
                return '%s = models.ForeignKey(%s)\n' % args
    
    def build_varchar_field(self, column):
        length = int(column.type.split('(')[1][:-1])
        return '%s = model.CharField(max_length=%d)\n' % (column.name, length)
        
    def referenced_tables(self, table):
        return tuple((fk.referenced_table for fk in table.foreign_keys))
        
def main():
    parser = FathomArgumentParser(description=DESCRIPTION)
    parser.add_argument('-o', '--output', help='print output to a file')
    parser.add_argument('--filter', help='regular expression by which tables '
                                         'will be filtered')
    db, args = parser.parse_args()
    DjangoExporter(db, filter=args.filter, output=args.output).run()

if __name__ == "__main__":
    main()
