#!/usr/bin/env python3
"""
Multi-Factor Risk Model - Fama-French 5-Factor Analysis
Analyzes portfolio factor exposures and attribution
Based on MSCI Barra / SimCorp Axioma research
"""

import argparse
import json
import os
import sys
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any

warnings.filterwarnings('ignore')

try:
    import pandas as pd
    import numpy as np
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import r2_score
    import joblib
except ImportError as e:
    print(f"Error importing required packages: {e}")
    sys.exit(1)


class FactorRiskModel:
    """
    Multi-factor risk model for portfolio analysis
    Implements Fama-French 5-factor + additional factors
    """
    
    def __init__(self):
        """Initialize factor risk model"""
        self.factors = [
            'MKT-RF',      # Market risk premium
            'SMB',         # Size (Small Minus Big)
            'HML',         # Value (High Minus Low book-to-market)
            'RMW',         # Profitability (Robust Minus Weak)
            'CMA',         # Investment (Conservative Minus Aggressive)
            'MOM',         # Momentum (Carhart addition)
            'QMJ',         # Quality Minus Junk
            'BAB',         # Betting Against Beta
        ]
        self.factor_model = None
        self.factor_loadings = {}
        self.factor_data = None
        
    def load_factor_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Load factor return data (would normally fetch from Kenneth French library)
        For now, generates synthetic data for demonstration
        """
        print(f"📊 Loading factor data from {start_date} to {end_date}...")
        
        # In production, fetch from:
        # https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html
        
        # Generate date range
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Synthetic factor returns (replace with real data in production)
        np.random.seed(42)
        factor_data = {
            'date': dates,
            'MKT-RF': np.random.normal(0.0004, 0.01, len(dates)),  # ~10% annual return, 16% vol
            'SMB': np.random.normal(0.0001, 0.005, len(dates)),
            'HML': np.random.normal(0.0001, 0.005, len(dates)),
            'RMW': np.random.normal(0.0002, 0.004, len(dates)),
            'CMA': np.random.normal(0.0001, 0.004, len(dates)),
            'MOM': np.random.normal(0.0003, 0.008, len(dates)),
            'QMJ': np.random.normal(0.0002, 0.006, len(dates)),
            'BAB': np.random.normal(0.0001, 0.005, len(dates)),
            'RF': np.random.normal(0.00001, 0.0001, len(dates)),  # Risk-free rate
        }
        
        self.factor_data = pd.DataFrame(factor_data)
        return self.factor_data
    
    def calculate_factor_exposures(self, portfolio_returns: pd.Series) -> Dict:
        """
        Perform factor regression to calculate portfolio's factor exposures
        
        Returns:
            Dict with factor loadings (betas) and statistics
        """
        print("📊 Calculating factor exposures...")
        
        if self.factor_data is None:
            raise ValueError("Factor data not loaded. Call load_factor_data() first.")
        
        # Align dates
        df = pd.DataFrame({
            'portfolio_return': portfolio_returns,
            'date': portfolio_returns.index
        })
        
        merged = pd.merge(df, self.factor_data, on='date', how='inner')
        
        # Calculate excess returns
        merged['excess_return'] = merged['portfolio_return'] - merged['RF']
        
        # Prepare factor matrix
        X = merged[self.factors].values
        y = merged['excess_return'].values
        
        # Run regression
        model = LinearRegression()
        model.fit(X, y)
        
        # Calculate statistics
        y_pred = model.predict(X)
        r_squared = r2_score(y, y_pred)
        residuals = y - y_pred
        residual_vol = np.std(residuals) * np.sqrt(252)  # Annualized
        
        # Factor loadings
        self.factor_loadings = dict(zip(self.factors, model.coef_))
        alpha = model.intercept_ * 252  # Annualized alpha
        
        # Factor contributions to return
        factor_returns = merged[self.factors].mean().values * 252  # Annualized
        factor_contributions = dict(zip(
            self.factors,
            model.coef_ * factor_returns
        ))
        
        # Calculate factor variances
        factor_vars = {}
        for i, factor in enumerate(self.factors):
            factor_vars[factor] = (model.coef_[i] ** 2) * (merged[factor].var() * 252)
        
        total_var = sum(factor_vars.values()) + residual_vol ** 2
        
        return {
            'factor_loadings': self.factor_loadings,
            'alpha_annualized': float(alpha),
            'r_squared': float(r_squared),
            'residual_volatility': float(residual_vol),
            'factor_contributions': factor_contributions,
            'factor_variances': factor_vars,
            'total_variance': float(total_var),
            'variance_explained': float(r_squared)
        }
    
    def decompose_risk(self, portfolio_returns: pd.Series) -> Dict:
        """
        Decompose portfolio risk into systematic and idiosyncratic components
        """
        exposures = self.calculate_factor_exposures(portfolio_returns)
        
        # Calculate risk decomposition
        systematic_risk = np.sqrt(sum(exposures['factor_variances'].values()))
        idiosyncratic_risk = exposures['residual_volatility']
        total_risk = np.sqrt(exposures['total_variance'])
        
        return {
            'total_risk': float(total_risk),
            'systematic_risk': float(systematic_risk),
            'idiosyncratic_risk': float(idiosyncratic_risk),
            'systematic_percent': float(100 * systematic_risk / total_risk),
            'idiosyncratic_percent': float(100 * idiosyncratic_risk / total_risk),
            'factor_contributions': exposures['factor_variances']
        }
    
    def analyze_portfolio(self, portfolio_data: List[Dict]) -> Dict:
        """
        Full factor analysis of portfolio
        
        Args:
            portfolio_data: List of holdings with symbols, weights, returns
        """
        print("🔍 Performing factor analysis...")
        
        df = pd.DataFrame(portfolio_data)
        
        # Calculate portfolio returns (weighted average)
        if 'returns' in df.columns and 'weight' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            portfolio_returns = df.groupby('date').apply(
                lambda x: (x['returns'] * x['weight']).sum()
            )
        else:
            raise ValueError("Portfolio data must include 'returns' and 'weight' columns")
        
        # Load factor data for the period
        start_date = df['date'].min()
        end_date = df['date'].max()
        self.load_factor_data(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        
        # Calculate factor exposures
        exposures = self.calculate_factor_exposures(portfolio_returns)
        
        # Risk decomposition
        risk_decomp = self.decompose_risk(portfolio_returns)
        
        # Factor tilts (compare to market-neutral)
        tilts = self._calculate_factor_tilts(exposures['factor_loadings'])
        
        return {
            'factor_exposures': exposures,
            'risk_decomposition': risk_decomp,
            'factor_tilts': tilts,
            'analysis_period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': (end_date - start_date).days
            }
        }
    
    def _calculate_factor_tilts(self, loadings: Dict) -> Dict:
        """Classify factor tilts as overweight/underweight"""
        tilts = {}
        
        # Benchmarks (market-neutral = 1.0 for MKT-RF, 0.0 for others)
        benchmarks = {
            'MKT-RF': 1.0,
            'SMB': 0.0,
            'HML': 0.0,
            'RMW': 0.0,
            'CMA': 0.0,
            'MOM': 0.0,
            'QMJ': 0.0,
            'BAB': 0.0,
        }
        
        for factor, loading in loadings.items():
            benchmark = benchmarks.get(factor, 0.0)
            diff = loading - benchmark
            
            if abs(diff) < 0.1:
                tilt = 'neutral'
            elif diff > 0.3:
                tilt = 'strong_overweight'
            elif diff > 0.1:
                tilt = 'overweight'
            elif diff < -0.3:
                tilt = 'strong_underweight'
            else:
                tilt = 'underweight'
            
            tilts[factor] = {
                'loading': float(loading),
                'benchmark': float(benchmark),
                'difference': float(diff),
                'tilt': tilt
            }
        
        return tilts
    
    def generate_recommendations(self, analysis: Dict) -> List[str]:
        """Generate actionable recommendations based on factor analysis"""
        recommendations = []
        
        tilts = analysis['factor_tilts']
        risk = analysis['risk_decomposition']
        
        # Market exposure
        if tilts['MKT-RF']['tilt'] in ['strong_overweight', 'overweight']:
            recommendations.append("Portfolio has high market beta - consider hedging in downturns")
        elif tilts['MKT-RF']['tilt'] in ['strong_underweight', 'underweight']:
            recommendations.append("Portfolio has low market beta - may underperform in bull markets")
        
        # Size factor
        if tilts['SMB']['tilt'] in ['strong_overweight', 'overweight']:
            recommendations.append("Overweight small-cap exposure - higher growth potential but more volatile")
        
        # Value factor
        if tilts['HML']['tilt'] in ['strong_overweight', 'overweight']:
            recommendations.append("Strong value tilt - may benefit from value recovery")
        elif tilts['HML']['tilt'] in ['strong_underweight', 'underweight']:
            recommendations.append("Growth-oriented portfolio - momentum-driven returns")
        
        # Quality factor
        if tilts['QMJ']['tilt'] in ['strong_overweight', 'overweight']:
            recommendations.append("High-quality holdings - defensive characteristics")
        
        # Risk concentration
        if risk['idiosyncratic_percent'] > 60:
            recommendations.append("High idiosyncratic risk - consider diversifying across more factors")
        
        return recommendations
    
    def save(self, path: str):
        """Save factor model"""
        model_data = {
            'factors': self.factors,
            'factor_loadings': self.factor_loadings,
        }
        joblib.dump(model_data, path)
        print(f"💾 Factor model saved to {path}")


def main():
    parser = argparse.ArgumentParser(description='Analyze Portfolio Factor Risk')
    parser.add_argument('--data', required=True, help='Path to portfolio data JSON')
    parser.add_argument('--output', required=True, help='Output directory')
    
    args = parser.parse_args()
    
    # Load data
    with open(args.data, 'r') as f:
        portfolio_data = json.load(f)
    
    print(f"📚 Loaded portfolio data with {len(portfolio_data)} records")
    
    # Analyze
    model = FactorRiskModel()
    analysis = model.analyze_portfolio(portfolio_data)
    recommendations = model.generate_recommendations(analysis)
    
    # Save model
    model_path = os.path.join(args.output, 'factor_risk_model.joblib')
    model.save(model_path)
    
    # Save results
    results = {
        'analysis': analysis,
        'recommendations': recommendations,
        'timestamp': datetime.now().isoformat()
    }
    
    results_path = os.path.join(args.output, 'factor_analysis_results.json')
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"✅ Factor analysis complete!")
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
