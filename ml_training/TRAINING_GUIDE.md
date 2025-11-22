# ML Training Guide

Complete guide for training and exporting ML models for HeyDividend.

## Prerequisites

### Local Training Environment

```bash
# Create isolated Python environment
python -m venv ml-training-env
source ml-training-env/bin/activate  # Linux/Mac
# or
ml-training-env\Scripts\activate  # Windows

# Install all training dependencies
pip install prophet scikit-learn statsmodels pandas joblib numpy scipy matplotlib
```

### Required Dependencies

Create `requirements.txt`:
```
prophet>=1.1.7
scikit-learn>=1.7.2
statsmodels>=0.14.5
pandas>=2.3.2
joblib>=1.5.2
numpy>=1.26.4
scipy>=1.16.2
matplotlib>=3.10.7
```

Install:
```bash
pip install -r requirements.txt
```

## Available Training Scripts

### 1. Dividend Growth Forecasting

**Script:** `dividend_growth_forecasting.py`

Predicts future dividend growth using time series and regression models.

```bash
python dividend_growth_forecasting.py
```

**Outputs:**
- `../models/dividend_growth_forecaster.joblib` - Main model
- `../models/dividend_growth_forecaster_lstm.keras` - LSTM variant
- `../data/dividend_growth_training.json` - Training metadata

**Features Used:**
- Historical dividend amounts
- Growth rates (1yr, 3yr, 5yr)
- Payout ratios
- Earnings stability
- Sector trends

### 2. Dividend Cut Prediction

**Script:** `dividend_cut_prediction.py`

Binary classifier for dividend cut risk.

```bash
python dividend_cut_prediction.py
```

**Outputs:**
- `../models/dividend_cut_predictor.joblib`
- `../data/dividend_cut_training.json`

**Features Used:**
- Payout ratio trends
- Cash flow stability
- Debt levels
- Historical cut frequency
- Sector risk

### 3. Anomaly Detection

**Script:** `anomaly_detection.py`

Detects unusual dividend patterns.

```bash
python anomaly_detection.py
```

**Outputs:**
- `../models/ensemble_anomaly_detection_model.joblib`
- `../models/ensemble_training_results.json`

**Use Cases:**
- Identify data quality issues
- Detect market anomalies
- Flag unusual distribution patterns

### 4. ESG Integration

**Script:** `esg_integration.py`

Scores dividend sustainability based on ESG factors.

```bash
python esg_integration.py
```

**Outputs:**
- `../models/esg_dividend_scorer.joblib`
- `../data/esg_training.json`

## Training Workflow

### Step 1: Prepare Training Data

Fetch data from production database:

```bash
# Connect to production DB (read-only)
export DATABASE_URL="your-azure-connection-string"

# Run data export script
python scripts/export_training_data.py
```

This creates:
- `../data/training_data.json` - Features
- `../data/training_params.json` - Hyperparameters

### Step 2: Train Models

Train all models:
```bash
# Train each model
python dividend_growth_forecasting.py
python dividend_cut_prediction.py
python anomaly_detection.py
python esg_integration.py

# Or train all at once
./train_all_models.sh
```

### Step 3: Validate Models

Check model performance:

```bash
python test_dependencies.py  # Verify installation
python scripts/validate_models.py  # Test predictions
```

### Step 4: Export for Production

Models are automatically saved to `../models/`:

```bash
ls -lh ../models/
# dividend_cut_predictor.joblib
# dividend_growth_forecaster.joblib
# ensemble_anomaly_detection_model.joblib
# esg_dividend_scorer.joblib
```

## Model Export Format

### Scikit-learn Models

```python
import joblib
from sklearn.ensemble import RandomForestClassifier

# Train model
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

# Export
joblib.dump(model, '../models/my_model.joblib')

# Load (in production)
model = joblib.load('../models/my_model.joblib')
predictions = model.predict(X_test)
```

### Prophet Models

```python
from prophet import Prophet
import joblib

# Train model
model = Prophet()
model.fit(df)

# Export
joblib.dump(model, '../models/prophet_model.joblib')

# Load (in production)
model = joblib.load('../models/prophet_model.joblib')
future = model.make_future_dataframe(periods=365)
forecast = model.predict(future)
```

### Keras/TensorFlow Models

```python
from tensorflow import keras

# Train model
model = keras.Sequential([...])
model.compile(...)
model.fit(X_train, y_train)

# Export
model.save('../models/lstm_model.keras')

# Load (in production)
model = keras.models.load_model('../models/lstm_model.keras')
predictions = model.predict(X_test)
```

## Feature Engineering

### Extract Features

```python
# server/ml/data/FeatureEngineering.ts handles this
import { FeatureEngineering } from '../data/FeatureEngineering';

const features = await FeatureEngineering.extractFeatures(symbol);
```

