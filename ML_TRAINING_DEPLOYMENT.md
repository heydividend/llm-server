# Harvey ML Training Pipeline - Deployment Guide

## Overview
This guide walks through deploying and running Harvey's complete ML training pipeline on Azure VM to train all 7 dividend intelligence models from scratch.

## 📦 What Was Built

### ML Models (7 Total)
1. **Dividend Quality Scorer** - RandomForest (0-100 score, A-F grade)
2. **Yield Predictor** - XGBoost (3/6/12/24 month horizons)
3. **Growth Rate Predictor** - RandomForest (annual growth %)
4. **Payout Ratio Predictor** - XGBoost (sustainability forecasting)
5. **Cut Risk Analyzer** - XGBoost Binary Classifier (cut probability)
6. **Anomaly Detector** - Isolation Forest (unusual patterns)
7. **Stock Clusterer** - KMeans (8 clusters for similarity)

### Files Created
```
ml_training/
├── train.py              # Main training script
├── validate.py           # Model validation with thresholds
├── data_extraction.py    # SQL data loading from Azure DB
├── requirements.txt      # ML dependencies
└── models/
    ├── __init__.py       # BaseModel + ModelRegistry
    ├── dividend_scorer.py
    ├── yield_predictor.py
    ├── growth_predictor.py
    ├── payout_predictor.py
    ├── cut_risk_analyzer.py
    ├── anomaly_detector.py
    └── stock_clusterer.py
```

---

## 🚀 Quick Deployment (Automated)

### Option 1: Use Deployment Script

From your Replit environment:

```bash
# Run the automated deployment
./deploy/deploy_ml_training.sh
```

This script will:
1. Package ml_training/ directory
2. Transfer to Azure VM via SCP
3. Extract to `/home/azureuser/ml-prediction-api/scripts/`
4. Install ML dependencies in conda environment
5. Create models directory structure

---

## 🔧 Manual Deployment (If Automated Fails)

### Step 1: Transfer Files to Azure VM

```bash
# From Replit terminal
cd /workspace
tar -czf ml_training.tar.gz ml_training/

# Transfer to VM
scp ml_training.tar.gz azureuser@20.81.210.213:/tmp/
```

### Step 2: SSH to Azure VM

```bash
ssh azureuser@20.81.210.213
```

### Step 3: Extract and Setup on VM

```bash
# Extract training code
cd /home/azureuser/ml-prediction-api
tar -xzf /tmp/ml_training.tar.gz
rm /tmp/ml_training.tar.gz

# Create directory structure
mkdir -p scripts
mkdir -p models

# Move training scripts to scripts directory
cp -r ml_training/* scripts/
mv ml_training ml_training_backup

# Verify structure
ls -la scripts/
ls -la models/
```

### Step 4: Install Dependencies

```bash
# Activate conda environment
source /home/azureuser/miniconda3/bin/activate
conda activate llm

# Install ML dependencies
cd /home/azureuser/ml-prediction-api/scripts
pip install -r requirements.txt
```

---

## 📊 Run Initial Training

### Train All Models

```bash
cd /home/azureuser/ml-prediction-api/scripts
conda activate llm

# Train all 7 models (takes 10-30 minutes depending on data size)
python train.py

# Expected output:
# ✓ Loading training data from Azure SQL...
# ✓ Training DividendQualityScorer...
# ✓ Training YieldPredictor...
# ✓ Training GrowthRatePredictor...
# ✓ Training PayoutRatioPredictor...
# ✓ Training CutRiskAnalyzer...
# ✓ Training AnomalyDetector...
# ✓ Training StockClusterer...
# ✓ All models trained successfully!
```

### Train Individual Model

```bash
# Train only one model
python train.py --model dividend_scorer

# Available models:
# - dividend_scorer
# - yield_predictor
# - growth_predictor
# - payout_predictor
# - cut_risk_analyzer
# - anomaly_detector
# - stock_clusterer
```

### Validate Models

```bash
# Validate all models (ensures accuracy thresholds met)
python validate.py

# Expected output:
# ✓ DividendQualityScorer: R² = 0.85 (PASS)
# ✓ YieldPredictor: R² = 0.78 (PASS)
# ✓ GrowthRatePredictor: R² = 0.72 (PASS)
# ✓ PayoutRatioPredictor: R² = 0.81 (PASS)
# ✓ CutRiskAnalyzer: Accuracy = 0.87 (PASS)
# ✓ AnomalyDetector: Silhouette = 0.68 (PASS)
# ✓ StockClusterer: Silhouette = 0.72 (PASS)

# Validate individual model
python validate.py --model cut_risk_analyzer
```

---

## ✅ Verify Model Files Created

```bash
# Check model files were saved
ls -lh /home/azureuser/ml-prediction-api/models/

# Expected output:
# dividend_scorer_model.pkl
# yield_predictor_3_months.pkl
# yield_predictor_6_months.pkl
# yield_predictor_12_months.pkl
# yield_predictor_24_months.pkl
# growth_predictor_model.pkl
# payout_predictor_12_months.pkl
# cut_risk_model.pkl
# anomaly_detector_model.pkl
# stock_clusterer_model.pkl
```

---

## 🔄 Load Models into Intelligence Engine

### Option 1: Restart Intelligence Engine Service

```bash
# Restart the service to load new models
sudo systemctl restart harvey-intelligence.service

# Or if using old service name:
sudo systemctl restart ml-api.service
```

