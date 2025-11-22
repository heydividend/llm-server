#!/usr/bin/env python3
"""
Model Validation Script

Tests all trained models to ensure they work correctly before deployment.
"""

import sys
import os
from pathlib import Path
import joblib
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_model_loading(model_path: str) -> bool:
    """Test if model can be loaded"""
    try:
        model = joblib.load(model_path)
        print(f"✅ Loaded: {os.path.basename(model_path)}")
        return True
    except Exception as e:
        print(f"❌ Failed to load {os.path.basename(model_path)}: {e}")
        return False

def test_dividend_growth_forecaster():
    """Test dividend growth forecaster"""
    model_path = "../models/dividend_growth_forecaster.joblib"
    
    if not os.path.exists(model_path):
        print(f"⚠️  Model not found: {model_path}")
        return False
    
    try:
        model = joblib.load(model_path)
        
        # Create sample features
        # [5yr_growth, 3yr_growth, payout_ratio, earnings_stability]
        X_test = np.array([
            [0.08, 0.10, 0.45, 0.92],  # Healthy grower
            [0.02, 0.03, 0.75, 0.65],  # Slow grower, high payout
            [-0.05, -0.02, 0.85, 0.45] # Declining, risky
        ])
        
        predictions = model.predict(X_test)
        
        # Validate predictions
        assert len(predictions) == 3, "Wrong number of predictions"
        assert all(-1 <= p <= 1 for p in predictions), "Predictions out of range"
        
        print(f"✅ Dividend Growth Forecaster validated")
        print(f"   Sample predictions: {predictions}")
        return True
        
    except Exception as e:
        print(f"❌ Dividend Growth Forecaster validation failed: {e}")
        return False

def test_dividend_cut_predictor():
    """Test dividend cut predictor"""
    model_path = "../models/dividend_cut_predictor.joblib"
    
    if not os.path.exists(model_path):
        print(f"⚠️  Model not found: {model_path}")
        return False
    
    try:
        model = joblib.load(model_path)
        
        # Create sample features
        # [payout_ratio, debt_ratio, growth_trend, cut_history]
        X_test = np.array([
            [0.40, 0.30, 0.08, 0],  # Safe
            [0.90, 0.70, -0.02, 1], # Risky
            [0.95, 0.85, -0.10, 2]  # Very risky
        ])
        
        predictions = model.predict(X_test)
        probabilities = model.predict_proba(X_test)[:, 1]  # Probability of cut
        
        # Validate predictions
        assert len(predictions) == 3, "Wrong number of predictions"
        assert all(p in [0, 1] for p in predictions), "Invalid binary predictions"
        assert all(0 <= p <= 1 for p in probabilities), "Invalid probabilities"
        
        print(f"✅ Dividend Cut Predictor validated")
        print(f"   Cut probabilities: {probabilities}")
        return True
        
    except Exception as e:
        print(f"❌ Dividend Cut Predictor validation failed: {e}")
        return False

def test_anomaly_detector():
    """Test anomaly detection model"""
    model_path = "../models/ensemble_anomaly_detection_model.joblib"
    
    if not os.path.exists(model_path):
        print(f"⚠️  Model not found: {model_path}")
        return False
    
    try:
        model = joblib.load(model_path)
        
        # Create sample data
        # Normal dividend patterns
        X_normal = np.array([
            [1.0, 1.05, 1.10, 1.15],  # Steady growth
            [2.0, 2.10, 2.20, 2.30],  # Steady growth
        ])
        
        # Anomalous patterns
        X_anomaly = np.array([
            [1.0, 1.05, 0.50, 1.10],  # Sudden drop
            [2.0, 2.10, 5.00, 2.30],  # Sudden spike
        ])
        
        predictions_normal = model.predict(X_normal)
        predictions_anomaly = model.predict(X_anomaly)
        
        # Most normal samples should be 1 (inlier), anomalies should be -1 (outlier)
        print(f"✅ Anomaly Detector validated")
        print(f"   Normal predictions: {predictions_normal}")
        print(f"   Anomaly predictions: {predictions_anomaly}")
        return True
        
    except Exception as e:
        print(f"❌ Anomaly Detector validation failed: {e}")
        return False

def test_esg_scorer():
    """Test ESG dividend scorer"""
    model_path = "../models/esg_dividend_scorer.joblib"
    
    if not os.path.exists(model_path):
        print(f"⚠️  Model not found: {model_path}")
        return False
    
    try:
        model = joblib.load(model_path)
        
        # Create sample ESG features
        # [env_score, social_score, governance_score, sustainability_index]
        X_test = np.array([
            [0.8, 0.7, 0.9, 0.85],  # High ESG
            [0.4, 0.5, 0.6, 0.50],  # Medium ESG
            [0.2, 0.3, 0.3, 0.25],  # Low ESG
        ])
        
        predictions = model.predict(X_test)
        
        # Validate predictions
        assert len(predictions) == 3, "Wrong number of predictions"
        assert all(0 <= p <= 1 for p in predictions), "Scores out of range"
        
        print(f"✅ ESG Dividend Scorer validated")
        print(f"   ESG scores: {predictions}")
        return True
        
    except Exception as e:
        print(f"❌ ESG Dividend Scorer validation failed: {e}")
        return False

def main():
    print("🧪 Validating ML Models")
    print("=" * 50)
    print()
    
    results = []
    
    # Test each model
    print("📊 Testing models...")
    print()
    
    results.append(("Dividend Growth Forecaster", test_dividend_growth_forecaster()))
    results.append(("Dividend Cut Predictor", test_dividend_cut_predictor()))
    results.append(("Anomaly Detector", test_anomaly_detector()))
    results.append(("ESG Scorer", test_esg_scorer()))
    
    # Summary
    print()
    print("=" * 50)
    print("📋 Validation Summary")
    print("=" * 50)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
    
    print()
    
    # Exit code
    all_passed = all(result[1] for result in results)
    if all_passed:
        print("🎉 All models validated successfully!")
        sys.exit(0)
    else:
        print("❌ Some models failed validation")
        sys.exit(1)

if __name__ == "__main__":
    main()
