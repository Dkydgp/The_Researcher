"""
Clean up future/incomplete predictions from database
Keeps only predictions for dates that have already passed
"""

import sqlite3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
from src.utils.config import config

def cleanup_future_predictions():
    conn = sqlite3.connect('predictions.db')
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("CLEANING UP FUTURE/INCOMPLETE PREDICTIONS")
    print("="*60)
    
    # Get today's date
    today = date.today().isoformat()
    print(f"\n📅 Today's date: {today}")
    
    # 1. Count total predictions
    total = cursor.execute("SELECT COUNT(*) FROM prediction_history").fetchone()[0]
    print(f"\n📊 Total predictions in database: {total}")
    
    # 2. Count future predictions (prediction_date > today)
    future = cursor.execute("""
        SELECT COUNT(*) FROM prediction_history 
        WHERE prediction_date > ?
    """, (today,)).fetchone()[0]
    print(f"⏰ Future predictions (will be deleted): {future}")
    
    # 3. Count past/today predictions (will be kept)
    past = cursor.execute("""
        SELECT COUNT(*) FROM prediction_history 
        WHERE prediction_date <= ?
    """, (today,)).fetchone()[0]
    print(f"✅ Past/Today predictions (will be kept): {past}")
    
    # 4. Show future predictions by stock
    if future > 0:
        print("\n📋 Future predictions to be deleted:")
        future_stocks = cursor.execute("""
            SELECT symbol, prediction_date, direction, confidence_score
            FROM prediction_history 
            WHERE prediction_date > ?
            ORDER BY symbol, prediction_date
        """, (today,)).fetchall()
        
        for stock, pred_date, direction, confidence in future_stocks:
            print(f"   {stock:20s} - Date: {pred_date}, Direction: {direction:8s}, Confidence: {confidence}/10")
    
    # 5. Ask for confirmation
    if future > 0:
        print("\n" + "="*60)
        print(f"⚠️  This will DELETE {future} future predictions")
        print("="*60)
        response = input("\nProceed with deletion? (yes/no): ").strip().lower()
        
        if response != 'yes':
            print("\n❌ Cleanup cancelled.")
            conn.close()
            return
        
        # 6. Delete future predictions
        print("\n🗑️  Deleting future predictions...")
        cursor.execute("""
            DELETE FROM prediction_history 
            WHERE prediction_date > ?
        """, (today,))
        
        deleted = cursor.rowcount
        conn.commit()
        
        print(f"✅ Deleted {deleted} future predictions")
    else:
        print("\n✅ No future predictions to delete!")
    
    # 7. Show final stats
    remaining = cursor.execute("SELECT COUNT(*) FROM prediction_history").fetchone()[0]
    print(f"\n📊 Remaining predictions: {remaining}")
    
    if remaining > 0:
        print("\n📋 Predictions by stock:")
        stocks = cursor.execute("""
            SELECT symbol, COUNT(*) as count, MIN(prediction_date) as earliest, MAX(prediction_date) as latest
            FROM prediction_history 
            GROUP BY symbol
            ORDER BY count DESC
        """).fetchall()
        
        for stock, count, earliest, latest in stocks:
            print(f"   {stock:20s} - {count:3d} predictions (from {earliest} to {latest})")
    
    conn.close()
    
    print("\n" + "="*60)
    print("✅ CLEANUP COMPLETE!")
    print("="*60)
    print(f"\nDatabase now contains only predictions for dates <= {today}")

if __name__ == "__main__":
    cleanup_future_predictions()
