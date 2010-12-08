import sys
from abc import ABCMeta, abstractmethod

class DatabaseInspector:
    __metaclass__ = ABCMeta
    
    def __init__(self, *db_params):
        self._db_params = db_params
        
    def get_tables(self):
        return [row[0] for row in self._select(self._TABLE_NAMES_SQL)]
        
    @abstractmethod
    def get_columns(self, table):
        pass
    
    def _select(self, sql):
        connection = self._api.connect(*self._db_params)
        cursor = connection.cursor()
        cursor.execute(sql)
        rows = list(cursor)
        connection.close()
        return rows


class SqliteInspector(DatabaseInspector):
    
    _TABLE_NAMES_SQL = "SELECT name FROM sqlite_master"
    
    def __init__(self, *db_params):
        DatabaseInspector.__init__(self, *db_params)
        import sqlite3
        self._api = sqlite3
        
    def get_columns(self, table):
        pass


class PostgresInspector(DatabaseInspector):
    
    _TABLE_NAMES_SQL = """SELECT table_name 
                          FROM information_schema.tables 
                          WHERE table_schema = 'public'"""
    _COLUMN_NAMES_SQL = """SELECT column_name 
                           FROM information_schema.columns
                           WHERE table_name = '%s'"""
    
    def __init__(self, *db_params):
        DatabaseInspector.__init__(self, *db_params)
        import psycopg2
        self._api = psycopg2
        
    def get_columns(self, table):
        sql = self._COLUMN_NAMES_SQL % table
        return [row[0] for row in self._select(sql)]
        

if __name__ == "__main__":
    print SqliteInspector("test.db3").get_tables()
    pgsql = PostgresInspector("dbname=django user=django")
    for table in pgsql.get_tables():
        print table, pgsql.get_columns(table)
