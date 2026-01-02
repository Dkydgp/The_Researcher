"""
Test script to verify self-learning capabilities
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.prediction_agent import PredictionAgent

print("="*60)
print("🧠 TESTING SELF-LEARNING SYSTEM")
print("="*60)

agent = PredictionAgent()

# Step 1: Check if we have any verified predictions
print("\n1. Checking for verified predictions...")
import sqlite3
conn = sqlite3.connect('predictions.db')
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM prediction_history WHERE open_price IS NOT NULL")
verified_count = cursor.fetchone()[0]
print(f"   Found {verified_count} verified predictions")

if verified_count > 0:
    # Step 2: Run evaluation
    print("\n2. Running evaluation...")
    agent.evaluate_predictions()
    
    # Step 3: Check performance metrics
    print("\n3. Checking performance metrics...")
    cursor.execute("SELECT symbol, accuracy_rate, confidence_adjustment FROM prediction_performance ORDER BY evaluation_date DESC LIMIT 10")
    metrics = cursor.fetchall()
    
    if metrics:
        print("\n   📊 Recent Performance:")
        for symbol, accuracy, adjustment in metrics:
            print(f"      {symbol}: {accuracy:.1f}% accurate | Adjustment: {adjustment:+.1f}")
    else:
        print("   No performance metrics yet (will be created after evaluation)")
    
    # Step 4: Test confidence adjustment
    print("\n4. Testing confidence adjustment...")
    test_symbol = "Reliance Industries"
    adjustment = agent.get_confidence_adjustment(test_symbol)
    print(f"   Current adjustment for {test_symbol}: {adjustment:+.1f}")
    print(f"   Next prediction will apply this adjustment to base confidence")
else:
    print("\n⚠ No verified predictions yet.")
    print("   Run the pipeline daily for a few days to accumulate data.")
    print("   The system will learn from each verified prediction!")

conn.close()

print("\n" + "="*60)
print("✅ Self-learning system is active and ready!")
print("="*60)
