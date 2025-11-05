# Harvey Passive Income Training System - Deployment Package Ready

## ✅ Deployment Package Complete

All necessary files and scripts have been prepared for deploying the fixed passive income training system to Azure VM 20.81.210.213.

## 📦 Package Contents

### 1. **Deployment Scripts**
- `deploy/HARVEY_TRAINING_DEPLOY.sh` - Main deployment script (can be run via Azure Portal Run Command)
- `deploy/PASSIVE_INCOME_TRAINING_DEPLOYMENT.md` - Comprehensive deployment guide

### 2. **Updated Code Files**
The deployment script contains embedded updates for:
- **PassiveIncomeTrainingService** - Fixed to preserve curated metadata
- **Ingestion Script** - Fixed to forward metadata instead of recalculating
- **Test Files** - CI/CD tests for category preservation

### 3. **Training Data Files** (in attached_assets/)
- `full6k_balanced_fold1_1762253797688.jsonl` - 1,320 questions
- `full6k_balanced_fold2_1762253797687.jsonl` - 1,320 questions  
- `full6k_balanced_fold3_1762253797688.jsonl` - 1,320 questions
- `full6k_balanced_fold4_1762253797688.jsonl` - 1,320 questions
- `full6k_balanced_fold5_1762253797688.jsonl` - 1,320 questions
- **Total**: 6,600 balanced questions across 5 categories (20% each)

## 🚀 Quick Deployment Steps

### Option 1: Azure Portal (No SSH Required) ⭐ Recommended

1. **Azure Portal** → VM (20.81.210.213) → Run Command → RunShellScript
2. **Copy & paste** entire contents of `deploy/HARVEY_TRAINING_DEPLOY.sh`
3. **Click Run** and wait 2-3 minutes
4. **Upload training data** via SCP or Azure File Transfer
5. **Run ingestion script** to populate database

### Option 2: SSH Deployment

```bash
# 1. SSH to VM
ssh azureuser@20.81.210.213

# 2. Run deployment script
bash /tmp/deploy_training.sh  # (after uploading)

# 3. Upload training data
scp attached_assets/full6k_balanced_fold*.jsonl azureuser@20.81.210.213:/opt/harvey-backend/training_data/

# 4. Run ingestion
cd /opt/harvey-backend
python3 app/scripts/ingest_balanced_passive_income.py
```

## ✅ What Gets Fixed

### Before (Issues):
- PassiveIncomeTrainingService was recalculating categories, losing curated metadata
- Ingestion script was not preserving the balanced distribution
- Training data categories were being overwritten with heuristics

### After (Fixed):
- ✅ Curated metadata is preserved throughout the pipeline
- ✅ Balanced 5-category distribution maintained (20% each)
- ✅ Complexity levels properly forwarded from source data
- ✅ Test suite validates metadata preservation

## 📊 Expected Results

After successful deployment:

1. **Service Running**: Harvey backend with updated training service
2. **Data Ingested**: 6,600 questions with balanced distribution:
   - comparison: 1,320 (20%)
   - portfolio-construction: 1,320 (20%)
   - payout_optimization: 1,320 (20%)
   - risk-check: 1,320 (20%)
   - tax-allocation: 1,320 (20%)
3. **Tests Passing**: Category preservation tests validate the fix
4. **API Responding**: Training endpoints functional

## 🔍 Verification Commands

```bash
# Check service
sudo systemctl status harvey-backend

# View logs
sudo journalctl -u harvey-backend -n 100

# Test API
curl http://localhost:8000/v1/training/passive-income/status

# Validate files
ls -la /opt/harvey-backend/training_data/*.jsonl

# Run tests
python3 /opt/harvey-backend/app/tests/test_passive_income_category_preservation.py
```

## ⏱️ Total Deployment Time

- Code deployment: 2-3 minutes
- Training data upload: 2-5 minutes  
- Service restart: < 1 minute
- Ingestion script: 3-5 minutes
- **Total**: ~15 minutes

## 📝 Critical Notes

1. **SSH credentials not available in environment** - Use Azure Portal Run Command method
2. **Training data must be uploaded separately** - Files are too large to embed in script
3. **Service name varies** - Could be `harvey.service` or `harvey-backend.service`
4. **Database connection required** - Ingestion script needs valid Harvey API key

## ✅ Deployment Checklist

- [ ] Deployment script ready (`HARVEY_TRAINING_DEPLOY.sh`)
- [ ] Training data files identified (5 JSONL files)
- [ ] Deployment guide documented
- [ ] Test files included
- [ ] Verification steps defined

## 🎯 Ready for Deployment

The deployment package is complete and ready to be executed on Azure VM 20.81.210.213. The fixes will ensure Harvey's passive income training system properly preserves the carefully curated metadata for optimal training performance.

---

**Deployment Method**: Azure Portal Run Command (recommended)
**Files Location**: `deploy/` directory
**Support Guide**: See `deploy/PASSIVE_INCOME_TRAINING_DEPLOYMENT.md`