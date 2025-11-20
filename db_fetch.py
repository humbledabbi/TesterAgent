import sqlite3

conn = sqlite3.connect("ai_test_memory.db")
cur = conn.cursor()
cur.execute("SELECT code FROM test_memory LIMIT 1;")
for row in cur.fetchall():
    print(row)
conn.close()