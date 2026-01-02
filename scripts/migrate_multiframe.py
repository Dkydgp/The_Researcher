"""
Database Migration: Multi-Timeframe Prediction System
Creates three separate tables for daily, weekly, and monthly predictions
"""

import sqlite3
from datetime import datetime

def migrate_database():
    """Create new tables for multi-timeframe predictions"""
    
    conn = sqlite3.connect('predictions.db')
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("MULTI-TIMEFRAME PREDICTION SYSTEM - DATABASE MIGRATION")
    print("="*60)
    
    # 1. CREATE DAILY PREDICTIONS TABLE
    print("\n📅 Creating daily_predictions table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            prediction_date DATE NOT NULL,
            
            -- Prediction
            direction TEXT NOT NULL,
            predicted_move REAL,
            confidence_score INTEGER,
            probability REAL,
            
            -- Price Targets
            target_price_min REAL,
            target_price_max REAL,
            expected_range_min REAL,
            expected_range_max REAL,
            
            -- Risk Assessment
            risk_level TEXT,
            stop_loss REAL,
            volatility_forecast TEXT,
            
            -- Analysis
            rationale TEXT,
            key_factors TEXT,
            technical_summary TEXT,
            fundamental_summary TEXT,
            
            -- Verification (populated after market close)
            actual_open REAL,
            actual_close REAL,
            actual_high REAL,
            actual_low REAL,
            prediction_accuracy TEXT,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, prediction_date)
        )
    """)
    print("✅ daily_predictions table created")
    
    # 2. CREATE WEEKLY PREDICTIONS TABLE
    print("\n📊 Creating weekly_predictions table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weekly_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            prediction_date DATE NOT NULL,
            prediction_week TEXT NOT NULL,
            
            -- Prediction
            direction TEXT NOT NULL,
            predicted_move REAL,
            confidence_score INTEGER,
            probability REAL,
            
            -- Weekly Targets
            week_high_target REAL,
            week_low_target REAL,
            expected_range_min REAL,
            expected_range_max REAL,
            
            -- Trend Analysis
            trend_strength TEXT,
            support_levels TEXT,
            resistance_levels TEXT,
            
            -- Analysis
            rationale TEXT,
            weekly_outlook TEXT,
            key_events TEXT,
            technical_patterns TEXT,
            
            -- Verification
            actual_week_high REAL,
            actual_week_low REAL,
            actual_week_close REAL,
            prediction_accuracy TEXT,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, prediction_week)
        )
    """)
    print("✅ weekly_predictions table created")
    
    # 3. CREATE MONTHLY PREDICTIONS TABLE
    print("\n📈 Creating monthly_predictions table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monthly_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            prediction_date DATE NOT NULL,
            prediction_month TEXT NOT NULL,
            
            -- Prediction
            direction TEXT NOT NULL,
            predicted_move REAL,
            confidence_score INTEGER,
            probability REAL,
            
            -- Monthly Targets
            month_high_target REAL,
            month_low_target REAL,
            expected_range_min REAL,
            expected_range_max REAL,
            
            -- Long-term Analysis
            trend_type TEXT,
            momentum_score INTEGER,
            fundamental_rating TEXT,
            
            -- Analysis
            rationale TEXT,
            monthly_outlook TEXT,
            macro_factors TEXT,
            earnings_impact TEXT,
            sector_outlook TEXT,
            
            -- Verification
            actual_month_high REAL,
            actual_month_low REAL,
            actual_month_close REAL,
            prediction_accuracy TEXT,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, prediction_month)
        )
    """)
    print("✅ monthly_predictions table created")
    
    # 4. CREATE INDEXES FOR PERFORMANCE
    print("\n🔍 Creating indexes for query performance...")
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_daily_symbol_date 
        ON daily_predictions(symbol, prediction_date DESC)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_weekly_symbol_week 
        ON weekly_predictions(symbol, prediction_week DESC)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_monthly_symbol_month 
        ON monthly_predictions(symbol, prediction_month DESC)
    """)
    print("✅ Indexes created")
    
    
    conn.commit()
    print("✅ Tables committed to database")
    
    # 6. VERIFY TABLES
    print("\n✅ Verifying database structure...")
    tables = cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name LIKE '%predictions'
        ORDER BY name
    """).fetchall()
    
    print(f"\n📊 Prediction tables in database:")
    for table in tables:
        count = cursor.execute(f"SELECT COUNT(*) FROM {table[0]}").fetchone()[0]
        print(f"   • {table[0]:25s} - {count:3d} records")
    
    conn.close()
    
    print("\n" + "="*60)
    print("✅ DATABASE MIGRATION COMPLETE!")
    print("="*60)
    print("\nNext steps:")
    print("  1. Update prediction_agent.py with predict_daily/weekly/monthly")
    print("  2. Create frontend pages for each timeframe")
    print("  3. Update API endpoints in app.py")
    print("  4. Update run_pipeline.py to generate all timeframes")

if __name__ == "__main__":
    migrate_database()
