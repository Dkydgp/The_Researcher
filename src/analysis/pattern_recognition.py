"""
Chart Pattern Recognition
Detects common technical analysis patterns in price data
"""
import pandas as pd
import numpy as np
from scipy.signal import argrelextrema

class PatternRecognition:
    """Detect chart patterns in price data"""
    
    @staticmethod
    def detect_support_resistance(prices, window=5):
        """Detect support and resistance levels"""
        if len(prices) < window * 2:
            return None, None
        
        # Find local maxima (resistance) and minima (support)
        prices_array = prices.values if isinstance(prices, pd.Series) else prices
        
        local_max = argrelextrema(prices_array, np.greater, order=window)[0]
        local_min = argrelextrema(prices_array, np.less, order=window)[0]
        
        # Get resistance and support levels
        resistance_levels = prices_array[local_max] if len(local_max) > 0 else []
        support_levels = prices_array[local_min] if len(local_min) > 0 else []
        
        # Current closest levels
        current_price = prices_array[-1]
        
        resistance = None
        if len(resistance_levels) > 0:
            above = [r for r in resistance_levels if r > current_price]
            resistance = min(above) if above else None
        
        support = None
        if len(support_levels) > 0:
            below = [s for s in support_levels if s < current_price]
            support = max(below) if below else None
        
        return support, resistance
    
    @staticmethod
    def detect_double_top(prices, tolerance=0.02):
        """Detect double top pattern (bearish)"""
        if len(prices) < 10:
            return False
        
        prices_array = prices.values if isinstance(prices, pd.Series) else prices
        
        # Find peaks
        peaks = argrelextrema(prices_array, np.greater, order=3)[0]
        
        if len(peaks) < 2:
            return False
        
        # Check last two peaks
        last_two_peaks = peaks[-2:]
        peak1_price = prices_array[last_two_peaks[0]]
        peak2_price = prices_array[last_two_peaks[1]]
        
        # Peaks should be at similar levels
        if abs(peak1_price - peak2_price) / peak1_price <= tolerance:
            # Check if there's a trough between them
            trough_idx = last_two_peaks[0] + np.argmin(prices_array[last_two_peaks[0]:last_two_peaks[1]])
            trough_price = prices_array[trough_idx]
            
            # Trough should be significantly lower
            if (peak1_price - trough_price) / peak1_price > 0.03:
                return True
        
        return False
    
    @staticmethod
    def detect_double_bottom(prices, tolerance=0.02):
        """Detect double bottom pattern (bullish)"""
        if len(prices) < 10:
            return False
        
        prices_array = prices.values if isinstance(prices, pd.Series) else prices
        
        # Find troughs
        troughs = argrelextrema(prices_array, np.less, order=3)[0]
        
        if len(troughs) < 2:
            return False
        
        # Check last two troughs
        last_two_troughs = troughs[-2:]
        trough1_price = prices_array[last_two_troughs[0]]
        trough2_price = prices_array[last_two_troughs[1]]
        
        # Troughs should be at similar levels
        if abs(trough1_price - trough2_price) / trough1_price <= tolerance:
            # Check if there's a peak between them
            peak_idx = last_two_troughs[0] + np.argmax(prices_array[last_two_troughs[0]:last_two_troughs[1]])
            peak_price = prices_array[peak_idx]
            
            # Peak should be significantly higher
            if (peak_price - trough1_price) / trough1_price > 0.03:
                return True
        
        return False
    
    @staticmethod
    def detect_head_and_shoulders(prices, tolerance=0.02):
        """Detect head and shoulders pattern (bearish)"""
        if len(prices) < 15:
            return False
        
        prices_array = prices.values if isinstance(prices, pd.Series) else prices
        
        # Find peaks
        peaks = argrelextrema(prices_array, np.greater, order=3)[0]
        
        if len(peaks) < 3:
            return False
        
        # Check last three peaks
        last_three_peaks = peaks[-3:]
        left_shoulder = prices_array[last_three_peaks[0]]
        head = prices_array[last_three_peaks[1]]
        right_shoulder = prices_array[last_three_peaks[2]]
        
        # Head should be higher than shoulders
        if head > left_shoulder and head > right_shoulder:
            # Shoulders should be at similar levels
            if abs(left_shoulder - right_shoulder) / left_shoulder <= tolerance:
                return True
        
        return False
    
    @staticmethod
    def detect_triangle_consolidation(prices):
        """Detect triangle consolidation (pending breakout)"""
        if len(prices) < 10:
            return False
        
        prices_array = prices.values if isinstance(prices, pd.Series) else prices
        
        # Calculate highs and lows over time
        recent_prices = prices_array[-10:]
        
        # Find peaks and troughs
        peaks = argrelextrema(recent_prices, np.greater, order=2)[0]
        troughs = argrelextrema(recent_prices, np.less, order=2)[0]
        
        if len(peaks) < 2 or len(troughs) < 2:
            return False
        
        # Check if range is narrowing
        early_range = np.max(recent_prices[:5]) - np.min(recent_prices[:5])
        late_range = np.max(recent_prices[-5:]) - np.min(recent_prices[-5:])
        
        # Range narrowing indicates consolidation
        if late_range < early_range * 0.7:
            return True
        
        return False
    
    @staticmethod
    def detect_breakout(prices, support=None, resistance=None):
        """Detect if price has broken support or resistance"""
        if len(prices) < 2:
            return None
        
        prices_array = prices.values if isinstance(prices, pd.Series) else prices
        current_price = prices_array[-1]
        previous_price = prices_array[-2]
        
        # Resistance breakout (bullish)
        if resistance and previous_price < resistance and current_price > resistance:
            return {
                'type': 'RESISTANCE_BREAKOUT',
                'signal': 'BULLISH',
                'level': resistance,
                'strength': (current_price - resistance) / resistance
            }
        
        # Support breakdown (bearish)
        if support and previous_price > support and current_price < support:
            return {
                'type': 'SUPPORT_BREAKDOWN',
                'signal': 'BEARISH',
                'level': support,
                'strength': (support - current_price) / support
            }
        
        return None
    
    @staticmethod
    def analyze_patterns(price_data):
        """Analyze all patterns and return summary"""
        if len(price_data) < 10:
            return {'patterns': [], 'support': None, 'resistance': None}
        
        prices = price_data['close'] if isinstance(price_data, pd.DataFrame) else price_data
        
        patterns = []
        
        # Support/Resistance
        support, resistance = PatternRecognition.detect_support_resistance(prices)
        
        # Double patterns
        if PatternRecognition.detect_double_top(prices):
            patterns.append({
                'pattern': 'DOUBLE_TOP',
                'signal': 'BEARISH',
                'description': 'Price tested resistance twice and failed'
            })
        
        if PatternRecognition.detect_double_bottom(prices):
            patterns.append({
                'pattern': 'DOUBLE_BOTTOM',
                'signal': 'BULLISH',
                'description': 'Price tested support twice and held'
            })
        
        # Head and Shoulders
        if PatternRecognition.detect_head_and_shoulders(prices):
            patterns.append({
                'pattern': 'HEAD_AND_SHOULDERS',
                'signal': 'BEARISH',
                'description': 'Classic reversal pattern detected'
            })
        
        # Triangle
        if PatternRecognition.detect_triangle_consolidation(prices):
            patterns.append({
                'pattern': 'TRIANGLE_CONSOLIDATION',
                'signal': 'NEUTRAL',
                'description': 'Price consolidating, breakout pending'
            })
        
        # Breakout
        breakout = PatternRecognition.detect_breakout(prices, support, resistance)
        if breakout:
            patterns.append(breakout)
        
        return {
            'patterns': patterns,
            'support': float(support) if support else None,
            'resistance': float(resistance) if resistance else None,
            'current_price': float(prices.iloc[-1]) if isinstance(prices, pd.Series) else float(prices[-1])
        }
