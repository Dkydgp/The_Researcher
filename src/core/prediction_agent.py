import google.generativeai as genai
import os
import pandas as pd
import sqlite3
from dotenv import load_dotenv
from src.core.vector_db import VectorDB
from src.utils.filter_companies import TOP_5_NIFTY
from src.analysis.pattern_recognition import PatternRecognition
from src.analysis.historical_matcher import HistoricalMatcher
import json
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

load_dotenv()

class PredictionAgent:
    def __init__(self):
        # Configure Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env")
        genai.configure(api_key=api_key)
        
        # Find a supported model
        # using Gemini 3 Pro for state-of-the-art reasoning as per Hackathon requirements
        model_name = "models/gemini-3-pro"
        print(f"Using model: {model_name}")
        self.model = genai.GenerativeModel(model_name)
        
        # Load data components
        self.main_db_path = "stock_market.db"
        self.pred_db_path = "predictions.db"
        self.vector_db = VectorDB()
        self.training_data_file = "training_data.csv"
        
        # Mapping Display Name -> YFinance Ticker in DB
        self.ticker_map = {
            # Original 5 stocks
            "Reliance Industries": "RELIANCE.NS",
            "TCS": "TCS.NS",
            "HDFC Bank": "HDFCBANK.NS",
            "Infosys": "INFY.NS",
            "ICICI Bank": "ICICIBANK.NS",
            # New 5 stocks
            "Bharti Airtel": "BHARTIARTL.NS",
            "ITC": "ITC.NS",
            "Wipro": "WIPRO.NS",
            "HCL Technologies": "HCLTECH.NS",
            "Bajaj Finance": "BAJFINANCE.NS",
            # Indices
            "NIFTY 50": "^NSEI",
            "SENSEX": "^BSESN"
        }
        
        # Sector mapping for sector-wise sentiment analysis
        self.sector_map = {
            "Reliance Industries": "OIL_GAS_CONGLOMERATE",
            "TCS": "IT_SERVICES",
            "HDFC Bank": "BANKING",
            "Infosys": "IT_SERVICES",
            "ICICI Bank": "BANKING",
            "Bharti Airtel": "TELECOM",
            "ITC": "FMCG",
            "Wipro": "IT_SERVICES",
            "HCL Technologies": "IT_SERVICES",
            "Bajaj Finance": "NBFC",
            "NIFTY 50": "INDEX",
            "SENSEX": "INDEX"
        }
        
        # Initialize Predictions Table
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.pred_db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prediction_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                prediction_date DATE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                prediction_json TEXT,
                direction TEXT,
                confidence_score INTEGER,
                predicted_move REAL,
                rationale TEXT,
                open_price REAL,
                close_price REAL
            )
        """)
        conn.commit()
        conn.close()

    def _calculate_technical_indicators(self, df):
        """Calculate basic technical indicators for algorithmic analysis"""
        if df.empty or len(df) < 14:
            return {}
        
        # Ensure sorted by date ascending for calculations
        df = df.sort_values('date')
        
        # 1. Simple Moving Averages
        sma_20 = df['close'].tail(20).mean()
        latest_price = df['close'].iloc[-1]
        trend = "BULLISH" if latest_price > sma_20 else "BEARISH"
        
        # 2. RSI (14-day)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs.iloc[-1]))
        
        rsi_signal = "NEUTRAL"
        if rsi > 70: rsi_signal = "OVERBOUGHT (SELL SIGNAL)"
        elif rsi < 30: rsi_signal = "OVERSOLD (BUY SIGNAL)"
        
        return {
            "sma_20": round(float(sma_20), 2) if not pd.isna(sma_20) else 0,
            "trend_signal": trend,
            "rsi": round(float(rsi), 2) if not pd.isna(rsi) else 50,
            "rsi_signal": rsi_signal
        }

    def _get_social_momentum(self, symbol):
        """Simulate social media momentum by searching for retail-specific sentiment in the news database"""
        queries = [
            f"{symbol} retail investor sentiment reddit twitter",
            f"{symbol} social media buzz viral news",
            f"{symbol} retail frenzy stock market"
        ]
        results = []
        for q in queries:
            search_res = self.vector_db.search(q, n_results=2)
            results.extend(search_res)
        
        # Filter duplicates and return top 3
        unique_results = []
        seen = set()
        for res in results:
            if res['title'] not in seen:
                unique_results.append(res)
                seen.add(res['title'])
        return unique_results[:3]
    
    def _get_sector_sentiment(self, symbol):
        """Get sector-wise sentiment by analyzing news for the entire sector"""
        sector = self.sector_map.get(symbol, "GENERAL")
        
        # Define sector keywords for news search
        sector_keywords = {
            "IT_SERVICES": "IT sector technology software services outsourcing",
            "BANKING": "banking sector HDFC ICICI SBI loans NPA interest rates RBI",
            "NBFC": "NBFC finance lending Bajaj credit growth",
            "TELECOM": "telecom 5G Airtel Jio spectrum tariff",
            "FMCG": "FMCG consumer goods retail demand rural",
            "OIL_GAS_CONGLOMERATE": "oil gas Reliance refinery petrol crude",
            "INDEX": "Nifty Sensex market index FII DII"
        }
        
        keywords = sector_keywords.get(sector, f"{sector} sector India")
        
        # Search for sector news
        sector_news = self.vector_db.search(f"{keywords} outlook trend", n_results=5)
        
        return {
            "sector": sector,
            "news_items": [f"- {n.get('title', '')}: {n.get('description', '')[:100]}..." for n in sector_news[:5]]
        }
    
    def _get_mutual_fund_data(self, symbol):
        """Get mutual fund related data - holdings and activity trends"""
        # Search for mutual fund news related to this stock
        mf_news = self.vector_db.search(
            f"{symbol} mutual fund holdings SIP investment institutional", 
            n_results=5
        )
        
        return {
            "mf_news_items": [f"- {n.get('title', '')}: {n.get('description', '')[:100]}..." for n in mf_news[:5]]
        }
    
    def _get_quarterly_results(self, symbol):
        """Get last 4 quarters earnings data and analysis"""
        # Search for quarterly results news
        earnings_news = self.vector_db.search(
            f"{symbol} quarterly results Q1 Q2 Q3 Q4 earnings profit revenue YoY", 
            n_results=8
        )
        
        # Try to get fundamentals from database
        conn = sqlite3.connect(self.main_db_path)
        try:
            fundamentals_df = pd.read_sql_query(
                f"SELECT * FROM stock_fundamentals WHERE symbol LIKE '%{symbol}%' ORDER BY date DESC LIMIT 4", 
                conn
            )
        except:
            fundamentals_df = pd.DataFrame()
        conn.close()
        
        return {
            "fundamentals": fundamentals_df.to_dict('records') if not fundamentals_df.empty else [],
            "earnings_news_items": [f"- {n.get('title', '')}: {n.get('description', '')[:100]}..." for n in earnings_news[:5]]
        }
    
    def _get_historical_seasonality(self, symbol):
        """Analyze stock behavior during same period in last 2 years"""
        ticker = self.ticker_map.get(symbol, symbol)
        today = date.today()
        
        # Get current month and day for seasonal comparison
        current_month = today.month
        current_day = today.day
        
        conn = sqlite3.connect(self.main_db_path)
        
        seasonal_data = []
        
        for years_ago in [1, 2]:
            try:
                # Target same period last year and 2 years ago
                target_year = today.year - years_ago
                start_date = f"{target_year}-{current_month:02d}-01"
                end_date = f"{target_year}-{current_month:02d}-28"
                
                query = f"""
                    SELECT date, open, close, high, low, volume 
                    FROM stock_daily_prices 
                    WHERE (symbol = '{ticker}' OR symbol LIKE '{ticker}%')
                    AND date >= '{start_date}' AND date <= '{end_date}'
                    ORDER BY date
                """
                df = pd.read_sql_query(query, conn)
                
                if not df.empty and len(df) >= 5:
                    # Calculate month performance
                    first_close = df['close'].iloc[0]
                    last_close = df['close'].iloc[-1]
                    month_return = ((last_close - first_close) / first_close) * 100
                    
                    # Calculate avg daily move
                    df['daily_return'] = df['close'].pct_change() * 100
                    avg_daily_return = df['daily_return'].mean()
                    volatility = df['daily_return'].std()
                    
                    # Determine trend
                    if month_return > 3:
                        trend = "BULLISH"
                    elif month_return < -3:
                        trend = "BEARISH"
                    else:
                        trend = "SIDEWAYS"
                    
                    seasonal_data.append({
                        "year": target_year,
                        "month_return": round(month_return, 2),
                        "avg_daily_return": round(avg_daily_return, 3),
                        "volatility": round(volatility, 2),
                        "trend": trend,
                        "trading_days": len(df)
                    })
            except Exception as e:
                pass
        
        conn.close()
        
        # Summarize seasonal pattern
        if len(seasonal_data) >= 2:
            avg_return = sum(d['month_return'] for d in seasonal_data) / len(seasonal_data)
            bullish_years = sum(1 for d in seasonal_data if d['trend'] == "BULLISH")
            pattern = "HISTORICALLY_BULLISH" if bullish_years >= 2 else "HISTORICALLY_BEARISH" if bullish_years == 0 else "MIXED"
        elif len(seasonal_data) == 1:
            avg_return = seasonal_data[0]['month_return']
            pattern = seasonal_data[0]['trend']
        else:
            avg_return = 0
            pattern = "NO_DATA"
        
        return {
            "seasonal_pattern": pattern,
            "avg_historical_return": round(avg_return, 2),
            "years_analyzed": len(seasonal_data),
            "yearly_data": seasonal_data,
            "analysis_period": f"{today.strftime('%B')} (same month, last 2 years)"
        }
    
    def _analyze_chart_patterns(self, price_data):
        """Detect chart patterns in price data"""
        if price_data.empty or len(price_data) < 10:
            return {'patterns': [], 'support': None, 'resistance': None}
        
        try:
            analysis = PatternRecognition.analyze_patterns(price_data)
            return analysis
        except Exception as e:
            print(f"Error in pattern analysis: {e}")
            return {'patterns': [], 'support': None, 'resistance': None}

    def _calculate_target_date(self, timeframe):
        """Calculate the specific target date for the prediction"""
        today = date.today()
        
        if timeframe == 'DAILY':
            # Next trading day (Monday if Fri/Sat/Sun)
            target = today + timedelta(days=1)
            while target.weekday() >= 5: # 5=Sat, 6=Sun
                target += timedelta(days=1)
            return target.isoformat()
            
        elif timeframe == 'WEEKLY':
            # Next Friday (Weekly Close)
            # If today is Friday, aim for NEXT Friday (7 days later)
            # If today is Mon-Thu, aim for THIS Friday
            days_until_friday = (4 - today.weekday() + 7) % 7
            if days_until_friday == 0:
                days_until_friday = 7
            target = today + timedelta(days=days_until_friday)
            return target.isoformat()
            
        elif timeframe == 'MONTHLY':
            # Last day of CURRENT month if we are early (<20th)
            # OR Last day of NEXT month if we are late (>20th)?
            # User said "monthly should be about last trading day of the month".
            # Usually prediction is for "Next Month".
            # Let's set it to Last Day of NEXT Full Month to give a 30-day horizon?
            # Or just Last Day of CURRENT month if predicting for "This Month"?
            # Prompt says "Analyze for NEXT MONTH (20-30 days)".
            # So if today is Dec 27, target is Jan 31.
            target = today + relativedelta(months=1)
            target = target + relativedelta(day=31)
            return target.isoformat()
        
        return None
    
    def _match_historical_scenarios(self, symbol, technical_indicators, market_context):
        """Find similar historical scenarios and analyze outcomes"""
        try:
            matcher = HistoricalMatcher(self.main_db_path)
            
            # Find similar scenarios
            similar = matcher.find_similar_scenarios(symbol, technical_indicators, lookback_days=365)
            
            # Get regime-specific performance
            regime = market_context.get('nifty_trend', 'UNKNOWN')
            regime_perf = None
            if regime != 'UNKNOWN':
                regime_perf = matcher.get_regime_specific_performance(symbol, regime, lookback_days=180)
            
            return {
                'similar_scenarios': similar,
                'regime_performance': regime_perf
            }
        except Exception as e:
            print(f"Error in historical matching: {e}")
            return {'similar_scenarios': None, 'regime_performance': None}

    def _format_pattern_analysis(self, patterns_data):
        """Format pattern analysis for AI prompt"""
        if not patterns_data or not patterns_data.get('patterns'):
            return "No significant chart patterns detected."
        
        output = []
        
        # Support/Resistance
        if patterns_data.get('support') or patterns_data.get('resistance'):
            current = patterns_data.get('current_price', 0)
            support = patterns_data.get('support')
            resistance = patterns_data.get('resistance')
            
            if support:
               output.append(f"- **Support Level**: ₹{support:.2f} ({((current-support)/support*100):+.1f}% below current)")
            if resistance:
                output.append(f"- **Resistance Level**: ₹{resistance:.2f} ({((resistance-current)/current*100):+.1f}% above current)")
        
        # Patterns
        for pattern in patterns_data.get('patterns', []):
            signal_emoji = "🔴" if pattern.get('signal') == 'BEARISH' else "🟢" if pattern.get('signal') == 'BULLISH' else "🟡"
            output.append(f"- {signal_emoji} **{pattern.get('pattern', 'Unknown')}**: {pattern.get('signal', 'NEUTRAL')} - {pattern.get('description', '')}")
        
        return "\n".join(output) if output else "No significant patterns."
    
    def _format_historical_match(self, hist_data):
        """Format historical matching results for AI prompt"""
        if not hist_data:
            return "Historical data not available."
        
        output = []
        
        # Similar scenarios
        similar = hist_data.get('similar_scenarios')
        if similar and similar.get('total_matches', 0) > 0:
            outcomes = similar.get('outcomes', {})
            output.append(f"**Found {similar['total_matches']} similar scenarios in past year:**")
            output.append(f"- Win Rate: {outcomes.get('win_rate', 0):.1f}%")
            output.append(f"- Average Outcome: {outcomes.get('average_return', 0):+.2f}%")
            output.append(f"- UP: {outcomes.get('up_probability', 0):.0%} | DOWN: {outcomes.get('down_probability', 0):.0%} | NEUTRAL: {outcomes.get('neutral_probability', 0):.0%}")
            output.append(f"- Best case: {outcomes.get('best_case', 0):+.2f}% | Worst case: {outcomes.get('worst_case', 0):+.2f}%")
        
        # Regime performance
        regime_perf = hist_data.get('regime_performance')
        if regime_perf:
            output.append(f"\n**Performance in {regime_perf.get('regime', 'UNKNOWN')} regime:**")
            output.append(f"- Success Rate: {regime_perf.get('success_rate', 0):.1f}% over {regime_perf.get('days_in_regime', 0)} days")
            output.append(f"- Average Daily Return: {regime_perf.get('average_return', 0):+.2f}%")
            output.append(f"- Volatility: {regime_perf.get('volatility', 0):.2f}%")
        
        return "\n".join(output) if output else "Insufficient historical data."


    def _get_latest_data(self, symbol):
        """Aggregate latest news, prices, and fundamentals for a symbol"""
        # Determine ticker or fallback to symbol pattern
        ticker = self.ticker_map.get(symbol, symbol)
        
        # 1. Prices (Extended to 200 days for better technical indicators and pattern recognition)
        conn = sqlite3.connect(self.main_db_path)
        all_prices_df = pd.read_sql_query(f"SELECT * FROM stock_daily_prices WHERE symbol = '{ticker}' OR symbol LIKE '{ticker}%' ORDER BY date DESC LIMIT 200", conn)
        
        # 2. Fundamentals
        fundamentals_df = pd.read_sql_query(f"SELECT * FROM stock_fundamentals WHERE symbol LIKE '{symbol}%' ORDER BY date DESC LIMIT 1", conn)
        
        # 3. **NEW**: Advanced Technical Indicators from DB
        technical_df = pd.read_sql_query(f"SELECT * FROM technical_indicators WHERE symbol = '{ticker}' ORDER BY date DESC LIMIT 1", conn)
        
        # 4. **NEW**: Market Context
        market_context = pd.read_sql_query("SELECT * FROM market_context ORDER BY date DESC LIMIT 1", conn)
        conn.close()
        
        # 5. News (Extended to 15 articles for better BTST sentiment analysis)
        news_results = self.vector_db.search(f"{symbol} latest business news", n_results=15)
        
        # 6. Social Media Momentum
        social_results = self._get_social_momentum(symbol)
        
        # 7. Basic Technical Indicators (Legacy - will be enhanced with DB data)
        technical_indicators = self._calculate_technical_indicators(all_prices_df)
        
        # 8. Enhanced technical indicators from DB
        if not technical_df.empty:
            tech_data = technical_df.to_dict('records')[0]
            technical_indicators.update({
                'db_rsi': tech_data.get('rsi'),
                'macd': tech_data.get('macd'),
                'macd_signal': tech_data.get('macd_signal'),
                'macd_histogram': tech_data.get('macd_histogram'),
                'bb_upper': tech_data.get('bb_upper'),
                'bb_middle': tech_data.get('bb_middle'),
                'bb_lower': tech_data.get('bb_lower'),
                'volume_ratio': tech_data.get('volume_ratio')
            })
        
        # 9. Market context data
        market_data = {}
        if not market_context.empty:
            mc = market_context.to_dict('records')[0]
            market_data = {
                'sp500_close': mc.get('sp500_close'),
                'sp500_change': mc.get('sp500_change'),
                'crude_oil': mc.get('crude_oil'),
                'usd_inr': mc.get('usd_inr'),
                'nifty_trend': mc.get('nifty_trend'),
                'volatility_regime': mc.get('volatility_regime')
            }
        
        # 10. Historical Examples from Training Data
        historical_examples = ""
        if os.path.exists(self.training_data_file):
            df = pd.read_csv(self.training_data_file)
            relevant = df[df['symbol'].str.contains(symbol, case=False, na=False)].tail(3)
            if not relevant.empty:
                historical_examples = relevant[['title', 'return_label']].to_string(index=False)

        # 11. NEW: Sector-wise sentiment
        sector_sentiment = self._get_sector_sentiment(symbol)
        
        # 12. NEW: Mutual Fund data
        mf_data = self._get_mutual_fund_data(symbol)
        
        # 13. NEW: Quarterly results (last 4 quarters)
        quarterly_results = self._get_quarterly_results(symbol)
        
        # 14. NEW: Historical seasonality (same period last 2 years)
        seasonality = self._get_historical_seasonality(symbol)

        return {
            "prices": all_prices_df.head(5).to_dict('records'),
            "fundamentals": fundamentals_df.to_dict('records')[0] if not fundamentals_df.empty else {},
            "news": news_results,
            "social_momentum": social_results,
            "technical_indicators": technical_indicators,
            "market_context": market_data,
            "historical": historical_examples,
            "chart_patterns": self._analyze_chart_patterns(all_prices_df),
            "historical_match": self._match_historical_scenarios(symbol, technical_indicators, market_data),
            # NEW DATA SOURCES
            "sector_sentiment": sector_sentiment,
            "mutual_fund_data": mf_data,
            "quarterly_results": quarterly_results,
            "seasonality": seasonality
        }

    def predict(self, symbol, save=False):
        print(f"\nAgent analyzing {symbol}...")
        data = self._get_latest_data(symbol)
        
        # Extract latest price for storage
        latest_price = data['prices'][0] if data['prices'] else {}
        open_price = latest_price.get('open', 0)
        close_price = latest_price.get('close', 0)
        
        # Get current price for BB position calculation
        current_price = close_price or latest_price.get('close', 0)
        tech = data['technical_indicators']
        mkt = data['market_context']
        
        # Calculate BB position if available
        bb_position = "Unknown"
        if tech.get('bb_upper') and tech.get('bb_lower') and current_price:
            bb_range = tech['bb_upper'] - tech['bb_lower']
            if bb_range > 0:
                pos_pct = ((current_price - tech['bb_lower']) / bb_range) * 100
                bb_position = f"{pos_pct:.0f}% (Lower={tech['bb_lower']:.2f}, Upper={tech['bb_upper']:.2f})"
        
        # Safe formatting for market context (handle None values)
        def safe_format(val, fmt=".2f"):
            if val is None:
                return 'N/A'
            if isinstance(val, (int, float)):
                return f"{val:{fmt}}"
            return str(val)
        
        prompt = f"""
        You are an institutional-grade AI analyst providing **MULTI-TIMEFRAME, PROBABILISTIC** predictions for **{symbol}**.
        
        ### 🌍 GLOBAL MARKET CONTEXT:
        - **S&P 500**: ${safe_format(mkt.get('sp500_close'))} ({safe_format(mkt.get('sp500_change', 0), '+.2f')}% today)
        - **Crude Oil (WTI)**: ${safe_format(mkt.get('crude_oil'))}/barrel
        - **USD/INR**: ₹{safe_format(mkt.get('usd_inr'))}
        - **Indian Market Regime**: {mkt.get('nifty_trend', 'UNKNOWN')} trend, {mkt.get('volatility_regime', 'UNKNOWN')} volatility
        
        ### 📊 ADVANCED TECHNICAL INDICATORS:
        - **RSI (14-day)**: {safe_format(tech.get('db_rsi') or tech.get('rsi'), '.1f')} → {tech.get('rsi_signal', 'NEUTRAL')}
        - **MACD**: {safe_format(tech.get('macd'))} | Signal: {safe_format(tech.get('macd_signal'))} | Histogram: {safe_format(tech.get('macd_histogram'))}
        - **Bollinger Bands**: Price at {bb_position}
        - **Volume**: {safe_format(tech.get('volume_ratio'))}x average volume
        - **20-day SMA**: ₹{tech.get('sma_20', 'N/A')} | Trend: {tech.get('trend_signal', 'UNKNOWN')}
        
        ### 💰 FUNDAMENTAL METRICS:
        {json.dumps(data['fundamentals'], indent=2)}
        
        ### 📰 RECENT NEWS & SENTIMENT:
        **Business News**: {[n['title'] for n in data['news']]}
        **Social Momentum**: {[s['title'] for s in data['social_momentum']]}
        
        ### 📈 RECENT PRICE ACTION:
        {json.dumps(data['prices'][:3], indent=2)}
        
        ### 🎓 HISTORICAL CONTEXT:
        {data['historical']}
        
        ### 📈 CHART PATTERNS DETECTED:
        {self._format_pattern_analysis(data.get('chart_patterns', {}))}
        
        ### 🔍 HISTORICAL PATTERN MATCHING:
        {self._format_historical_match(data.get('historical_match', {}))}
        
        ---
        
        ## 🧠 ANALYSIS FRAMEWORK:
        Apply these professional theories:
        1. **Global Macro Impact**: How do S&P 500 trend, oil prices, and currency affect Indian stocks?
        2. **Technical Confluence**: Do RSI, MACD, and BB signals agree or diverge?
        3. **Market Regime Adjustment**: In a {mkt.get('nifty_trend', 'UNKNOWN')} / {mkt.get('volatility_regime', 'UNKNOWN')} vol regime, adjust expectations
        4. **Volume Confirmation**: Does volume support the price trend?
        5. **Sentiment vs Fundamentals**: Are news catalysts aligned with technical momentum?
        6. **Mean Reversion vs Momentum**: Is this trending or range-bound?
        7. **Chart Pattern Recognition**: Do detected patterns (double tops, H&S, triangles) suggest reversals or continuations?
        8. **Historical Precedent**: What happened in similar scenarios? Does historical win rate support current direction?
        9. **Support/Resistance Levels**: Is price near breakout or breakdown levels?
        
        ## 📋 OUTPUT FORMAT (STRICT JSON):
        Provide **TWO timeframe predictions**:
        ```json
        {{
            "weekly_trend": "UP" | "DOWN" | "NEUTRAL",
            "weekly_range_min": float (min % move over next 5 days),
            "weekly_range_max": float (max % move over next 5 days),
            "daily_direction": "UP" | "DOWN" | "NEUTRAL",
            "daily_probability": float (0.0 to 1.0, probability of daily_direction),
            "daily_range_min": float (min % move tomorrow),
            "daily_range_max": float (max % move tomorrow),
            "confidence_score": int (1-10),
            "rationale": "2-3 sentences explaining the prediction using market context, technical signals, and fundamental/news factors"
        }}
        ```
        
        **IMPORTANT**: 
        - Weekly predictions reflect 5-day outlook
        - Daily predictions are for the NEXT trading day only
        - Be realistic with ranges based on the {mkt.get('volatility_regime', 'MEDIUM')} volatility regime
        - Confidence score should reflect signal strength and market uncertainty
        """
        
        try:
            # Parse enhanced probabilistic prediction
            response = self.model.generate_content(prompt)
            text = response.text
            start = text.find('{')
            end = text.rfind('}') + 1
            prediction_str = text[start:end]
            prediction = json.loads(prediction_str)
            
            # 🧠 ACTIVE LEARNING: Adjust confidence based on past performance
            base_confidence = prediction.get('confidence_score', 5)
            adjustment = self.get_confidence_adjustment(symbol)
            adjusted_confidence = min(10, max(1, base_confidence + adjustment))
            
            if adjustment != 0:
                print(f"   🧠 Learning Adjustment: Base {base_confidence} → {adjusted_confidence:.1f} (Δ{adjustment:+.1f})")
                prediction['confidence_score'] = int(round(adjusted_confidence))
            
            # For backwards compatibility, add legacy fields
            if 'direction' not in prediction:
                prediction['direction'] = prediction.get('daily_direction', 'NEUTRAL')
            if 'predicted_percentage_move' not in prediction:
                # Use midpoint of daily range
                daily_min = prediction.get('daily_range_min', 0)
                daily_max = prediction.get('daily_range_max', 0)
                prediction['predicted_percentage_move'] = (daily_min + daily_max) / 2
            
            print(f"Prediction for {symbol}:")
            print(f"   📅 WEEKLY: {prediction.get('weekly_trend', 'N/A')} ({prediction.get('weekly_range_min', 0):+.1f}% to {prediction.get('weekly_range_max', 0):+.1f}%)")
            print(f"   📆 DAILY: {prediction.get('daily_direction', 'N/A')} (P={prediction.get('daily_probability', 0):.0%}, Range: {prediction.get('daily_range_min', 0):+.1f}% to {prediction.get('daily_range_max', 0):+.1f}%)")
            print(f"   🎯 Confidence: {prediction['confidence_score']}/10")
            print(f"   💡 Rationale: {prediction.get('rationale', 'N/A')}")
            
            if save:
                self._save_prediction(symbol, prediction, prediction_str, open_price, close_price)
            
            return prediction
        except Exception as e:
            print(f"Error generating prediction: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _save_prediction(self, symbol, prediction, raw_json, open_price, close_price):
        try:
            conn = sqlite3.connect(self.pred_db_path)
            cursor = conn.cursor()
            
            # Use current local time for next trading day calculation
            # If after 3:30 PM, target is next business day.
            # For simplicity, we assume the prediction is for the NEXT business day from today.
            from datetime import date, datetime, timedelta
            today = date.today()
            
            # Simple next trading day logic (Skips Weekends)
            next_day = today + timedelta(days=1)
            while next_day.weekday() >= 5: # 5=Sat, 6=Sun
                next_day += timedelta(days=1)
            
            target_date = next_day.isoformat()
            
            # Save the prediction for the TARGET date
            # Note: open_price and close_price are initially 0 or None as they haven't happened yet.
            # We only store them if we are backfilling (but here we are predicting for tomorrow).
            
            cursor.execute("""
                INSERT INTO prediction_history (
                    symbol, prediction_date, prediction_json, direction, 
                    confidence_score, predicted_move, rationale, open_price, close_price
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol,
                target_date,
                raw_json, 
                prediction.get('direction'), 
                prediction.get('confidence_score'),
                prediction.get('predicted_percentage_move'),
                prediction.get('rationale'),
                None, # Open price for tomorrow (unknown)
                None  # Close price for tomorrow (unknown)
            ))
            conn.commit()
            conn.close()
            print(f"   [Saved to DB] Prediction for {symbol} (Target: {target_date}) stored.")
        except Exception as e:
            print(f"Error saving prediction to DB: {e}")
    
    def predict_daily(self, symbol, save=False):
        """
        Generate DAILY prediction (next 1-2 trading days)
        Focus: Short-term technical indicators, intraday patterns, momentum
        """
        import json
        from datetime import datetime, timedelta, date
        
        print(f"\n📅 Generating DAILY prediction for {symbol}...")
        try:
            data = self._get_latest_data(symbol)
        except Exception as e:
            print(f"Error fetching data: {e}")
            import traceback; traceback.print_exc()
            return None
        
        # Extract latest price
        latest_price = data['prices'][0] if data['prices'] else {}
        
        #  Build DAILY-focused prompt with STRUCTURED REASONING
        tech = data['technical_indicators']
        mkt = data['market_context']
        fundamentals = data.get('fundamentals', {})
        
        # Pre-calculate signals for structured analysis
        rsi_val = tech.get('db_rsi') or tech.get('rsi')
        rsi_signal = "OVERSOLD (Bullish)" if rsi_val and rsi_val < 30 else "OVERBOUGHT (Bearish)" if rsi_val and rsi_val > 70 else "NEUTRAL"
        
        macd_val = tech.get('macd')
        macd_sig = tech.get('macd_signal')
        macd_signal = "BULLISH" if macd_val and macd_sig and macd_val > macd_sig else "BEARISH" if macd_val and macd_sig and macd_val < macd_sig else "NEUTRAL"
        
        vol_ratio = tech.get('volume_ratio', 1.0)
        volume_signal = "STRONG" if vol_ratio and vol_ratio > 1.5 else "WEAK" if vol_ratio and vol_ratio < 0.5 else "AVERAGE"
        
        # Pre-format news for prompt (AI Generated Analysis)
        sector_news_txt = "\n".join(data.get('sector_sentiment', {}).get('news_items', []) or ["No recent news"])
        mf_news_txt = "\n".join(data.get('mutual_fund_data', {}).get('mf_news_items', []) or ["No recent news"])
        earnings_news_txt = "\n".join(data.get('quarterly_results', {}).get('earnings_news_items', []) or ["No recent news"])
        
        prompt = f"""You are an EXPERT Indian stock market analyst. Analyze {symbol} using this STRICT step-by-step framework.

**IMPORTANT RULES:**
1. You MUST complete ALL steps before making a prediction
2. If signals CONFLICT, you MUST predict NEUTRAL with lower confidence
3. High confidence (8+) is ONLY allowed when ALL signals agree
4. Daily moves for Nifty 50 stocks rarely exceed 2.5%

**STRATEGY ADVICE FOR {symbol}:**
{self._get_strategy_instruction(symbol)}

=== INPUT DATA ===
Stock: {symbol}
Current Price: ₹{latest_price.get('close', 'N/A')}
Volume: {latest_price.get('volume', 'N/A')} ({volume_signal})

Technical Indicators:
- RSI (14): {rsi_val} → {rsi_signal}
- MACD: {macd_val} vs Signal: {macd_sig} → {macd_signal}
- Bollinger Bands: Upper ₹{tech.get('bb_upper', 'N/A')} | Lower ₹{tech.get('bb_lower', 'N/A')}
- Volume Ratio: {vol_ratio}x average

Market Context:
- NIFTY Trend: {mkt.get('nifty_trend', 'N/A')}
- Volatility Regime: {mkt.get('volatility_regime', 'N/A')}
- S&P 500 Change: {mkt.get('sp500_change', 'N/A')}%

Chart Patterns:
{self._format_pattern_analysis(data.get('chart_patterns', {}))}

Recent News Headlines:
{[n.get('title', '') for n in data.get('news', [])[:5]]}

Social Momentum/Buzz (Retail Sentiment):
{[n.get('title', '') for n in data.get('social_momentum', [])[:3]]}

Historical Pattern Match:
{self._format_historical_match(data.get('historical_match', {}))}

=== NEW ENHANCED DATA SOURCES ===

**SECTOR ANALYSIS:**
- Sector: {data.get('sector_sentiment', {}).get('sector', 'N/A')}
- Key News Summaries (Analyze for Sector Sentiment):
{sector_news_txt}

**MUTUAL FUND / INSTITUTIONAL ACTIVITY:**
- Key News Summaries (Analyze for Institutional Sentiment):
{mf_news_txt}

**QUARTERLY RESULTS (Last 4 Quarters):**
- Fundamentals: {data.get('quarterly_results', {}).get('fundamentals', [])}
- Recent Results News (Analyze for Growth Trend):
{earnings_news_txt}

**HISTORICAL SEASONALITY (Same period last 2 years):**
- Seasonal Pattern: {data.get('seasonality', {}).get('seasonal_pattern', 'N/A')}
- Avg Historical Return: {data.get('seasonality', {}).get('avg_historical_return', 0)}%
- Analysis Period: {data.get('seasonality', {}).get('analysis_period', 'N/A')}
- Yearly Data: {data.get('seasonality', {}).get('yearly_data', [])}

=== STEP-BY-STEP ANALYSIS (Complete ALL steps) ===

**STEP 1: TECHNICAL SCORE (Rate each 1-10, then average)**
Think about: RSI position, MACD crossover, BB position, Volume confirmation
- RSI Signal Strength: ?/10 (based on {rsi_signal})
- MACD Signal Strength: ?/10 (based on {macd_signal})
- Volume Confirmation: ?/10 (based on {volume_signal})
- Overall Technical Score: ?/10

**STEP 2: MARKET CONTEXT SCORE**
Think about: Is NIFTY supporting this move? Global markets favorable?
- Market Alignment Score: ?/10

**STEP 3: NEWS SENTIMENT SCORE**
Think about: Are recent news positive, negative, or neutral for this stock?
- Sentiment Score: ?/10

**STEP 4: SIGNAL CONFLUENCE CHECK**
- Does Technical signal support direction? (YES/NO)
    - Does Market Context support direction? (YES/NO)
    - Does News Sentiment support direction? (YES/NO)
    - Does Sector Sentiment (based on your analysis of news) support direction? (YES/NO/NEUTRAL)
    - Does Institutional Activity (based on your analysis of news) support direction? (YES/NO/NEUTRAL)
    - Does Historical Seasonality support direction? (YES/NO/NEUTRAL)
- **Signals Aligned: ?/6** (Ignore NEUTRAL signals, do not count as conflict)

**STEP 5: CONFLICT RESOLUTION**
If signals conflict:
- Weight NEWS SENTIMENT heavily (Breaking news overrides technicals).
- NEUTRAL signals should NOT lower confidence. Only OPPOSING signals are conflicts.
- Weight SECTOR and INSTITUTIONAL activity higher than generic news.
- Weight TECHNICALS higher for short-term/BTST.
- If signals are split (e.g. 3 vs 3), prediction MUST be NEUTRAL.

**STEP 6: FINAL PREDICTION**
Based on Steps 1-5:
- If 5-6 signals agree → High confidence (8-10)
- If 4 signals agree → Medium confidence (6-7)
- If < 4 signals agree → Low confidence (3-5) or NEUTRAL

=== OUTPUT (JSON ONLY) ===
Provide ONLY valid JSON, no other text:
{{
    "timeframe": "DAILY",
    "direction": "UP|DOWN|NEUTRAL",
    "confidence_score": 1-10,
    "probability": 0.0-1.0,
    "predicted_move": float (realistic: 0.1 to 2.5),
    "target_price_min": float,
    "target_price_max": float,
    "expected_range_min": float,
    "expected_range_max": float,
    "risk_level": "LOW|MEDIUM|HIGH",
    "stop_loss": float,
    "volatility_forecast": "LOW|MODERATE|HIGH",
    "entry_time": "Market Open|Mid-day|Before Close",
    "rationale": "Detailed rationale citing specific signals",
    "key_factors": "comma,separated,factors",
    "technical_summary": "Brief technical verdict",
    "support_level": float,
    "resistance_level": float,
    "technical_score": float,
    "market_score": float,
    "sentiment_score": float,
    "signals_aligned": 5
}}

TARGET DATE: {self._calculate_target_date('DAILY')}
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
            
            # ===== PHASE 1: CONFIDENCE CALIBRATION & BTST FILTERS =====
            
            # 1. Extract base confidence and signals
            base_confidence = prediction.get('confidence_score', 5)
            
            try:
                signals_aligned = int(prediction.get('signals_aligned', 0))
            except:
                signals_aligned = 0
                
            direction = prediction.get('direction', 'NEUTRAL')
            
            # 2. Calibration (Start at base, no penalty)
            calibrated_confidence = base_confidence
            
            # 3. Signal alignment adjustment (TIERED REWARDS)
            if signals_aligned == 6:
                calibrated_confidence += 2  # Strong bonus for perfect alignment
                print(f"   ✅ Perfect Signal Match (6/6) - adjusting confidence +2")
            elif signals_aligned == 5:
                calibrated_confidence += 1  # Bonus for high alignment
                print(f"   ✅ High Signal Match (5/6) - adjusting confidence +1")
            elif signals_aligned <= 3:
                calibrated_confidence -= 2  # Strong penalty for weak alignment
                if direction != 'NEUTRAL':
                    print(f"   ⚠️ Major Signal conflict ({signals_aligned}/6) - reducing confidence -2")
            
            # 4. Volume filter: Low volume = unreliable signal (mild penalty)
            vol_ratio = tech.get('volume_ratio', 1.0) if 'tech' in dir() else 1.0
            if vol_ratio and vol_ratio < 0.5:
                calibrated_confidence -= 1
                print(f"   ⚠️ Low volume ({vol_ratio:.1f}x) - reducing confidence")
            elif vol_ratio and vol_ratio > 1.5:
                calibrated_confidence += 1  # Bonus for high volume confirmation
                print(f"   ✅ High volume ({vol_ratio:.1f}x) - boosting confidence")
            
            # 5. News Sentiment Weighting (User Request: "Give more pressing to news")
            sentiment_score = prediction.get('sentiment_score', 5)
            if sentiment_score >= 8:
                calibrated_confidence += 1
                print(f"   ✅ Strong Positive News (Score {sentiment_score}) - boosting confidence +1")
            elif sentiment_score <= 3:
                if direction == 'UP':
                    calibrated_confidence -= 2
                    print(f"   ⚠️ Negative News (Score {sentiment_score}) vs UP prediction - reducing confidence -2")
                elif direction == 'DOWN':
                    calibrated_confidence += 1
                    print(f"   ✅ Negative News confirms DOWN prediction - boosting confidence +1")
            
            # 5. RSI extreme filter: Only penalize extreme continuation trades
            rsi_val = prediction.get('technical_score', 5)
            if rsi_val and rsi_val > 80 and direction == 'UP':  # Only at extreme overbought
                calibrated_confidence -= 1
                print(f"   ⚠️ RSI very overbought - reducing UP confidence")
            elif rsi_val and rsi_val < 20 and direction == 'DOWN':  # Only at extreme oversold
                calibrated_confidence -= 1
                print(f"   ⚠️ RSI very oversold - reducing DOWN confidence")
            
            # 6. Apply historical accuracy adjustment
            accuracy_adjustment = self.get_confidence_adjustment(symbol)
            calibrated_confidence += accuracy_adjustment
            
            # 8. Clamp confidence between 1-10
            final_confidence = max(1, min(10, int(round(calibrated_confidence))))
            
            # 9. Enforce Realism Constraint (Max 2.5% move for daily)
            pred_move = prediction.get('predicted_move', 0.0)
            if pred_move > 2.5: pred_move = 2.5
            if pred_move < -2.5: pred_move = -2.5
            prediction['predicted_move'] = pred_move
            
            # Log calibration
            if final_confidence != base_confidence:
                print(f"   🎯 Confidence calibrated: {base_confidence} → {final_confidence} (Δ{final_confidence - base_confidence:+d})")
            
            prediction['confidence_score'] = final_confidence
            prediction['raw_confidence'] = base_confidence
            
            # Ensure required fields
            prediction['timeframe'] = 'DAILY'
            prediction.setdefault('direction', 'NEUTRAL')
            
            print(f"   ✅ Daily BTST Prediction: {prediction['direction']} (Confidence: {prediction['confidence_score']}/10)")
            
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
                        volatility_forecast, rationale, key_factors, technical_summary, target_date,
                        signals_aligned, sentiment_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol, next_day.isoformat(),
                    prediction.get('direction'), prediction.get('predicted_move'),
                    prediction.get('confidence_score'), prediction.get('probability'),
                    prediction.get('target_price_min'), prediction.get('target_price_max'),
                    prediction.get('expected_range_min'), prediction.get('expected_range_max'),
                    prediction.get('risk_level'), prediction.get('stop_loss'),
                    prediction.get('volatility_forecast'), prediction.get('rationale'),
                    prediction.get('key_factors'), prediction.get('technical_summary'),
                    self._calculate_target_date('DAILY'),
                    prediction.get('signals_aligned', 0),
                    prediction.get('sentiment_score', 5.0)
                ))
                
                conn.commit()
                conn.close()
                print(f"   💾 Saved to daily_predictions")
            
            return prediction
            
        except Exception as e:
            print(f"   ❌ Error generating daily prediction: {e}")
            import traceback
            traceback.print_exc()
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
        
        # Build WEEKLY-focused prompt with STRUCTURED REASONING
        tech = data['technical_indicators']
        mkt = data['market_context']
        fundamentals = data.get('fundamentals', {})
        
        # Pre-calculate signals
        rsi_val = tech.get('db_rsi') or tech.get('rsi')
        rsi_signal = "OVERSOLD" if rsi_val and rsi_val < 35 else "OVERBOUGHT" if rsi_val and rsi_val > 65 else "NEUTRAL"
        
        macd_hist = tech.get('macd_histogram', 0)
        macd_trend = "BULLISH" if macd_hist and macd_hist > 0 else "BEARISH" if macd_hist and macd_hist < 0 else "NEUTRAL"
        
        nifty_trend = mkt.get('nifty_trend', 'N/A')
        
        prompt = f"""You are an EXPERT Indian stock market analyst for SWING TRADING. Analyze {symbol} for the NEXT WEEK using this STRICT framework.

