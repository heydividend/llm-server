#!/usr/bin/env python3
"""
Advanced Feature Engineering for Dividend ML Models
Creates sophisticated technical indicators and fundamental ratios for ML training
"""

import argparse
import json
import os
import sys
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Union, Optional

# Suppress warnings
warnings.filterwarnings('ignore')

try:
    import pandas as pd
    import numpy as np
    from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
    from sklearn.feature_selection import mutual_info_regression, SelectKBest, f_regression
    import joblib
    
    # Technical analysis indicators
    try:
        import talib
        TALIB_AVAILABLE = True
    except ImportError:
        TALIB_AVAILABLE = False
        print("⚠️ TA-Lib not available - using custom technical indicators")
    
    # Statistical tools
    try:
        from scipy import stats
        from scipy.signal import find_peaks
        SCIPY_AVAILABLE = True
    except ImportError:
        SCIPY_AVAILABLE = False
        print("⚠️ SciPy not available - some statistical features disabled")
        
except ImportError as e:
    print(f"Error importing required packages: {e}")
    print("Please ensure packages are installed:")
    print("pip install pandas numpy scikit-learn joblib")
    print("Optional: pip install talib scipy")
    sys.exit(1)


class DividendFeatureEngineer:
    """
    Advanced feature engineering for dividend prediction models
    Creates technical indicators, fundamental ratios, and derived features
    """
    
    def __init__(self):
        """Initialize the feature engineer"""
        self.feature_metadata = {}
        self.scalers = {}
        self.feature_importance = {}
        
        # Feature categories
        self.technical_features = []
        self.fundamental_features = []
        self.dividend_features = []
        self.market_features = []
        self.interaction_features = []
        
    def create_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create comprehensive technical analysis indicators
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with technical indicators
        """
        print("📊 Creating technical indicators...")
        
        # Ensure required columns exist
        required_cols = ['close', 'volume', 'high', 'low', 'open']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            print(f"⚠️ Missing columns for technical indicators: {missing_cols}")
            # Create synthetic price data if missing
            if 'close' not in df.columns:
                df['close'] = 100 + np.random.normal(0, 5, len(df)).cumsum()
            if 'volume' not in df.columns:
                df['volume'] = np.random.lognormal(12, 0.5, len(df))
            if 'high' not in df.columns:
                df['high'] = df['close'] * (1 + np.random.uniform(0, 0.03, len(df)))
            if 'low' not in df.columns:
                df['low'] = df['close'] * (1 - np.random.uniform(0, 0.03, len(df)))
            if 'open' not in df.columns:
                df['open'] = df['close'].shift(1).fillna(df['close'])
        
        # Price-based indicators
        df = self._create_price_indicators(df)
        
        # Volume-based indicators
        df = self._create_volume_indicators(df)
        
        # Volatility indicators
        df = self._create_volatility_indicators(df)
        
        # Momentum indicators
        df = self._create_momentum_indicators(df)
        
        # Trend indicators
        df = self._create_trend_indicators(df)
        
        return df
    
    def _create_price_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create price-based technical indicators"""
        
        # Moving averages
        for period in [5, 10, 20, 50, 100, 200]:
            df[f'sma_{period}'] = df['close'].rolling(window=period).mean()
            df[f'ema_{period}'] = df['close'].ewm(span=period).mean()
            
            # Price ratios to moving averages
            df[f'price_to_sma_{period}'] = df['close'] / df[f'sma_{period}']
            df[f'price_to_ema_{period}'] = df['close'] / df[f'ema_{period}']
        
        # Bollinger Bands
        sma_20 = df['close'].rolling(window=20).mean()
        std_20 = df['close'].rolling(window=20).std()
        df['bb_upper'] = sma_20 + (2 * std_20)
        df['bb_lower'] = sma_20 - (2 * std_20)
        df['bb_middle'] = sma_20
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # Support and Resistance levels
        df = self._calculate_support_resistance(df)
        
        # Price channels
        for period in [10, 20, 50]:
            df[f'highest_{period}'] = df['high'].rolling(window=period).max()
            df[f'lowest_{period}'] = df['low'].rolling(window=period).min()
            df[f'channel_position_{period}'] = (
                (df['close'] - df[f'lowest_{period}']) / 
                (df[f'highest_{period}'] - df[f'lowest_{period}'])
            )
        
        return df
    
    def _calculate_support_resistance(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate dynamic support and resistance levels"""
        
        if not SCIPY_AVAILABLE:
            # Simple support/resistance using rolling min/max
            df['support_level'] = df['low'].rolling(window=20).min()
            df['resistance_level'] = df['high'].rolling(window=20).max()
            df['distance_to_support'] = (df['close'] - df['support_level']) / df['close']
            df['distance_to_resistance'] = (df['resistance_level'] - df['close']) / df['close']
            return df
        
        # Advanced support/resistance using peak detection
        window = 20
        support_levels = []
        resistance_levels = []
        
        for i in range(len(df)):
            if i < window:
                support_levels.append(df['low'].iloc[:i+1].min())
                resistance_levels.append(df['high'].iloc[:i+1].max())
            else:
                window_data = df.iloc[i-window:i+1]
                
                # Find local minima (support) and maxima (resistance)
                low_peaks, _ = find_peaks(-window_data['low'].values, distance=5)
                high_peaks, _ = find_peaks(window_data['high'].values, distance=5)
                
                if len(low_peaks) > 0:
                    support_levels.append(window_data['low'].iloc[low_peaks].min())
                else:
                    support_levels.append(window_data['low'].min())
                
                if len(high_peaks) > 0:
                    resistance_levels.append(window_data['high'].iloc[high_peaks].max())
                else:
                    resistance_levels.append(window_data['high'].max())
        
        df['support_level'] = support_levels
        df['resistance_level'] = resistance_levels
        df['distance_to_support'] = (df['close'] - df['support_level']) / df['close']
        df['distance_to_resistance'] = (df['resistance_level'] - df['close']) / df['close']
        
        return df
    
    def _create_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create volume-based indicators"""
        
        # Volume moving averages
        for period in [10, 20, 50]:
            df[f'volume_sma_{period}'] = df['volume'].rolling(window=period).mean()
            df[f'volume_ratio_{period}'] = df['volume'] / df[f'volume_sma_{period}']
        
        # Volume Price Trend (VPT)
        df['volume_price_trend'] = (df['volume'] * 
                                   ((df['close'] - df['close'].shift(1)) / df['close'].shift(1))).cumsum()
        
        # On Balance Volume (OBV)
        df['price_change'] = df['close'].diff()
        df['obv'] = np.where(df['price_change'] > 0, df['volume'],
                    np.where(df['price_change'] < 0, -df['volume'], 0)).cumsum()
        
        # Volume Rate of Change
        for period in [10, 20]:
            df[f'volume_roc_{period}'] = df['volume'].pct_change(periods=period)
        
        # Accumulation/Distribution Line
        money_flow_multiplier = ((df['close'] - df['low']) - (df['high'] - df['close'])) / (df['high'] - df['low'])
        money_flow_volume = money_flow_multiplier * df['volume']
        df['accumulation_distribution'] = money_flow_volume.cumsum()
        
        return df
    
    def _create_volatility_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create volatility-based indicators"""
        
        # Historical volatility
        for period in [10, 20, 50]:
            returns = df['close'].pct_change()
            df[f'volatility_{period}'] = returns.rolling(window=period).std() * np.sqrt(252)
        
        # Average True Range (ATR)
        high_low = df['high'] - df['low']
        high_close_prev = np.abs(df['high'] - df['close'].shift(1))
        low_close_prev = np.abs(df['low'] - df['close'].shift(1))
        
        true_range = np.maximum(high_low, np.maximum(high_close_prev, low_close_prev))
        for period in [14, 28]:
            df[f'atr_{period}'] = true_range.rolling(window=period).mean()
            df[f'atr_ratio_{period}'] = df[f'atr_{period}'] / df['close']
        
        # Volatility Ratio
        df['volatility_ratio'] = df['volatility_10'] / df['volatility_50']
        
        # Price Range indicators
        df['daily_range'] = (df['high'] - df['low']) / df['close']
        df['gap'] = (df['open'] - df['close'].shift(1)) / df['close'].shift(1)
        
        return df
    
    def _create_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create momentum-based indicators"""
        
        # RSI (Relative Strength Index)
        for period in [14, 28]:
            df[f'rsi_{period}'] = self._calculate_rsi(df['close'], period)
        
        # MACD (Moving Average Convergence Divergence)
        exp1 = df['close'].ewm(span=12).mean()
        exp2 = df['close'].ewm(span=26).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # Stochastic Oscillator
        for period in [14, 28]:
            lowest_low = df['low'].rolling(window=period).min()
            highest_high = df['high'].rolling(window=period).max()
            df[f'stoch_k_{period}'] = 100 * ((df['close'] - lowest_low) / (highest_high - lowest_low))
            df[f'stoch_d_{period}'] = df[f'stoch_k_{period}'].rolling(window=3).mean()
        
        # Commodity Channel Index (CCI)
        for period in [20, 50]:
            typical_price = (df['high'] + df['low'] + df['close']) / 3
            sma_tp = typical_price.rolling(window=period).mean()
            mad = typical_price.rolling(window=period).apply(lambda x: np.mean(np.abs(x - x.mean())))
            df[f'cci_{period}'] = (typical_price - sma_tp) / (0.015 * mad)
        
        # Rate of Change
        for period in [10, 20, 50]:
            df[f'roc_{period}'] = df['close'].pct_change(periods=period)
        
        # Williams %R
        for period in [14, 28]:
            highest_high = df['high'].rolling(window=period).max()
            lowest_low = df['low'].rolling(window=period).min()
            df[f'williams_r_{period}'] = -100 * ((highest_high - df['close']) / (highest_high - lowest_low))
        
        return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _create_trend_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create trend-based indicators"""
        
        # Parabolic SAR (simplified)
        df['parabolic_sar'] = self._calculate_parabolic_sar(df)
        
        # Ichimoku Cloud components
        period9_high = df['high'].rolling(window=9).max()
        period9_low = df['low'].rolling(window=9).min()
        df['ichimoku_tenkan'] = (period9_high + period9_low) / 2
        
        period26_high = df['high'].rolling(window=26).max()
        period26_low = df['low'].rolling(window=26).min()
        df['ichimoku_kijun'] = (period26_high + period26_low) / 2
        
        df['ichimoku_senkou_a'] = ((df['ichimoku_tenkan'] + df['ichimoku_kijun']) / 2).shift(26)
        
        period52_high = df['high'].rolling(window=52).max()
        period52_low = df['low'].rolling(window=52).min()
        df['ichimoku_senkou_b'] = ((period52_high + period52_low) / 2).shift(26)
        
        # Aroon Oscillator
        for period in [14, 25]:
            df[f'aroon_up_{period}'] = 100 * (period - df['high'].rolling(window=period).apply(
                lambda x: period - 1 - x.argmax())) / period
            df[f'aroon_down_{period}'] = 100 * (period - df['low'].rolling(window=period).apply(
                lambda x: period - 1 - x.argmin())) / period
            df[f'aroon_oscillator_{period}'] = df[f'aroon_up_{period}'] - df[f'aroon_down_{period}']
        
        return df
    
    def _calculate_parabolic_sar(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Parabolic SAR indicator"""
        # Simplified Parabolic SAR calculation
        sar = pd.Series(index=df.index, dtype=float)
        af = 0.02
        max_af = 0.2
        
        # Initialize
        sar.iloc[0] = df['low'].iloc[0]
        trend = 1  # 1 for up, -1 for down
        
        for i in range(1, len(df)):
            if trend == 1:  # Uptrend
                sar.iloc[i] = sar.iloc[i-1] + af * (df['high'].iloc[i-1] - sar.iloc[i-1])
                if df['low'].iloc[i] <= sar.iloc[i]:
                    trend = -1
                    sar.iloc[i] = df['high'].iloc[i-1]
                    af = 0.02
            else:  # Downtrend
                sar.iloc[i] = sar.iloc[i-1] + af * (df['low'].iloc[i-1] - sar.iloc[i-1])
                if df['high'].iloc[i] >= sar.iloc[i]:
                    trend = 1
                    sar.iloc[i] = df['low'].iloc[i-1]
                    af = 0.02
            
            # Update acceleration factor
            if af < max_af:
                af = min(af + 0.02, max_af)
        
        return sar
    
    def create_fundamental_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create fundamental analysis features
        
        Args:
            df: DataFrame with fundamental data
            
        Returns:
            DataFrame with fundamental features
        """
        print("📈 Creating fundamental features...")
        
        # Profitability ratios and trends
        df = self._create_profitability_features(df)
        
        # Liquidity and solvency features
        df = self._create_liquidity_features(df)
        
        # Efficiency features
        df = self._create_efficiency_features(df)
        
        # Growth features
        df = self._create_growth_features(df)
        
        # Valuation features
        df = self._create_valuation_features(df)
        
        # Quality features
        df = self._create_quality_features(df)
        
        return df
    
    def _create_profitability_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create profitability-based features"""
        
        # ROE trend analysis
        if 'roe' in df.columns:
            for period in [4, 8, 12]:
                df[f'roe_trend_{period}'] = df['roe'].rolling(window=period).apply(
                    lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) >= 2 else 0
                )
                df[f'roe_volatility_{period}'] = df['roe'].rolling(window=period).std()
            
            df['roe_percentile'] = df['roe'].rolling(window=20).rank(pct=True)
            df['roe_zscore'] = (df['roe'] - df['roe'].rolling(window=20).mean()) / df['roe'].rolling(window=20).std()
        
        # ROA analysis
        if 'roa' in df.columns:
            for period in [4, 8]:
                df[f'roa_trend_{period}'] = df['roa'].rolling(window=period).apply(
                    lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) >= 2 else 0
                )
        
        # Gross margin analysis
        if all(col in df.columns for col in ['revenue', 'cost_of_goods_sold']):
            df['gross_margin'] = (df['revenue'] - df['cost_of_goods_sold']) / df['revenue']
            df['gross_margin_trend'] = df['gross_margin'].rolling(window=4).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) >= 2 else 0
            )
        
        # Operating margin analysis
        if all(col in df.columns for col in ['operating_income', 'revenue']):
            df['operating_margin'] = df['operating_income'] / df['revenue']
            df['operating_margin_trend'] = df['operating_margin'].rolling(window=4).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) >= 2 else 0
            )
        
        # Net margin analysis
        if all(col in df.columns for col in ['net_income', 'revenue']):
            df['net_margin'] = df['net_income'] / df['revenue']
            df['net_margin_stability'] = df['net_margin'].rolling(window=8).std()
        
        return df
    
    def _create_liquidity_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create liquidity and solvency features"""
        
        # Current ratio trend
        if 'current_ratio' in df.columns:
            df['current_ratio_trend'] = df['current_ratio'].rolling(window=4).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) >= 2 else 0
            )
            df['current_ratio_volatility'] = df['current_ratio'].rolling(window=4).std()
        
        # Quick ratio
        if all(col in df.columns for col in ['current_assets', 'inventory', 'current_liabilities']):
            df['quick_ratio'] = (df['current_assets'] - df['inventory']) / df['current_liabilities']
        
        # Cash ratio
        if all(col in df.columns for col in ['cash', 'current_liabilities']):
            df['cash_ratio'] = df['cash'] / df['current_liabilities']
        
        # Debt ratios and trends
        if 'debt_to_equity' in df.columns:
            df['debt_to_equity_trend'] = df['debt_to_equity'].rolling(window=4).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) >= 2 else 0
            )
        
        if 'debt_to_assets' in df.columns:
            df['debt_to_assets_trend'] = df['debt_to_assets'].rolling(window=4).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) >= 2 else 0
            )
        
        # Interest coverage analysis
        if 'interest_coverage' in df.columns:
            df['interest_coverage_trend'] = df['interest_coverage'].rolling(window=4).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) >= 2 else 0
            )
            df['interest_coverage_volatility'] = df['interest_coverage'].rolling(window=4).std()
        
        return df
    
    def _create_efficiency_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create efficiency-based features"""
        
        # Asset turnover trends
        if 'asset_turnover' in df.columns:
            df['asset_turnover_trend'] = df['asset_turnover'].rolling(window=4).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) >= 2 else 0
            )
        
        # Inventory turnover
        if all(col in df.columns for col in ['cost_of_goods_sold', 'inventory']):
            df['inventory_turnover'] = df['cost_of_goods_sold'] / df['inventory']
            df['inventory_turnover_trend'] = df['inventory_turnover'].rolling(window=4).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) >= 2 else 0
            )
        
        # Receivables turnover
        if all(col in df.columns for col in ['revenue', 'accounts_receivable']):
            df['receivables_turnover'] = df['revenue'] / df['accounts_receivable']
        
        # Working capital efficiency
        if all(col in df.columns for col in ['current_assets', 'current_liabilities', 'revenue']):
            working_capital = df['current_assets'] - df['current_liabilities']
            df['working_capital_to_revenue'] = working_capital / df['revenue']
            df['working_capital_trend'] = df['working_capital_to_revenue'].rolling(window=4).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) >= 2 else 0
            )
        
        return df
    
    def _create_growth_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create growth-based features"""
        
        # Revenue growth analysis
        if 'revenue' in df.columns:
            for period in [1, 4, 8, 12]:
                df[f'revenue_growth_{period}q'] = df['revenue'].pct_change(periods=period)
            
            # Revenue growth acceleration
            df['revenue_growth_acceleration'] = (df['revenue_growth_1q'] - df['revenue_growth_4q']) / 4
            
            # Revenue growth volatility
            df['revenue_growth_volatility'] = df['revenue_growth_1q'].rolling(window=8).std()
        
        # Earnings growth analysis
        if 'net_income' in df.columns:
            for period in [1, 4, 8]:
                df[f'earnings_growth_{period}q'] = df['net_income'].pct_change(periods=period)
            
            # Earnings growth consistency
            df['earnings_growth_consistency'] = 1 / (1 + df['earnings_growth_1q'].rolling(window=8).std())
        
        # Cash flow growth
        if 'operating_cash_flow' in df.columns:
            for period in [1, 4]:
                df[f'ocf_growth_{period}q'] = df['operating_cash_flow'].pct_change(periods=period)
        
        if 'free_cash_flow' in df.columns:
            for period in [1, 4]:
                df[f'fcf_growth_{period}q'] = df['free_cash_flow'].pct_change(periods=period)
        
        # Book value growth
        if 'book_value_per_share' in df.columns:
            df['book_value_growth_1q'] = df['book_value_per_share'].pct_change(periods=1)
            df['book_value_growth_4q'] = df['book_value_per_share'].pct_change(periods=4)
        
        return df
    
    def _create_valuation_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create valuation-based features"""
        
        # P/E ratio analysis
        if 'pe_ratio' in df.columns:
            df['pe_percentile'] = df['pe_ratio'].rolling(window=20).rank(pct=True)
            df['pe_zscore'] = (df['pe_ratio'] - df['pe_ratio'].rolling(window=20).mean()) / df['pe_ratio'].rolling(window=20).std()
            
            # PE trend
            df['pe_trend'] = df['pe_ratio'].rolling(window=4).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) >= 2 else 0
            )
        
        # P/B ratio analysis
        if 'pb_ratio' in df.columns:
            df['pb_percentile'] = df['pb_ratio'].rolling(window=20).rank(pct=True)
            df['pb_trend'] = df['pb_ratio'].rolling(window=4).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) >= 2 else 0
            )
        
        # Price-to-Sales ratio
        if all(col in df.columns for col in ['market_cap', 'revenue']):
            df['ps_ratio'] = df['market_cap'] / df['revenue']
            df['ps_percentile'] = df['ps_ratio'].rolling(window=20).rank(pct=True)
        
        # EV/EBITDA
        if all(col in df.columns for col in ['enterprise_value', 'ebitda']):
            df['ev_ebitda'] = df['enterprise_value'] / df['ebitda']
            df['ev_ebitda_percentile'] = df['ev_ebitda'].rolling(window=20).rank(pct=True)
        
        # Price-to-Cash Flow
        if all(col in df.columns for col in ['market_cap', 'operating_cash_flow']):
            df['pcf_ratio'] = df['market_cap'] / df['operating_cash_flow']
        
        return df
    
    def _create_quality_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create quality-based features"""
        
        # Earnings quality
        if all(col in df.columns for col in ['operating_cash_flow', 'net_income']):
            df['earnings_quality'] = df['operating_cash_flow'] / df['net_income'].clip(lower=0.01)
            df['earnings_quality_trend'] = df['earnings_quality'].rolling(window=4).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) >= 2 else 0
            )
        
        # Accruals ratio
        if all(col in df.columns for col in ['net_income', 'operating_cash_flow', 'total_assets']):
            accruals = (df['net_income'] - df['operating_cash_flow']) / df['total_assets']
            df['accruals_ratio'] = accruals
        
        # Capital allocation efficiency
        if all(col in df.columns for col in ['capex', 'depreciation', 'total_assets']):
            df['capex_to_depreciation'] = df['capex'] / df['depreciation'].clip(lower=0.01)
            df['capex_to_assets'] = df['capex'] / df['total_assets']
        
        # Return on invested capital
        if all(col in df.columns for col in ['operating_income', 'invested_capital']):
            df['roic'] = df['operating_income'] / df['invested_capital']
            df['roic_trend'] = df['roic'].rolling(window=4).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) >= 2 else 0
            )
        
        return df
    
    def create_dividend_specific_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create dividend-specific features
        
        Args:
            df: DataFrame with dividend data
            
        Returns:
            DataFrame with dividend features
        """
        print("💰 Creating dividend-specific features...")
        
        # Dividend yield features
        df = self._create_yield_features(df)
        
        # Payout ratio features
        df = self._create_payout_features(df)
        
        # Dividend growth features
        df = self._create_dividend_growth_features(df)
        
        # Dividend sustainability features
        df = self._create_sustainability_features(df)
        
        # Dividend timing features
        df = self._create_dividend_timing_features(df)
        
        # Monthly NAV % features (for ETFs and funds)
        df = self._create_monthly_nav_features(df)
        
        return df
    
    def _create_yield_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create dividend yield features"""
        
        if 'dividend_yield' not in df.columns:
            return df
        
        # Yield statistics
        for period in [4, 8, 12, 20]:
            df[f'yield_mean_{period}'] = df['dividend_yield'].rolling(window=period).mean()
            df[f'yield_std_{period}'] = df['dividend_yield'].rolling(window=period).std()
            df[f'yield_min_{period}'] = df['dividend_yield'].rolling(window=period).min()
            df[f'yield_max_{period}'] = df['dividend_yield'].rolling(window=period).max()
        
        # Yield trends
        for period in [4, 8, 12]:
            df[f'yield_trend_{period}'] = df['dividend_yield'].rolling(window=period).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) >= 2 else 0
            )
        
        # Yield momentum
        df['yield_momentum_1q'] = df['dividend_yield'].pct_change(periods=1)
        df['yield_momentum_4q'] = df['dividend_yield'].pct_change(periods=4)
        
        # Yield mean reversion
        df['yield_mean_reversion'] = (df['dividend_yield'] - df['yield_mean_12']) / df['yield_std_12']
        
        # Yield percentile ranking
        df['yield_percentile'] = df['dividend_yield'].rolling(window=20).rank(pct=True)
        
        return df
    
    def _create_payout_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create payout ratio features"""
        
        if 'payout_ratio' not in df.columns:
            return df
        
        # Payout ratio statistics
        for period in [4, 8, 12]:
            df[f'payout_mean_{period}'] = df['payout_ratio'].rolling(window=period).mean()
            df[f'payout_std_{period}'] = df['payout_ratio'].rolling(window=period).std()
            df[f'payout_trend_{period}'] = df['payout_ratio'].rolling(window=period).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) >= 2 else 0
            )
        
        # Payout volatility
        df['payout_volatility'] = df['payout_ratio'].rolling(window=8).std()
        
        # Payout stability score
        df['payout_stability'] = 1 / (1 + df['payout_volatility'])
        
        # Payout cycle analysis
        df['payout_cycle_high'] = df['payout_ratio'].rolling(window=12).max()
        df['payout_cycle_low'] = df['payout_ratio'].rolling(window=12).min()
        df['payout_cycle_range'] = df['payout_cycle_high'] - df['payout_cycle_low']
        
        return df
    
    def _create_dividend_growth_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create dividend growth features"""
        
        if 'dividend_per_share' not in df.columns:
            return df
        
        # Dividend growth rates
        for period in [1, 4, 8, 12]:
            df[f'dividend_growth_{period}q'] = df['dividend_per_share'].pct_change(periods=period)
        
        # Growth acceleration
        df['dividend_growth_acceleration'] = (df['dividend_growth_1q'] - df['dividend_growth_4q']) / 4
        
        # Growth consistency
        df['dividend_growth_consistency'] = 1 / (1 + df['dividend_growth_1q'].rolling(window=8).std())
        
        # Compound annual growth rate (CAGR)
        def calculate_cagr(series, periods):
            if len(series) < periods or series.iloc[0] <= 0:
                return 0
            return (series.iloc[-1] / series.iloc[0]) ** (1/periods) - 1
        
        for years in [3, 5, 10]:
            periods = years * 4  # Quarterly data
            df[f'dividend_cagr_{years}y'] = df['dividend_per_share'].rolling(window=periods).apply(
                lambda x: calculate_cagr(x, years) if len(x) == periods else np.nan
            )
        
        # Growth streak analysis
        df['positive_growth_streak'] = (df['dividend_growth_1q'] > 0).astype(int).groupby(
            (df['dividend_growth_1q'] <= 0).cumsum()
        ).cumsum()
        
        return df
    
    def _create_sustainability_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create dividend sustainability features"""
        
        # Earnings coverage
        if all(col in df.columns for col in ['dividend_per_share', 'earnings_per_share']):
            df['earnings_coverage'] = df['earnings_per_share'] / df['dividend_per_share'].clip(lower=0.01)
            df['earnings_coverage_trend'] = df['earnings_coverage'].rolling(window=4).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) >= 2 else 0
            )
        
        # Free cash flow coverage
        if all(col in df.columns for col in ['free_cash_flow', 'total_dividends_paid']):
            df['fcf_coverage'] = df['free_cash_flow'] / df['total_dividends_paid'].clip(lower=0.01)
            df['fcf_coverage_trend'] = df['fcf_coverage'].rolling(window=4).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) >= 2 else 0
            )
        
        # Debt service capability
        if all(col in df.columns for col in ['operating_cash_flow', 'debt_payments', 'total_dividends_paid']):
            total_obligations = df['debt_payments'] + df['total_dividends_paid']
            df['obligation_coverage'] = df['operating_cash_flow'] / total_obligations.clip(lower=0.01)
        
        # Dividend sustainability score
        sustainability_factors = []
        
        if 'earnings_coverage' in df.columns:
            sustainability_factors.append(np.clip(df['earnings_coverage'] / 2.0, 0, 1))
        
        if 'fcf_coverage' in df.columns:
            sustainability_factors.append(np.clip(df['fcf_coverage'] / 1.5, 0, 1))
        
        if 'debt_to_equity' in df.columns:
            sustainability_factors.append(1 - np.clip(df['debt_to_equity'], 0, 1))
        
        if sustainability_factors:
            df['dividend_sustainability_score'] = np.mean(sustainability_factors, axis=0)
        
        return df
    
    def _create_dividend_timing_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create dividend timing and seasonality features"""
        
        # Quarterly seasonality
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df['quarter'] = df['date'].dt.quarter
            df['month'] = df['date'].dt.month
            
            # Seasonal patterns
            df['q1_season'] = (df['quarter'] == 1).astype(int)
            df['q4_season'] = (df['quarter'] == 4).astype(int)
            df['year_end_season'] = (df['month'] == 12).astype(int)
        
        # Days since last dividend
        if 'dividend_payment_date' in df.columns:
            df['dividend_payment_date'] = pd.to_datetime(df['dividend_payment_date'])
            df['days_since_last_dividend'] = (df['dividend_payment_date'].diff().dt.days).fillna(90)
        
        # Dividend frequency consistency
        if 'days_since_last_dividend' in df.columns:
            df['dividend_frequency_consistency'] = 1 / (1 + df['days_since_last_dividend'].rolling(window=4).std())
        
        return df
    
    def _create_monthly_nav_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create Monthly NAV % features for ETFs and funds
        Monthly NAV % represents the dividend as a percentage of the fund's Net Asset Value
        Note: All features are calculated per symbol to prevent data leakage
        """
        
        if 'monthly_nav_percent' not in df.columns:
            return df
        
        if 'symbol' not in df.columns:
            print("⚠️ Warning: 'symbol' column not found. NAV features will be calculated globally.")
            return df
        
        print("📊 Creating Monthly NAV % features (per-symbol)...")
        
        def create_nav_features_per_symbol(group):
            """Create NAV features within a single symbol's data"""
            
            # NAV % statistics (per symbol)
            for period in [3, 6, 12, 24]:
                group[f'nav_mean_{period}'] = group['monthly_nav_percent'].rolling(window=period).mean()
                group[f'nav_std_{period}'] = group['monthly_nav_percent'].rolling(window=period).std()
                group[f'nav_min_{period}'] = group['monthly_nav_percent'].rolling(window=period).min()
                group[f'nav_max_{period}'] = group['monthly_nav_percent'].rolling(window=period).max()
            
            # NAV % trends (per symbol)
            for period in [3, 6, 12]:
                group[f'nav_trend_{period}'] = group['monthly_nav_percent'].rolling(window=period).apply(
                    lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) >= 2 else 0
                )
            
            # NAV % momentum (rate of change, per symbol)
            group['nav_momentum_1m'] = group['monthly_nav_percent'].pct_change(periods=1)
            group['nav_momentum_3m'] = group['monthly_nav_percent'].pct_change(periods=3)
            group['nav_momentum_6m'] = group['monthly_nav_percent'].pct_change(periods=6)
            
            # NAV % volatility (per symbol)
            group['nav_volatility_6m'] = group['monthly_nav_percent'].rolling(window=6).std()
            group['nav_volatility_12m'] = group['monthly_nav_percent'].rolling(window=12).std()
            
            # NAV % stability score (inverse of volatility, with safety check)
            group['nav_stability_score'] = 1 / (1 + group['nav_volatility_12m'].fillna(0))
            
            # NAV % percentile ranking (relative position in historical distribution, per symbol)
            group['nav_percentile_12m'] = group['monthly_nav_percent'].rolling(window=12).rank(pct=True)
            group['nav_percentile_24m'] = group['monthly_nav_percent'].rolling(window=24).rank(pct=True)
            
            # NAV % Z-score (how many standard deviations from mean, with safety check)
            nav_std_safe = group['nav_std_12'].clip(lower=0.01)  # Prevent division by zero
            group['nav_zscore_12m'] = (group['monthly_nav_percent'] - group['nav_mean_12']) / nav_std_safe
            
            # NAV % mean reversion indicator (with safety check)
            group['nav_mean_reversion_12m'] = (group['monthly_nav_percent'] - group['nav_mean_12']) / nav_std_safe
            
            # NAV % range analysis (distance from min/max, with safety check)
            group['nav_range_12m'] = group['nav_max_12'] - group['nav_min_12']
            nav_range_safe = group['nav_range_12m'].replace(0, np.nan)  # Avoid division by zero
            group['nav_position_in_range'] = (group['monthly_nav_percent'] - group['nav_min_12']) / nav_range_safe
            
            # NAV % consistency (coefficient of variation, with safety check)
            nav_mean_safe = group['nav_mean_12'].clip(lower=0.01)  # Prevent division by zero
            group['nav_cv_12m'] = group['nav_std_12'] / nav_mean_safe
            
            # NAV % acceleration (second derivative)
            group['nav_acceleration'] = group['nav_momentum_1m'].diff()
            
            # High/Low NAV % flags (with NaN handling)
            group['high_nav_flag'] = (
                (group['monthly_nav_percent'] > group['nav_mean_12'] + group['nav_std_12'])
                .fillna(False).astype(int)
            )
            group['low_nav_flag'] = (
                (group['monthly_nav_percent'] < group['nav_mean_12'] - group['nav_std_12'])
                .fillna(False).astype(int)
            )
            
            # NAV % streak analysis (consecutive periods of increase/decrease, per symbol)
            nav_momentum_filled = group['nav_momentum_1m'].fillna(0)
            
            group['nav_increasing_streak'] = (
                (nav_momentum_filled > 0).astype(int)
                .groupby((nav_momentum_filled <= 0).cumsum())
                .cumsum()
            )
            
            group['nav_decreasing_streak'] = (
                (nav_momentum_filled < 0).astype(int)
                .groupby((nav_momentum_filled >= 0).cumsum())
                .cumsum()
            )
            
            return group
        
        # Apply NAV feature creation per symbol to prevent data leakage
        df = df.groupby('symbol', group_keys=False).apply(create_nav_features_per_symbol)
        
        return df
    
    def create_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create interaction features between different variable types
        
        Args:
            df: DataFrame with base features
            
        Returns:
            DataFrame with interaction features
        """
        print("🔗 Creating interaction features...")
        
        # Yield-Growth interactions
        if all(col in df.columns for col in ['dividend_yield', 'dividend_growth_4q']):
            df['yield_growth_interaction'] = df['dividend_yield'] * df['dividend_growth_4q']
        
        # Quality-Yield interactions
        if all(col in df.columns for col in ['dividend_yield', 'roe']):
            df['quality_yield_interaction'] = df['dividend_yield'] * df['roe']
        
        # Size-Yield interactions
        if all(col in df.columns for col in ['dividend_yield', 'market_cap']):
            df['size_yield_interaction'] = df['dividend_yield'] * np.log(df['market_cap'])
        
        # Risk-Yield interactions
        if all(col in df.columns for col in ['dividend_yield', 'debt_to_equity']):
            df['risk_yield_interaction'] = df['dividend_yield'] * df['debt_to_equity']
        
        # Value-Growth interactions
        if all(col in df.columns for col in ['pe_ratio', 'revenue_growth_4q']):
            df['value_growth_interaction'] = df['pe_ratio'] * df['revenue_growth_4q']
        
        # Profitability-Leverage interactions
        if all(col in df.columns for col in ['roe', 'debt_to_equity']):
            df['profitability_leverage_interaction'] = df['roe'] / (1 + df['debt_to_equity'])
        
        # Momentum-Volatility interactions
        if all(col in df.columns for col in ['roc_20', 'volatility_20']):
            df['momentum_volatility_interaction'] = df['roc_20'] / df['volatility_20']
        
        # Payout-Coverage interactions
        if all(col in df.columns for col in ['payout_ratio', 'earnings_coverage']):
            df['payout_coverage_interaction'] = df['payout_ratio'] * df['earnings_coverage']
        
        # Monthly NAV % interaction features (for ETFs and funds)
        
        # NAV-Yield interactions (relationship between NAV % and yield)
        if all(col in df.columns for col in ['monthly_nav_percent', 'dividend_yield']):
            df['nav_yield_interaction'] = df['monthly_nav_percent'] * df['dividend_yield']
            df['nav_yield_ratio'] = df['monthly_nav_percent'] / df['dividend_yield'].clip(lower=0.01)
        
        # NAV-Volatility interactions (NAV stability vs market volatility)
        if all(col in df.columns for col in ['monthly_nav_percent', 'volatility_20']):
            df['nav_volatility_interaction'] = df['monthly_nav_percent'] / df['volatility_20'].clip(lower=0.01)
        
        # NAV-Growth interactions (NAV % vs dividend growth)
        if all(col in df.columns for col in ['monthly_nav_percent', 'dividend_growth_4q']):
            df['nav_growth_interaction'] = df['monthly_nav_percent'] * df['dividend_growth_4q']
        
        # NAV-Payout interactions (NAV % vs payout ratio)
        if all(col in df.columns for col in ['monthly_nav_percent', 'payout_ratio']):
            df['nav_payout_interaction'] = df['monthly_nav_percent'] * df['payout_ratio']
        
        # NAV stability vs dividend sustainability
        if all(col in df.columns for col in ['nav_stability_score', 'dividend_sustainability_score']):
            df['nav_sustainability_interaction'] = df['nav_stability_score'] * df['dividend_sustainability_score']
        
        # NAV momentum vs market momentum
        if all(col in df.columns for col in ['nav_momentum_3m', 'roc_20']):
            df['nav_market_momentum_interaction'] = df['nav_momentum_3m'] * df['roc_20']
        
        return df
    
    def create_market_regime_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create market regime and macroeconomic features
        
        Args:
            df: DataFrame with market data
            
        Returns:
            DataFrame with market regime features
        """
        print("🌍 Creating market regime features...")
        
        # Market volatility regimes
        if 'market_volatility' in df.columns:
            df['low_vol_regime'] = (df['market_volatility'] < df['market_volatility'].quantile(0.33)).astype(int)
            df['high_vol_regime'] = (df['market_volatility'] > df['market_volatility'].quantile(0.67)).astype(int)
        
        # Interest rate environment
        if 'interest_rate_10yr' in df.columns:
            df['low_rate_environment'] = (df['interest_rate_10yr'] < 0.03).astype(int)
            df['high_rate_environment'] = (df['interest_rate_10yr'] > 0.05).astype(int)
            df['rate_trend'] = df['interest_rate_10yr'].rolling(window=4).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) >= 2 else 0
            )
        
        # Market cycle indicators
        if 'sp500_level' in df.columns:
            # Bull/Bear market indicators
            df['sp500_ma_200'] = df['sp500_level'].rolling(window=200).mean()
            df['bull_market'] = (df['sp500_level'] > df['sp500_ma_200']).astype(int)
            
            # Market momentum
            df['market_momentum'] = df['sp500_level'].pct_change(periods=20)
        
        # Economic cycle features
        if 'gdp_growth' in df.columns:
            df['recession_risk'] = (df['gdp_growth'] < 0).astype(int)
            df['economic_acceleration'] = df['gdp_growth'].diff()
        
        # Sector rotation features
        if 'sector' in df.columns:
            # Relative sector performance
            df['sector_momentum'] = df.groupby('sector')['close'].pct_change(periods=20)
        
        return df
    
    def select_important_features(self, df: pd.DataFrame, target_col: str, 
                                method: str = 'mutual_info', k: int = 50) -> List[str]:
        """
        Select most important features for prediction
        
        Args:
            df: DataFrame with features and target
            target_col: Name of target column
            method: Feature selection method ('mutual_info', 'f_test', 'correlation')
            k: Number of features to select
            
        Returns:
            List of selected feature names
        """
        print(f"🎯 Selecting top {k} features using {method}...")
        
        # Prepare data
        y = df[target_col].fillna(df[target_col].median())
        
        # Get numerical features only
        numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if target_col in numerical_cols:
            numerical_cols.remove(target_col)
        
        X = df[numerical_cols].fillna(df[numerical_cols].median())
        
        if method == 'mutual_info':
            selector = SelectKBest(score_func=mutual_info_regression, k=min(k, len(numerical_cols)))
        elif method == 'f_test':
            selector = SelectKBest(score_func=f_regression, k=min(k, len(numerical_cols)))
        elif method == 'correlation':
            # Correlation-based selection
            correlations = X.corrwith(y).abs().sort_values(ascending=False)
            selected_features = correlations.head(k).index.tolist()
            return selected_features
        else:
            raise ValueError(f"Unknown feature selection method: {method}")
        
        # Fit selector
        selector.fit(X, y)
        selected_features = X.columns[selector.get_support()].tolist()
        
        # Store feature importance scores
        feature_scores = selector.scores_
        self.feature_importance[method] = dict(zip(X.columns, feature_scores))
        
        print(f"✅ Selected {len(selected_features)} features")
        return selected_features
    
    def create_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create comprehensive feature set
        
        Args:
            df: Raw financial data
            
        Returns:
            DataFrame with all engineered features
        """
        print("🚀 Creating comprehensive feature set...")
        
        # Technical indicators
        df = self.create_technical_indicators(df)
        
        # Fundamental features
        df = self.create_fundamental_features(df)
        
        # Dividend-specific features
        df = self.create_dividend_specific_features(df)
        
        # Market regime features
        df = self.create_market_regime_features(df)
        
        # Interaction features
        df = self.create_interaction_features(df)
        
        # Store feature metadata
        self.feature_metadata = {
            'timestamp': datetime.now().isoformat(),
            'total_features': len(df.columns),
            'technical_features': len([col for col in df.columns if any(indicator in col.lower() 
                                     for indicator in ['rsi', 'macd', 'sma', 'ema', 'bb_', 'atr'])]),
            'fundamental_features': len([col for col in df.columns if any(metric in col.lower() 
                                       for metric in ['roe', 'roa', 'margin', 'ratio', 'coverage'])]),
            'dividend_features': len([col for col in df.columns if any(div_term in col.lower() 
                                    for div_term in ['yield', 'payout', 'dividend', 'growth'])]),
            'interaction_features': len([col for col in df.columns if 'interaction' in col.lower()]),
        }
        
        print("✅ Comprehensive feature engineering completed!")
        print(f"📊 Total features created: {self.feature_metadata['total_features']}")
        
        return df
    
    def save_feature_engineering(self, save_dir: str = 'models') -> str:
        """Save feature engineering components"""
        os.makedirs(save_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save metadata
        metadata_file = os.path.join(save_dir, f'feature_engineering_metadata_{timestamp}.json')
        with open(metadata_file, 'w') as f:
            json.dump(self.feature_metadata, f, indent=2)
        
        # Save feature importance
        if self.feature_importance:
            importance_file = os.path.join(save_dir, f'feature_importance_{timestamp}.json')
            with open(importance_file, 'w') as f:
                json.dump(self.feature_importance, f, indent=2)
        
        print(f"💾 Saved feature engineering to {save_dir}")
        return timestamp


def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description='Advanced Feature Engineering for Dividend ML')
    parser.add_argument('--input', required=True, help='Input data file (JSON)')
    parser.add_argument('--output', default='.', help='Output directory')
    parser.add_argument('--target', default='dividend_yield', help='Target column for feature selection')
    parser.add_argument('--select-features', type=int, default=50, help='Number of features to select')
    parser.add_argument('--method', default='mutual_info', choices=['mutual_info', 'f_test', 'correlation'],
                       help='Feature selection method')
    
    args = parser.parse_args()
    
    # Load data
    with open(args.input, 'r') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    
    # Initialize feature engineer
    engineer = DividendFeatureEngineer()
    
    # Create all features
    df_features = engineer.create_all_features(df)
    
    # Select important features
    if args.target in df_features.columns:
        selected_features = engineer.select_important_features(
            df_features, args.target, args.method, args.select_features
        )
        
        # Save selected features
        selected_df = df_features[selected_features + [args.target]]
        output_file = os.path.join(args.output, 'selected_features.json')
        selected_df.to_json(output_file, orient='records')
        print(f"💾 Selected features saved to {output_file}")
    
    # Save all features
    all_features_file = os.path.join(args.output, 'all_features.json')
    df_features.to_json(all_features_file, orient='records')
    print(f"💾 All features saved to {all_features_file}")
    
    # Save feature engineering metadata
    engineer.save_feature_engineering(args.output)
    
    print("✅ Feature engineering completed successfully!")


if __name__ == '__main__':
    main()