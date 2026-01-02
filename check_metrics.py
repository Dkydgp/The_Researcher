import sqlite3

try:
    conn = sqlite3.connect('predictions.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM daily_accuracy_metrics ORDER BY date DESC LIMIT 5")
    rows = cursor.fetchall()
    if rows:
        print("Found metrics:")
        for row in rows:
            print(row)
    else:
        print("No metrics found in daily_accuracy_metrics.")
        
    # Check table schema
    cursor.execute("PRAGMA table_info(daily_accuracy_metrics)")
    columns = cursor.fetchall()
    print("\nSchema:")
    for col in columns:
        print(col)
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")
