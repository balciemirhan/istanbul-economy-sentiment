import sqlite3

conn = sqlite3.connect('istanbul_ekonomi.db')
c = conn.cursor()
c.execute('SELECT id, text FROM tweets ORDER BY created_at ASC')
tweets = c.fetchall()

seen = set()
to_delete = []

for t_id, text in tweets:
    prefix = text[:50]
    if prefix in seen:
        to_delete.append((t_id,))
    else:
        seen.add(prefix)

print(f"Eski kopyalardan silinecek olanlar: {len(to_delete)} adet.")
c.executemany('DELETE FROM tweets WHERE id = ?', to_delete)
conn.commit()
conn.close()
print("Veritabani temizlendi!")
