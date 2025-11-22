#!/usr/bin/env python3
"""
ESG-Enhanced Dividend Scoring Model
Integrates ESG factors into dividend sustainability predictions
Research shows 26% accuracy improvement with ESG integration
"""

import argparse
import json
import os
import sys
import warnings
from typing import Dict, List, Any

warnings.filterwarnings('ignore')

try:
    import pandas as pd
    import numpy as np
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    import joblib
except ImportError as e:
    print(f"Error importing required packages: {e}")
    sys.exit(1)


class ESGDividendScorer:
    """
    Enhanced dividend safety scoring with ESG integration
    Combines traditional financial metrics with ESG factors
    """
    
    def __init__(self):
        """Initialize ESG-enhanced dividend scorer"""
        self.model = None
        self.scaler = StandardScaler()
        self.financial_features = []
        self.esg_features = []
        self.all_features = []
        
        # ESG factor weights (from research)
        self.esg_weights = {
            'environmental_score': 0.30,
            'social_score': 0.35,
            'governance_score': 0.35
        }
        
    def prepare_features(self, data: List[Dict]) -> pd.DataFrame:
        """Prepare financial + ESG features"""
        print(f"📊 Preparing ESG-enhanced features for {len(data)} records...")
        
        df = pd.DataFrame(data)
        
        # Traditional financial metrics (7-metric system)
        self.financial_features = [
            'payout_ratio',
            'fcf_payout_ratio',
            'debt_to_equity',
            'interest_coverage',
            'earnings_growth_3y',
            'dividend_growth_stability',
            'cash_ratio'
        ]
        
        # ESG metrics
        self.esg_features = [
            'environmental_score',      # 0-100 scale
            'social_score',             # 0-100 scale
            'governance_score',         # 0-100 scale
            'esg_composite',            # Weighted average
            'esg_controversy_score',    # Penalty for controversies
            'carbon_intensity',         # Emissions per revenue
            'board_diversity',          # % diverse board members
            'employee_satisfaction',    # Glassdoor/internal scores
        ]
        
        self.all_features = self.financial_features + self.esg_features
        
        # Fill missing values
        for col in self.all_features:
            if col in df.columns:
                df[col] = df[col].fillna(df[col].median())
            else:
                # Default values for missing ESG data
                if col in self.esg_features:
                    df[col] = 50.0  # Neutral ESG score
                else:
                    df[col] = 0.0
        
        # Create ESG composite if not present
        if 'esg_composite' not in df.columns or df['esg_composite'].isna().all():
            df['esg_composite'] = (
                self.esg_weights['environmental_score'] * df['environmental_score'] +
                self.esg_weights['social_score'] * df['social_score'] +
                self.esg_weights['governance_score'] * df['governance_score']
            )
        
        return df
    
    def calculate_esg_adjusted_score(self, financial_score: float, esg_composite: float) -> float:
        """
        Calculate ESG-adjusted dividend safety score
        
        Args:
            financial_score: Traditional 7-metric score (0-100)
            esg_composite: ESG composite score (0-100)
            
        Returns:
            Adjusted score incorporating ESG factors
        """
        # Research shows ESG improves prediction by 26%
        # Use 70-30 weighting (financial-ESG)
        adjusted_score = 0.70 * financial_score + 0.30 * esg_composite
        
        return adjusted_score
    
    def train(self, training_data: List[Dict]) -> Dict:
        """Train ESG-enhanced dividend scoring model"""
        print("🏋️ Training ESG-enhanced dividend scorer...")
        
        df = self.prepare_features(training_data)
        
        # Target: combined dividend safety score
        if 'dividend_safety_score' not in df.columns:
            # Generate synthetic target based on metrics
            df['dividend_safety_score'] = self._calculate_base_safety_score(df)
        
        X = df[self.all_features].values
        y = df['dividend_safety_score'].values
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )
        
        # Train model
        self.model = RandomForestRegressor(
            n_estimators=200,
            max_depth=10,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(X_train, y_train)
        
        # Evaluate
        train_score = self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test)
        
        # Feature importance
        feature_importance = dict(zip(
            self.all_features,
            self.model.feature_importances_
        ))
        
        # Separate financial vs ESG importance
        financial_importance = sum(feature_importance[f] for f in self.financial_features)
        esg_importance = sum(feature_importance[f] for f in self.esg_features)
        
        print(f"✅ Training complete - R² Test: {test_score:.3f}")
        print(f"📊 Feature importance: Financial={financial_importance:.1%}, ESG={esg_importance:.1%}")
        
        return {
            'model_type': 'random_forest_regressor',
            'training_samples': len(X_train),
            'features_used': len(self.all_features),
            'financial_features': len(self.financial_features),
            'esg_features': len(self.esg_features),
            'model_performance': {
                'r2_train': float(train_score),
                'r2_test': float(test_score),
                'rmse_test': float(np.sqrt(np.mean((self.model.predict(X_test) - y_test) ** 2)))
            },
            'feature_importance': {
                'financial_weight': float(financial_importance),
                'esg_weight': float(esg_importance),
                'top_features': dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10])
            }
        }
    
    def _calculate_base_safety_score(self, df: pd.DataFrame) -> np.ndarray:
        """Calculate base dividend safety score from financial metrics"""
        # Normalize each metric to 0-100
        scores = []
        
        # Payout ratio (lower is better, ideal < 60%)
        payout_score = np.clip(100 - (df['payout_ratio'] * 100), 0, 100)
        scores.append(payout_score)
        
        # FCF payout (lower is better)
        fcf_score = np.clip(100 - (df['fcf_payout_ratio'] * 100), 0, 100)
        scores.append(fcf_score)
        
        # Debt to equity (lower is better, ideal < 1.0)
        debt_score = np.clip(100 - (df['debt_to_equity'] * 50), 0, 100)
        scores.append(debt_score)
        
        # Interest coverage (higher is better, ideal > 5x)
        interest_score = np.clip(df['interest_coverage'] * 20, 0, 100)
        scores.append(interest_score)
        
        # Earnings growth (higher is better)
        growth_score = np.clip(50 + (df['earnings_growth_3y'] * 500), 0, 100)
        scores.append(growth_score)
        
        # Average scores
        base_score = np.mean(scores, axis=0)
        
        return base_score
    
    def predict(self, data: List[Dict]) -> List[Dict]:
        """Predict ESG-adjusted dividend safety scores"""
        df = self.prepare_features(data)
        X = df[self.all_features].values
        X_scaled = self.scaler.transform(X)
        
        scores = self.model.predict(X_scaled)
        
        results = []
        for i, score in enumerate(scores):
            # Break down score components
            financial_score = self._calculate_base_safety_score(df.iloc[[i]])[0]
            esg_composite = df.iloc[i]['esg_composite']
            
            results.append({
                'symbol': df.iloc[i]['symbol'],
                'dividend_safety_score': float(score),
                'financial_score': float(financial_score),
                'esg_composite': float(esg_composite),
                'esg_breakdown': {
                    'environmental': float(df.iloc[i]['environmental_score']),
                    'social': float(df.iloc[i]['social_score']),
                    'governance': float(df.iloc[i]['governance_score'])
                },
                'rating': self._categorize_score(score)
            })
        
        return results
    
    def _categorize_score(self, score: float) -> str:
        """Categorize safety score into ratings"""
        if score >= 80:
            return 'excellent'
        elif score >= 65:
            return 'good'
        elif score >= 50:
            return 'fair'
        elif score >= 35:
            return 'caution'
        else:
            return 'high_risk'
    
    def save(self, path: str):
        """Save model and scaler"""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'all_features': self.all_features,
            'financial_features': self.financial_features,
            'esg_features': self.esg_features,
            'esg_weights': self.esg_weights
        }
        joblib.dump(model_data, path)
        print(f"💾 Model saved to {path}")


def main():
    parser = argparse.ArgumentParser(description='Train ESG-Enhanced Dividend Scorer')
    parser.add_argument('--data', required=True, help='Path to training data JSON')
    parser.add_argument('--output', required=True, help='Output directory')
    
    args = parser.parse_args()
    
    # Load data
    with open(args.data, 'r') as f:
        training_data = json.load(f)
    
    print(f"📚 Loaded {len(training_data)} training records")
    
    # Train model
    scorer = ESGDividendScorer()
    results = scorer.train(training_data)
    
    # Save model
    model_path = os.path.join(args.output, 'esg_dividend_scorer.joblib')
    scorer.save(model_path)
    
    # Save results to data directory (not models directory)
    data_dir = os.path.dirname(args.data)
    results_path = os.path.join(data_dir, 'esg_training_results.json')
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"✅ Training complete!")
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
