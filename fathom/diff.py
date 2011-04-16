#!/usr/bin/python3

class DiffDatabase(object):

    def __init__(self, db1, db2):
        super(DiffDatabase, self).__init__()
        self.db1 = db1
        self.db2 = db2


    def	_get_tables(self):
        return {}

    tables = property(_get_tables)

