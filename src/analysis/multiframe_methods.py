"""
Multi-Timeframe Prediction Methods - To be added to PredictionAgent class

Add these methods to prediction_agent.py before the update_historical_outcomes method
"""

def predict_daily(self, symbol, save=False):
    """
    Generate DAILY prediction (next 1-2 trading days)
    Focus: Short-term technical indicators, intraday patterns, momentum
    """
    import json
    from datetime import datetime, timedelta, date
    
    print(f"\n📅 Generating DAILY prediction for {symbol}...")
    data = self._get_latest_data(symbol)
    
    # Extract latest price
    latest_price = data['prices'][0] if data['prices'] else {}
    
    #  Build DAILY-focused prompt
    prompt = f"""
You are an AI stock market analyst specializing in DAY TRADING and SHORT-TERM predictions.

Analyze {symbol} for the NEXT 1-2 TRADING DAYS.

CURRENT DATA:
==============
Latest Price: ₹{latest_price.get('close', 'N/A')}
Volume: {latest_price.get('volume', 'N/A')}

Technical Indicators:
- RSI: {data['technical_indicators'].get('db_rsi', 'N/A')}
- MACD: {data['technical_indicators'].get('macd', 'N/A')}
- Signal: {data['technical_indicators'].get('macd_signal', 'N/A')}
- BB Upper/Lower: {data['technical_indicators'].get('bb_upper', 'N/A')} / {data['technical_indicators'].get('bb_lower', 'N/A')}
- Volume Ratio: {data['technical_indicators'].get('volume_ratio', 'N/A')}

Chart Patterns Detected:
{self._format_pattern_analysis(data.get('chart_patterns', {}))}

Market Context:
- NIFTY Trend: {data['market_context'].get('nifty_trend', 'N/A')}
- Volatility: {data['market_context'].get('volatility_regime', 'N/A')}
- S&P 500: {data['market_context'].get('sp500_change', 'N/A')}%

Recent News:
{data.get('news', 'No recent news')}

DAILY TRADING ANALYSIS FRAMEWORK:
===================================
1. **Intraday Momentum** - Short-term price action, volume spikes
2. **Support/Resistance** - Key intraday levels from patterns
3. **Quick Reversals** - RSI overbought/oversold for day trading
4. **Volume Analysis** - Unusual volume indicating breakout/breakdown
5. **Gap Analysis** - Potential gaps up/down at market open
6. **Time-based Patterns** - Best entry/exit times

REQUIRED OUTPUT (JSON format):
{{
    "timeframe": "DAILY",
    "direction": "UP|DOWN|NEUTRAL",
    "confidence_score": 1-10,
    "probability": 0.0-1.0,
    "predicted_move": percentage,
    "target_price_min": float,
    "target_price_max": float,
    "expected_range_min": percentage,
    "expected_range_max": percentage,
    "risk_level": "LOW|MEDIUM|HIGH",
    "stop_loss": float,
    "volatility_forecast": "LOW|MODERATE|HIGH",
    "entry_time": "Market Open|Mid-day|Before Close",
    "rationale": "Brief 2-3 sentence explanation focusing on DAY TRADING signals",
    "key_factors": "comma,separated,factors",
    "technical_summary": "RSI/MACD/Volume signals for TODAY",
    "support_level": float,
    "resistance_level": float
}}

Provide ONLY the JSON response.
REALISM CONSTRAINT: For large cap stocks (Nifty 50), daily moves rarely exceed 3%. Keep "predicted_move" realistic (typically 0.1% to 2.5%).
Focus strictly on the NEXT SINGLE TRADING DAY.
"""
    
    # Get AI prediction
    try:
        response = self.model.generate_content(prompt)
        raw_text = response.text.strip()
        
        # Clean and parse JSON
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
        
        prediction = json.loads(raw_text)
        
        # Ensure required fields
        prediction['timeframe'] = 'DAILY'
        prediction.setdefault('confidence_score', 5)
        prediction.setdefault('direction', 'NEUTRAL')
        
        print(f"   ✅ Daily Prediction: {prediction['direction']} (Confidence: {prediction['confidence_score']}/10)")
        
        # Save to database if requested
        if save:
            conn = sqlite3.connect(self.pred_db_path)
            cursor = conn.cursor()
            
            today = date.today()
            next_day = today + timedelta(days=1)
            while next_day.weekday() >= 5:
                next_day += timedelta(days=1)
            
            cursor.execute("""
                INSERT OR REPLACE INTO daily_predictions (
                    symbol, prediction_date, direction, predicted_move, 
                    confidence_score, probability, target_price_min, target_price_max,
                    expected_range_min, expected_range_max, risk_level, stop_loss,
                    volatility_forecast, rationale, key_factors, technical_summary
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol, next_day.isoformat(),
                prediction.get('direction'), prediction.get('predicted_move'),
                prediction.get('confidence_score'), prediction.get('probability'),
                prediction.get('target_price_min'), prediction.get('target_price_max'),
                prediction.get('expected_range_min'), prediction.get('expected_range_max'),
                prediction.get('risk_level'), prediction.get('stop_loss'),
                prediction.get('volatility_forecast'), prediction.get('rationale'),
                prediction.get('key_factors'), prediction.get('technical_summary')
            ))
            
            conn.commit()
            conn.close()
            print(f"   💾 Saved to daily_predictions")
        
        return prediction
        
    except Exception as e:
        print(f"   ❌ Error generating daily prediction: {e}")
        return None


def predict_weekly(self, symbol, save=False):
    """
    Generate WEEKLY prediction (next 5-7 trading days)
    Focus: Swing trading signals, weekly patterns, trend continuation
    """
    import json
    from datetime import datetime, timedelta, date
    
    print(f"\n📊 Generating WEEKLY prediction for {symbol}...")
    data = self._get_latest_data(symbol)
    
    latest_price = data['prices'][0] if data['prices'] else {}
    
    # Build WEEKLY-focused prompt
    prompt = f"""
You are an AI stock market analyst specializing in SWING TRADING and WEEKLY predictions.

Analyze {symbol} for the NEXT WEEK (5-7 trading days).

CURRENT DATA:
==============
Current Price: ₹{latest_price.get('close', 'N/A')}
Weekly Volume Trend: {data['technical_indicators'].get('volume_ratio', 'N/A')}

Technical Indicators:
- RSI: {data['technical_indicators'].get('db_rsi', 'N/A')}
- MACD Trend: {data['technical_indicators'].get('macd_histogram', 'N/A')}
- Bollinger Band Position: {data['technical_indicators'].get('bb_middle', 'N/A')}

Chart Patterns:
{self._format_pattern_analysis(data.get('chart_patterns', {}))}

Historical Pattern Match:
{self._format_historical_match(data.get('historical_match', {}))}

Fundamentals:
{data.get('fundamentals', {})}

Market Context:
- Market Trend: {data['market_context'].get('nifty_trend', 'N/A')}
- Volatility: {data['market_context'].get('volatility_regime', 'N/A')}

WEEKLY SWING TRADING FRAMEWORK:
=================================
1. **Weekly Candle Pattern** - Bullish/bearish weekly formation
2. **Swing Levels** - Major support/resistance for the week
3. **Trend Strength** - ADX, momentum indicators
4. **Volume Confirmation** - Volume supporting the trend
5. **Key Events** - Earnings, announcements this week
6. **Sector Rotation** - Is this sector hot this week?

REQUIRED OUTPUT (JSON format):
{{
    "timeframe": "WEEKLY",
    "direction": "UP|DOWN|NEUTRAL",
    "confidence_score": 1-10,
    "probability": 0.0-1.0,
    "predicted_move": percentage,
    "week_high_target": float,
    "week_low_target": float,
    "expected_range_min": percentage,
    "expected_range_max": percentage,
    "trend_strength": "STRONG_UP|WEAK_UP|NEUTRAL|WEAK_DOWN|STRONG_DOWN",
    "support_levels": "level1,level2,level3",
    "resistance_levels": "level1,level2,level3",
    "rationale": "Brief 3-4 sentence explanation for SWING TRADERS",
    "weekly_outlook": "Detailed weekly forecast",
    "key_events": "Earnings/Events this week",
    "technical_patterns": "Head-shoulders, triangles, etc"
}}

Provide ONLY the JSON response. Focus on SWING TRADING signals for the WEEK.
"""
    
    try:
        response = self.model.generate_content(prompt)
        raw_text = response.text.strip()
        
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
        
        prediction = json.loads(raw_text)
        prediction['timeframe'] = 'WEEKLY'
        prediction.setdefault('confidence_score', 5)
        prediction.setdefault('direction', 'NEUTRAL')
        
        print(f"   ✅ Weekly Prediction: {prediction['direction']} (Confidence: {prediction['confidence_score']}/10)")
        
        if save:
            conn = sqlite3.connect(self.pred_db_path)
            cursor = conn.cursor()
            
            today = date.today()
            week_str = today.strftime("%Y-W%W")
            
            cursor.execute("""
                INSERT OR REPLACE INTO weekly_predictions (
                    symbol, prediction_date, prediction_week, direction, predicted_move,
                    confidence_score, probability, week_high_target, week_low_target,
                    expected_range_min, expected_range_max, trend_strength,
                    support_levels, resistance_levels, rationale, weekly_outlook,
                    key_events, technical_patterns
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol, today.isoformat(), week_str,
                prediction.get('direction'), prediction.get('predicted_move'),
                prediction.get('confidence_score'), prediction.get('probability'),
                prediction.get('week_high_target'), prediction.get('week_low_target'),
                prediction.get('expected_range_min'), prediction.get('expected_range_max'),
                prediction.get('trend_strength'), prediction.get('support_levels'),
                prediction.get('resistance_levels'), prediction.get('rationale'),
                prediction.get('weekly_outlook'), prediction.get('key_events'),
                prediction.get('technical_patterns')
            ))
            
            conn.commit()
            conn.close()
            print(f"   💾 Saved to weekly_predictions")
        
        return prediction
        
    except Exception as e:
        print(f"   ❌ Error generating weekly prediction: {e}")
        return None


