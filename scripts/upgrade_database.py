"""
Add self-learning capabilities to the predictions database
This migration adds accuracy tracking and performance metrics
"""
import sqlite3

def upgrade_database():
    conn = sqlite3.connect('predictions.db')
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("UPGRADING PREDICTIONS DATABASE - PHASE 1: ACTIVE LEARNING")
    print("="*60)
    
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(prediction_history)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    
    # Add new columns if they don't exist
    new_columns = {
        'was_correct': 'BOOLEAN',
        'accuracy_score': 'REAL',
        'error_margin': 'REAL'  # Difference between predicted and actual move
    }
    
    for col_name, col_type in new_columns.items():
        if col_name not in existing_columns:
            print(f"  Adding column: {col_name} ({col_type})")
            cursor.execute(f"ALTER TABLE prediction_history ADD COLUMN {col_name} {col_type}")
        else:
            print(f"  ✓ Column already exists: {col_name}")
    
    # Create performance tracking table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prediction_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            evaluation_date DATE,
            total_predictions INTEGER,
            correct_predictions INTEGER,
            accuracy_rate REAL,
            avg_confidence REAL,
            confidence_adjustment REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  ✓ Created prediction_performance table")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Database upgrade complete!")
    print("   New capabilities:")
    print("   - Track prediction accuracy")
    print("   - Calculate error margins")
    print("   - Store performance metrics per stock")

if __name__ == "__main__":
    upgrade_database()
