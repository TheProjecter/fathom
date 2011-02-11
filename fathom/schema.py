#!/usr/bin/python

class Database(object):
    
    def __init__(self, name='', inspector=None):
        # TODO: somehow database name should be set too, maybe inspector should
        # get it too
        super(Database, self).__init__()
        self.name = name
        self.inspector = inspector

        self._tables = None
        self._views = None

    def _refresh_tables(self):
        if self.inspector is not None:
            self._tables = self.inspector.get_tables()
        else:
            self._tables = []
        
    def _get_tables(self):
        if self._tables is None:
            self._refresh_tables()
        return self._tables
    
    tables = property(_get_tables)
    
    def _refresh_views(self):
        if self.inspector is not None:
            self._views = self.inspector.get_views()
        else:
            self._views = []
    
    def _get_views(self):
        if self._views is None:
            self._refresh_views()
        return self._views
        
    views = property(_get_views)
        
    def add_table(self, name):
        self.tables[name] = Table(name)
        return self.tables[name]
        
    def add_view(self, name):
        self.views[name] = View(name)
        return self.views[name]
    
    def add_index(self, name):
        self.indices[name] = Index(name)
        return self.indices[name]
        
    def add_stored_procedure(self, name):
        self.stored_procedures[name] = StoredProcedure(name)
        return self.stored_procedures[name]


class Table(object):
    
    def __init__(self, name):
        super(Table, self).__init__()
        self.name = name
        self.columns = dict()
        
    def add_column(self, name):
        self.columns[name] = Column(name)
        return self.columns[name]
        

class View(object):
    
    def __init__(self, name):
        super(View, self).__init__()
        self.name = name


class Index(object):
    
    def __init__(self, name):
        super(Index, self).__init__()
        self.name = name
        

class StoredProcedure(object):
    
    def __init__(self, name):
        super(Table, self).__init__()
        self.name = name
        self.parametres = dict()
        

class Column(object):
    
    def __init__(self, name):
        super(Column, self).__init__()
        self.name = name
