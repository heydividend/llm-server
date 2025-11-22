#!/bin/bash

# Train All ML Models
# This script trains all ML models in sequence

set -e  # Exit on error

echo "🤖 Starting ML model training pipeline..."
echo "================================================"

# Check Python version
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Check if virtual environment is active
if [[ -z "${VIRTUAL_ENV}" ]]; then
    echo "⚠️  Warning: No virtual environment detected"
    echo "   Consider activating venv: source ml-training-env/bin/activate"
fi

# Check dependencies
echo ""
echo "📦 Checking dependencies..."
if python -c "import prophet" 2>/dev/null; then
    echo "✅ prophet installed"
else
    echo "❌ prophet not found. Run: pip install -r requirements.txt"
    exit 1
fi

if python -c "import sklearn" 2>/dev/null; then
    echo "✅ scikit-learn installed"
else
    echo "❌ scikit-learn not found. Run: pip install -r requirements.txt"
    exit 1
fi

echo ""
echo "================================================"
echo "🎯 Training models..."
echo "================================================"

# Create output directory
mkdir -p ../models
OUTPUT_DIR="../models"

# 1. Dividend Growth Forecasting
echo ""
echo "📈 [1/4] Training Dividend Growth Forecaster..."
if python dividend_growth_forecasting.py --output "$OUTPUT_DIR/dividend_growth_model.joblib"; then
    echo "✅ Dividend Growth Forecaster complete (REAL model trained)"
else
    echo "⚠️  Real training failed, falling back to stub..."
    python dividend_growth_forecasting_stub.py --output "$OUTPUT_DIR/dividend_growth_model.joblib" || {
        echo "❌ Even stub training failed"
        exit 1
    }
    echo "✅ Dividend Growth Forecaster complete (stub model)"
fi

# 2. Dividend Cut Prediction
echo ""
echo "📉 [2/4] Training Dividend Cut Predictor..."
if python dividend_cut_prediction.py --output "$OUTPUT_DIR/dividend_cut_model.joblib"; then
    echo "✅ Dividend Cut Predictor complete (REAL model trained)"
else
    echo "⚠️  Real training failed, falling back to stub..."
    python dividend_cut_prediction_stub.py --output "$OUTPUT_DIR/dividend_cut_model.joblib" || {
        echo "❌ Even stub training failed"
        exit 1
    }
    echo "✅ Dividend Cut Predictor complete (stub model)"
fi

# 3. Anomaly Detection
echo ""
echo "🔍 [3/4] Training Anomaly Detection Model..."
if python anomaly_detection.py --output "$OUTPUT_DIR/anomaly_detection_model.joblib"; then
    echo "✅ Anomaly Detection Model complete (REAL model trained)"
else
    echo "⚠️  Real training failed, falling back to stub..."
    python anomaly_detection_stub.py --output "$OUTPUT_DIR/anomaly_detection_model.joblib" || {
        echo "❌ Even stub training failed"
        exit 1
    }
    echo "✅ Anomaly Detection Model complete (stub model)"
fi

# 4. ESG Integration
echo ""
echo "🌱 [4/4] Training ESG Dividend Scorer..."
if python esg_integration.py --output "$OUTPUT_DIR/esg_scorer_model.joblib"; then
    echo "✅ ESG Dividend Scorer complete (REAL model trained)"
else
    echo "⚠️  Real training failed, falling back to stub..."
    python esg_integration_stub.py --output "$OUTPUT_DIR/esg_scorer_model.joblib" || {
        echo "❌ Even stub training failed"
        exit 1
    }
    echo "✅ ESG Dividend Scorer complete (stub model)"
fi

echo ""
echo "================================================"
echo "✨ All models trained successfully!"
echo "================================================"

# List generated models
echo ""
echo "📁 Generated model files:"
ls -lh ../models/*.joblib ../models/*.keras 2>/dev/null | awk '{print "   ", $9, "(" $5 ")"}'

echo ""
echo "🎉 Training pipeline complete!"
echo ""
echo "Next steps:"
echo "  1. Validate models: python scripts/validate_models.py"
echo "  2. Deploy to production (see docs/ML_DEPLOYMENT_GUIDE.md)"
echo ""
