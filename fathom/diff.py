#!/usr/bin/python3

UNCHANGED, CREATED, ALTERED, DROPPED = range(4)

class ColumnDiff(object):
    def __init__(self, name, source_col=None, dest_col=None):
        super(ColumnDiff, self).__init__()
        self.name = name
        self.source_col = source_col
        self.dest_col = dest_col
        self._state = None

    def _get_state(self):
        if self._state is None:
            if self.source_col is None and self.dest_col is not None:
                self._state = CREATED
            elif self.source_col is not None and self.dest_col is None:
                self._state = DROPPED
            else:
                if (self.source_col.type == self.dest_col.type and
                    self.source_col.not_null == self.dest_col.not_null and
                    self.source_col.default == self.dest_col.default):
                    self._state = UNCHANGED
                else:
                    self._state = ALTERED
        return self._state
    
    state = property(_get_state)


class TableDiff(object):
   
    def __init__(self, name, source_table=None, dest_table=None):
        super(TableDiff, self).__init__()
        self.name = name
        self.source_table = source_table
        self.dest_table = dest_table
        self._state = None
        self._columns = None
    
    def _get_state(self):
        if self._state is None:
            if self.source_table is None and self.dest_table is not None:
                self._state = CREATED
            elif self.source_table is not None and self.dest_table is None:
                self._state = DROPPED
            else:
                self._state = UNCHANGED
                for col in self.columns.values():
                    if col.state != UNCHANGED:
                        self._state = ALTERED
                        break
        return self._state
    
    state = property(_get_state) 


    def _get_columns(self):
        if self._columns == None:
            matching = {}
            source_cols = self.source_table.columns
            dest_cols = self.dest_table.columns
            #matching by name
            source_cols_names = {c for c in source_cols.keys()}
            dest_cols_names = {c for c in dest_cols.keys()}
            for name in source_cols_names & dest_cols_names:
                matching[name] = ColumnDiff(name, source_cols[name], dest_cols[name])
            for name in source_cols_names - dest_cols_names:
                matching[name] = ColumnDiff(name, source_cols[name], None)
            for name in dest_cols_names - source_cols_names:
                matching[name] = ColumnDiff(name, None, dest_cols[name])
            self._columns = matching
        return self._columns

    columns = property(_get_columns)


class DatabaseDiff(object):

    def __init__(self, source_db, dest_db):
        super(DatabaseDiff, self).__init__()
        if source_db is None or dest_db is None:
            raise ValueError
        self.source_db = source_db
        self.dest_db = dest_db
        self._tables = None 
    
    def _find_tables_matching(self):

        matching = {}

        source_tables = self.source_db.tables
        dest_tables = self.dest_db.tables
        
        #simply matching by name
        source_tables_names = { k for k in source_tables.keys()}
        dest_tables_names = {k for k in dest_tables.keys()}
        
        for name in source_tables_names & dest_tables_names:
            matching[name] = TableDiff(name=name, 
                                       source_table=source_tables[name], dest_table=dest_tables[name])
        for name in source_tables_names - dest_tables_names:
            matching[name] = TableDiff(name=name,
                                       source_table=source_tables[name], dest_table=None)
        for name in dest_tables_names - source_tables_names:
            matching[name] = TableDiff(name=name,
                                       source_table=None, dest_table=dest_tables[name])
        return matching

    def	_get_tables(self):
        if self._tables is None:
            self._tables = self._find_tables_matching()

        return self._tables

    tables = property(_get_tables)

