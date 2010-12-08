import sys
from abc import ABCMeta, abstractmethod

class DatabaseInspector:
    __metaclass__ = ABCMeta
    
    def __init__(self, *db_params):
        self._db_params = db_params
        
    def get_tables(self):
        return [row[0] for row in self._select(self._TABLE_NAMES_SQL)]
        
    @abstractmethod
    def get_fields(self, table):
        pass
    
    def _select(self, sql):
        connection = self._api.connect(*self._db_params)
        cursor = connection.cursor()
        cursor.execute(self._TABLE_NAMES_SQL)
        rows = list(cursor)
        connection.close()
        return rows


class SqliteInspector(DatabaseInspector):
    
    _TABLE_NAMES_SQL = "SELECT name FROM sqlite_master"
    
    def __init__(self, *db_params):
        DatabaseInspector.__init__(self, *db_params)
        import sqlite3
        self._api = sqlite3
        
    def get_fields(self, table):
        pass


class PostgresInspector(DatabaseInspector):
    
    _TABLE_NAMES_SQL = "SELECT table_name FROM information_schema.tables " \
                        "WHERE table_schema = 'public'"
    
    def __init__(self, *db_params):
        DatabaseInspector.__init__(self, *db_params)
        import psycopg2
        self._api = psycopg2
        
    def get_fields(self, table):
        pass
        

if __name__ == "__main__":
    print SqliteInspector("test.db3").get_tables()
    print PostgresInspector("dbname=django user=django").get_tables()
