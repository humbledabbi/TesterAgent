import sqlite3

conn = sqlite3.connect("ai_test_memory.db")
cur = conn.cursor()
cur.execute("select * from test_memory;")
for row in cur.fetchall():
    print(row)
conn.close()