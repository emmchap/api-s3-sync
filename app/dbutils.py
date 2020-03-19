import sqlite3
from flask import g

class dbModel:
    def __init__(self):
        self._db=':memory:'
    
    def get_db(self):
        db = getattr(g, '_database', None)
        if db is None:
            db = g._database = sqlite3.connect(self._db)
        return db
    
    def close_connection(self, exception):
        db = getattr(g, '_database', None)
        if db is not None:
            db.close()