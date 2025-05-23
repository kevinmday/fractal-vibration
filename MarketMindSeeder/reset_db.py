import sqlite3

conn = sqlite3.connect("marketmind_seeder.db")
c = conn.cursor()

# ⚠️ WARNING: This will delete all existing intention data
c.execute("DROP TABLE IF EXISTS asset_intention")

c.execute("""
CREATE TABLE asset_intention (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT,
    timestamp TEXT,
    direction INTEGER,
    scale REAL,
    notes TEXT,
    level TEXT,
    source TEXT
)
""")

conn.commit()
conn.close()

print("✅ Database table 'asset_intention' has been reset.")
