#!/usr/bin/python3

lower = lambda string: string.lower()
upper = lambda string: string.upper()

class Named(object):
    
    def __init__(self, name):
        super(Named, self).__init__()
        self.name = name


def build_get_database_objects_function(name):
    def function(self):
        if getattr(self, '_' + name, None) is None:
            if self.inspector is not None:
                dictionary = getattr(self.inspector, 'get_' + name)()
                for obj in dictionary.values():
                    obj.database = self
                setattr(self, '_' + name, dictionary)
            else:
                setattr(self, '_' + name, {})
        return getattr(self, '_' + name)
    return function
    
def build_set_database_objects_function(name):
    def function(self, dictionary):
        assert self.inspector is None, \
               'Cannot set tables on already inspected database!'
        setattr(self, '_' + name, dictionary)
    return function
        
def build_accessors(name):
    return (build_get_database_objects_function(name),
            build_set_database_objects_function(name))

class Database(Named):
    
    def __init__(self, name='', inspector=None, **kwargs):
        # TODO: somehow database name should be set too, maybe inspector should
        # get it too
        super(Database, self).__init__(name, **kwargs)
        self.inspector = inspector
        self.refresh()
                        
    def refresh(self):
        self._tables = None
        self._views = None
        self._procedures = None
        self._triggers = None
        self._indices = None
        
    def _get_version(self):
        return self.inspector.version
    version = property(_get_version)
                
    def _get_case_sensitivity(self):
        return self.inspector.CASE_SENSITIVITY
    case_sensitivity = property(_get_case_sensitivity)
        
    tables = property(*build_accessors('tables'))
    views = property(*build_accessors('views'))
    procedures = property(*build_accessors('procedures'))
    indices = property(*build_accessors('indices'))
    triggers = property(*build_accessors('triggers'))
            
    def supports_stored_procedures(self):
        return self.inspector.supports_stored_procedures()
    
    def case(self, string):
        if self.inspector is not None:
            return self.inspector.case(string)
        return string

class WithColumns(object):

    def __init__(self):
        super(WithColumns, self).__init__()
        self._columns = None

    def _get_columns(self):
        if self._columns is None:
            self.inspector.build_columns(self)
        return self._columns
    
    def _set_columns(self, columns):
        self._columns = columns
    
    columns = property(_get_columns, _set_columns)


class Table(Named, WithColumns):
    
    def __init__(self, name, database=None, inspector=None):
        super(Table, self).__init__(name)
        self.inspector = inspector
        self._foreign_keys = None
        self.database = database
    
    def _get_foreign_keys(self):
        if self._foreign_keys is None:
            self.inspector.build_foreign_keys(self)
        return self._foreign_keys
        
    def _set_foreign_keys(self, foreign_keys):
        self._foreign_keys = foreign_keys
        
    foreign_keys = property(_get_foreign_keys, _set_foreign_keys)
    
    def drop(self):
        if self.inspector:
            self.inspector.drop_table(self)
        if self.database:
            del self.database.tables[self.name]
        

class View(Named, WithColumns):
    
    def __init__(self, name, database=None, inspector=None, **kwargs):
        super(View, self).__init__(name, **kwargs)
        self.inspector = inspector
        self.database = database


class Index(Named):
    
    def __init__(self, name, table, base_name=None, database=None, 
                 inspector=None, **kwargs):
        super(Index, self).__init__(name, **kwargs)
        self.table = table
        self._columns = None
        self.is_unique = False
        self.inspector = inspector
        self.base_name = base_name if base_name is not None else name
        self.database = database
        
    def _get_columns(self):
        if self._columns is None:
            self._columns = self.inspector.get_index_columns(self)
        return self._columns
        
    columns = property(_get_columns)

        
class Procedure(Named):
    
    def __init__(self, name, database=None, inspector=None, **kwargs):
        super(Procedure, self).__init__(name, **kwargs)
        self._arguments = None
        self.returns = None
        self.inspector = inspector
        # this is a protected dictionary that can be used by inspectors to
        # hold additional data required to operate on schema object
        self._private = {}
                
    def get_argument_types(self):
        types = []
        for argument in list(self.arguments.values()):
            type = argument.type
            types.append('varchar' if type.startswith('varchar') else type)
        return types
        
    def _get_arguments(self):
        if self._arguments is None:
            self.inspector.build_procedure(self)
        return self._arguments
        
    def _set_arguments(self, arguments):
        self._arguments = arguments

    arguments = property(_get_arguments, _set_arguments)
            

class Trigger(Named):
    
    BEFORE, AFTER, INSTEAD = range(3)
    UPDATE, INSERT, DELETE = range(3)
    
    def __init__(self, name, when=None, event=None, database=None, 
                 inspector=None, **kwargs):
        super(Trigger, self).__init__(name, **kwargs)
        self._table = None
        self.when = when
        self.event = event
        self.inspector = inspector
        self.database = database
        
    def _get_table(self):
        if self._table is None:
            self.inspector.build_trigger(self)
        return self._table
        
    def _set_table(self, table):
        self._table = table
        
    table = property(_get_table, _set_table)


class Argument(Named):
    
    def __init__(self, name, type, **kwargs):
        super(Argument, self).__init__(name, **kwargs)
        self.type = type


class Column(Named):
    
    def __init__(self, name, type, not_null=False, default=None, **kwargs):
        super(Column, self).__init__(name, **kwargs)
        self.type = type
        self.not_null = not_null
        self.default = default


class ForeignKey(object):
    
    def __init__(self):
        super(object, self).__init__()
        self.columns = []
        self.referenced_table = None
        self.referenced_columns = []
