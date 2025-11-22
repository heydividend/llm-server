#!/usr/bin/env python3
"""
Dividend Payout Rating Model
Rates dividend quality by combining payout strength and NAV erosion resistance
Output: 0-100 rating (Payout Quality 0-50 + NAV Protection 0-50)
"""

import argparse
import json
import sys
import warnings
from typing import Dict, List, Any

warnings.filterwarnings('ignore')

try:
    import pandas as pd
    import numpy as np
    from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
    from sklearn.preprocessing import RobustScaler
    from sklearn.model_selection import train_test_split, cross_val_score
    import joblib
except ImportError as e:
    print(f"Error importing required packages: {e}")
    print("Please install: pip install pandas numpy scikit-learn joblib")
    sys.exit(1)


class DividendPayoutRatingModel:
    """
    Dual-component ML model for rating dividend quality
    Component 1: Payout Quality Score (0-50)
    Component 2: NAV Protection Score (0-50)
    Total Rating: 0-100
    """
    
    def __init__(self):
        self.payout_model = None  # Model for payout quality
        self.nav_model = None  # Model for NAV protection
        self.scaler = RobustScaler()
        self.feature_columns = []
        self.model_metadata = {
            'version': '1.0.0',
            'trained_date': None,
            'num_samples': 0,
            'payout_score_range': [0, 50],
            'nav_score_range': [0, 50],
            'total_score_range': [0, 100]
        }
        
    def prepare_features(self, data: List[Dict]) -> pd.DataFrame:
        """Extract and engineer features for dividend payout rating"""
        print(f"📊 Preparing features for {len(data)} records...")
        
        df = pd.DataFrame(data)
        
        # Core payout quality features
        payout_features = [
            'dividend_yield',          # Current yield
            'payout_ratio',            # Earnings-based payout
            'fcf_payout_ratio',        # Free cash flow coverage
            'dividend_growth_3y',      # 3-year dividend CAGR
            'dividend_consistency',     # Payment regularity score
            'roe',                     # Return on equity
            'earnings_growth',         # YoY earnings growth
        ]
        
        # NAV erosion protection features
        nav_features = [
            'monthly_nav_percent',     # Dividend as % of NAV
            'nav_stability_score',     # NAV volatility measure
            'nav_trend',               # NAV direction (up/down/stable)
            'nav_coverage_ratio',      # NAV / Annual Dividend
        ]
        
        # Financial health features
        health_features = [
            'leverage_ratio',          # Debt levels
            'market_cap_log',          # Company size
            'volatility_30d',          # Price stability
            'beta',                    # Market sensitivity
        ]
        
        # Combine all features
        self.feature_columns = payout_features + nav_features + health_features
        
        # Calculate derived features if not present
        if 'dividend_consistency' not in df.columns:
            df['dividend_consistency'] = self._calculate_consistency(df)
        
        if 'nav_stability_score' not in df.columns and 'monthly_nav_percent' in df.columns:
            df['nav_stability_score'] = self._calculate_nav_stability(df)
        
        if 'nav_trend' not in df.columns and 'nav_per_share' in df.columns:
            df['nav_trend'] = self._calculate_nav_trend(df)
            
        if 'nav_coverage_ratio' not in df.columns:
            df['nav_coverage_ratio'] = self._calculate_nav_coverage(df)
        
        if 'market_cap_log' not in df.columns and 'market_cap' in df.columns:
            df['market_cap_log'] = np.log1p(df['market_cap'])
        
        # Handle missing values
        for col in self.feature_columns:
            if col not in df.columns:
                df[col] = 0.0
            else:
                df[col] = df[col].fillna(df[col].median() if df[col].notna().sum() > 0 else 0.0)
        
        print(f"✅ Features prepared: {len(self.feature_columns)} features")
        return df
    
    def _calculate_consistency(self, df: pd.DataFrame) -> pd.Series:
        """Calculate dividend payment consistency score"""
        # Placeholder: In production, analyze payment frequency stability
        return pd.Series(75.0, index=df.index)  # Default good consistency
    
    def _calculate_nav_stability(self, df: pd.DataFrame) -> pd.Series:
        """Calculate NAV stability score (lower volatility = higher score)"""
        if 'monthly_nav_percent' not in df.columns:
            return pd.Series(50.0, index=df.index)
        
        # Group by symbol and calculate rolling volatility
        nav_volatility = df.groupby('symbol')['monthly_nav_percent'].transform(
            lambda x: x.rolling(window=12, min_periods=3).std()
        )
        
        # Convert volatility to stability score (0-100, inverted)
        max_vol = nav_volatility.quantile(0.95) if nav_volatility.notna().sum() > 0 else 1.0
        stability = 100 * (1 - nav_volatility / max_vol)
        
        return stability.fillna(50.0)
    
    def _calculate_nav_trend(self, df: pd.DataFrame) -> pd.Series:
        """Calculate NAV trend: -1 (declining), 0 (stable), 1 (growing)"""
        if 'nav_per_share' not in df.columns:
            return pd.Series(0.0, index=df.index)
        
        # Calculate 6-month NAV change
        nav_change = df.groupby('symbol')['nav_per_share'].transform(
            lambda x: x.pct_change(periods=6)
        )
        
        # Classify trend
        trend = pd.Series(0.0, index=df.index)
        trend[nav_change > 0.02] = 1.0   # Growing
        trend[nav_change < -0.02] = -1.0  # Declining
        
        return trend
    
    def _calculate_nav_coverage(self, df: pd.DataFrame) -> pd.Series:
        """Calculate how many years of dividends NAV can cover"""
        if 'nav_per_share' not in df.columns or 'dividend_amount' not in df.columns:
            return pd.Series(10.0, index=df.index)  # Default coverage
        
        # Annual dividend estimate (multiply by frequency)
        freq_multiplier = df['frequency'].map({
            'monthly': 12, 'quarterly': 4, 'semi-annual': 2, 'annual': 1
        }).fillna(4)
        
        annual_dividend = df['dividend_amount'] * freq_multiplier
        coverage = df['nav_per_share'] / annual_dividend.replace(0, np.nan)
        
        return coverage.fillna(10.0).clip(0, 50)  # Cap at 50 years
    
    def calculate_payout_quality_target(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate ground truth payout quality score (0-50)
        Based on: yield strength, growth, coverage, consistency
        """
        scores = pd.Series(0.0, index=df.index)
        
        # Component 1: Yield strength (0-15 points)
        yield_score = df['dividend_yield'].clip(0, 15)
        scores += yield_score
        
        # Component 2: Growth trajectory (0-15 points)
        growth_score = (df['dividend_growth_3y'].clip(-10, 20) + 10) / 2
        scores += growth_score
        
        # Component 3: Coverage strength (0-10 points)
        coverage_score = (100 - df['payout_ratio'].clip(0, 100)) / 10
        scores += coverage_score
        
        # Component 4: Consistency (0-10 points)
        consistency_score = df['dividend_consistency'] / 10
        scores += consistency_score
        
        return scores.clip(0, 50)
    
    def calculate_nav_protection_target(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate ground truth NAV protection score (0-50)
        Based on: low NAV erosion, stability, trend
        """
        scores = pd.Series(0.0, index=df.index)
        
        # Component 1: Low NAV distribution (0-20 points)
        # Lower monthly_nav_percent = better NAV protection
        nav_dist_score = 20 * (1 - df['monthly_nav_percent'].clip(0, 10) / 10)
        scores += nav_dist_score
        
        # Component 2: NAV stability (0-15 points)
        stability_score = df['nav_stability_score'] / 100 * 15
        scores += stability_score
        
        # Component 3: NAV trend (0-10 points)
        # Growing NAV = better, stable = ok, declining = worse
        trend_score = (df['nav_trend'] + 1) * 5  # -1→0, 0→5, 1→10
        scores += trend_score
        
        # Component 4: NAV coverage (0-5 points)
        coverage_score = (df['nav_coverage_ratio'].clip(0, 10) / 10) * 5
        scores += coverage_score
        
        return scores.clip(0, 50)
    
    def train(self, training_data: List[Dict]) -> Dict[str, Any]:
        """
        Train both payout quality and NAV protection models
        """
        print("🏋️ Training Dividend Payout Rating Model...")
        
        # Prepare features
        df = self.prepare_features(training_data)
        
        if len(df) < 100:
            raise ValueError(f"Insufficient training data: {len(df)} records. Need at least 100.")
        
        # Calculate target scores
        df['payout_quality_target'] = self.calculate_payout_quality_target(df)
        df['nav_protection_target'] = self.calculate_nav_protection_target(df)
        
        # Prepare feature matrix
        X = df[self.feature_columns].values
        y_payout = df['payout_quality_target'].values
        y_nav = df['nav_protection_target'].values
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_payout_train, y_payout_test = train_test_split(
            X_scaled, y_payout, test_size=0.2, random_state=42
        )
        _, _, y_nav_train, y_nav_test = train_test_split(
            X_scaled, y_nav, test_size=0.2, random_state=42
        )
        
        # Train Payout Quality Model
        print("📊 Training Payout Quality Model...")
        self.payout_model = GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=5,
            min_samples_split=10,
            min_samples_leaf=5,
            subsample=0.8,
            random_state=42
        )
        self.payout_model.fit(X_train, y_payout_train)
        
        # Train NAV Protection Model
        print("📊 Training NAV Protection Model...")
        self.nav_model = GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=5,
            min_samples_split=10,
            min_samples_leaf=5,
            subsample=0.8,
            random_state=42
        )
        self.nav_model.fit(X_train, y_nav_train)
        
        # Evaluate models
        payout_train_score = self.payout_model.score(X_train, y_payout_train)
        payout_test_score = self.payout_model.score(X_test, y_payout_test)
        nav_train_score = self.nav_model.score(X_train, y_nav_train)
        nav_test_score = self.nav_model.score(X_test, y_nav_test)
        
        # Calculate feature importance
        payout_importance = dict(zip(
            self.feature_columns,
            self.payout_model.feature_importances_
        ))
        nav_importance = dict(zip(
            self.feature_columns,
            self.nav_model.feature_importances_
        ))
        
        # Update metadata
        self.model_metadata['trained_date'] = pd.Timestamp.now().isoformat()
        self.model_metadata['num_samples'] = len(df)
        
        results = {
            'success': True,
            'metrics': {
                'payout_model': {
                    'train_r2': float(payout_train_score),
                    'test_r2': float(payout_test_score),
                    'feature_importance': payout_importance
                },
                'nav_model': {
                    'train_r2': float(nav_train_score),
                    'test_r2': float(nav_test_score),
                    'feature_importance': nav_importance
                }
            },
            'metadata': self.model_metadata,
            'feature_columns': self.feature_columns
        }
        
        print(f"✅ Training complete!")
        print(f"   Payout Model R²: Train={payout_train_score:.3f}, Test={payout_test_score:.3f}")
        print(f"   NAV Model R²: Train={nav_train_score:.3f}, Test={nav_test_score:.3f}")
        
        return results
    
    def predict(self, data: List[Dict]) -> List[Dict]:
        """
        Generate dividend payout ratings for given data
        Returns: List of ratings with payout_quality, nav_protection, and total scores
        """
        if self.payout_model is None or self.nav_model is None:
            raise ValueError("Models not trained. Call train() first.")
        
        print(f"🔮 Generating payout ratings for {len(data)} records...")
        
        # Prepare features
        df = self.prepare_features(data)
        
        # Scale features
        X = df[self.feature_columns].values
        X_scaled = self.scaler.transform(X)
        
        # Generate predictions
        payout_scores = self.payout_model.predict(X_scaled)
        nav_scores = self.nav_model.predict(X_scaled)
        
        # Clip to valid ranges
        payout_scores = np.clip(payout_scores, 0, 50)
        nav_scores = np.clip(nav_scores, 0, 50)
        total_scores = payout_scores + nav_scores
        
        # Classify ratings
        def get_rating_label(score: float) -> str:
            if score >= 85: return 'Excellent'
            elif score >= 70: return 'Very Good'
            elif score >= 55: return 'Good'
            elif score >= 40: return 'Fair'
            else: return 'Poor'
        
        # Build results
        results = []
        for i in range(len(df)):
            results.append({
                'symbol': df.iloc[i].get('symbol', f'UNKNOWN_{i}'),
                'payout_quality_score': float(payout_scores[i]),
                'nav_protection_score': float(nav_scores[i]),
                'total_rating': float(total_scores[i]),
                'rating_label': get_rating_label(total_scores[i]),
                'payout_percentile': float(np.percentile(payout_scores, 
                    (payout_scores <= payout_scores[i]).sum() / len(payout_scores) * 100)),
                'nav_percentile': float(np.percentile(nav_scores,
                    (nav_scores <= nav_scores[i]).sum() / len(nav_scores) * 100)),
                'total_percentile': float(np.percentile(total_scores,
                    (total_scores <= total_scores[i]).sum() / len(total_scores) * 100))
            })
        
        print(f"✅ Generated {len(results)} payout ratings")
        return results
    
    def save_model(self, filepath: str):
        """Save trained model to disk"""
        model_data = {
            'payout_model': self.payout_model,
            'nav_model': self.nav_model,
            'scaler': self.scaler,
            'feature_columns': self.feature_columns,
            'metadata': self.model_metadata
        }
        joblib.dump(model_data, filepath)
        print(f"💾 Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load trained model from disk"""
        model_data = joblib.load(filepath)
        self.payout_model = model_data['payout_model']
        self.nav_model = model_data['nav_model']
        self.scaler = model_data['scaler']
        self.feature_columns = model_data['feature_columns']
        self.model_metadata = model_data['metadata']
        print(f"📂 Model loaded from {filepath}")


def main():
    parser = argparse.ArgumentParser(description='Dividend Payout Rating Model')
    parser.add_argument('--mode', choices=['train', 'predict'], required=True)
    parser.add_argument('--input', required=True, help='Input JSON file')
    parser.add_argument('--output', required=True, help='Output path (model file or results dir)')
    parser.add_argument('--model', help='Model file for prediction mode')
    parser.add_argument('--params', help='Training parameters JSON file')
    
    args = parser.parse_args()
    
    # Load input data
    with open(args.input, 'r') as f:
        data = json.load(f)
    
    model = DividendPayoutRatingModel()
    
    if args.mode == 'train':
        # Load parameters if provided
        params = {}
        if args.params:
            with open(args.params, 'r') as f:
                params = json.load(f)
        
        # Train model
        results = model.train(data)
        
        # Save model
        model.save_model(args.output)
        
        # Save training results
        results_file = args.output.replace('.joblib', '_training_results.json')
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"✅ Training results saved to {results_file}")
        
    elif args.mode == 'predict':
        # Load model
        if not args.model:
            raise ValueError("--model required for prediction mode")
        
        model.load_model(args.model)
        
        # Generate predictions
        predictions = model.predict(data)
        
        # Save predictions
        import os
        output_file = os.path.join(args.output, 'payout_rating_predictions.json')
        with open(output_file, 'w') as f:
            json.dump(predictions, f, indent=2)
        
        print(f"✅ Predictions saved to {output_file}")


if __name__ == '__main__':
    main()
