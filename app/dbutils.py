import sqlite3
from flask import g

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('db.sqlite')
    g.db = db

def close_connection():
    if g.db is not None:
        g.db.close()

def create_model():
    sql = 'create table if not exists syncs (id integer PRIMARY KEY, source text, dest text, status text)'
    g.db.execute(sql)
    g.db.commit()

def query_db(query, args=(), one=False):
    cur = g.db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv

def save_db(sync_object):
    sql = 'insert into syncs (source, dest, status) values ("' + sync_object.source + '", "' + sync_object.dest + '", "' + sync_object.status +'")'
    cur = g.db.execute(sql)
    g.db.commit()
    return(cur.lastrowid)