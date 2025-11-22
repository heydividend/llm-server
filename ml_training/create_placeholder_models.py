#!/usr/bin/env python3
"""
Create placeholder ML models for RegressionService and TimeSeriesService
This ensures the services can initialize properly while real models are being trained
"""

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
import os
import sys

def create_placeholder_models():
    # Get models directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(script_dir, '..', 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    # Create placeholder training data
    np.random.seed(42)
    X_train = np.random.rand(100, 10)
    y_train = np.random.rand(100)
    
    print("🔧 Creating placeholder ML models...")
    print()
    print("Creating yield regression models...")
    
    # Yield Regressor - Random Forest
    rf_model = RandomForestRegressor(n_estimators=10, max_depth=5, random_state=42)
    rf_model.fit(X_train, y_train)
    rf_path = os.path.join(models_dir, 'yield_regressor_random_forest.joblib')
    joblib.dump(rf_model, rf_path)
    print(f"  ✅ Created: yield_regressor_random_forest.joblib")
    
    # Yield Regressor - XGBoost placeholder (using Linear Regression)
    xgb_model = LinearRegression()
    xgb_model.fit(X_train, y_train)
    xgb_path = os.path.join(models_dir, 'yield_regressor_xgboost.joblib')
    joblib.dump(xgb_model, xgb_path)
    print(f"  ✅ Created: yield_regressor_xgboost.joblib")
    
    # Yield Regressor - SVR placeholder (using Linear Regression)
    svr_model = LinearRegression()
    svr_model.fit(X_train, y_train)
    svr_path = os.path.join(models_dir, 'yield_regressor_svr.joblib')
    joblib.dump(svr_model, svr_path)
    print(f"  ✅ Created: yield_regressor_svr.joblib")
    
    print()
    print("Creating time series forecasting models...")
    
    # Payout Forecaster - ARIMA placeholder
    arima_model = LinearRegression()
    arima_model.fit(X_train, y_train)
    arima_path = os.path.join(models_dir, 'payout_forecaster_arima.joblib')
    joblib.dump(arima_model, arima_path)
    print(f"  ✅ Created: payout_forecaster_arima.joblib")
    
    # Payout Forecaster - SARIMA placeholder
    sarima_model = RandomForestRegressor(n_estimators=5, max_depth=3, random_state=42)
    sarima_model.fit(X_train, y_train)
    sarima_path = os.path.join(models_dir, 'payout_forecaster_sarima.joblib')
    joblib.dump(sarima_model, sarima_path)
    print(f"  ✅ Created: payout_forecaster_sarima.joblib")
    
    # Growth Rate Predictor
    growth_model = RandomForestRegressor(n_estimators=10, max_depth=5, random_state=42)
    growth_model.fit(X_train, y_train)
    growth_path = os.path.join(models_dir, 'growth_rate_predictor.joblib')
    joblib.dump(growth_model, growth_path)
    print(f"  ✅ Created: growth_rate_predictor.joblib")
    
    print()
    print("✅ All placeholder models created successfully!")
    print(f"   Location: {models_dir}")
    print()
    print("⚠️  Note: These are placeholder models for development.")
    print("   For production, train proper models with real dividend data.")
    
    # List all models
    model_files = [f for f in os.listdir(models_dir) if f.endswith('.joblib')]
    print()
    print(f"📦 Total models available: {len(model_files)}")
    
    return 0

if __name__ == '__main__':
    try:
        sys.exit(create_placeholder_models())
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
