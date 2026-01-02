import sqlite3

db_path = 'predictions.db'
print(f"Migrating {db_path}...")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Add signals_aligned
try:
    cursor.execute("ALTER TABLE daily_predictions ADD COLUMN signals_aligned INTEGER DEFAULT 0")
    print("✅ Added column: signals_aligned")
except Exception as e:
    print(f"ℹ️ signals_aligned: {e}")

# 2. Add sentiment_score
try:
    cursor.execute("ALTER TABLE daily_predictions ADD COLUMN sentiment_score REAL DEFAULT 5.0")
    print("✅ Added column: sentiment_score")
except Exception as e:
    print(f"ℹ️ sentiment_score: {e}")

conn.commit()
conn.close()
print("Migration complete.")
