import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.prediction_agent import PredictionAgent
from src.utils.filter_companies import TOP_5_NIFTY, INDICES
import time

def main():
    print("🚀 RETRYING PREDICTIONS WITH REALISTIC CONSTRAINTS & RATE LIMITING")
    print("This process will take about 10-15 minutes due to quota safety delays.")
    
    agent = PredictionAgent()
    
    # Combined list
    all_symbols = list(TOP_5_NIFTY.keys()) + list(INDICES.keys())
    print(f"Queue: {len(all_symbols)} items")
    
    for i, symbol in enumerate(all_symbols):
        print(f"\n[{i+1}/{len(all_symbols)}] Processing {symbol}...")
        
        try:
            # 1. Daily Prediction (Uses new realistic prompt)
            res = agent.predict_daily(symbol, save=True)
            if res:
                print(f"   > Daily Move: {res.get('predicted_move')}%")
            else:
                print("   > Daily Failed")
            
            time.sleep(1) # Fast processing for paid tier
            
            # 2. Weekly Prediction
            agent.predict_weekly(symbol, save=True)
            time.sleep(10)
            
            # 3. Monthly Prediction
            agent.predict_monthly(symbol, save=True)
            time.sleep(10)
            
        except Exception as e:
            print(f"Error processing {symbol}: {e}")
            
    print("\n✅ RETRY COMPLETE! Please refresh the dashboard.")

if __name__ == "__main__":
    main()
