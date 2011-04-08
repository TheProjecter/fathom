#!/usr/bin/python3

import argparse

import fathom

DESCRIPTION = 'Build django models from database schema.'

def database2django():
    pass

def table2django():
    pass

def fathom2django(args):
    pass

def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    subparsers = parser.add_subparsers(dest="database_type")
    
    postgres = subparsers.add_parser('postgresql')
    postgres.add_argument('connection', type=str, help='connection string')
    
    sqlite = subparsers.add_parser('sqlite3')
    sqlite.add_argument('path', type=str, help='database path')
    
    mysql = subparsers.add_parser('mysql')
    mysql.add_argument('db', type=str, help='database name')
    mysql.add_argument('-u', '--user', type=str, help='database user')
    mysql.add_argument('-p', '--password', type=str, help='database password')
    mysql.add_argument('-H', '--host', type=str, help='database host')
    mysql.add_argument('-P', '--port', type=str, help='database port')
    
    args = vars(parser.parse_args())
    fathom2django(args)

if __name__ == "__main__":
    main()
