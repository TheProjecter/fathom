#!/usr/bin/python3

class FathomError(Exception):
    pass

class FathomParsingError(FathomError):
    
    def __init__(self, msg, sql=None):
        self.msg = msg
        self.sql = sql
        
    def __str__(self):
        return 'Failed to parse %s.' % self.msg
