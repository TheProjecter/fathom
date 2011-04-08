#!/usr/bin/python3

import argparse

import fathom

DESCRIPTION = 'Build django models from database schema.'

def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    subparsers = parser.add_subparsers()
    subparsers.add_parser('postgresql')
    subparsers.add_parser('sqlite3')
    subparsers.add_parser('mysql')
    parser.parse_args()

if __name__ == "__main__":
    main()
