import sqlite3
conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()
tables = [r[0] for r in cur.execute("select name from sqlite_master where type='table'").fetchall()]
print(sorted(tables))
