import oracledb
from flask import g

pool = None

def init_db(app):
    global pool
    pool = oracledb.create_pool(
        user=app.config['ORACLE_USER'],
        password=app.config['ORACLE_PASSWORD'],
        dsn=app.config['ORACLE_DSN'],
        min=2, max=10, increment=1
    )

def get_db():
    if 'db' not in g:
        g.db = pool.acquire()
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db:
        pool.release(db)