**IMPORTANT RULES:**
1. Complete ALL analysis steps before prediction
2. Weekly moves for Nifty 50 stocks typically range 2-7%
3. If Technical conflicts with Fundamental → reduce confidence
4. High confidence (8+) requires ALL signals aligned

=== INPUT DATA ===
Stock: {symbol}
Current Price: ₹{latest_price.get('close', 'N/A')}
Volume Trend: {tech.get('volume_ratio', 'N/A')}x average

Technical Indicators:
- RSI (14): {rsi_val} → {rsi_signal}
- MACD Histogram: {macd_hist} → {macd_trend}
- Bollinger Mid: ₹{tech.get('bb_middle', 'N/A')}

Chart Patterns:
{self._format_pattern_analysis(data.get('chart_patterns', {}))}

Historical Pattern Match:
{self._format_historical_match(data.get('historical_match', {}))}

Fundamentals:
- P/E: {fundamentals.get('stock_pe', 'N/A')}
- ROCE: {fundamentals.get('roce', 'N/A')}%
- ROE: {fundamentals.get('roe', 'N/A')}%

Market Context:
- NIFTY Trend: {nifty_trend}
- Volatility Regime: {mkt.get('volatility_regime', 'N/A')}

=== STEP-BY-STEP ANALYSIS ===

