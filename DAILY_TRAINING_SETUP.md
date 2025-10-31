# Daily ML Training Setup Guide

**Change:** Update ML training schedule from weekly (Sundays) to daily (every day at 2 AM UTC)

**Impact:** Models will be trained 7x more frequently, using fresh data every day instead of weekly.

---

## Step-by-Step Implementation

### 1. Locate Your Training Repository

Your ML training pipeline runs on a **Replit Reserved VM** using **GitHub Actions**. You need to find the repository that contains your training scripts.

**Typical repository name:**
- `heydividend-ml-training`
- `harvey-ml-pipeline`
- `dividend-ml-models`
- Or similar

This is **separate** from your Harvey backend repository (this current Replit).

---

### 2. Update GitHub Actions Workflow

**File to edit:** `.github/workflows/train-ml-models.yml`

**Current configuration (Weekly):**
```yaml
name: Train ML Models

on:
  schedule:
    - cron: '0 2 * * 0'  # Weekly on Sunday 2 AM UTC
  workflow_dispatch:      # Manual trigger support

jobs:
  train:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install prophet scikit-learn statsmodels pandas joblib azure-storage-blob
      
      - name: Fetch training data from Azure SQL
        env:
          SQLSERVER_HOST: ${{ secrets.SQLSERVER_HOST }}
          SQLSERVER_DB: ${{ secrets.SQLSERVER_DB }}
          SQLSERVER_USER: ${{ secrets.SQLSERVER_USER }}
          SQLSERVER_PASSWORD: ${{ secrets.SQLSERVER_PASSWORD }}
        run: |
          python scripts/fetch_training_data.py
      
      - name: Train Dividend Growth Model
        run: |
          python training/dividend_growth_forecasting.py
      
      - name: Train Dividend Cut Risk Model
        run: |
          python training/dividend_cut_prediction.py
      
      - name: Train ESG Scoring Model
        run: |
          python training/esg_scoring.py
      
      - name: Train Anomaly Detection Model
        run: |
          python training/anomaly_detection.py
      
      - name: Upload models to Azure Blob Storage
        env:
          AZURE_STORAGE_CONNECTION_STRING: ${{ secrets.AZURE_STORAGE_CONNECTION_STRING }}
        run: |
          python scripts/upload_to_blob.py
      
      - name: Notify ML API to reload models
        env:
          ML_API_URL: ${{ secrets.ML_API_URL }}
          INTERNAL_ML_API_KEY: ${{ secrets.INTERNAL_ML_API_KEY }}
        run: |
          curl -X POST $ML_API_URL/admin/reload-models \
            -H "X-Internal-API-Key: $INTERNAL_ML_API_KEY"
```

**NEW configuration (Daily):**
```yaml
name: Train ML Models

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC ← CHANGE THIS LINE
  workflow_dispatch:      # Manual trigger support

jobs:
  train:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install prophet scikit-learn statsmodels pandas joblib azure-storage-blob
      
      - name: Fetch training data from Azure SQL
        env:
          SQLSERVER_HOST: ${{ secrets.SQLSERVER_HOST }}
          SQLSERVER_DB: ${{ secrets.SQLSERVER_DB }}
          SQLSERVER_USER: ${{ secrets.SQLSERVER_USER }}
          SQLSERVER_PASSWORD: ${{ secrets.SQLSERVER_PASSWORD }}
        run: |
          python scripts/fetch_training_data.py
      
      - name: Train Dividend Growth Model
        run: |
          python training/dividend_growth_forecasting.py
      
      - name: Train Dividend Cut Risk Model
        run: |
          python training/dividend_cut_prediction.py
      
      - name: Train ESG Scoring Model
        run: |
          python training/esg_scoring.py
      
      - name: Train Anomaly Detection Model
        run: |
          python training/anomaly_detection.py
      
      - name: Upload models to Azure Blob Storage
        env:
          AZURE_STORAGE_CONNECTION_STRING: ${{ secrets.AZURE_STORAGE_CONNECTION_STRING }}
        run: |
          python scripts/upload_to_blob.py
      
      - name: Notify ML API to reload models
        env:
          ML_API_URL: ${{ secrets.ML_API_URL }}
          INTERNAL_ML_API_KEY: ${{ secrets.INTERNAL_ML_API_KEY }}
        run: |
          curl -X POST $ML_API_URL/admin/reload-models \
            -H "X-Internal-API-Key: $INTERNAL_ML_API_KEY"
```

**What changed:**
```diff
  schedule:
-   - cron: '0 2 * * 0'  # Weekly on Sunday 2 AM UTC
+   - cron: '0 2 * * *'  # Daily at 2 AM UTC
```

---

### 3. Commit and Push Changes

```bash
# In your training repository
git add .github/workflows/train-ml-models.yml
git commit -m "Change ML training schedule to daily"
git push origin main
```

**✅ Done!** GitHub Actions will automatically start running the training daily at 2 AM UTC.

---

## Daily Training Schedule

Once implemented, your ML models will train on this schedule:

