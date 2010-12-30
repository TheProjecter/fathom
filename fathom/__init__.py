#!/usr/bin/python

from inspectors import PostgresInspector, SqliteInspector

if __name__ == "__main__":
    print 'sqlite3'
    sqlite = SqliteInspector("test.db3")
    for table in sqlite.get_tables():
        print table, sqlite.get_columns(table)
    sqlite.build_scheme()
    pgsql = PostgresInspector("dbname=django user=django")
    print 'postgresql'
    for table in pgsql.get_tables():
        print table, pgsql.get_columns(table)
    pgsql.build_scheme()
