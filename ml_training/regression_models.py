#!/usr/bin/env python3
"""
Advanced Regression Models for Dividend Yield Prediction
Implements ensemble of regression algorithms for accurate yield forecasting
"""

import argparse
import json
import os
import sys
import time
import warnings
from datetime import datetime
from typing import Dict, List, Tuple, Any, Union, Optional

# Suppress warnings
warnings.filterwarnings('ignore')

try:
    import pandas as pd
    import numpy as np
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
    from sklearn.svm import SVR
    from sklearn.neural_network import MLPRegressor
    from sklearn.model_selection import train_test_split, GridSearchCV, TimeSeriesSplit, cross_val_score
    from sklearn.preprocessing import StandardScaler, RobustScaler, QuantileTransformer
    from sklearn.metrics import (
        mean_squared_error, mean_absolute_error, r2_score, 
        mean_absolute_percentage_error
    )
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    from sklearn.feature_selection import SelectKBest, f_regression, mutual_info_regression
    import joblib
    
    try:
        import xgboost as xgb
        XGBOOST_AVAILABLE = True
    except ImportError:
        XGBOOST_AVAILABLE = False
        print("⚠️ XGBoost not available - will use Gradient Boosting instead")
        
    try:
        from sklearn.experimental import enable_hist_gradient_boosting
        from sklearn.ensemble import HistGradientBoostingRegressor
        HIST_GB_AVAILABLE = True
    except ImportError:
        HIST_GB_AVAILABLE = False
        
except ImportError as e:
    print(f"Error importing required packages: {e}")
    print("Please ensure all required packages are installed:")
    print("pip install pandas numpy scikit-learn joblib")
    if not XGBOOST_AVAILABLE:
        print("Optional: pip install xgboost (for enhanced performance)")
    sys.exit(1)


