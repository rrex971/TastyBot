import sqlite3

def load_db():
    c = sqlite3.connect("data.db")
    cur = c.cursor()
    c.execute("create table if not exists users(userID int(15), osuID int(15))")
    return cur, c