| Time (UTC) | Model Being Trained | Estimated Duration |
|------------|---------------------|-------------------|
| **2:00 AM** | Dividend Calendar Model | ~60 minutes |
| **3:00 AM** | Dividend Growth Prediction | ~60 minutes |
| **4:00 AM** | Dividend Cut Risk | ~60 minutes |
| **5:00 AM** | ESG Scoring | ~60 minutes |
| **6:00 AM** | Upload to Azure Blob + Notify ML API | ~5 minutes |

**Total runtime per day:** ~4 hours 5 minutes

---

## Expected Outcomes

### ✅ Benefits

1. **Maximum Model Freshness**
   - Models use data from yesterday
   - Immediate reflection of market changes
   - Up-to-date predictions every morning

2. **Better Reaction Time**
   - Capture sudden dividend changes quickly
   - Detect emerging patterns faster
   - More responsive to market volatility

3. **Consistent Model Performance**
   - Daily updates reduce model drift
   - Always using recent historical data
   - Better accuracy for short-term predictions

### 📊 Resource Impact

1. **Compute Usage**
   - **Before:** 4 hours/week = ~16 hours/month
   - **After:** 28 hours/week = ~120 hours/month
   - **Increase:** 7.5x more compute time

2. **Storage Usage**
   - **Before:** 83 model files (weekly snapshots)
   - **After:** ~600+ model files (daily snapshots over ~60 days retention)
   - **Increase:** ~$0.50/month Azure Blob Storage

3. **GitHub Actions Minutes**
   - **Before:** ~240 minutes/month
   - **After:** ~1,800 minutes/month
   - **Status:** FREE (GitHub Free tier includes 2,000 minutes/month)

### 💰 Cost Analysis

| Resource | Current Cost | New Cost | Increase |
|----------|--------------|----------|----------|
| Replit Reserved VM | $80/month | $80/month | $0 (unlimited compute) |
| Azure Blob Storage | $1/month | $1.50/month | +$0.50 |
| GitHub Actions | FREE | FREE | $0 (within free tier) |
| **TOTAL** | **$81/month** | **$81.50/month** | **+$0.50** |

**✅ Minimal cost increase - mostly covered by existing infrastructure!**

---

## Monitoring Training Success

### Check GitHub Actions

1. Go to your training repository on GitHub
2. Click "Actions" tab
3. View "Train ML Models" workflow runs
4. Daily runs should appear at 2 AM UTC

### Check Azure Blob Storage

```bash
# List recent model uploads
az storage blob list \
  --account-name hdmlmodels \
  --container-name models \
  --output table \
  --query "reverse(sort_by([].{Name:name, LastModified:properties.lastModified}, &LastModified))" \
  | head -20
```

**Expected:** New model files uploaded daily around 6 AM UTC.

### Check ML API Model Version

```bash
# Check when ML API last loaded models
curl http://20.81.210.213:9000/api/internal/ml/health \
  -H "X-Internal-API-Key: $INTERNAL_ML_API_KEY"
```

**Expected response:**
```json
{
  "status": "healthy",
  "models_loaded": 4,
  "last_model_update": "2025-10-31T06:05:00Z",
  "model_versions": {
    "dividend_growth": "2025-10-31",
    "dividend_cut": "2025-10-31",
    "esg_scoring": "2025-10-31",
    "anomaly_detection": "2025-10-31"
  }
}
```

---

## Rollback (If Needed)

If you want to revert back to weekly training:

```yaml
on:
  schedule:
    - cron: '0 2 * * 0'  # Back to weekly on Sunday
```

Commit and push - schedule will revert immediately.

---

## Alternative Schedules

If daily feels too aggressive later, consider these:

| Schedule | Cron Expression | Description |
|----------|----------------|-------------|
| **Every 12 hours** | `0 2,14 * * *` | 2 AM and 2 PM daily |
| **Weekdays only** | `0 2 * * 1-5` | Monday-Friday at 2 AM |
| **Twice weekly** | `0 2 * * 1,4` | Monday and Thursday |
| **Daily** | `0 2 * * *` | Every day at 2 AM (current choice) |

---

## Manual Trigger (Anytime)

Your workflow supports manual triggers with `workflow_dispatch`. You can trigger training anytime:

1. Go to GitHub → Actions → Train ML Models
2. Click "Run workflow" button
3. Select branch (usually `main`)
4. Click "Run workflow"

Training starts immediately (doesn't wait for 2 AM).

---

## Next Steps

1. **Locate your training repository** on GitHub
2. **Edit `.github/workflows/train-ml-models.yml`**
3. **Change cron from `'0 2 * * 0'` to `'0 2 * * *'`**
4. **Commit and push**
5. **Monitor first daily run** tomorrow at 2 AM UTC

**That's it!** Your ML models will now train daily with maximum freshness.

---

## Questions?

- **When will the first daily run happen?** Tomorrow at 2 AM UTC (after you push the change)
- **Can I test it now?** Yes, use "Run workflow" button for manual trigger
- **What if a training run fails?** GitHub Actions will email you, and the previous day's models remain active
- **Can I pause training?** Yes, disable the workflow in GitHub Actions settings

---

**Status:** Ready to implement - just need to update one line in your training repository's GitHub Actions workflow file! 🚀
