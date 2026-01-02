import sqlite3

conn = sqlite3.connect('predictions.db')
cursor = conn.cursor()

print("PREDICTION_HISTORY TABLE SCHEMA:")
print("="*60)
cursor.execute('PRAGMA table_info(prediction_history)')
for row in cursor.fetchall():
    print(f"{row[1]:20} {row[2]:15}")

print("\n\nSAMPLE DATA:")
print("="*60)
cursor.execute('SELECT * FROM prediction_history WHERE was_correct IS NOT NULL LIMIT 2')
columns = [description[0] for description in cursor.description]
print("Columns:", columns)
for row in cursor.fetchall():
    for col, val in zip(columns, row):
        print(f"  {col}: {val}")
    print()

conn.close()
