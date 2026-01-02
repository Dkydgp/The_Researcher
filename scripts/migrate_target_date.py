import sqlite3
import os

DB_PATH = "predictions.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    tables = ["prediction_history", "weekly_predictions", "monthly_predictions", "daily_predictions"]
    
    print("Migrating database schema...")
    
    for table in tables:
        try:
            # Check if table exists
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not cursor.fetchone():
                print(f"Table {table} does not exist, skipping.")
                continue
                
            # Check if column exists
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [info[1] for info in cursor.fetchall()]
            
            if "target_date" not in columns:
                print(f"Adding target_date column to {table}...")
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN target_date DATE")
            else:
                print(f"Column target_date already exists in {table}.")
                
        except Exception as e:
            print(f"Error migrating {table}: {e}")
            
    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
