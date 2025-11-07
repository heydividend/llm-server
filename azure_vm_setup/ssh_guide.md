# Azure VM SSH Access & ML Training Guide

## VM Connection Details
- **IP Address**: 20.81.210.213
- **Ports**: 
  - Harvey API: 8001
  - ML Service: 9000
  - SSH: 22 (standard)

## 1. SSH Access Setup

### From Windows (PowerShell/Command Prompt)
```bash
ssh username@20.81.210.213
```

### From Mac/Linux Terminal
```bash
ssh username@20.81.210.213
```

### Using SSH Key (Recommended)
```bash
# If you have an SSH key
ssh -i ~/.ssh/your-azure-key.pem username@20.81.210.213
```

## 2. Initial ML Training Setup

Once connected to the VM:

```bash
# Navigate to Harvey project
cd /home/harvey/harvey-backend  # Update path as needed

# Check current ML service status
sudo systemctl status harvey-ml

# Navigate to ML training directory
cd ml_training

# Install training dependencies (if needed)
pip install -r requirements.txt

# Run initial training for all models
python train.py --all --save-dir ./models

# Validate trained models
python validate.py --model-dir ./models

# Check training logs
tail -f training.log
```

## 3. Manual Training Commands

### Train Individual Models
```bash
# Train specific models
python train.py --model dividend_scorer
python train.py --model yield_predictor
python train.py --model growth_predictor
python train.py --model payout_predictor
python train.py --model cut_risk_analyzer
python train.py --model anomaly_detector
python train.py --model stock_clusterer
```

### Train All Models
```bash
python train.py --all
```

### Validate Models
```bash
# Validate all models
python validate.py

# Validate specific model
python validate.py --model dividend_scorer
```

## 4. Check Model Performance

```bash
# View validation results
cat validation_results.json

# Check model files
ls -la models/

# Expected files after training:
# - dividend_quality_scorer.pkl
# - yield_predictor.pkl
# - growth_predictor.pkl
# - payout_predictor.pkl
# - cut_risk_analyzer.pkl
# - anomaly_detector.pkl
# - stock_clusterer.pkl
```

## 5. Restart ML Service After Training

```bash
# Restart ML service to load new models
sudo systemctl restart harvey-ml

# Check service status
sudo systemctl status harvey-ml

# View ML service logs
sudo journalctl -u harvey-ml -f
```

## 6. Test New Models

```bash
# Test ML API with new models
curl -X POST http://localhost:9000/api/internal/ml/score/symbol \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $INTERNAL_ML_API_KEY" \
  -d '{"symbols": ["AAPL", "JNJ", "O"]}'

# Check model status
curl http://localhost:9000/api/internal/ml/models/status \
  -H "X-API-Key: $INTERNAL_ML_API_KEY"
```

## 7. Troubleshooting

### Check Database Connection
```bash
# Test database connection
python -c "from data_extraction import DataExtractor; e = DataExtractor(); print('DB Connected')"
```

### View Environment Variables
```bash
# Check required env vars
env | grep SQLSERVER
env | grep ML_API
```

### Check Available Data
```bash
# Run data extraction test
python -c "
from data_extraction import DataExtractor
e = DataExtractor()
df = e.load_dividend_history(limit=10)
print(f'Loaded {len(df)} records')
print(df.columns.tolist())
"
```

## 8. Performance Monitoring

```bash
# Monitor training progress
tail -f training.log

# Check memory usage during training
htop

# Monitor disk space
df -h

# Check model file sizes
du -sh models/*.pkl
```