import sqlite3

DB_NAME = "database.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  
    return conn

def init_db():
    with sqlite3.connect(DB_NAME) as db:
        with open("schema.sql", "r", encoding="utf-8") as f:
            db.executescript(f.read())

from db import init_db

init_db()