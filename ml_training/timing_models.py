#!/usr/bin/env python3
"""
Dividend Payment Timing Prediction Models
Implements sophisticated models for predicting dividend announcement and payment dates
"""

import argparse
import json
import os
import sys
import time
import warnings
from datetime import datetime, timedelta, date
from typing import Dict, List, Tuple, Any, Union, Optional

# Suppress warnings
warnings.filterwarnings('ignore')

try:
    import pandas as pd
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.model_selection import train_test_split, GridSearchCV, TimeSeriesSplit
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score, f1_score,
        classification_report, confusion_matrix
    )
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    import joblib
    
    # Statistical models for survival analysis
    try:
        from lifelines import KaplanMeierFitter, CoxPHFitter
        from lifelines.statistics import logrank_test
        LIFELINES_AVAILABLE = True
    except ImportError:
        LIFELINES_AVAILABLE = False
        print("⚠️ Lifelines not available - Survival analysis models disabled")
    
    # XGBoost for enhanced performance
    try:
        import xgboost as xgb
        XGBOOST_AVAILABLE = True
    except ImportError:
        XGBOOST_AVAILABLE = False
        print("⚠️ XGBoost not available - will use Gradient Boosting instead")
    
    # Additional statistical tools
    try:
        from scipy import stats
        from scipy.optimize import minimize
        SCIPY_AVAILABLE = True
    except ImportError:
        SCIPY_AVAILABLE = False
        print("⚠️ SciPy not available - some statistical features disabled")
        
except ImportError as e:
    print(f"Error importing required packages: {e}")
    print("Please ensure packages are installed:")
    print("pip install pandas numpy scikit-learn joblib")
    print("Optional: pip install lifelines xgboost scipy")
    sys.exit(1)


