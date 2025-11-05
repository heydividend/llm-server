# Harvey Passive Income Training System - Deployment Guide

## 🎯 Critical Updates for Production

This deployment includes **critical fixes** that preserve curated category and complexity metadata in the training data.

**Fixed Issues:**
- PassiveIncomeTrainingService now preserves curated metadata instead of recalculating
- Ingestion script properly forwards metadata from balanced training datasets
- 6,600 questions properly distributed across 5 categories (20% each)

## 📋 Deployment Package Contents

### Files to Deploy:
1. **deploy/HARVEY_TRAINING_DEPLOY.sh** - Main deployment script
2. **Training Data Files** (from attached_assets/):
   - full6k_balanced_fold1_1762253797688.jsonl
   - full6k_balanced_fold2_1762253797687.jsonl
   - full6k_balanced_fold3_1762253797688.jsonl
   - full6k_balanced_fold4_1762253797688.jsonl
   - full6k_balanced_fold5_1762253797688.jsonl

## 🚀 Deployment Instructions

### Option 1: Azure Portal Run Command (No SSH Required) ⭐

This is the **recommended method** if you don't have SSH access:

1. **Open Azure Portal**:
   - Navigate to: https://portal.azure.com
   - Find VM: 20.81.210.213
   - Go to: Operations → Run command → RunShellScript

2. **Deploy the Code**:
   - Copy the entire contents of `deploy/HARVEY_TRAINING_DEPLOY.sh`
   - Paste into the Run Command script box
   - Click "Run"
   - Wait for completion (2-3 minutes)

3. **Upload Training Data** (requires separate step):
   
   After the script completes, you need to upload the training data. If you have Azure CLI:
   
   ```bash
   # Use Azure CLI to copy files
   az vm run-command invoke \
     --resource-group YOUR_RESOURCE_GROUP \
     --name YOUR_VM_NAME \
     --command-id RunShellScript \
     --scripts "mkdir -p /opt/harvey-backend/training_data"
   ```
   
   Or use SCP if you have SSH access (see Option 2).

### Option 2: SSH Deployment (If You Have SSH Access)

```bash
# 1. SSH into the VM
ssh azureuser@20.81.210.213

# 2. Create deployment script on the VM
cat > /tmp/deploy_training.sh << 'EOF'
[Paste contents of deploy/HARVEY_TRAINING_DEPLOY.sh here]
EOF

# 3. Make it executable and run
chmod +x /tmp/deploy_training.sh
sudo /tmp/deploy_training.sh

# 4. Upload training data (from your local machine)
# Exit SSH and run from your local machine:
scp attached_assets/full6k_balanced_fold*.jsonl azureuser@20.81.210.213:/tmp/

# 5. SSH back in and move files
ssh azureuser@20.81.210.213
sudo mv /tmp/full6k_balanced_fold*.jsonl /opt/harvey-backend/training_data/
sudo chown azureuser:azureuser /opt/harvey-backend/training_data/*.jsonl
```

### Option 3: Manual File Updates

If automated deployment fails, manually update the files:

```bash
# 1. SSH into the VM
ssh azureuser@20.81.210.213

# 2. Navigate to Harvey backend
cd /opt/harvey-backend

# 3. Backup existing files
timestamp=$(date +%Y%m%d_%H%M%S)
mkdir -p backups
cp app/services/passive_income_training_service.py backups/passive_income_training_service.py.$timestamp
cp app/scripts/ingest_balanced_passive_income.py backups/ingest_balanced_passive_income.py.$timestamp

# 4. Update PassiveIncomeTrainingService
# Create/edit app/services/passive_income_training_service.py with the updated code

# 5. Update Ingestion Script
# Create/edit app/scripts/ingest_balanced_passive_income.py with the updated code

# 6. Create training data directory
mkdir -p training_data

# 7. Upload training data files
# (Use SCP from your local machine)

# 8. Set permissions
sudo chown -R azureuser:azureuser app/
sudo chown -R azureuser:azureuser training_data/

# 9. Restart service
sudo systemctl restart harvey-backend
```

## 📊 Running the Ingestion Script

After deployment, populate the database with balanced training data:

```bash
# 1. SSH into the VM
ssh azureuser@20.81.210.213

# 2. Navigate to Harvey backend
cd /opt/harvey-backend

# 3. Activate virtual environment
source venv/bin/activate

# 4. Set API key from environment
export HARVEY_AI_API_KEY=$(grep HARVEY_AI_API_KEY .env | cut -d'=' -f2)

# 5. Run the ingestion script
python3 app/scripts/ingest_balanced_passive_income.py

# Expected output:
# ============================================================
# Passive Income Training Data Ingestion
# ============================================================
# 
# Processing full6k_balanced_fold1_1762253797688.jsonl...
# ✅ full6k_balanced_fold1_1762253797688: 1320 questions ingested
#    Categories: {'comparison': 264, 'portfolio-construction': 264, ...}
# 
# [... continues for all 5 folds ...]
# 
# ============================================================
# ✅ Ingestion Complete!
# ============================================================
```

