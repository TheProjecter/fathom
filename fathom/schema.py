#!/usr/bin/python3

lower = lambda string: string.lower()
upper = lambda string: string.upper()

class Named(object):
    
    def __init__(self, name):
        super(Named, self).__init__()
        self.name = name

class Database(Named):
    
    def __init__(self, name='', inspector=None, **kwargs):
        # TODO: somehow database name should be set too, maybe inspector should
        # get it too
        super(Database, self).__init__(name, **kwargs)
        self.inspector = inspector

        self._tables = None
        self._views = None
        self._procedures = None
        self._triggers = None
        
    def get_refresh_method(name):
        def refresh_attribute(self):
            if self.inspector is not None:
                value = getattr(self.inspector, 'get_' + name)()
                setattr(self, '_' + name,  value)
            else:
                setattr(self, '_' + name, {})
        return refresh_attribute

    _refresh_tables = get_refresh_method('tables')
            
    def _get_tables(self):
        if self._tables is None:
            self._refresh_tables()
            for table in self._tables.values():
                table.database = self
        return self._tables

    def _set_tables(self, tables):
        assert self.inspector is None, "Cannot set tables on already inspected database"
        self._tables = tables
	 
    
    tables = property(_get_tables, _set_tables)
    
    _refresh_views = get_refresh_method('views')
    
    def _get_views(self):
        if self._views is None:
            self._refresh_views()
        return self._views
        
    views = property(_get_views)

    _refresh_procedures = get_refresh_method('procedures')
    
    def _get_procedures(self):
        if self._procedures is None:
            self._refresh_procedures()
        return self._procedures
    
    procedures = property(_get_procedures)
    
    _refresh_triggers = get_refresh_method('triggers')
    
    def _get_triggers(self):
        if self._triggers is None:
            self._refresh_triggers()
        return self._triggers
        
    triggers = property(_get_triggers)
    
    def supports_stored_procedures(self):
        return self.inspector.supports_stored_procedures()


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
    
    def __init__(self, name, inspector=None, **kwargs):
        super(Table, self).__init__(name, **kwargs)
        self.inspector = inspector
        self._indices = None
        self._foreign_keys = None

    def _get_indices(self):
        if self._indices is None:
            self.inspector.build_indices(self)
        return self._indices
    
    def _set_indices(self, indices):
        self._indices = indices
    
    indices = property(_get_indices, _set_indices)
    
    def _get_foreign_keys(self):
        if self._foreign_keys is None:
            self.inspector.build_foreign_keys(self)
        return self._foreign_keys
        
    def _set_foreign_keys(self, foreign_keys):
        self._foreign_keys = foreign_keys
        
    foreign_keys = property(_get_foreign_keys, _set_foreign_keys)
        

class View(Named, WithColumns):
    
    def __init__(self, name, inspector=None, **kwargs):
        super(View, self).__init__(name, **kwargs)
        self.inspector = inspector


class Index(Named):
    
    def __init__(self, name, inspector=None, **kwargs):
        super(Index, self).__init__(name, **kwargs)
        self._columns = None
        self.inspector = inspector
        
    def _get_columns(self):
        if self._columns is None:
            self._columns = self.inspector.get_index_columns(self)
        return self._columns
        
    columns = property(_get_columns)

        
class Procedure(Named):
    
    def __init__(self, name, inspector=None, **kwargs):
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
    
    def __init__(self, name, when=None, event=None, inspector=None, **kwargs):
        super(Trigger, self).__init__(name, **kwargs)
        self._table = None
        self.when = when
        self.event = event
        self.inspector = inspector
        
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
