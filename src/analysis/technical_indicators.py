"""
Technical Indicators Calculator
Calculates RSI, MACD, Bollinger Bands, and Volume indicators
"""
import pandas as pd
import numpy as np

class TechnicalIndicators:
    """Calculate advanced technical indicators"""
    
    @staticmethod
    def calculate_rsi(prices, period=14):
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return None
        
        # Calculate price changes
        delta = prices.diff()
        
        # Separate gains and losses
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)
        
        # Calculate average gains and losses
        avg_gains = gains.rolling(window=period).mean()
        avg_losses = losses.rolling(window=period).mean()
        
        # Calculate RS and RSI
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else None
    
    @staticmethod
    def calculate_macd(prices, fast=12, slow=26, signal=9):
        """Calculate MACD (Moving Average Convergence Divergence)"""
        if len(prices) < slow + signal:
            return None, None, None
        
        # Calculate EMAs
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        
        # MACD line
        macd_line = ema_fast - ema_slow
        
        # Signal line
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        
        # Histogram
        histogram = macd_line - signal_line
        
        return (macd_line.iloc[-1] if not pd.isna(macd_line.iloc[-1]) else None,
                signal_line.iloc[-1] if not pd.isna(signal_line.iloc[-1]) else None,
                histogram.iloc[-1] if not pd.isna(histogram.iloc[-1]) else None)
    
    @staticmethod
    def calculate_bollinger_bands(prices, period=20, num_std=2):
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            return None, None, None
        
        # Middle band (SMA)
        middle_band = prices.rolling(window=period).mean()
        
        # Standard deviation
        std_dev = prices.rolling(window=period).std()
        
        # Upper and lower bands
        upper_band = middle_band + (std_dev * num_std)
        lower_band = middle_band - (std_dev * num_std)
        
        return (upper_band.iloc[-1] if not pd.isna(upper_band.iloc[-1]) else None,
                middle_band.iloc[-1] if not pd.isna(middle_band.iloc[-1]) else None,
                lower_band.iloc[-1] if not pd.isna(lower_band.iloc[-1]) else None)
    
    @staticmethod
    def calculate_volume_indicators(volumes, period=20):
        """Calculate volume moving average and ratio"""
        if len(volumes) < period:
            return None, None
        
        volume_ma = volumes.rolling(window=period).mean()
        
        current_volume = volumes.iloc[-1]
        avg_volume = volume_ma.iloc[-1]
        
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else None
        
        return (avg_volume if not pd.isna(avg_volume) else None,
                volume_ratio if volume_ratio and not pd.isna(volume_ratio) else None)
    
    @staticmethod
    def get_rsi_signal(rsi):
        """Interpret RSI value"""
        if rsi is None:
            return "UNKNOWN"
        if rsi > 70:
            return "OVERBOUGHT"
        elif rsi < 30:
            return "OVERSOLD"
        else:
            return "NEUTRAL"
    
    @staticmethod
    def get_macd_signal(macd, signal):
        """Interpret MACD"""
        if macd is None or signal is None:
            return "UNKNOWN"
        if macd > signal:
            return "BULLISH"
        else:
            return "BEARISH"
    
    @staticmethod
    def get_bb_position(current_price, bb_upper, bb_middle, bb_lower):
        """Calculate where price is positioned in Bollinger Bands"""
        if None in [current_price, bb_upper, bb_lower]:
            return None
        
        band_width = bb_upper - bb_lower
        if band_width == 0:
            return 50
        
        position = ((current_price - bb_lower) / band_width) * 100
        return round(position, 1)