**STEP 1: WEEKLY TECHNICAL SCORE**
- RSI Position Score: ?/10 ({rsi_signal})
- MACD Trend Score: ?/10 ({macd_trend})
- Chart Pattern Score: ?/10
- Overall Technical: ?/10

**STEP 2: FUNDAMENTAL SCORE**
- Valuation (P/E): Fair/Expensive/Cheap → ?/10
- Quality (ROCE/ROE): ?/10
- Overall Fundamental: ?/10

**STEP 3: MARKET ALIGNMENT**
- Does NIFTY ({nifty_trend}) support this prediction? ?/10

**STEP 4: CONFLUENCE CHECK**
- Technical agrees with Fundamental? YES/NO
- Technical agrees with Market? YES/NO
- Signals aligned: ?/3

**STEP 5: WEEKLY VERDICT**
- If 3/3 aligned → High confidence (7-9)
- If 2/3 aligned → Medium confidence (5-6)  
- If conflict → NEUTRAL, confidence 3-5

=== OUTPUT (JSON ONLY) ===
{{
    "timeframe": "WEEKLY",
    "direction": "UP|DOWN|NEUTRAL",
    "confidence_score": 1-10,
    "probability": 0.0-1.0,
    "predicted_move": float (realistic: 1-6%),
    "week_high_target": float,
    "week_low_target": float,
    "expected_range_min": float,
    "expected_range_max": float,
    "trend_strength": "STRONG_UP|WEAK_UP|NEUTRAL|WEAK_DOWN|STRONG_DOWN",
    "support_levels": "level1,level2,level3",
    "resistance_levels": "level1,level2,level3",
    "rationale": "3-4 sentences explaining signal alignment",
    "weekly_outlook": "Detailed weekly forecast",
    "key_events": "Earnings/Events this week",
    "technical_patterns": "Detected patterns",
    "technical_score": float,
    "fundamental_score": float,
    "market_score": float,
    "signals_aligned": int (0-3)
}}

