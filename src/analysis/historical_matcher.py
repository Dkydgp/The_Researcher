"""
Historical Pattern Matching
Finds similar past scenarios and analyzes outcomes
"""
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime, timedelta

class HistoricalMatcher:
    """Match current conditions to historical scenarios"""
    
    def __init__(self, db_path="stock_market.db"):
        self.db_path = db_path
    
    def find_similar_scenarios(self, symbol, current_indicators, lookback_days=365):
        """Find historical days with similar technical indicators"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get historical technical indicators
            query = f"""
            SELECT ti.*, sdp.close, sdp.open
            FROM technical_indicators ti
            JOIN stock_daily_prices sdp ON ti.symbol = sdp.symbol AND ti.date = sdp.date
            WHERE ti.symbol = ? 
            AND ti.date >= date('now', '-{lookback_days} days')
            AND ti.date < date('now', '-1 days')
            ORDER BY ti.date DESC
            """
            
            df = pd.read_sql_query(query, conn, params=(symbol,))
            conn.close()
            
            if df.empty:
                return None
            
            # Define similarity criteria
            rsi_current = current_indicators.get('rsi') or current_indicators.get('db_rsi')
            macd_current = current_indicators.get('macd')
            bb_position_current = current_indicators.get('bb_position', 50)  # % position in BB
            
            if not rsi_current:
                return None
            
            # Find similar days
            similar_days = []
            
            for idx, row in df.iterrows():
                # RSI similarity (within ±10)
                rsi_match = abs(row['rsi'] - rsi_current) <= 10 if pd.notna(row['rsi']) else False
                
                # MACD signal similarity
                macd_match = True
                if macd_current and pd.notna(row['macd']) and pd.notna(row['macd_signal']):
                    current_macd_signal = 'BULLISH' if macd_current > current_indicators.get('macd_signal', 0) else 'BEARISH'
                    hist_macd_signal = 'BULLISH' if row['macd'] > row['macd_signal'] else 'BEARISH'
                    macd_match = (current_macd_signal == hist_macd_signal)
                
                if rsi_match and macd_match:
                    similar_days.append(row)
            
            if not similar_days:
                return None
            
            # Analyze outcomes
            outcomes = self._analyze_outcomes(similar_days, symbol)
            
            return {
                'total_matches': len(similar_days),
                'outcomes': outcomes,
                'confidence_boost': self._calculate_confidence_boost(outcomes)
            }
            
        except Exception as e:
            print(f"Error in historical matching: {e}")
            return None
    
    def _analyze_outcomes(self, similar_days, symbol):
        """Analyze what happened after similar scenarios"""
        conn = sqlite3.connect(self.db_path)
        
        up_count = 0
        down_count = 0
        neutral_count = 0
        total_return = 0
        returns = []
        
        for day in similar_days:
            # Get next day's performance
            next_day_query = f"""
            SELECT open, close 
            FROM stock_daily_prices 
            WHERE symbol = ? 
            AND date > ?
            ORDER BY date ASC
            LIMIT 1
            """
            
            next_day = pd.read_sql_query(next_day_query, conn, params=(symbol, day['date']))
            
            if not next_day.empty and pd.notna(next_day['open'].iloc[0]) and pd.notna(next_day['close'].iloc[0]):
                next_open = next_day['open'].iloc[0]
                next_close = next_day['close'].iloc[0]
                
                if next_open > 0:
                    day_return = ((next_close - next_open) / next_open) * 100
                    returns.append(day_return)
                    total_return += day_return
                    
                    if day_return > 0.2:
                        up_count += 1
                    elif day_return < -0.2:
                        down_count += 1
                    else:
                        neutral_count += 1
        
        conn.close()
        
        total_scenarios = len(returns)
        
        if total_scenarios == 0:
            return None
        
        return {
            'up_probability': up_count / total_scenarios if total_scenarios > 0 else 0,
            'down_probability': down_count / total_scenarios if total_scenarios > 0 else 0,
            'neutral_probability': neutral_count / total_scenarios if total_scenarios > 0 else 0,
            'average_return': total_return / total_scenarios if total_scenarios > 0 else 0,
            'median_return': np.median(returns) if returns else 0,
            'std_deviation': np.std(returns) if returns else 0,
            'best_case': max(returns) if returns else 0,
            'worst_case': min(returns) if returns else 0,
            'win_rate': (up_count / total_scenarios * 100) if total_scenarios > 0 else 0
        }
    
    def _calculate_confidence_boost(self, outcomes):
        """Calculate confidence adjustment based on historical success rate"""
        if not outcomes:
            return 0
        
        win_rate = outcomes.get('win_rate', 50)
        avg_return = abs(outcomes.get('average_return', 0))
        
        # Boost confidence if historical win rate is high
        if win_rate >= 70 and avg_return > 1.0:
            return +1.5
        elif win_rate >= 65:
            return +1.0
        elif win_rate >= 55:
            return +0.5
        elif win_rate <= 35:
            return -1.0
        elif win_rate <= 45:
            return -0.5
        
        return 0
    
    def get_regime_specific_performance(self, symbol, market_regime, lookback_days=180):
        """Get stock performance in specific market regimes"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get historical data with market context
            query = f"""
            SELECT sdp.date, sdp.open, sdp.close, mc.nifty_trend, mc.volatility_regime
            FROM stock_daily_prices sdp
            LEFT JOIN market_context mc ON sdp.date = mc.date
            WHERE sdp.symbol = ?
            AND sdp.date >= date('now', '-{lookback_days} days')
            ORDER BY sdp.date DESC
            """
            
            df = pd.read_sql_query(query, conn, params=(symbol,))
            conn.close()
            
            if df.empty:
                return None
            
            # Filter by current regime
            regime_data = df[df['nifty_trend'] == market_regime]
            
            if regime_data.empty:
                return None
            
            # Calculate returns in this regime
            returns = []
            for idx, row in regime_data.iterrows():
                if pd.notna(row['open']) and pd.notna(row['close']) and row['open'] > 0:
                    day_return = ((row['close'] - row['open']) / row['open']) * 100
                    returns.append(day_return)
            
            if not returns:
                return None
            
            return {
                'regime': market_regime,
                'days_in_regime': len(returns),
                'average_return': np.mean(returns),
                'volatility': np.std(returns),
                'up_days': sum(1 for r in returns if r > 0),
                'down_days': sum(1 for r in returns if r < 0),
                'success_rate': (sum(1 for r in returns if r > 0) / len(returns) * 100) if returns else 0
            }
            
        except Exception as e:
            print(f"Error in regime performance: {e}")
            return None