Features include:
- Historical dividend data (10+ years)
- Growth rates (1yr, 3yr, 5yr, 10yr)
- Payout ratios
- Sector comparisons
- Market indicators

### Export Features for Python

```bash
# Export features to JSON for training
npm run export:features

# Creates: server/ml/data/features_input.json
```

## Hyperparameter Tuning

### Grid Search Example

```python
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestClassifier

# Define parameter grid
param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [10, 20, None],
    'min_samples_split': [2, 5, 10]
}

# Grid search
grid_search = GridSearchCV(
    RandomForestClassifier(),
    param_grid,
    cv=5,
    scoring='f1'
)

grid_search.fit(X_train, y_train)

# Best parameters
print(grid_search.best_params_)

# Export best model
joblib.dump(grid_search.best_estimator_, '../models/tuned_model.joblib')
```

## Testing Models

### Unit Tests

```python
# test_models.py
import joblib
import numpy as np

def test_dividend_growth_forecaster():
    model = joblib.load('../models/dividend_growth_forecaster.joblib')
    
    # Test with sample data
    X_test = np.array([[0.5, 0.3, 100, 50]])  # [growth, payout, earnings, div]
    predictions = model.predict(X_test)
    
    assert predictions.shape[0] == 1
    assert 0 <= predictions[0] <= 1  # Growth rate between 0-100%
    
test_dividend_growth_forecaster()
print("✅ Model test passed")
```

### Integration Tests

```bash
# Test model loading in production environment
npm run test:ml-models
```

## Model Versioning

### Naming Convention

```
{model_name}_v{version}_{date}.joblib

Examples:
- dividend_growth_forecaster_v1_20251015.joblib
- dividend_cut_predictor_v2_20251101.joblib
```

### Version Tracking

Create `model_versions.json`:
```json
{
  "dividend_growth_forecaster": {
    "current": "v2",
    "versions": {
      "v1": {
        "file": "dividend_growth_forecaster_v1_20251001.joblib",
        "trained": "2025-10-01",
        "accuracy": 0.85
      },
      "v2": {
        "file": "dividend_growth_forecaster_v2_20251015.joblib",
        "trained": "2025-10-15",
        "accuracy": 0.89
      }
    }
  }
}
```

## Deployment Checklist

Before deploying new models:

- [ ] Train on latest data (past 30 days)
- [ ] Validate accuracy metrics
- [ ] Test predictions on sample data
- [ ] Export with consistent naming
- [ ] Update `model_versions.json`
- [ ] Commit to repository or upload to cloud storage
- [ ] Test loading in production
- [ ] Monitor prediction performance

## Troubleshooting

### Common Issues

**Issue:** `ImportError: No module named 'sklearn'`
```bash
# Solution: Reinstall in correct environment
pip install scikit-learn==1.7.2
```

**Issue:** Model file too large (>100 MB)
```bash
# Solution: Use Git LFS
git lfs track "*.joblib"
git add .gitattributes
```

**Issue:** Version mismatch warnings
```bash
# Solution: Pin versions
pip install scikit-learn==1.7.2 joblib==1.5.2
```

**Issue:** Memory errors during training
```bash
# Solution: Reduce batch size or use incremental learning
from sklearn.linear_model import SGDClassifier
model = SGDClassifier()
model.partial_fit(X_batch, y_batch)
```

## Performance Optimization

### Model Compression

```python
# Reduce model size
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,  # Limit depth
    min_samples_split=10,  # Increase split threshold
    n_jobs=-1  # Parallel training
)
```

### Quantization (TensorFlow)

```python
import tensorflow as tf

# Convert to TensorFlow Lite
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
tflite_model = converter.convert()

# Save quantized model (smaller size)
with open('../models/model_quantized.tflite', 'wb') as f:
    f.write(tflite_model)
```

## Automated Retraining

### Cron Schedule

```bash
# crontab -e
# Retrain weekly on Sunday at 2 AM
0 2 * * 0 cd /path/to/heydividend/server/ml/training && python train_all_models.sh
```

### GitHub Actions (See ML_DEPLOYMENT_GUIDE.md Option B)

Automated pipeline with cloud deployment.

## Model Monitoring

Track model performance in production:

```typescript
// server/services/ModelMonitoringService.ts
export class ModelMonitoringService {
  async logPrediction(modelName: string, prediction: any, actual?: any) {
    // Log for drift detection
  }
  
  async checkModelDrift(modelName: string): Promise<boolean> {
    // Compare recent vs training distribution
  }
}
```

## Next Steps

1. Set up training environment
2. Run `test_dependencies.py` to verify installation
3. Train first model: `python dividend_growth_forecasting.py`
4. Validate predictions
5. Deploy to production

For deployment options, see `docs/ML_DEPLOYMENT_GUIDE.md`.