TARGET DATE: {self._calculate_target_date('WEEKLY')}
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
                        key_events, technical_patterns, target_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol, today.isoformat(), week_str,
                    prediction.get('direction'), prediction.get('predicted_move'),
                    prediction.get('confidence_score'), prediction.get('probability'),
                    prediction.get('week_high_target'), prediction.get('week_low_target'),
                    prediction.get('expected_range_min'), prediction.get('expected_range_max'),
                    prediction.get('trend_strength'), prediction.get('support_levels'),
                    prediction.get('resistance_levels'), prediction.get('rationale'),
                    prediction.get('weekly_outlook'), prediction.get('key_events'),
                    prediction.get('technical_patterns'),
                    self._calculate_target_date('WEEKLY')
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
        
        # Build MONTHLY-focused prompt with STRUCTURED REASONING
        tech = data['technical_indicators']
        mkt = data['market_context']
        
        # Fundamental evaluation
        pe_ratio = fundamentals.get('stock_pe')
        pe_signal = "EXPENSIVE" if pe_ratio and pe_ratio > 40 else "FAIR" if pe_ratio and pe_ratio > 15 else "CHEAP" if pe_ratio else "N/A"
        
        roce = fundamentals.get('roce')
        roce_signal = "EXCELLENT" if roce and roce > 20 else "GOOD" if roce and roce > 12 else "POOR" if roce else "N/A"
        
        debt = fundamentals.get('debt_to_equity')
        debt_signal = "LOW (Good)" if debt and debt < 0.5 else "HIGH (Risk)" if debt and debt > 1 else "MODERATE" if debt else "N/A"
        
        prompt = f"""You are an EXPERT Indian stock market analyst for POSITION TRADING. Analyze {symbol} for the NEXT MONTH using this STRICT framework.

**IMPORTANT RULES:**
1. Monthly analysis emphasizes FUNDAMENTALS over technicals
2. Monthly moves typically range 5-15%
3. High confidence (8+) requires strong fundamentals + supportive market
4. NEUTRAL if fundamentals don't justify directional bet

=== INPUT DATA ===
Stock: {symbol}
Current Price: ₹{latest_price.get('close', 'N/A')}

Fundamentals:
- P/E Ratio: {pe_ratio} → {pe_signal}
- ROCE: {roce}% → {roce_signal}
- ROE: {fundamentals.get('roe', 'N/A')}%
- Debt/Equity: {debt} → {debt_signal}

Technical (Long-term view):
- RSI: {tech.get('db_rsi', 'N/A')}
- MACD: {tech.get('macd', 'N/A')}

Market Context:
- NIFTY Trend: {mkt.get('nifty_trend', 'N/A')}
- S&P 500: {mkt.get('sp500_change', 'N/A')}%
- Volatility: {mkt.get('volatility_regime', 'N/A')}

Recent News:
{[n.get('title', '') for n in data.get('news', [])[:5]]}

=== STEP-BY-STEP ANALYSIS ===

**STEP 1: FUNDAMENTAL SCORE**
- Valuation (P/E: {pe_ratio}): {pe_signal} → ?/10
- Quality (ROCE: {roce}%): {roce_signal} → ?/10
- Financial Health (D/E: {debt}): {debt_signal} → ?/10
- Overall Fundamental Score: ?/10

**STEP 2: TECHNICAL SCORE (Long-term)**
- Monthly trend strength: ?/10
- Momentum score: ?/10
- Overall Technical Score: ?/10

**STEP 3: MACRO/MARKET SCORE**
- Market alignment with position: ?/10
- Sector outlook: ?/10
- Overall Macro Score: ?/10

**STEP 4: CONFLUENCE CHECK**
- Fundamentals support direction? YES/NO (weight: 50%)
- Technicals support direction? YES/NO (weight: 25%)
- Macro supports direction? YES/NO (weight: 25%)

**STEP 5: MONTHLY VERDICT**
- Strong fundamentals + supportive market → High confidence (7-9)
- Mixed signals → Medium confidence (5-6)
- Weak fundamentals → NEUTRAL or bearish

=== OUTPUT (JSON ONLY) ===
{{
    "timeframe": "MONTHLY",
    "direction": "UP|DOWN|NEUTRAL",
    "confidence_score": 1-10,
    "probability": 0.0-1.0,
    "predicted_move": float (realistic: 3-12%),
    "month_high_target": float,
    "month_low_target": float,
    "expected_range_min": float,
    "expected_range_max": float,
    "trend_type": "BULLISH|BEARISH|SIDEWAYS",
    "momentum_score": 1-10,
    "fundamental_rating": "STRONG_BUY|BUY|HOLD|SELL|STRONG_SELL",
    "rationale": "5-6 sentences explaining fundamental justification",
    "monthly_outlook": "Comprehensive monthly forecast",
    "macro_factors": "Key macro drivers",
    "earnings_impact": "Expected earnings impact",
    "sector_outlook": "Sector performance",
    "fundamental_score": float,
    "technical_score": float,
    "macro_score": float
}}

TARGET DATE: {self._calculate_target_date('MONTHLY')}
"""
        
        try:
            response = self.model.generate_content(prompt)
            raw_text = response.text.strip()
            
            # Clean and parse JSON
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
                        earnings_impact, sector_outlook, target_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol, today.isoformat(), month_str,
                    prediction.get('direction'), prediction.get('predicted_move'),
                    prediction.get('confidence_score'), prediction.get('probability'),
                    prediction.get('month_high_target'), prediction.get('month_low_target'),
                    prediction.get('expected_range_min'), prediction.get('expected_range_max'),
                    prediction.get('trend_type'), prediction.get('momentum_score'),
                    prediction.get('fundamental_rating'), prediction.get('rationale'),
                    prediction.get('monthly_outlook'), prediction.get('macro_factors'),
                    prediction.get('earnings_impact'), prediction.get('sector_outlook'),
                    self._calculate_target_date('MONTHLY')
                ))
                
                conn.commit()
                conn.close()
                print(f"   💾 Saved to monthly_predictions")
            
            return prediction
            
        except Exception as e:
            print(f"   ❌ Error generating monthly prediction: {e}")
            return None

    def update_historical_outcomes(self):
        """Finds predictions targeted for TODAY and updates them with actual prices from stock_market.db"""
        print(f"\n{'-'*20}")
        print("VERIFYING PAST PREDICTIONS...")
        print(f"{'-'*20}")
        
        try:
            from datetime import date
            today = date.today().isoformat()
            
            # Connect to both databases
            conn_pred = sqlite3.connect(self.pred_db_path)
            conn_stock = sqlite3.connect(self.main_db_path)
            
            # Find symbols we have predictions for TODAY
            cursor = conn_pred.execute("SELECT id, symbol FROM prediction_history WHERE prediction_date = ? AND close_price IS NULL", (today,))
            pending = cursor.fetchall()
            
            if not pending:
                print(f"No pending outcomes found for today ({today}).")
                return

            for row_id, symbol in pending:
                ticker = self.ticker_map.get(symbol, symbol)
                # Fetch actual price for today from stock market DB
                price_cursor = conn_stock.execute("SELECT open, close FROM stock_daily_prices WHERE symbol = ? AND date = ?", (ticker, today))
                actual = price_cursor.fetchone()
                
                if actual:
                    actual_open, actual_close = actual
                    conn_pred.execute("UPDATE prediction_history SET open_price = ?, close_price = ? WHERE id = ?", (actual_open, actual_close, row_id))
                    print(f"  ✓ Updated {symbol}: Actual Open {actual_open}, Close {actual_close}")
                else:
                    print(f"  ? No actual price data found for {symbol} on {today} yet.")
            
            conn_pred.commit()
            conn_pred.close()
            conn_stock.close()
            print("Historical verification complete.")
            
        except Exception as e:
            print(f"Error updating historical outcomes: {e}")

    def evaluate_predictions(self):
        """🧠 PHASE 1 ACTIVE LEARNING: Evaluate accuracy and update confidence adjustments"""
        print(f"\n{' -'*20}")
        print("🧠 EVALUATING PREDICTION ACCURACY...")
        print(f"{'-'*40}")
        
        try:
            conn = sqlite3.connect(self.pred_db_path)
            cursor = conn.cursor()
            
            # Find all predictions with verified outcomes that haven't been evaluated
            cursor.execute("""
                SELECT id, symbol, direction, predicted_move, open_price, close_price, confidence_score
                FROM prediction_history 
                WHERE open_price IS NOT NULL 
                AND close_price IS NOT NULL 
                AND was_correct IS NULL
            """)
            
            unevaluated = cursor.fetchall()
            
            if not unevaluated:
                print("  No new predictions to evaluate.")
                conn.close()
                return
            
            print(f"  Evaluating {len(unevaluated)} predictions...")
            
            for row in unevaluated:
                pred_id, symbol, direction, predicted_move, open_p, close_p, confidence = row
                
                # Calculate actual movement
                if open_p and open_p != 0:
                    actual_move = ((close_p - open_p) / open_p) * 100
                else:
                    continue
                
                # Determine actual direction
                if actual_move > 0.2:
                    actual_dir = 'UP'
                elif actual_move < -0.2:
                    actual_dir = 'DOWN'
                else:
                    actual_dir = 'NEUTRAL'
                
                # Check if prediction was correct
                was_correct = (direction == actual_dir)
                
                # Calculate error margin
                error_margin = abs(predicted_move - actual_move)
                
                # Accuracy score (0-1, based on direction + magnitude)
                direction_score = 1.0 if was_correct else 0.0
                magnitude_score = max(0, 1 - (error_margin / 10))  # Penalize large errors
                accuracy_score = (direction_score * 0.7) + (magnitude_score * 0.3)
                
                # Update the prediction record
                cursor.execute("""
                    UPDATE prediction_history 
                    SET was_correct = ?, accuracy_score = ?, error_margin = ?
                    WHERE id = ?
                """, (was_correct, accuracy_score, error_margin, pred_id))
                
                status = "✅" if was_correct else "❌"
                print(f"  {status} {symbol}: Pred {direction} ({predicted_move:+.2f}%) | Actual {actual_dir} ({actual_move:+.2f}%) | Score: {accuracy_score:.2f}")
            
            conn.commit()
            
            # Now calculate rolling performance per stock
            print(f"\n  📊 Calculating rolling performance...")
            self._update_performance_metrics(cursor)
            
            conn.commit()
            conn.close()
            print("✅ Evaluation complete!")
            
        except Exception as e:
            print(f"Error evaluating predictions: {e}")
    
    def _update_performance_metrics(self, cursor):
        """Calculate rolling accuracy and confidence adjustments per symbol"""
        from datetime import date
        today = date.today().isoformat()
        
        # Get unique symbols from evaluated predictions
        cursor.execute("SELECT DISTINCT symbol FROM prediction_history WHERE was_correct IS NOT NULL")
        symbols = [row[0] for row in cursor.fetchall()]
        
        for symbol in symbols:
            # Get last 10 evaluated predictions for this symbol
            cursor.execute("""
                SELECT was_correct, confidence_score, accuracy_score
                FROM prediction_history
                WHERE symbol = ? AND was_correct IS NOT NULL
                ORDER BY prediction_date DESC
                LIMIT 10
            """, (symbol,))
            
            results = cursor.fetchall()
            if not results:
                continue
            
            total = len(results)
            correct = sum(1 for r in results if r[0])
            accuracy_rate = (correct / total) * 100
            avg_confidence = sum(r[1] for r in results) / total
            avg_accuracy_score = sum(r[2] for r in results) / total
            
            # Calculate confidence adjustment
            # If accuracy > 70%: boost confidence (+1 to +2)
            # If accuracy < 50%: reduce confidence (-1 to -2)
            if accuracy_rate >= 70:
                adjustment = min(2.0, (accuracy_rate - 70) / 15)
            elif accuracy_rate < 50:
                adjustment = max(-2.0, (accuracy_rate - 50) / 15)
            else:
                adjustment = 0.0
            
            # Store performance metrics
            cursor.execute("""
                INSERT INTO prediction_performance (
                    symbol, evaluation_date, total_predictions, correct_predictions,
                    accuracy_rate, avg_confidence, confidence_adjustment
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (symbol, today, total, correct, accuracy_rate, avg_confidence, adjustment))
            
            print(f"    {symbol}: {accuracy_rate:.1f}% accurate ({correct}/{total}) → Confidence adj: {adjustment:+.1f}")
    
    def get_confidence_adjustment(self, symbol):
        """Get the current confidence adjustment for a symbol based on past performance"""
        try:
            conn = sqlite3.connect(self.pred_db_path)
            cursor = conn.cursor()
            
            # Get most recent performance record
            cursor.execute("""
                SELECT confidence_adjustment
                FROM prediction_performance
                WHERE symbol = ?
                ORDER BY evaluation_date DESC
                LIMIT 1
            """, (symbol,))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else 0.0
        except:
            return 0.0

    def _update_signal_performance(self, cursor, symbol, prediction_json, was_correct, actual_dir):
        """Track which specific signals (News, Technicals) worked or failed"""
        try:
            # Ensure table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signal_performance (
                    symbol TEXT,
                    indicator TEXT,
                    correct INTEGER DEFAULT 0,
                    total INTEGER DEFAULT 0,
                    accuracy REAL DEFAULT 0.0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (symbol, indicator)
                )
            """)
            
            pred_data = json.loads(prediction_json)
            
            # --- 1. EXTRACT SIGNALS ---
            
            # News Sentiment (From sentiment_score)
            sent_score = float(pred_data.get('sentiment_score', 5.0))
            if sent_score >= 7.0:
                news_signal = "UP"
            elif sent_score <= 3.0:
                news_signal = "DOWN"
            else:
                news_signal = "NEUTRAL"
                
            # Technical Score (From technical_score)
            tech_score = float(pred_data.get('technical_score', 5.0))
            if tech_score >= 7.0:
                tech_signal = "UP"
            elif tech_score <= 3.0:
                tech_signal = "DOWN"
            else:
                tech_signal = "NEUTRAL"
            
            signals = {
                'NEWS': news_signal,
                'TECHNICAL_OVERALL': tech_signal
            }
            
            # --- 2. EVALUATE & UPDATE ---
            
            for indicator, signal_dir in signals.items():
                if signal_dir == 'NEUTRAL':
                    continue # Skip neutral signals for accuracy tracking
                
                # Check correctness
                is_hit = False
                if signal_dir == 'UP' and actual_dir in ['UP', 'NEUTRAL']: # Generous for neutral
                    if actual_dir == 'UP': is_hit = True
                elif signal_dir == 'DOWN' and actual_dir in ['DOWN', 'NEUTRAL']:
                    if actual_dir == 'DOWN': is_hit = True
                
                # Update DB
                cursor.execute("""
                    INSERT OR IGNORE INTO signal_performance (symbol, indicator, correct, total, accuracy)
                    VALUES (?, ?, 0, 0, 0.0)
                """, (symbol, indicator))
                
                cursor.execute("""
                    UPDATE signal_performance
                    SET total = total + 1,
                        correct = correct + ?,
                        accuracy = ((correct + ?) * 100.0) / (total + 1),
                        last_updated = CURRENT_TIMESTAMP
                    WHERE symbol = ? AND indicator = ?
                """, (1 if is_hit else 0, 1 if is_hit else 0, symbol, indicator))
                
                if is_hit:
                    print(f"      ✅ {indicator} signal Correct for {symbol} (Acc updated)")
                else:
                    print(f"      ❌ {indicator} signal Failed for {symbol} (Acc updated)")

        except Exception as e:
            print(f"      ⚠️ Error updating signal performance: {e}")
            pass

    def _get_strategy_instruction(self, symbol):
        """Get dynamic instructions based on what signals work best for this stock"""
        try:
            conn = sqlite3.connect(self.pred_db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT indicator, accuracy, total_count FROM signal_performance WHERE symbol = ? AND total_count > 5", (symbol,))
            stats = cursor.fetchall()
            conn.close()
            
            if not stats:
                return "No specific strategy adjustments yet (insufficient data)."
            
            instructions = []
            for indicator, acc, count in stats:
                if acc > 70:
                    instructions.append(f"- TRUST {indicator}: High accuracy ({acc:.0f}%) for this stock.")
                elif acc < 40:
                    instructions.append(f"- IGNORE {indicator}: Low accuracy ({acc:.0f}%) for this stock.")
            
            return "\n".join(instructions) if instructions else "Standard strategy applies."
        except:
            return "Standard strategy applies."

if __name__ == "__main__":
    from src.utils.filter_companies import TOP_5_NIFTY, INDICES
    from datetime import date
    import calendar
    
    agent = PredictionAgent()
    
    # STEP 1: Update previous predictions with actual results
    agent.update_historical_outcomes()
    
    # STEP 2: 🧠 EVALUATE & LEARN from verified predictions
    agent.evaluate_predictions()
    
    # STEP 3: Generate new predictions for next trading day
    print("\nGenerating new MULTI-TIMEFRAME predictions...")
    import time
    
    # Check today's date for weekly/monthly triggers
    today = date.today()
    is_friday = today.weekday() == 4  # Friday = 4
    is_last_day_of_month = today.day == calendar.monthrange(today.year, today.month)[1]
    
    print(f"\n📅 Today: {today.strftime('%A, %B %d, %Y')}")
    print(f"   Weekly predictions: {'✅ ENABLED (Friday)' if is_friday else '❌ DISABLED (Only runs on Fridays)'}")
    print(f"   Monthly predictions: {'✅ ENABLED (Last day of month)' if is_last_day_of_month else '❌ DISABLED (Only runs on last day of month)'}")
    
    # Process all stocks
    all_symbols = {**TOP_5_NIFTY, **INDICES}
    for symbol in all_symbols.keys():
        print(f"\n{'='*40}")
        print(f"PROCESSING: {symbol}")
        print(f"{'='*40}")
        
        # 1. Daily Prediction (ALWAYS RUN)
        agent.predict_daily(symbol, save=True)
        time.sleep(3) # Rate limit safe
        
        # 2. Weekly Prediction (ONLY ON FRIDAYS)
        if is_friday:
            agent.predict_weekly(symbol, save=True)
            time.sleep(3)
        else:
            print(f"   ⏭️  Skipping weekly prediction (not Friday)")
        
        # 3. Monthly Prediction (ONLY ON LAST DAY OF MONTH)
        if is_last_day_of_month:
            agent.predict_monthly(symbol, save=True)
            time.sleep(3)
        else:
            print(f"   ⏭️  Skipping monthly prediction (not last day of month)")
    
    print(f"\nBatch process completed for {len(all_symbols)} items.")
