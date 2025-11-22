#!/usr/bin/env python3
"""
Dividend Growth Forecasting Model - Stub for GitHub Actions
Creates a minimal model for deployment
"""

import argparse
import json
import joblib
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

def main():
    parser = argparse.ArgumentParser(description='Train Dividend Growth Forecasting Model')
    parser.add_argument('--output', required=True, help='Output path for model')
    args = parser.parse_args()
    
    print("🏋️ Training Dividend Growth Forecaster (stub model)...")
    
    # Create minimal stub model
    model = Ridge(alpha=1.0)
    scaler = StandardScaler()
    
    # Train on dummy data
    X_dummy = np.random.rand(100, 12)
    y_dummy = np.random.rand(100) * 0.2 - 0.1  # -10% to +10% growth
    X_scaled = scaler.fit_transform(X_dummy)
    model.fit(X_scaled, y_dummy)
    
    # Save model
    model_data = {
        'model': model,
        'scaler': scaler,
        'feature_columns': [f'feature_{i}' for i in range(12)],
        'use_deep_learning': False,
        'lookback_periods': 12,
        'forecast_horizon': 4,
        'version': '1.0-stub'
    }
    joblib.dump(model_data, args.output)
    
    print(f"✅ Stub model saved to {args.output}")
    print("📊 Model type: Ridge (stub)")
    print("⚠️  Note: This is a stub model for deployment testing")

if __name__ == '__main__':
    main()
