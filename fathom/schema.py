#!/usr/bin/python

class Database(object):
    
    def __init__(self, name=''):
        # TODO: somehow database name should be set too, maybe inspector should
        # get it too
        super(Database, self).__init__()
        self.name = name
        self.tables = dict()
        self.views = dict()
        self.indices = dict()
        self.stored_procedures = dict()
        
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