class DividendTimingPredictor:
    """
    Advanced predictor for dividend announcement and payment timing
    Combines classification, survival analysis, and time-to-event modeling
    """
    
    def __init__(self, random_state: int = 42):
        """Initialize the dividend timing predictor"""
        self.random_state = random_state
        np.random.seed(random_state)
        
        # Model ensemble for different prediction tasks
        self.models = {
            'announcement_classifier': {},
            'payment_classifier': {},
            'survival_model': {},
            'days_until_regressor': {}
        }
        
        # Feature engineering components
        self.preprocessors = {}
        self.label_encoders = {}
        
        # Historical pattern storage
        self.company_patterns = {}
        self.sector_patterns = {}
        
        # Performance tracking
        self.training_metrics = {}
        self.validation_scores = {}
        
        # Timing feature columns
        self.timing_features = [
            # Historical timing patterns
            'avg_days_announce_to_pay', 'std_days_announce_to_pay',
            'avg_days_announce_to_ex', 'std_days_announce_to_ex',
            'typical_announcement_quarter', 'announcement_consistency_score',
            
            # Calendar features
            'quarter', 'month', 'day_of_year', 'week_of_year',
            'days_since_last_announcement', 'days_since_last_payment',
            'days_until_quarter_end', 'days_until_year_end',
            
            # Earnings calendar relationship
            'days_from_earnings_announcement', 'earnings_announcement_proximity',
            'typical_earnings_to_dividend_lag', 'earnings_dividend_correlation',
            
            # Board meeting patterns
            'board_meeting_month', 'board_meeting_frequency',
            'days_from_last_board_meeting', 'board_meeting_predictability',
            
            # Market and company factors
            'market_volatility', 'sector_announcement_clustering',
            'company_announcement_tradition', 'regulatory_requirements',
            'company_size_category', 'dividend_policy_stability',
            
            # Seasonal factors
            'holiday_proximity', 'quarter_end_effect', 'month_end_effect',
            'earnings_season_effect', 'tax_deadline_proximity',
            
            # Company lifecycle factors
            'years_paying_dividends', 'dividend_policy_maturity',
            'announcement_pattern_stability', 'management_consistency'
        ]
        
        self.categorical_features = [
            'sector', 'industry', 'exchange', 'company_size_category',
            'dividend_frequency', 'announcement_tradition_category',
            'board_meeting_pattern', 'earnings_announcement_pattern'
        ]
    
    def prepare_timing_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare data for timing prediction models
        
        Args:
            data: Raw dividend and announcement data
            
        Returns:
            Prepared DataFrame with timing features
        """
        print("🔧 Preparing timing prediction data...")
        
        df = data.copy()
        
        # Ensure date columns are datetime
        date_columns = [
            'announcement_date', 'ex_dividend_date', 'payment_date',
            'earnings_announcement_date', 'board_meeting_date'
        ]
        
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Sort by symbol and date
        if 'symbol' in df.columns and 'announcement_date' in df.columns:
            df = df.sort_values(['symbol', 'announcement_date'])
        
        # Create timing features
        df = self._create_timing_features(df)
        
        # Create target variables
        df = self._create_timing_targets(df)
        
        # Fill missing values
        df = self._fill_timing_missing_values(df)
        
        return df
    
    def _create_timing_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create comprehensive timing features"""
        
        # Basic calendar features
        if 'announcement_date' in df.columns:
            df['quarter'] = df['announcement_date'].dt.quarter
            df['month'] = df['announcement_date'].dt.month
            df['day_of_year'] = df['announcement_date'].dt.dayofyear
            df['week_of_year'] = df['announcement_date'].dt.isocalendar().week
            df['weekday'] = df['announcement_date'].dt.weekday
        
        # Historical timing patterns by company
        df = self._create_company_timing_patterns(df)
        
        # Earnings calendar relationship
        df = self._create_earnings_timing_features(df)
        
        # Board meeting patterns
        df = self._create_board_meeting_features(df)
        
        # Market and seasonal factors
        df = self._create_market_timing_features(df)
        
        # Regulatory and industry patterns
        df = self._create_regulatory_timing_features(df)
        
        return df
    
    def _create_company_timing_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create company-specific timing patterns"""
        
        if 'symbol' not in df.columns:
            return df
        
        # Calculate historical patterns for each company
        for symbol in df['symbol'].unique():
            symbol_data = df[df['symbol'] == symbol].copy()
            
            if len(symbol_data) < 2:
                continue
            
            # Days between announcement and payment
            if all(col in symbol_data.columns for col in ['announcement_date', 'payment_date']):
                symbol_data['days_announce_to_pay'] = (
                    symbol_data['payment_date'] - symbol_data['announcement_date']
                ).dt.days
                
                # Rolling averages and stability metrics
                symbol_data['avg_days_announce_to_pay'] = (
                    symbol_data['days_announce_to_pay'].rolling(4, min_periods=1).mean()
                )
                symbol_data['std_days_announce_to_pay'] = (
                    symbol_data['days_announce_to_pay'].rolling(4, min_periods=1).std().fillna(0)
                )
            
            # Days between announcement and ex-dividend
            if all(col in symbol_data.columns for col in ['announcement_date', 'ex_dividend_date']):
                symbol_data['days_announce_to_ex'] = (
                    symbol_data['ex_dividend_date'] - symbol_data['announcement_date']
                ).dt.days
                
                symbol_data['avg_days_announce_to_ex'] = (
                    symbol_data['days_announce_to_ex'].rolling(4, min_periods=1).mean()
                )
                symbol_data['std_days_announce_to_ex'] = (
                    symbol_data['days_announce_to_ex'].rolling(4, min_periods=1).std().fillna(0)
                )
            
            # Days since last announcement/payment
            if 'announcement_date' in symbol_data.columns:
                symbol_data['days_since_last_announcement'] = (
                    symbol_data['announcement_date'].diff().dt.days.fillna(90)
                )
            
            if 'payment_date' in symbol_data.columns:
                symbol_data['days_since_last_payment'] = (
                    symbol_data['payment_date'].diff().dt.days.fillna(90)
                )
            
            # Announcement consistency
            if 'quarter' in symbol_data.columns:
                symbol_data['typical_announcement_quarter'] = (
                    symbol_data.groupby('quarter')['quarter'].transform('count') / len(symbol_data)
                )
                
                # Consistency score based on quarterly patterns
                quarter_counts = symbol_data['quarter'].value_counts()
                max_quarter_freq = quarter_counts.max() / len(symbol_data) if len(symbol_data) > 0 else 0
                symbol_data['announcement_consistency_score'] = max_quarter_freq
            
            # Update main dataframe
            df.loc[df['symbol'] == symbol, symbol_data.columns] = symbol_data
        
        return df
    
    def _create_earnings_timing_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create earnings announcement timing features"""
        
        if 'earnings_announcement_date' not in df.columns or 'announcement_date' not in df.columns:
            # Create synthetic earnings timing if not available
            df['days_from_earnings_announcement'] = np.random.normal(14, 7, len(df))
            df['earnings_announcement_proximity'] = np.random.uniform(0.3, 0.9, len(df))
            df['typical_earnings_to_dividend_lag'] = 14
            df['earnings_dividend_correlation'] = 0.7
            return df
        
        # Days from earnings announcement to dividend announcement
        df['days_from_earnings_announcement'] = (
            df['announcement_date'] - df['earnings_announcement_date']
        ).dt.days
        
        # Proximity score (0-1, higher means closer timing)
        df['earnings_announcement_proximity'] = np.exp(-np.abs(df['days_from_earnings_announcement']) / 30)
        
        # Historical patterns by company
        if 'symbol' in df.columns:
            df['typical_earnings_to_dividend_lag'] = df.groupby('symbol')[
                'days_from_earnings_announcement'
            ].transform('median').fillna(14)
            
            # Correlation between earnings and dividend announcements
            earnings_correlation = df.groupby('symbol').apply(
                lambda x: x['days_from_earnings_announcement'].corr(
                    x['days_from_earnings_announcement'].shift(1)
                ) if len(x) > 2 else 0.5
            )
            df['earnings_dividend_correlation'] = df['symbol'].map(earnings_correlation).fillna(0.5)
        
        return df
    
    def _create_board_meeting_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create board meeting timing features"""
        
        if 'board_meeting_date' not in df.columns:
            # Create synthetic board meeting patterns
            df['board_meeting_month'] = np.random.choice([1, 4, 7, 10], len(df))  # Quarterly
            df['board_meeting_frequency'] = 4  # Quarterly meetings
            df['days_from_last_board_meeting'] = np.random.normal(90, 15, len(df))
            df['board_meeting_predictability'] = 0.8
            return df
        
        # Board meeting calendar features
        df['board_meeting_month'] = df['board_meeting_date'].dt.month
        df['board_meeting_quarter'] = df['board_meeting_date'].dt.quarter
        
        # Days from board meeting to dividend announcement
        if 'announcement_date' in df.columns:
            df['days_board_to_announcement'] = (
                df['announcement_date'] - df['board_meeting_date']
            ).dt.days
        
        # Board meeting frequency and predictability by company
        if 'symbol' in df.columns:
            board_patterns = df.groupby('symbol').agg({
                'board_meeting_date': lambda x: len(x.dropna()),
                'days_board_to_announcement': ['mean', 'std']
            }).fillna(0)
            
            # Flatten column names
            board_patterns.columns = ['_'.join(col).strip() for col in board_patterns.columns]
            
            # Meeting frequency (meetings per year)
            df['board_meeting_frequency'] = df['symbol'].map(
                board_patterns['board_meeting_date_<lambda>'] / 
                (df.groupby('symbol')['announcement_date'].transform('nunique') / 4)
            ).fillna(4)
            
            # Meeting predictability (inverse of std)
            df['board_meeting_predictability'] = 1 / (
                1 + df['symbol'].map(board_patterns['days_board_to_announcement_std']).fillna(5)
            )
        
        return df
    
    def _create_market_timing_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create market and seasonal timing features"""
        
        # Quarter-end and year-end effects
        if 'announcement_date' in df.columns:
            df['days_until_quarter_end'] = df['announcement_date'].apply(
                lambda x: (pd.Timestamp(x.year, ((x.quarter) * 3), 1) + 
                          pd.DateOffset(months=3) - pd.DateOffset(days=1) - x).days
            )
            df['days_until_year_end'] = df['announcement_date'].apply(
                lambda x: (pd.Timestamp(x.year, 12, 31) - x).days
            )
            
            # Quarter-end effect (higher announcement probability near quarter end)
            df['quarter_end_effect'] = np.exp(-df['days_until_quarter_end'] / 15)
            
            # Month-end effect
            df['days_until_month_end'] = df['announcement_date'].apply(
                lambda x: (x + pd.offsets.MonthEnd(0) - x).days
            )
            df['month_end_effect'] = np.exp(-df['days_until_month_end'] / 7)
        
        # Holiday proximity effects
        df = self._create_holiday_effects(df)
        
        # Market volatility effects
        if 'market_volatility' not in df.columns:
            df['market_volatility'] = 0.15 + 0.05 * np.random.randn(len(df))
        
        # Sector clustering effects (companies in same sector tend to announce together)
        if 'sector' in df.columns:
            sector_announcement_density = df.groupby(['sector', 'quarter']).size() / df.groupby('quarter').size()
            df['sector_announcement_clustering'] = df.apply(
                lambda row: sector_announcement_density.get((row['sector'], row.get('quarter', 2)), 0.25),
                axis=1
            )
        else:
            df['sector_announcement_clustering'] = 0.25
        
        return df
    
    def _create_holiday_effects(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create holiday proximity effects"""
        
        if 'announcement_date' not in df.columns:
            df['holiday_proximity'] = 0.5
            return df
        
        # Major US holidays affecting dividend announcements
        holidays = [
            (1, 1),   # New Year's Day
            (1, 15),  # MLK Day (approximate)
            (2, 15),  # Presidents' Day (approximate)
            (5, 30),  # Memorial Day (approximate)
            (7, 4),   # Independence Day
            (9, 5),   # Labor Day (approximate)
            (10, 10), # Columbus Day (approximate)
            (11, 11), # Veterans Day
            (11, 25), # Thanksgiving (approximate)
            (12, 25)  # Christmas
        ]
        
        def calculate_holiday_proximity(date_val):
            if pd.isna(date_val):
                return 0.5
            
            min_distance = float('inf')
            for month, day in holidays:
                holiday_date = pd.Timestamp(date_val.year, month, day)
                distance = abs((date_val - holiday_date).days)
                min_distance = min(min_distance, distance)
            
            # Proximity score (higher when further from holidays)
            return 1 / (1 + np.exp(-(min_distance - 7) / 3))
        
        df['holiday_proximity'] = df['announcement_date'].apply(calculate_holiday_proximity)
        
        return df
    
    def _create_regulatory_timing_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create regulatory and compliance timing features"""
        
        # Tax deadline proximity (April 15)
        if 'announcement_date' in df.columns:
            df['tax_deadline_proximity'] = df['announcement_date'].apply(
                lambda x: abs((pd.Timestamp(x.year, 4, 15) - x).days) if not pd.isna(x) else 180
            )
            df['tax_deadline_effect'] = np.exp(-df['tax_deadline_proximity'] / 30)
        else:
            df['tax_deadline_proximity'] = 180
            df['tax_deadline_effect'] = 0.5
        
        # Earnings season effects
        earnings_seasons = [
            (1, 15, 2, 15),  # Q4 earnings (Jan 15 - Feb 15)
            (4, 15, 5, 15),  # Q1 earnings (Apr 15 - May 15)
            (7, 15, 8, 15),  # Q2 earnings (Jul 15 - Aug 15)
            (10, 15, 11, 15) # Q3 earnings (Oct 15 - Nov 15)
        ]
        
        if 'announcement_date' in df.columns:
            def earnings_season_effect(date_val):
                if pd.isna(date_val):
                    return 0.5
                
                for start_month, start_day, end_month, end_day in earnings_seasons:
                    season_start = pd.Timestamp(date_val.year, start_month, start_day)
                    season_end = pd.Timestamp(date_val.year, end_month, end_day)
                    
                    if season_start <= date_val <= season_end:
                        return 0.8  # High effect during earnings season
                
                return 0.3  # Lower effect outside earnings season
            
            df['earnings_season_effect'] = df['announcement_date'].apply(earnings_season_effect)
        else:
            df['earnings_season_effect'] = 0.5
        
        # Company announcement tradition
        if 'symbol' in df.columns and 'announcement_date' in df.columns:
            company_tradition = df.groupby('symbol')['month'].apply(
                lambda x: x.value_counts().max() / len(x) if len(x) > 0 else 0.25
            )
            df['company_announcement_tradition'] = df['symbol'].map(company_tradition).fillna(0.25)
        else:
            df['company_announcement_tradition'] = 0.25
        
        return df
    
    def _create_timing_targets(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create target variables for timing prediction"""
        
        # Next announcement date prediction (classification by week)
        if 'announcement_date' in df.columns:
            df['announcement_week'] = df['announcement_date'].dt.isocalendar().week
            df['announcement_month'] = df['announcement_date'].dt.month
            
            # Days until next announcement (for regression)
            df = df.sort_values(['symbol', 'announcement_date'])
            df['days_until_next_announcement'] = df.groupby('symbol')['announcement_date'].diff().dt.days.shift(-1)
        
        # Payment date prediction
        if all(col in df.columns for col in ['announcement_date', 'payment_date']):
            df['days_announce_to_payment'] = (df['payment_date'] - df['announcement_date']).dt.days
            
            # Classify payment timing (bins: 0-14, 15-30, 31-45, 46+ days)
            df['payment_timing_category'] = pd.cut(
                df['days_announce_to_payment'],
                bins=[0, 14, 30, 45, float('inf')],
                labels=['immediate', 'short', 'medium', 'long']
            )
        
        # Ex-dividend date prediction
        if all(col in df.columns for col in ['announcement_date', 'ex_dividend_date']):
            df['days_announce_to_ex'] = (df['ex_dividend_date'] - df['announcement_date']).dt.days
            
            # Ex-dividend timing (usually 2-4 weeks)
            df['ex_dividend_timing_category'] = pd.cut(
                df['days_announce_to_ex'],
                bins=[0, 7, 21, 35, float('inf')],
                labels=['very_short', 'short', 'normal', 'long']
            )
        
        return df
    
    def _fill_timing_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fill missing values for timing features"""
        
        # Fill timing patterns with reasonable defaults
        timing_defaults = {
            'avg_days_announce_to_pay': 21,
            'std_days_announce_to_pay': 7,
            'avg_days_announce_to_ex': 14,
            'std_days_announce_to_ex': 5,
            'days_since_last_announcement': 90,
            'days_since_last_payment': 90,
            'typical_announcement_quarter': 0.25,
            'announcement_consistency_score': 0.5,
            'days_from_earnings_announcement': 14,
            'earnings_announcement_proximity': 0.6,
            'typical_earnings_to_dividend_lag': 14,
            'earnings_dividend_correlation': 0.7,
            'board_meeting_frequency': 4,
            'board_meeting_predictability': 0.8,
            'days_until_quarter_end': 45,
            'days_until_year_end': 180,
            'quarter_end_effect': 0.3,
            'month_end_effect': 0.3,
            'holiday_proximity': 0.7,
            'market_volatility': 0.15,
            'sector_announcement_clustering': 0.25,
            'company_announcement_tradition': 0.25,
            'tax_deadline_proximity': 180,
            'tax_deadline_effect': 0.5,
            'earnings_season_effect': 0.5
        }
        
        for col, default_val in timing_defaults.items():
            if col in df.columns:
                df[col] = df[col].fillna(default_val)
        
        # Fill categorical features
        categorical_defaults = {
            'sector': 'Unknown',
            'industry': 'Unknown',
            'exchange': 'NYSE',
            'company_size_category': 'Large Cap',
            'dividend_frequency': 'Quarterly',
            'announcement_tradition_category': 'Regular',
            'board_meeting_pattern': 'Quarterly',
            'earnings_announcement_pattern': 'Regular'
        }
        
        for col, default_val in categorical_defaults.items():
            if col in df.columns:
                df[col] = df[col].fillna(default_val)
        
        return df
    
    def train_timing_models(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Train ensemble of timing prediction models
        
        Args:
            data: Historical dividend timing data
            
        Returns:
            Training results and metrics
        """
        print("🏋️ Training Dividend Timing Prediction Models...")
        
        # Prepare timing data
        df = self.prepare_timing_data(data)
        
        if len(df) < 20:  # Need minimum data
            return {
                'success': False,
                'error': f'Insufficient data for training: {len(df)} records (need >= 20)'
            }
        
        # Extract features
        available_numerical = [col for col in self.timing_features if col in df.columns]
        available_categorical = [col for col in self.categorical_features if col in df.columns]
        
        print(f"📊 Training with {len(available_numerical)} numerical and {len(available_categorical)} categorical features")
        
        # Prepare features
        X = df[available_numerical + available_categorical]
        
        # Train different prediction models
        results = {}
        
        # 1. Announcement timing classifier
        if 'announcement_month' in df.columns:
            results['announcement_classifier'] = self._train_announcement_classifier(X, df['announcement_month'])
        
        # 2. Payment timing classifier
        if 'payment_timing_category' in df.columns:
            results['payment_classifier'] = self._train_payment_classifier(X, df['payment_timing_category'])
        
        # 3. Days until prediction regressor
        if 'days_until_next_announcement' in df.columns:
            results['days_until_regressor'] = self._train_days_until_regressor(X, df['days_until_next_announcement'])
        
        # 4. Survival analysis model
        if LIFELINES_AVAILABLE and 'days_until_next_announcement' in df.columns:
            results['survival_model'] = self._train_survival_model(df)
        
        # Store training metadata
        self.training_metrics = {
            'timestamp': datetime.now().isoformat(),
            'training_size': len(df),
            'feature_count': len(available_numerical + available_categorical),
            'models_trained': [name for name, result in results.items() if result.get('success', False)],
            'individual_results': results
        }
        
        successful_models = [name for name, result in results.items() if result.get('success', False)]
        print(f"✅ Training completed. Successful models: {successful_models}")
        
        return self.training_metrics
    
    def _train_announcement_classifier(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """Train classifier for announcement month prediction"""
        
        try:
            print("📅 Training announcement timing classifier...")
            
            # Remove missing targets
            mask = ~y.isna()
            X_clean = X[mask]
            y_clean = y[mask]
            
            if len(y_clean) < 10:
                return {'success': False, 'error': 'Insufficient data for announcement classifier'}
            
            # Create preprocessor
            if any(X_clean.dtypes == 'object'):
                from sklearn.preprocessing import OneHotEncoder
                categorical_cols = X_clean.select_dtypes(include=['object']).columns
                numerical_cols = X_clean.select_dtypes(exclude=['object']).columns
                
                preprocessor = ColumnTransformer([
                    ('num', StandardScaler(), numerical_cols),
                    ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_cols)
                ])
            else:
                preprocessor = StandardScaler()
            
            # Train model
            if XGBOOST_AVAILABLE:
                classifier = xgb.XGBClassifier(
                    n_estimators=100,
                    max_depth=6,
                    random_state=self.random_state
                )
            else:
                classifier = RandomForestClassifier(
                    n_estimators=100,
                    max_depth=10,
                    random_state=self.random_state
                )
            
            # Create pipeline
            pipeline = Pipeline([
                ('preprocessor', preprocessor),
                ('classifier', classifier)
            ])
            
            # Train-test split
            X_train, X_test, y_train, y_test = train_test_split(
                X_clean, y_clean, test_size=0.2, random_state=self.random_state, stratify=y_clean
            )
            
            # Fit model
            pipeline.fit(X_train, y_train)
            
            # Evaluate
            y_pred = pipeline.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Store model
            self.models['announcement_classifier'] = {
                'model': pipeline,
                'accuracy': accuracy,
                'classes': classifier.classes_ if hasattr(classifier, 'classes_') else None
            }
            
            return {
                'success': True,
                'accuracy': accuracy,
                'test_size': len(X_test)
            }
            
        except Exception as e:
            print(f"❌ Announcement classifier training failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _train_payment_classifier(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """Train classifier for payment timing prediction"""
        
        try:
            print("💰 Training payment timing classifier...")
            
            # Remove missing targets
            mask = ~y.isna()
            X_clean = X[mask]
            y_clean = y[mask]
            
            if len(y_clean) < 10:
                return {'success': False, 'error': 'Insufficient data for payment classifier'}
            
            # Create preprocessor
            if any(X_clean.dtypes == 'object'):
                from sklearn.preprocessing import OneHotEncoder
                categorical_cols = X_clean.select_dtypes(include=['object']).columns
                numerical_cols = X_clean.select_dtypes(exclude=['object']).columns
                
                preprocessor = ColumnTransformer([
                    ('num', StandardScaler(), numerical_cols),
                    ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_cols)
                ])
            else:
                preprocessor = StandardScaler()
            
            # Train model
            classifier = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=6,
                random_state=self.random_state
            )
            
            # Create pipeline
            pipeline = Pipeline([
                ('preprocessor', preprocessor),
                ('classifier', classifier)
            ])
            
            # Train-test split
            X_train, X_test, y_train, y_test = train_test_split(
                X_clean, y_clean, test_size=0.2, random_state=self.random_state, stratify=y_clean
            )
            
            # Fit model
            pipeline.fit(X_train, y_train)
            
            # Evaluate
            y_pred = pipeline.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred, average='weighted')
            
            # Store model
            self.models['payment_classifier'] = {
                'model': pipeline,
                'accuracy': accuracy,
                'f1_score': f1
            }
            
            return {
                'success': True,
                'accuracy': accuracy,
                'f1_score': f1,
                'test_size': len(X_test)
            }
            
        except Exception as e:
            print(f"❌ Payment classifier training failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _train_days_until_regressor(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """Train regressor for days until next announcement"""
        
        try:
            print("⏱️ Training days-until regressor...")
            
            # Remove missing targets
            mask = ~y.isna() & (y > 0) & (y < 365)  # Reasonable range
            X_clean = X[mask]
            y_clean = y[mask]
            
            if len(y_clean) < 10:
                return {'success': False, 'error': 'Insufficient data for days-until regressor'}
            
            # Create preprocessor
            if any(X_clean.dtypes == 'object'):
                from sklearn.preprocessing import OneHotEncoder
                categorical_cols = X_clean.select_dtypes(include=['object']).columns
                numerical_cols = X_clean.select_dtypes(exclude=['object']).columns
                
                preprocessor = ColumnTransformer([
                    ('num', StandardScaler(), numerical_cols),
                    ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_cols)
                ])
            else:
                preprocessor = StandardScaler()
            
            # Train model
            from sklearn.ensemble import RandomForestRegressor
            regressor = RandomForestRegressor(
                n_estimators=100,
                max_depth=15,
                random_state=self.random_state
            )
            
            # Create pipeline
            pipeline = Pipeline([
                ('preprocessor', preprocessor),
                ('regressor', regressor)
            ])
            
            # Train-test split
            X_train, X_test, y_train, y_test = train_test_split(
                X_clean, y_clean, test_size=0.2, random_state=self.random_state
            )
            
            # Fit model
            pipeline.fit(X_train, y_train)
            
            # Evaluate
            from sklearn.metrics import mean_absolute_error, r2_score
            y_pred = pipeline.predict(X_test)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            # Store model
            self.models['days_until_regressor'] = {
                'model': pipeline,
                'mae': mae,
                'r2_score': r2
            }
            
            return {
                'success': True,
                'mae': mae,
                'r2_score': r2,
                'test_size': len(X_test)
            }
            
        except Exception as e:
            print(f"❌ Days-until regressor training failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _train_survival_model(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Train survival analysis model for time-to-event prediction"""
        
        if not LIFELINES_AVAILABLE:
            return {'success': False, 'error': 'Lifelines not available'}
        
        try:
            print("📊 Training survival analysis model...")
            
            # Prepare survival data
            if 'days_until_next_announcement' not in df.columns:
                return {'success': False, 'error': 'No duration data for survival analysis'}
            
            survival_data = df[['days_until_next_announcement']].copy()
            survival_data['duration'] = survival_data['days_until_next_announcement'].fillna(365)
            survival_data['event'] = ~df['days_until_next_announcement'].isna()
            
            # Remove extreme outliers
            survival_data = survival_data[
                (survival_data['duration'] > 0) & (survival_data['duration'] < 365)
            ]
            
            if len(survival_data) < 10:
                return {'success': False, 'error': 'Insufficient data for survival analysis'}
            
            # Kaplan-Meier estimator
            kmf = KaplanMeierFitter()
            kmf.fit(survival_data['duration'], survival_data['event'])
            
            # Cox Proportional Hazards model (if we have covariates)
            numerical_features = [col for col in self.timing_features if col in df.columns][:5]  # Limit features
            
            if numerical_features:
                cox_data = df[numerical_features + ['days_until_next_announcement']].copy()
                cox_data['duration'] = cox_data['days_until_next_announcement'].fillna(365)
                cox_data['event'] = ~df['days_until_next_announcement'].isna()
                cox_data = cox_data.dropna()
                
                if len(cox_data) >= 10:
                    cph = CoxPHFitter()
                    cph.fit(cox_data, duration_col='duration', event_col='event')
                    
                    self.models['survival_model'] = {
                        'kmf': kmf,
                        'cph': cph,
                        'features': numerical_features
                    }
                else:
                    self.models['survival_model'] = {
                        'kmf': kmf,
                        'cph': None,
                        'features': []
                    }
            else:
                self.models['survival_model'] = {
                    'kmf': kmf,
                    'cph': None,
                    'features': []
                }
            
            return {
                'success': True,
                'survival_data_size': len(survival_data),
                'has_cox_model': self.models['survival_model']['cph'] is not None
            }
            
        except Exception as e:
            print(f"❌ Survival model training failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def predict_timing(self, data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """
        Predict dividend timing for a specific symbol
        
        Args:
            data: Feature data for prediction
            symbol: Stock symbol to predict
            
        Returns:
            Timing predictions with confidence intervals
        """
        print(f"🔮 Predicting dividend timing for {symbol}...")
        
        if not any(self.models.values()):
            raise ValueError("Models not trained. Please train the timing models first.")
        
        # Prepare data
        df = self.prepare_timing_data(data)
        
        # Filter for symbol
        if 'symbol' in df.columns:
            symbol_data = df[df['symbol'] == symbol]
        else:
            symbol_data = df
        
        if len(symbol_data) == 0:
            return {
                'success': False,
                'error': f'No data available for symbol {symbol}'
            }
        
        # Use the latest record for prediction
        latest_record = symbol_data.iloc[-1:].copy()
        
        # Extract features
        available_numerical = [col for col in self.timing_features if col in latest_record.columns]
        available_categorical = [col for col in self.categorical_features if col in latest_record.columns]
        
        X = latest_record[available_numerical + available_categorical]
        
        # Make predictions
        predictions = {}
        
        # Announcement month prediction
        if 'announcement_classifier' in self.models and self.models['announcement_classifier']:
            try:
                model = self.models['announcement_classifier']['model']
                announcement_month = model.predict(X)[0]
                announcement_proba = model.predict_proba(X)[0]
                
                predictions['announcement_month'] = {
                    'predicted_month': int(announcement_month),
                    'confidence': float(announcement_proba.max()),
                    'probability_distribution': {
                        f'month_{i+1}': float(prob) for i, prob in enumerate(announcement_proba)
                    }
                }
            except Exception as e:
                print(f"⚠️ Announcement prediction failed: {e}")
        
        # Payment timing prediction
        if 'payment_classifier' in self.models and self.models['payment_classifier']:
            try:
                model = self.models['payment_classifier']['model']
                payment_category = model.predict(X)[0]
                payment_proba = model.predict_proba(X)[0]
                
                predictions['payment_timing'] = {
                    'predicted_category': payment_category,
                    'confidence': float(payment_proba.max()),
                    'estimated_days': self._category_to_days(payment_category)
                }
            except Exception as e:
                print(f"⚠️ Payment timing prediction failed: {e}")
        
        # Days until next announcement
        if 'days_until_regressor' in self.models and self.models['days_until_regressor']:
            try:
                model = self.models['days_until_regressor']['model']
                days_until = model.predict(X)[0]
                
                # Calculate predicted announcement date
                last_date = latest_record['announcement_date'].iloc[0] if 'announcement_date' in latest_record.columns else datetime.now()
                predicted_date = last_date + timedelta(days=int(days_until))
                
                predictions['next_announcement'] = {
                    'days_until': int(days_until),
                    'predicted_date': predicted_date.isoformat(),
                    'confidence_range': [int(days_until - 7), int(days_until + 7)]
                }
            except Exception as e:
                print(f"⚠️ Days-until prediction failed: {e}")
        
        # Generate comprehensive timing forecast
        timing_forecast = self._generate_timing_forecast(symbol, latest_record, predictions)
        
        return {
            'success': True,
            'symbol': symbol,
            'predictions': predictions,
            'timing_forecast': timing_forecast,
            'timestamp': datetime.now().isoformat()
        }
    
    def _category_to_days(self, category: str) -> int:
        """Convert payment timing category to estimated days"""
        category_mapping = {
            'immediate': 7,
            'short': 21,
            'medium': 35,
            'long': 50
        }
        return category_mapping.get(category, 21)
    
    def _generate_timing_forecast(self, symbol: str, latest_record: pd.DataFrame, 
                                 predictions: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive timing forecast"""
        
        forecast = {
            'symbol': symbol,
            'analysis_date': datetime.now().isoformat(),
            'forecast_quarter': (datetime.now().month - 1) // 3 + 1,
            'forecast_year': datetime.now().year
        }
        
        # Announcement timing forecast
        if 'announcement_month' in predictions:
            month_pred = predictions['announcement_month']['predicted_month']
            year = datetime.now().year if month_pred >= datetime.now().month else datetime.now().year + 1
            
            forecast['announcement_forecast'] = {
                'predicted_month': month_pred,
                'predicted_quarter': f"Q{(month_pred - 1) // 3 + 1}",
                'estimated_date_range': {
                    'start': datetime(year, month_pred, 1).isoformat(),
                    'end': datetime(year, month_pred, 28).isoformat()
                },
                'confidence': predictions['announcement_month']['confidence']
            }
        
        # Payment timing forecast
        if 'payment_timing' in predictions and 'announcement_forecast' in forecast:
            payment_days = predictions['payment_timing']['estimated_days']
            announcement_date = datetime.fromisoformat(forecast['announcement_forecast']['estimated_date_range']['start'])
            payment_date = announcement_date + timedelta(days=payment_days)
            
            forecast['payment_forecast'] = {
                'estimated_payment_date': payment_date.isoformat(),
                'days_after_announcement': payment_days,
                'payment_category': predictions['payment_timing']['predicted_category'],
                'confidence': predictions['payment_timing']['confidence']
            }
        
        # Ex-dividend date forecast (typically 2-3 weeks before payment)
        if 'payment_forecast' in forecast:
            payment_date = datetime.fromisoformat(forecast['payment_forecast']['estimated_payment_date'])
            ex_dividend_date = payment_date - timedelta(days=14)  # Typical 2-week lead
            
            forecast['ex_dividend_forecast'] = {
                'estimated_ex_dividend_date': ex_dividend_date.isoformat(),
                'days_before_payment': 14,
                'confidence': 0.8  # Generally predictable pattern
            }
        
        # Risk assessment
        forecast['risk_assessment'] = self._assess_timing_risks(latest_record, predictions)
        
        return forecast
    
    def _assess_timing_risks(self, latest_record: pd.DataFrame, predictions: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risks to timing predictions"""
        
        risks = {
            'overall_risk': 'low',
            'risk_factors': [],
            'confidence_adjustments': []
        }
        
        # Check announcement consistency
        consistency_score = latest_record.get('announcement_consistency_score', [0.5]).iloc[0]
        if consistency_score < 0.3:
            risks['risk_factors'].append('Low historical announcement consistency')
            risks['overall_risk'] = 'medium'
        
        # Check market volatility
        market_volatility = latest_record.get('market_volatility', [0.15]).iloc[0]
        if market_volatility > 0.25:
            risks['risk_factors'].append('High market volatility may delay announcements')
            risks['confidence_adjustments'].append('Reduce confidence by 10%')
        
        # Check holiday proximity
        holiday_proximity = latest_record.get('holiday_proximity', [0.7]).iloc[0]
        if holiday_proximity < 0.3:
            risks['risk_factors'].append('Proximity to holidays may affect timing')
            risks['overall_risk'] = 'medium'
        
        # Check earnings correlation
        earnings_correlation = latest_record.get('earnings_dividend_correlation', [0.7]).iloc[0]
        if earnings_correlation < 0.4:
            risks['risk_factors'].append('Weak earnings-dividend timing correlation')
        
        if len(risks['risk_factors']) >= 3:
            risks['overall_risk'] = 'high'
        elif len(risks['risk_factors']) >= 2:
            risks['overall_risk'] = 'medium'
        
        return risks
    
    def save_models(self, model_dir: str = 'models') -> str:
        """Save trained models to disk"""
        os.makedirs(model_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save models
        for model_type, model_info in self.models.items():
            if model_info:  # Only save non-empty models
                filename = f'timing_{model_type}_{timestamp}.joblib'
                filepath = os.path.join(model_dir, filename)
                joblib.dump(model_info, filepath)
                print(f"💾 Saved {model_type} model to {filepath}")
        
        # Save metadata
        metadata_file = os.path.join(model_dir, f'timing_models_metadata_{timestamp}.json')
        metadata = {
            'training_metrics': self.training_metrics,
            'timestamp': timestamp,
            'model_files': {
                model_type: f'timing_{model_type}_{timestamp}.joblib'
                for model_type in self.models.keys() if self.models[model_type]
            }
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"📋 Saved timing models metadata to {metadata_file}")
        return timestamp
    
    def load_models(self, model_dir: str, timestamp: str) -> bool:
        """Load trained models from disk"""
        try:
            # Load metadata
            metadata_file = os.path.join(model_dir, f'timing_models_metadata_{timestamp}.json')
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            self.training_metrics = metadata['training_metrics']
            
            # Load individual models
            for model_type, filename in metadata['model_files'].items():
                filepath = os.path.join(model_dir, filename)
                self.models[model_type] = joblib.load(filepath)
                print(f"📂 Loaded {model_type} model from {filepath}")
            
            print(f"✅ Successfully loaded timing models from {timestamp}")
            return True
        except Exception as e:
            print(f"❌ Failed to load models: {e}")
            return False


def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description='Dividend Timing Prediction Models')
    parser.add_argument('--mode', choices=['train', 'predict'], required=True,
                      help='Mode: train or predict')
    parser.add_argument('--input', required=True,
                      help='Input data file (JSON)')
    parser.add_argument('--symbol', 
                      help='Stock symbol to predict (required for predict mode)')
    parser.add_argument('--output', default='.',
                      help='Output directory')
    parser.add_argument('--model-dir', default='models',
                      help='Model directory')
    parser.add_argument('--load-timestamp', 
                      help='Timestamp of models to load for prediction')
    
    args = parser.parse_args()
    
    # Load input data
    with open(args.input, 'r') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    
    # Initialize predictor
    predictor = DividendTimingPredictor()
    
    if args.mode == 'train':
        # Train models
        results = predictor.train_timing_models(df)
        
        # Save models
        timestamp = predictor.save_models(args.model_dir)
        
        # Save results
        output_file = os.path.join(args.output, 'timing_prediction_results.json')
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"✅ Training completed. Results saved to {output_file}")
        
    elif args.mode == 'predict':
        if not args.symbol:
            print("❌ --symbol required for prediction mode")
            return
        
        if not args.load_timestamp:
            print("❌ --load-timestamp required for prediction mode")
            return
        
        # Load models
        if not predictor.load_models(args.model_dir, args.load_timestamp):
            print("❌ Failed to load models")
            return
        
        # Make prediction
        prediction = predictor.predict_timing(df, args.symbol)
        
        # Save prediction
        output_file = os.path.join(args.output, 'timing_prediction.json')
        with open(output_file, 'w') as f:
            json.dump(prediction, f, indent=2)
        
        print(f"✅ Prediction completed. Results saved to {output_file}")


if __name__ == '__main__':
    main()