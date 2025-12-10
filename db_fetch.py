import sqlite3

conn = sqlite3.connect("ai_test_memory.db")
cur = conn.cursor()
cur.execute("SELECT * FROM test_memory;")
for row in cur.fetchall():
    print(row)
conn.close()