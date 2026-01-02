import subprocess
import sys
import os
import time

def run_step(command, description):
    print(f"\n{'='*60}")
    print(f"STEP: {description}")
    print(f"COMMAND: {command}")
    print(f"{'='*60}")
    
    try:
        # Using shell=True for windows compatibility and to handle potential path issues
        result = subprocess.run(command, shell=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nError in step '{description}': {e}")
        return False

def main():
    print("STARTING STOCK PREDICTION PIPELINE")
    start_time = time.time()
    
    steps = [
        ("python main.py fetch", "Fetching Latest News from RSS"),
        ("python -m src.utils.filter_companies", "Filtering News for Top 10 Companies + Indices (Smart Filter)"),
        ("python -m src.collectors.market_context_fetcher", "Fetching Global Market Context (S&P 500, Oil, USD/INR)"),
        ("python main.py prices", "Fetching Daily Stock Prices (Yahoo Finance)"),
        ("python main.py fundamentals", "Fetching Corporate Fundamentals (Screener.in)"),
        ("python scripts/prepare_training_data.py", "Merging Data into Training Dataset"),
        ("python -m src.core.prediction_agent", "Generating Enhanced AI Predictions with Technical Indicators"),
        ("python scripts/calculate_daily_accuracy.py", "Calculating Consolidated Accuracy Metrics")
    ]
    
    for cmd, desc in steps:
        if not run_step(cmd, desc):
            print(f"\nError in step '{desc}': Pipeline failed")
            sys.exit(1)
            
    end_time = time.time()
    duration = end_time - start_time
    print(f"\n{'='*60}")
    print(f"PIPELINE COMPLETED IN {duration:.2f} SECONDS")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