### Option 2: Update Intelligence Engine to Auto-Load

The Intelligence Engine at `/home/azureuser/ml-prediction-api/main.py` needs to be updated to load models from the `models/` directory on startup.

---

## 🧪 Test End-to-End

### Step 1: Check Intelligence Engine Health

```bash
# Verify service is running
curl http://127.0.0.1:9000/api/internal/ml/health

# Expected output:
{
  "status": "healthy",
  "models_loaded": 10,
  "available_models": [
    "dividend_scorer",
    "yield_predictor_3m",
    "yield_predictor_6m",
    "yield_predictor_12m",
    "yield_predictor_24m",
    "growth_predictor",
    "payout_predictor",
    "cut_risk_analyzer",
    "anomaly_detector",
    "stock_clusterer"
  ]
}
```

### Step 2: Test Model Predictions

```bash
# Test dividend scoring endpoint
curl -X POST http://127.0.0.1:9000/api/internal/ml/score/symbol \
  -H "X-Internal-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL"}'

# Expected output:
{
  "success": true,
  "data": {
    "symbol": "AAPL",
    "score": 87.5,
    "grade": "A",
    "confidence": 0.92
  }
}
```

### Step 3: Test from Harvey Backend

```bash
# On the VM, test Harvey's ML integration
curl -X POST http://20.81.210.213/chat \
  -H "Authorization: Bearer YOUR_HARVEY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is your dividend quality score for AAPL?",
    "stream": false
  }'
```

---

## 🤖 Enable Nightly Training Automation

Now that training scripts exist, update the automation paths:

### Step 1: Update Training Automation Script

```bash
# Edit the training script
sudo nano /opt/harvey-intelligence/train_daily.sh

# Update these paths (should already be correct):
SCRIPTS_DIR="/home/azureuser/ml-prediction-api/scripts"
MODEL_DIR="/home/azureuser/ml-prediction-api/models"
```

### Step 2: Test Manual Training Run

```bash
# Test the automation script manually
sudo systemctl start harvey-training.service

# Watch logs
sudo journalctl -u harvey-training.service -f

# Expected output:
# 📦 Backing up current models...
# 🚀 Starting model training...
# ✅ Conda environment activated: llm
# ✅ Training completed successfully
# 🔍 Validating new models...
# ✅ Model validation passed
# 🔄 Restarting Intelligence Engine...
# ✅ Intelligence Engine is healthy
# ✅ Daily training completed successfully!
```

### Step 3: Enable Nightly Automation

```bash
# Verify timer is enabled
sudo systemctl status harvey-training.timer

# Should show:
# Active: active (waiting)
# Trigger: Next run at 02:00:00 UTC

# If not enabled:
sudo systemctl enable harvey-training.timer
sudo systemctl start harvey-training.timer
```

---

## 📋 Troubleshooting

### Problem: Training Fails with "No Data"

**Solution:** Check database connection

```bash
# Test database connection
cd /home/azureuser/ml-prediction-api/scripts
python -c "from data_extraction import DataExtractor; de = DataExtractor(); print(de.extract_dividend_data().shape)"

# Should show: (rows, columns) e.g., (25000, 15)
```

### Problem: Model Validation Fails

**Solution:** Check validation thresholds

```bash
# Run validation with verbose output
python validate.py --verbose

# Adjust thresholds if needed (edit validate.py):
# R2_THRESHOLD = 0.65  # Lower if needed
# ACCURACY_THRESHOLD = 0.75
```

### Problem: Intelligence Engine Can't Load Models

**Solution:** Check model file paths

```bash
# Verify models exist
ls -la /home/azureuser/ml-prediction-api/models/*.pkl

# Check Intelligence Engine logs
sudo journalctl -u harvey-intelligence.service -n 50

# Look for model loading errors
```

### Problem: Training Takes Too Long

**Solution:** Train models individually

```bash
# Train fastest models first
python train.py --model dividend_scorer  # ~2 min
python train.py --model anomaly_detector  # ~1 min
python train.py --model stock_clusterer   # ~3 min

# Train slower models separately
python train.py --model yield_predictor   # ~10 min
python train.py --model cut_risk_analyzer # ~8 min
```

---

## 📊 Next Steps After Deployment

1. ✅ **Verify All Models Trained** - Check models/ directory
2. ✅ **Validate Model Accuracy** - Run validate.py
3. ✅ **Test Intelligence Engine** - Curl health endpoint
4. ✅ **Test Harvey Integration** - Make prediction requests
5. ✅ **Enable Nightly Training** - Systemd timer active
6. ✅ **Monitor First Automated Run** - Check logs at 2 AM UTC

---

## 🎯 Success Criteria

- ✅ All 7 models trained (10 .pkl files total with horizons)
- ✅ Validation passes for all models (R² > 0.7, accuracy > 0.80)
- ✅ Intelligence Engine loads models successfully
- ✅ Harvey can make ML predictions via API
- ✅ Nightly training automation runs without errors
- ✅ Models auto-update and Intelligence Engine restarts

---

## 📞 Support

If you encounter issues:

1. **Check logs**: `sudo journalctl -u harvey-training.service -f`
2. **Test database**: Run data extraction script independently
3. **Verify environment**: `conda activate llm && python --version`
4. **Check disk space**: `df -h /home/azureuser`
5. **Review model files**: `ls -lh /home/azureuser/ml-prediction-api/models/`

All training scripts have comprehensive logging to help diagnose issues.
