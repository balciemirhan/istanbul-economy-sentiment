import sqlite3

conn = sqlite3.connect('istanbul_ekonomi.db')
c = conn.cursor()
search_text = "taksi şoförünü defalarca yumruklayarak"
c.execute("SELECT id, text FROM tweets WHERE text LIKE ?", (f"%{search_text}%",))
results = c.fetchall()

print(f"Bulunan eslesme: {len(results)}")
for r in results:
    print(f"--- ID: {r[0]} ---")
    print(f"TEXT: {r[1]}")
    print(f"PREFIX50: '{r[1][:50]}'")
conn.close()