class DividendYieldRegressor:
    """
    Advanced ensemble regressor for dividend yield prediction
    Combines multiple algorithms for robust predictions
    """
    
    def __init__(self, random_state: int = 42):
        """Initialize the dividend yield regressor ensemble"""
        self.random_state = random_state
        
        # Model ensemble
        self.models = {}
        self.ensemble_weights = {
            'random_forest': 0.25,
            'xgboost': 0.25,
            'gradient_boosting': 0.20,
            'svr': 0.15,
            'neural_network': 0.10,
            'linear': 0.05
        }
        
        # Data preprocessing
        self.preprocessor = None
        self.feature_selector = None
        
        # Feature columns for yield prediction
        self.numerical_features = [
            # Financial Ratios
            'pe_ratio', 'pb_ratio', 'roe', 'roa', 'debt_to_equity', 'current_ratio',
            'debt_to_assets', 'interest_coverage', 'asset_turnover', 'equity_multiplier',
            
            # Historical Yield Patterns
            'dividend_yield_1yr_avg', 'dividend_yield_3yr_avg', 'dividend_yield_5yr_avg',
            'yield_volatility_1yr', 'yield_volatility_3yr', 'yield_trend_1yr', 'yield_trend_3yr',
            'yield_momentum', 'yield_mean_reversion', 'yield_percentile_rank',
            
            # Company Fundamentals
            'revenue_growth_1yr', 'revenue_growth_3yr', 'revenue_growth_5yr',
            'earnings_growth_1yr', 'earnings_growth_3yr', 'earnings_growth_5yr',
            'free_cash_flow_growth_1yr', 'free_cash_flow_growth_3yr',
            'dividend_growth_1yr', 'dividend_growth_3yr', 'dividend_growth_5yr',
            'payout_ratio', 'earnings_coverage', 'fcf_coverage', 'dividend_coverage',
            
            # Market Conditions
            'market_cap_log', 'beta', 'correlation_to_market', 'relative_strength',
            'sector_relative_performance', 'market_volatility', 'interest_rate_10yr',
            'credit_spread', 'vix_level', 'economic_sentiment',
            
            # Seasonal Factors
            'quarter_effect', 'month_effect', 'dividend_seasonality_score',
            'earnings_announcement_proximity', 'ex_dividend_proximity',
            
            # Technical Indicators
            'rsi_14', 'macd_signal', 'bollinger_position', 'moving_avg_20_ratio',
            'moving_avg_50_ratio', 'moving_avg_200_ratio', 'volume_ratio',
            'price_momentum_3m', 'price_momentum_6m', 'price_momentum_12m',
            
            # Company Lifecycle
            'company_age', 'dividend_paying_years', 'dividend_consistency_score',
            'aristocrat_status', 'king_status', 'growth_stage_score'
        ]
        
        self.categorical_features = [
            'sector', 'industry', 'exchange', 'market_size_category',
            'dividend_frequency', 'credit_rating_category', 'growth_stage',
            'business_cycle_stage', 'competitive_position'
        ]
        
        # Performance tracking
        self.feature_importance = {}
        self.training_metrics = {}
        self.validation_scores = {}
        
    def create_advanced_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create advanced features for yield prediction
        
        Args:
            data: Raw financial data
            
        Returns:
            DataFrame with engineered features
        """
        print("🔧 Creating advanced features for yield prediction...")
        
        df = data.copy()
        
        # Fill missing values with appropriate defaults
        df = self._fill_missing_values(df)
        
        # Technical Indicators
        df = self._create_technical_indicators(df)
        
        # Fundamental Ratios
        df = self._create_fundamental_ratios(df)
        
        # Yield-specific features
        df = self._create_yield_features(df)
        
        # Market condition features
        df = self._create_market_features(df)
        
        # Seasonal features
        df = self._create_seasonal_features(df)
        
        # Interaction features
        df = self._create_interaction_features(df)
        
        return df
    
    def _fill_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fill missing values with appropriate defaults"""
        
        # Financial ratios
        df = df.fillna({
            'pe_ratio': 15.0, 'pb_ratio': 2.0, 'roe': 0.12, 'roa': 0.06,
            'debt_to_equity': 0.5, 'current_ratio': 1.5, 'debt_to_assets': 0.3,
            'interest_coverage': 5.0, 'asset_turnover': 1.0, 'equity_multiplier': 2.0,
        })
        
        # Growth rates
        df = df.fillna({
            'revenue_growth_1yr': 0.03, 'revenue_growth_3yr': 0.03, 'revenue_growth_5yr': 0.03,
            'earnings_growth_1yr': 0.05, 'earnings_growth_3yr': 0.05, 'earnings_growth_5yr': 0.05,
            'free_cash_flow_growth_1yr': 0.04, 'free_cash_flow_growth_3yr': 0.04,
            'dividend_growth_1yr': 0.03, 'dividend_growth_3yr': 0.03, 'dividend_growth_5yr': 0.03,
        })
        
        # Dividend metrics
        df = df.fillna({
            'payout_ratio': 0.5, 'earnings_coverage': 2.0, 'fcf_coverage': 1.5,
            'dividend_coverage': 1.8, 'dividend_yield_1yr_avg': 0.03,
            'dividend_yield_3yr_avg': 0.03, 'dividend_yield_5yr_avg': 0.03,
        })
        
        # Market data
        df = df.fillna({
            'beta': 1.0, 'market_cap_log': 9.0, 'correlation_to_market': 0.7,
            'relative_strength': 1.0, 'sector_relative_performance': 1.0,
            'market_volatility': 0.15, 'interest_rate_10yr': 0.04, 'credit_spread': 0.02,
            'vix_level': 20.0, 'economic_sentiment': 0.5,
        })
        
        # Technical indicators
        df = df.fillna({
            'rsi_14': 50.0, 'macd_signal': 0.0, 'bollinger_position': 0.5,
            'moving_avg_20_ratio': 1.0, 'moving_avg_50_ratio': 1.0, 'moving_avg_200_ratio': 1.0,
            'volume_ratio': 1.0, 'price_momentum_3m': 0.0, 'price_momentum_6m': 0.0,
            'price_momentum_12m': 0.0,
        })
        
        # Company characteristics
        df = df.fillna({
            'company_age': 25.0, 'dividend_paying_years': 15.0,
            'dividend_consistency_score': 0.7, 'aristocrat_status': 0,
            'king_status': 0, 'growth_stage_score': 0.5,
        })
        
        # Categorical features
        df = df.fillna({
            'sector': 'Unknown', 'industry': 'Unknown', 'exchange': 'NYSE',
            'market_size_category': 'Large Cap', 'dividend_frequency': 'Quarterly',
            'credit_rating_category': 'Investment Grade', 'growth_stage': 'Mature',
            'business_cycle_stage': 'Expansion', 'competitive_position': 'Average'
        })
        
        return df
    
    def _create_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create technical analysis indicators"""
        
        # Price momentum indicators
        if 'price' in df.columns:
            # RSI calculation (simplified)
            if 'rsi_14' not in df.columns:
                df['rsi_14'] = 50.0  # Default RSI
                
            # MACD signal
            if 'macd_signal' not in df.columns:
                df['macd_signal'] = 0.0
                
            # Bollinger Band position
            if 'bollinger_position' not in df.columns:
                df['bollinger_position'] = 0.5
        
        # Dividend-specific technical indicators
        if 'dividend_yield' in df.columns:
            df['yield_momentum'] = df['dividend_yield'].pct_change(4).fillna(0)
            df['yield_mean_reversion'] = (df['dividend_yield'] - df['dividend_yield'].rolling(12).mean()).fillna(0)
            df['yield_percentile_rank'] = df['dividend_yield'].rolling(252).rank(pct=True).fillna(0.5)
        
        if 'payout_ratio' in df.columns:
            df['payout_stability'] = df['payout_ratio'].rolling(8).std().fillna(0.1)
            df['payout_trend'] = df['payout_ratio'].rolling(4).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) >= 2 else 0
            ).fillna(0)
        
        return df
    
    def _create_fundamental_ratios(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create fundamental analysis ratios"""
        
        # Profitability trend analysis
        if 'roe' in df.columns:
            df['roe_trend'] = df['roe'].rolling(4).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) >= 2 else 0
            ).fillna(0)
            df['roe_stability'] = df['roe'].rolling(4).std().fillna(0.02)
        
        # Cash flow quality metrics
        if all(col in df.columns for col in ['free_cash_flow', 'market_cap']):
            df['fcf_yield'] = df['free_cash_flow'] / df['market_cap']
        else:
            df['fcf_yield'] = 0.05  # Default 5% FCF yield
            
        if all(col in df.columns for col in ['operating_cash_flow', 'net_income']):
            df['earnings_quality'] = df['operating_cash_flow'] / df['net_income'].clip(lower=0.01)
        else:
            df['earnings_quality'] = 1.2  # Default earnings quality
        
        # Debt sustainability metrics
        if all(col in df.columns for col in ['operating_cash_flow', 'total_debt_payments']):
            df['debt_service_coverage'] = df['operating_cash_flow'] / df['total_debt_payments'].clip(lower=0.01)
        else:
            df['debt_service_coverage'] = 3.0  # Default coverage
            
        if all(col in df.columns for col in ['free_cash_flow', 'total_dividends_paid']):
            df['dividend_coverage'] = df['free_cash_flow'] / df['total_dividends_paid'].clip(lower=0.01)
        else:
            df['dividend_coverage'] = 1.8  # Default coverage
        
        return df
    
    def _create_yield_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create yield-specific features"""
        
        # Yield volatility measures
        if 'dividend_yield' in df.columns:
            df['yield_volatility_1yr'] = df['dividend_yield'].rolling(252).std().fillna(0.01)
            df['yield_volatility_3yr'] = df['dividend_yield'].rolling(756).std().fillna(0.01)
            
            # Yield trend analysis
            df['yield_trend_1yr'] = df['dividend_yield'].rolling(252).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) >= 2 else 0
            ).fillna(0)
            df['yield_trend_3yr'] = df['dividend_yield'].rolling(756).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) >= 2 else 0
            ).fillna(0)
        
        # Dividend sustainability score
        sustainability_factors = ['payout_ratio', 'earnings_coverage', 'debt_to_equity']
        if all(col in df.columns for col in sustainability_factors):
            # Lower payout ratio is better (inverse)
            payout_score = np.where(df['payout_ratio'] < 0.6, 1.0, 
                          np.where(df['payout_ratio'] < 0.8, 0.7, 0.3))
            
            # Higher coverage is better
            coverage_score = np.where(df['earnings_coverage'] > 2.0, 1.0,
                            np.where(df['earnings_coverage'] > 1.5, 0.7, 0.3))
            
            # Lower debt is better (inverse)
            debt_score = np.where(df['debt_to_equity'] < 0.5, 1.0,
                        np.where(df['debt_to_equity'] < 1.0, 0.7, 0.3))
            
            df['dividend_sustainability_score'] = (payout_score * 0.4 + 
                                                 coverage_score * 0.4 + 
                                                 debt_score * 0.2)
        else:
            df['dividend_sustainability_score'] = 0.7  # Default moderate sustainability
        
        return df
    
    def _create_market_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create market condition features"""
        
        # Sector relative performance
        if 'sector' in df.columns and 'relative_performance' in df.columns:
            df['sector_relative_yield'] = df.groupby('sector')['dividend_yield'].transform(
                lambda x: x / x.mean() if x.mean() > 0 else 1.0
            ).fillna(1.0)
        else:
            df['sector_relative_yield'] = 1.0
        
        # Market regime indicators
        if 'market_volatility' in df.columns:
            df['low_volatility_regime'] = (df['market_volatility'] < 0.15).astype(int)
            df['high_volatility_regime'] = (df['market_volatility'] > 0.25).astype(int)
        
        if 'interest_rate_10yr' in df.columns:
            df['low_rate_environment'] = (df['interest_rate_10yr'] < 0.03).astype(int)
            df['high_rate_environment'] = (df['interest_rate_10yr'] > 0.05).astype(int)
        
        return df
    
    def _create_seasonal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create seasonal and calendar features"""
        
        # Quarter effects (many dividends paid quarterly)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df['quarter'] = df['date'].dt.quarter
            df['month'] = df['date'].dt.month
            
            # Q4 and Q1 often have higher dividend announcements
            df['high_dividend_quarter'] = df['quarter'].isin([1, 4]).astype(int)
            
            # December effect (year-end special dividends)
            df['december_effect'] = (df['month'] == 12).astype(int)
        else:
            df['quarter'] = 2  # Default to Q2
            df['month'] = 6   # Default to June
            df['high_dividend_quarter'] = 0
            df['december_effect'] = 0
        
        # Ex-dividend proximity effect
        if 'ex_dividend_proximity' not in df.columns:
            df['ex_dividend_proximity'] = 0.5  # Default moderate proximity
        
        return df
    
    def _create_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create interaction features between key variables"""
        
        # Yield-Growth interaction
        if all(col in df.columns for col in ['dividend_yield', 'dividend_growth_3yr']):
            df['yield_growth_interaction'] = df['dividend_yield'] * df['dividend_growth_3yr']
        
        # Quality-Yield interaction
        if all(col in df.columns for col in ['dividend_yield', 'roe']):
            df['quality_yield_interaction'] = df['dividend_yield'] * df['roe']
        
        # Size-Yield interaction
        if all(col in df.columns for col in ['dividend_yield', 'market_cap_log']):
            df['size_yield_interaction'] = df['dividend_yield'] * df['market_cap_log']
        
        # Risk-Yield interaction
        if all(col in df.columns for col in ['dividend_yield', 'beta']):
            df['risk_yield_interaction'] = df['dividend_yield'] * df['beta']
        
        return df
    
    def train_ensemble(self, data: pd.DataFrame, target_col: str = 'future_yield') -> Dict[str, Any]:
        """
        Train the ensemble of regression models
        
        Args:
            data: Training data with features and target
            target_col: Name of target column
            
        Returns:
            Training results and metrics
        """
        print("🏋️ Training Dividend Yield Regression Ensemble...")
        
        # Feature engineering
        df = self.create_advanced_features(data)
        
        # Prepare target variable
        if target_col not in df.columns:
            print(f"⚠️ Target column '{target_col}' not found. Creating synthetic target...")
            # Create synthetic future yield based on current yield + growth
            df[target_col] = df.get('dividend_yield', 0.03) * (1 + df.get('dividend_growth_1yr', 0.03))
        
        y = df[target_col].fillna(df[target_col].median())
        
        # Select features
        available_numerical = [col for col in self.numerical_features if col in df.columns]
        available_categorical = [col for col in self.categorical_features if col in df.columns]
        
        # Add engineered features
        engineered_features = [
            'yield_momentum', 'yield_mean_reversion', 'yield_percentile_rank',
            'payout_stability', 'payout_trend', 'roe_trend', 'roe_stability',
            'fcf_yield', 'earnings_quality', 'debt_service_coverage',
            'dividend_coverage', 'dividend_sustainability_score',
            'sector_relative_yield', 'yield_growth_interaction',
            'quality_yield_interaction', 'size_yield_interaction', 'risk_yield_interaction'
        ]
        
        available_numerical.extend([f for f in engineered_features if f in df.columns])
        
        print(f"📊 Using {len(available_numerical)} numerical and {len(available_categorical)} categorical features")
        
        # Create preprocessor
        if available_categorical:
            from sklearn.preprocessing import OneHotEncoder
            self.preprocessor = ColumnTransformer(
                transformers=[
                    ('num', StandardScaler(), available_numerical),
                    ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), available_categorical)
                ],
                remainder='drop'
            )
        else:
            self.preprocessor = StandardScaler()
        
        # Prepare features
        X = df[available_numerical + available_categorical]
        
        # Time-aware split for financial data
        split_point = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_point], X.iloc[split_point:]
        y_train, y_test = y.iloc[:split_point], y.iloc[split_point:]
        
        print(f"📊 Training set: {len(X_train)}, Test set: {len(X_test)}")
        
        # Train individual models
        self._train_individual_models(X_train, y_train, X_test, y_test)
        
        # Evaluate ensemble
        ensemble_results = self._evaluate_ensemble(X_test, y_test)
        
        # Store training metadata
        self.training_metrics = {
            'timestamp': datetime.now().isoformat(),
            'training_size': len(X_train),
            'test_size': len(X_test),
            'feature_count': len(available_numerical + available_categorical),
            'models_trained': list(self.models.keys()),
            'ensemble_results': ensemble_results
        }
        
        print("✅ Ensemble training completed!")
        print(f"📊 Ensemble RMSE: {ensemble_results['rmse']:.4f}")
        print(f"📊 Ensemble R²: {ensemble_results['r2']:.4f}")
        
        return self.training_metrics
    
    def _train_individual_models(self, X_train, y_train, X_test, y_test):
        """Train individual models in the ensemble"""
        
        # 1. Linear Regression
        print("📈 Training Linear Regression...")
        linear_pipeline = Pipeline([
            ('preprocessor', self.preprocessor),
            ('regressor', Ridge(alpha=1.0, random_state=self.random_state))
        ])
        linear_pipeline.fit(X_train, y_train)
        self.models['linear'] = linear_pipeline
        
        # 2. Random Forest
        print("🌲 Training Random Forest...")
        rf_pipeline = Pipeline([
            ('preprocessor', self.preprocessor),
            ('regressor', RandomForestRegressor(
                n_estimators=100,
                max_depth=15,
                min_samples_split=10,
                min_samples_leaf=5,
                random_state=self.random_state,
                n_jobs=-1
            ))
        ])
        rf_pipeline.fit(X_train, y_train)
        self.models['random_forest'] = rf_pipeline
        
        # 3. Gradient Boosting (XGBoost if available)
        if XGBOOST_AVAILABLE:
            print("🚀 Training XGBoost...")
            xgb_pipeline = Pipeline([
                ('preprocessor', self.preprocessor),
                ('regressor', xgb.XGBRegressor(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=self.random_state,
                    eval_metric='rmse'
                ))
            ])
            xgb_pipeline.fit(X_train, y_train)
            self.models['xgboost'] = xgb_pipeline
        else:
            print("📈 Training Gradient Boosting...")
            gb_pipeline = Pipeline([
                ('preprocessor', self.preprocessor),
                ('regressor', GradientBoostingRegressor(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    random_state=self.random_state
                ))
            ])
            gb_pipeline.fit(X_train, y_train)
            self.models['gradient_boosting'] = gb_pipeline
        
        # 4. Support Vector Regression
        print("🎯 Training Support Vector Regression...")
        svr_pipeline = Pipeline([
            ('preprocessor', self.preprocessor),
            ('regressor', SVR(
                kernel='rbf',
                C=1.0,
                gamma='scale',
                epsilon=0.01
            ))
        ])
        svr_pipeline.fit(X_train, y_train)
        self.models['svr'] = svr_pipeline
        
        # 5. Neural Network
        print("🧠 Training Neural Network...")
        nn_pipeline = Pipeline([
            ('preprocessor', self.preprocessor),
            ('regressor', MLPRegressor(
                hidden_layer_sizes=(100, 50),
                activation='relu',
                solver='adam',
                alpha=0.001,
                learning_rate='adaptive',
                max_iter=500,
                random_state=self.random_state
            ))
        ])
        nn_pipeline.fit(X_train, y_train)
        self.models['neural_network'] = nn_pipeline
    
    def _evaluate_ensemble(self, X_test, y_test) -> Dict[str, float]:
        """Evaluate ensemble performance"""
        
        # Get predictions from all models
        predictions = {}
        for name, model in self.models.items():
            pred = model.predict(X_test)
            predictions[name] = pred
        
        # Ensemble prediction (weighted average)
        ensemble_pred = np.zeros(len(y_test))
        for name, pred in predictions.items():
            weight = self.ensemble_weights.get(name, 0.0)
            ensemble_pred += weight * pred
        
        # Calculate metrics
        rmse = np.sqrt(mean_squared_error(y_test, ensemble_pred))
        mae = mean_absolute_error(y_test, ensemble_pred)
        r2 = r2_score(y_test, ensemble_pred)
        
        try:
            mape = mean_absolute_percentage_error(y_test, ensemble_pred)
        except:
            mape = np.mean(np.abs((y_test - ensemble_pred) / np.clip(y_test, 0.001, None))) * 100
        
        # Directional accuracy
        actual_direction = np.sign(np.diff(y_test))
        pred_direction = np.sign(np.diff(ensemble_pred))
        directional_accuracy = np.mean(actual_direction == pred_direction) if len(actual_direction) > 0 else 0.5
        
        return {
            'rmse': rmse,
            'mae': mae,
            'r2': r2,
            'mape': mape,
            'directional_accuracy': directional_accuracy
        }
    
    def predict_yield(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Predict dividend yields for given data
        
        Args:
            data: Feature data for prediction
            
        Returns:
            List of yield predictions with confidence intervals
        """
        print(f"🔮 Predicting yields for {len(data)} records...")
        
        if not self.models:
            raise ValueError("Models not trained. Please train the ensemble first.")
        
        # Feature engineering
        df = self.create_advanced_features(data)
        
        # Select features
        available_numerical = [col for col in self.numerical_features if col in df.columns]
        available_categorical = [col for col in self.categorical_features if col in df.columns]
        
        # Add engineered features
        engineered_features = [
            'yield_momentum', 'yield_mean_reversion', 'yield_percentile_rank',
            'payout_stability', 'payout_trend', 'roe_trend', 'roe_stability',
            'fcf_yield', 'earnings_quality', 'debt_service_coverage',
            'dividend_coverage', 'dividend_sustainability_score',
            'sector_relative_yield', 'yield_growth_interaction',
            'quality_yield_interaction', 'size_yield_interaction', 'risk_yield_interaction'
        ]
        
        available_numerical.extend([f for f in engineered_features if f in df.columns])
        
        X = df[available_numerical + available_categorical]
        
        # Get predictions from all models
        predictions = {}
        for name, model in self.models.items():
            pred = model.predict(X)
            predictions[name] = pred
        
        # Ensemble prediction
        ensemble_pred = np.zeros(len(X))
        for name, pred in predictions.items():
            weight = self.ensemble_weights.get(name, 0.0)
            ensemble_pred += weight * pred
        
        # Calculate prediction confidence (based on model agreement)
        pred_std = np.std([pred for pred in predictions.values()], axis=0)
        confidence_lower = ensemble_pred - 1.96 * pred_std
        confidence_upper = ensemble_pred + 1.96 * pred_std
        
        # Prepare results
        results = []
        for i in range(len(X)):
            result = {
                'symbol': df.iloc[i].get('symbol', f'STOCK_{i}'),
                'predicted_yield': float(ensemble_pred[i]),
                'confidence_lower': float(confidence_lower[i]),
                'confidence_upper': float(confidence_upper[i]),
                'model_agreement': float(1.0 - pred_std[i] / (np.mean(ensemble_pred) + 1e-8)),
                'individual_predictions': {
                    name: float(pred[i]) for name, pred in predictions.items()
                },
                'key_features': self._get_key_features(df.iloc[i]),
                'prediction_rationale': self._generate_rationale(df.iloc[i], ensemble_pred[i]),
                'timestamp': datetime.now().isoformat()
            }
            results.append(result)
        
        return results
    
    def _get_key_features(self, row: pd.Series) -> Dict[str, float]:
        """Get key features that influence the prediction"""
        key_features = [
            'dividend_yield', 'payout_ratio', 'earnings_coverage', 'dividend_growth_3yr',
            'roe', 'debt_to_equity', 'pe_ratio', 'dividend_sustainability_score'
        ]
        
        feature_dict = {}
        for feature in key_features:
            if feature in row:
                feature_dict[feature] = float(row[feature])
        
        return feature_dict
    
    def _generate_rationale(self, row: pd.Series, prediction: float) -> List[str]:
        """Generate human-readable rationale for the prediction"""
        rationale = []
        
        current_yield = row.get('dividend_yield', 0.03)
        
        if prediction > current_yield * 1.1:
            rationale.append(f"Yield expected to increase to {prediction:.2%} from current {current_yield:.2%}")
        elif prediction < current_yield * 0.9:
            rationale.append(f"Yield expected to decrease to {prediction:.2%} from current {current_yield:.2%}")
        else:
            rationale.append(f"Yield expected to remain stable around {prediction:.2%}")
        
        # Payout ratio analysis
        payout = row.get('payout_ratio', 0.5)
        if payout > 0.8:
            rationale.append(f"High payout ratio of {payout:.1%} suggests limited room for yield increases")
        elif payout < 0.5:
            rationale.append(f"Conservative payout ratio of {payout:.1%} supports potential yield growth")
        
        # Growth analysis
        growth = row.get('dividend_growth_3yr', 0.03)
        if growth > 0.05:
            rationale.append(f"Strong dividend growth of {growth:.1%} supports higher future yields")
        elif growth < 0:
            rationale.append(f"Negative dividend growth of {growth:.1%} pressures yield sustainability")
        
        # Financial strength
        coverage = row.get('earnings_coverage', 2.0)
        if coverage > 2.5:
            rationale.append(f"Strong earnings coverage of {coverage:.1f}x supports dividend security")
        elif coverage < 1.5:
            rationale.append(f"Low earnings coverage of {coverage:.1f}x raises dividend risk concerns")
        
        return rationale
    
    def save_models(self, model_dir: str = 'models') -> str:
        """Save trained models to disk"""
        os.makedirs(model_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for name, model in self.models.items():
            filename = f'yield_regressor_{name}_{timestamp}.joblib'
            filepath = os.path.join(model_dir, filename)
            joblib.dump(model, filepath)
            print(f"💾 Saved {name} model to {filepath}")
        
        # Save ensemble metadata
        metadata_file = os.path.join(model_dir, f'yield_ensemble_metadata_{timestamp}.json')
        metadata = {
            'ensemble_weights': self.ensemble_weights,
            'training_metrics': self.training_metrics,
            'timestamp': timestamp,
            'model_files': {
                name: f'yield_regressor_{name}_{timestamp}.joblib' 
                for name in self.models.keys()
            }
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"📋 Saved ensemble metadata to {metadata_file}")
        return timestamp
    
    def load_models(self, model_dir: str, timestamp: str) -> bool:
        """Load trained models from disk"""
        try:
            # Load metadata
            metadata_file = os.path.join(model_dir, f'yield_ensemble_metadata_{timestamp}.json')
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            self.ensemble_weights = metadata['ensemble_weights']
            self.training_metrics = metadata['training_metrics']
            
            # Load individual models
            for name, filename in metadata['model_files'].items():
                filepath = os.path.join(model_dir, filename)
                self.models[name] = joblib.load(filepath)
                print(f"📂 Loaded {name} model from {filepath}")
            
            print(f"✅ Successfully loaded ensemble from {timestamp}")
            return True
        except Exception as e:
            print(f"❌ Failed to load models: {e}")
            return False


def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description='Dividend Yield Regression Models')
    parser.add_argument('--mode', choices=['train', 'predict'], required=True,
                      help='Mode: train or predict')
    parser.add_argument('--input', required=True,
                      help='Input data file (JSON)')
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
    
    # Initialize regressor
    regressor = DividendYieldRegressor()
    
    if args.mode == 'train':
        # Train models
        results = regressor.train_ensemble(df)
        
        # Save models
        timestamp = regressor.save_models(args.model_dir)
        
        # Save results
        output_file = os.path.join(args.output, 'yield_regression_results.json')
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"✅ Training completed. Results saved to {output_file}")
        
    elif args.mode == 'predict':
        if not args.load_timestamp:
            print("❌ --load-timestamp required for prediction mode")
            return
        
        # Load models
        if not regressor.load_models(args.model_dir, args.load_timestamp):
            print("❌ Failed to load models")
            return
        
        # Make predictions
        predictions = regressor.predict_yield(df)
        
        # Save predictions
        output_file = os.path.join(args.output, 'yield_predictions.json')
        with open(output_file, 'w') as f:
            json.dump(predictions, f, indent=2)
        
        print(f"✅ Predictions completed. Results saved to {output_file}")


if __name__ == '__main__':
    main()