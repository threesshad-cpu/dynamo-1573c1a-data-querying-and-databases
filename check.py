import sqlite3
conn = sqlite3.connect('task/data/manufacturing.db')
print(conn.execute("SELECT * FROM parts WHERE part_id='L100'").fetchall())
print(conn.execute("SELECT * FROM parts WHERE part_id='SA100'").fetchall())