def predict_monthly(self, symbol, save=False):
    """
    Generate MONTHLY prediction (next 20-30 trading days)
    Focus: Fundamental analysis, macro trends, earnings, long-term positioning
    """
    import json
    from datetime import datetime, timedelta, date
    
    print(f"\n📈 Generating MONTHLY prediction for {symbol}...")
    data = self._get_latest_data(symbol)
    
    latest_price = data['prices'][0] if data['prices'] else {}
    fundamentals = data.get('fundamentals', {})
    
    # Build MONTHLY-focused prompt
    prompt = f"""
You are an AI stock market analyst specializing in POSITION TRADING and MONTHLY forecasts.

Analyze {symbol} for the NEXT MONTH (20-30 trading days).

CURRENT DATA:
==============
Current Price: ₹{latest_price.get('close', 'N/A')}

Fundamentals:
- P/E Ratio: {fundamentals.get('stock_pe', 'N/A')}
- ROCE: {fundamentals.get('roce', 'N/A')}%
- ROE: {fundamentals.get('roe', 'N/A')}%
- Debt/Equity: {fundamentals.get('debt_to_equity', 'N/A')}

Technical Indicators (Monthly view):
- Long-term RSI: {data['technical_indicators'].get('db_rsi', 'N/A')}
- MACD Trend: {data['technical_indicators'].get('macd', 'N/A')}

Market Context:
- Overall Market: {data['market_context'].get('nifty_trend', 'N/A')}
- Global Influence (S&P): {data['market_context'].get('sp500_change', 'N/A')}%
- Volatility Regime: {data['market_context'].get('volatility_regime', 'N/A')}

Recent News & Sentiment:
{data.get('news', 'No recent news')}

MONTHLY POSITION TRADING FRAMEWORK:
====================================
1. **Fundamental Valuation** - Is stock cheap/expensive vs peers?
2. **Earnings Trend** - Growth trajectory
3. **Macro Factors** - Interest rates, sector rotation
4. **Monthly Chart Pattern** - Long-term trends
5. **Institutional Activity** - FII/DII flows
6. **Sector Outlook** - Industry tailwinds/headwinds

REQUIRED OUTPUT (JSON format):
{{
    "timeframe": "MONTHLY",
    "direction": "UP|DOWN|NEUTRAL",
    "confidence_score": 1-10,
    "probability": 0.0-1.0,
    "predicted_move": percentage,
    "month_high_target": float,
    "month_low_target": float,
    "expected_range_min": percentage,
    "expected_range_max": percentage,
    "trend_type": "BULLISH|BEARISH|SIDEWAYS",
    "momentum_score": 1-10,
    "fundamental_rating": "STRONG_BUY|BUY|HOLD|SELL|STRONG_SELL",
    "rationale": "Detailed 5-6 sentence analysis for LONG-TERM investors",
    "monthly_outlook": "Comprehensive monthly forecast",
    "macro_factors": "Interest rates, economy, sector trends",
    "earnings_impact": "Expected earnings impact",
    "sector_outlook": "How is the sector performing?"
}}

Provide ONLY the JSON response. Focus on FUNDAMENTAL and LONG-TERM signals.
"""
    
    try:
        response = self.model.generate_content(prompt)
        raw_text = response.text.strip()
        
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
        
        prediction = json.loads(raw_text)
        prediction['timeframe'] = 'MONTHLY'
        prediction.setdefault('confidence_score', 5)
        prediction.setdefault('direction', 'NEUTRAL')
        
        print(f"   ✅ Monthly Prediction: {prediction['direction']} (Confidence: {prediction['confidence_score']}/10)")
        
        if save:
            conn = sqlite3.connect(self.pred_db_path)
            cursor = conn.cursor()
            
            today = date.today()
            month_str = today.strftime("%Y-%m")
            
            cursor.execute("""
                INSERT OR REPLACE INTO monthly_predictions (
                    symbol, prediction_date, prediction_month, direction, predicted_move,
                    confidence_score, probability, month_high_target, month_low_target,
                    expected_range_min, expected_range_max, trend_type, momentum_score,
                    fundamental_rating, rationale, monthly_outlook, macro_factors,
                    earnings_impact, sector_outlook
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol, today.isoformat(), month_str,
                prediction.get('direction'), prediction.get('predicted_move'),
                prediction.get('confidence_score'), prediction.get('probability'),
                prediction.get('month_high_target'), prediction.get('month_low_target'),
                prediction.get('expected_range_min'), prediction.get('expected_range_max'),
                prediction.get('trend_type'), prediction.get('momentum_score'),
                prediction.get('fundamental_rating'), prediction.get('rationale'),
                prediction.get('monthly_outlook'), prediction.get('macro_factors'),
                prediction.get('earnings_impact'), prediction.get('sector_outlook')
            ))
            
            conn.commit()
            conn.close()
            print(f"   💾 Saved to monthly_predictions")
        
        return prediction
        
    except Exception as e:
        print(f"   ❌ Error generating monthly prediction: {e}")
        return None
