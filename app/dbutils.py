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
    sql = 'create table if not exists syncs (id integer PRIMARY KEY, status text, progress text)'
    g.db.execute(sql)
    g.db.commit()

def query_db(query, args=(), one=False):
    cur = g.db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv

def get_sync_status(id):
    return query_db('select id, status, progress from syncs where id=' + id)[0]

def get_running_syncs():
    return query_db('select id from syncs where status like "running"')

def cancel_sync(id):
    if get_sync_status(id)['status'] == 'running':
        sql = 'update syncs set status="cancelled" where id=' + id
        g.db.execute(sql)
        g.db.commit()

def save_sync(sync_object):
    if sync_object.id is None:
        sql = 'insert into syncs (status, progress) values ("' + sync_object.status + '", "' + sync_object.progress + '")'
    else:
        sql = 'update syncs set status="' + sync_object.status +'", progress="' + sync_object.progress + '" where id=' + sync_object.id
    cur = g.db.execute(sql)
    id = str(cur.lastrowid)
    g.db.commit()
    return(id)