## ✅ Verification Steps

### 1. Verify File Deployment
```bash
cd /opt/harvey-backend

# Check if files were updated
ls -la app/services/passive_income_training_service.py
ls -la app/scripts/ingest_balanced_passive_income.py

# Check training data
ls -la training_data/*.jsonl
# Should show 5 files
```

### 2. Test the Service
```bash
# Check if Harvey is running
sudo systemctl status harvey-backend

# Test API endpoint
curl http://localhost:8000/

# Check logs for errors
sudo journalctl -u harvey-backend -n 100 | grep -i error
```

### 3. Validate Category Preservation
```bash
cd /opt/harvey-backend
source venv/bin/activate

# Run the test
python3 app/tests/test_passive_income_category_preservation.py
# Expected: ✅ Category preservation test passed
```

### 4. Check Training Data Distribution
```bash
# Quick check of category distribution in first file
cd /opt/harvey-backend/training_data
head -n 100 full6k_balanced_fold1_1762253797688.jsonl | \
  grep -o '"category":"[^"]*"' | sort | uniq -c

# Should show roughly equal distribution across:
# - comparison
# - portfolio-construction  
# - payout_optimization
# - risk-check
# - tax-allocation
```

## 🔍 Troubleshooting

### Service Won't Start
```bash
# Check for Python errors
cd /opt/harvey-backend
source venv/bin/activate
python3 -m py_compile app/services/passive_income_training_service.py

# Check service logs
sudo journalctl -u harvey-backend -n 200 --no-pager
```

### Training Data Not Found
```bash
# Verify files exist
ls -la /opt/harvey-backend/training_data/

# Check permissions
# Files should be owned by azureuser
sudo chown -R azureuser:azureuser /opt/harvey-backend/training_data/
```

### Ingestion Script Fails
```bash
# Test database connection
cd /opt/harvey-backend
source venv/bin/activate
python3 -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('API Key:', 'Set' if os.getenv('HARVEY_AI_API_KEY') else 'Missing')
print('DB Host:', os.getenv('SQLSERVER_HOST'))
"

# Check if Harvey API is responding
curl -H "Authorization: Bearer $(grep HARVEY_AI_API_KEY .env | cut -d'=' -f2)" \
  http://localhost:8000/v1/training/passive-income/status
```

## 📈 Expected Results

After successful deployment:

✅ **Files Updated**: 
- PassiveIncomeTrainingService with metadata preservation
- Ingestion script with proper forwarding

✅ **Training Data**: 
- 5 JSONL files with 1,320 questions each
- Total: 6,600 balanced questions
- Categories: 20% each (comparison, portfolio-construction, payout_optimization, risk-check, tax-allocation)

✅ **Service Status**:
- Harvey backend running without errors
- API endpoints responding
- Tests passing

✅ **Database**:
- Training data ingested successfully
- Balanced distribution maintained
- Metadata preserved

## 📝 Post-Deployment Checklist

- [ ] Deployment script executed successfully
- [ ] Training data files uploaded (5 files)
- [ ] Service restarted
- [ ] No errors in logs
- [ ] API responding
- [ ] Tests passing
- [ ] Ingestion script completed
- [ ] Category distribution verified

## 🆘 Support Commands

```bash
# Service management
sudo systemctl status harvey-backend
sudo systemctl restart harvey-backend
sudo journalctl -u harvey-backend -f

# File locations
ls -la /opt/harvey-backend/app/services/
ls -la /opt/harvey-backend/app/scripts/
ls -la /opt/harvey-backend/training_data/

# Quick health check
curl http://localhost:8000/
curl http://20.81.210.213/

# View recent errors
sudo journalctl -u harvey-backend -n 500 | grep -i error
```

## ⏱️ Deployment Timeline

- Code deployment: 2-3 minutes
- Training data upload: 2-5 minutes (depending on method)
- Service restart: < 1 minute
- Ingestion script: 3-5 minutes
- **Total time**: ~15 minutes

## 🎯 Success Criteria

The deployment is successful when:

1. PassiveIncomeTrainingService preserves metadata (no recalculation)
2. All 5 training data files are present
3. Service is running without errors
4. Ingestion completes with balanced distribution
5. Tests pass successfully

---

**Note**: This deployment is critical for maintaining the quality of Harvey's passive income training system. The fixes ensure that carefully curated category and complexity metadata is preserved throughout the training pipeline.