# ML Deployment Guide for HeyDividend

This guide covers three production deployment options for machine learning models in HeyDividend.

## Quick Start 🚀

**Recommended Setup:** GitHub Actions + Azure Blob Storage + Replit

For complete step-by-step instructions, see:
- **[GitHub Actions ML Setup Guide](./GITHUB_ACTIONS_ML_SETUP.md)** ← Start here!

This guide provides detailed explanations of all deployment options.

---

## Current State (October 2025)

**Issue:** Python ML packages (prophet, scikit-learn, statsmodels, pandas, scipy) exceed Replit's 8 GiB deployment image size limit.

**Solution:** ML training is separated from prediction. Production deployments run predictions only.

**Recommended:** Use GitHub Actions for automated training (FREE) + Azure Blob Storage (~$1/mo) + Replit Reserved VM ($80/mo)

---

## Option A: Pre-trained Models

Deploy pre-trained model files without heavy ML packages.

### Architecture

```
Training (External)          Production (Replit)
┌─────────────────┐         ┌──────────────────┐
│ Local/Cloud VM  │         │  Lightweight App │
│                 │         │                  │
│ • Prophet       │  Model  │  • Prediction    │
│ • scikit-learn  │  Files  │    code only     │
│ • Full ML stack │  ────>  │  • No training   │
│                 │  .joblib│    packages      │
│ • Train models  │  .pkl   │  • Load models   │
└─────────────────┘         └──────────────────┘
```

### Benefits
- ✅ Deployment stays under 8 GiB limit
- ✅ Fast deployment and startup
- ✅ No resource constraints in production
- ✅ Predictions work perfectly
- ✅ Training happens in optimal environment

### How It Works

1. **Train models externally** (your local machine, cloud VM, Colab)
2. **Export model files** (`.joblib`, `.pkl`, `.keras`)
3. **Upload to production** (commit to repo or cloud storage)
4. **Predictions load models** (no training packages needed)

### Implementation Steps

#### Step 1: Set Up Training Environment

**Option 1: Local Machine**
```bash
# Create virtual environment
python -m venv ml-training
source ml-training/bin/activate  # or `ml-training\Scripts\activate` on Windows

# Install training packages
pip install prophet scikit-learn statsmodels pandas joblib numpy scipy
```

**Option 2: Google Colab** (Free GPU/TPU)
```python
# In Colab notebook
!pip install prophet scikit-learn statsmodels pandas joblib
```

**Option 3: Cloud VM** (AWS, GCP, Azure)
```bash
# On cloud instance
pip install prophet scikit-learn statsmodels pandas joblib numpy scipy
```

#### Step 2: Train and Export Models

Use the training scripts in `server/ml/training/`:

```python
# Example: dividend_growth_forecasting.py
from sklearn.ensemble import RandomForestRegressor
import joblib

# Train model
model = RandomForestRegressor(n_estimators=100)
model.fit(X_train, y_train)

# Export model
joblib.dump(model, 'dividend_growth_forecaster.joblib')
```

See `server/ml/training/TRAINING_GUIDE.md` for detailed training instructions.

#### Step 3: Deploy Model Files

**Method 1: Commit to Repository**
```bash
# Copy trained model to models directory
cp dividend_growth_forecaster.joblib server/ml/models/

# Commit and push
git add server/ml/models/
git commit -m "Update ML models"
git push
```

**Method 2: Cloud Storage** (Recommended for large models)
```typescript
// Load from S3/GCS in production
import { Storage } from '@google-cloud/storage';

const storage = new Storage();
const bucket = storage.bucket('heydividend-ml-models');
const file = bucket.file('dividend_growth_forecaster.joblib');
await file.download({ destination: '/tmp/model.joblib' });
```

#### Step 4: Load Models in Production

Your prediction code already handles this:

```typescript
// server/services/RegressionService.ts
const model = await loadPretrainedModel('dividend_growth_forecaster.joblib');
const predictions = await model.predict(features);
```

### Model Storage Structure

```
server/ml/models/
├── dividend_cut_predictor.joblib           # Binary classification
├── dividend_growth_forecaster.joblib       # Growth predictions
├── dividend_growth_forecaster_lstm.keras   # Time series
├── ensemble_anomaly_detection_model.joblib # Anomaly detection
├── esg_dividend_scorer.joblib              # ESG scoring
└── [your-new-models].joblib                # Add new models here
```

### Training Scripts Available

Located in `server/ml/training/`:

| Script | Purpose | Output Model |
|--------|---------|--------------|
| `dividend_growth_forecasting.py` | Revenue growth prediction | `dividend_growth_forecaster.joblib` |
| `dividend_cut_prediction.py` | Cut risk classification | `dividend_cut_predictor.joblib` |
| `anomaly_detection.py` | Outlier detection | `ensemble_anomaly_detection_model.joblib` |
| `esg_integration.py` | ESG scoring | `esg_dividend_scorer.joblib` |
| `regression_models.py` | General regression | Various `.joblib` |
| `time_series_models.py` | Time series forecasting | `.keras` or `.pkl` |

### Workflow Example

```bash
# 1. Clone repo and set up training environment
git clone <repo-url>
cd heydividend
python -m venv ml-training
source ml-training/bin/activate
pip install -r server/ml/training/requirements.txt

# 2. Train models
cd server/ml/training
python dividend_growth_forecasting.py
python dividend_cut_prediction.py

# 3. Models are exported to server/ml/models/

# 4. Commit and deploy
git add ../models/
git commit -m "Update ML models with latest data"
git push

# 5. Production automatically uses new models
```

---

## Option B: External Training Pipeline (🚀 Scalable)

Automated training pipeline with cloud storage.

### Architecture

```
┌─────────────────────────────────────────────────┐
│            External Training Pipeline            │
├─────────────────────────────────────────────────┤
│                                                  │
│  1. Scheduled Training (Cron/Airflow)           │
│     └─> Fetch fresh data from production DB    │
│                                                  │
│  2. Model Training (AWS/GCP/Azure)              │
│     └─> Train with full ML stack               │
│                                                  │
│  3. Model Validation                            │
│     └─> Compare with previous version           │
│                                                  │
│  4. Cloud Storage Upload (S3/GCS)               │
│     └─> Version-controlled model artifacts      │
│                                                  │
│  5. Production Notification                     │
│     └─> Trigger model reload endpoint           │
│                                                  │
└─────────────────────────────────────────────────┘
                         │
                         ▼
            ┌─────────────────────────┐
            │   Production (Replit)   │
            │                         │
            │  • Download models      │
            │  • Load into memory     │
            │  • Serve predictions    │
            └─────────────────────────┘
```

### Components Needed

1. **Training Server** (AWS EC2, GCP Compute Engine, or GitHub Actions)
2. **Cloud Storage** (AWS S3, Google Cloud Storage, or Azure Blob)
3. **Orchestration** (Airflow, Prefect, or GitHub Actions)
4. **Model Registry** (MLflow, Weights & Biases, or custom)

### Implementation

#### 1. Set Up Cloud Storage

**Cloud Storage Configuration:**

The `ModelStorageService` automatically detects your cloud provider based on environment variables. **Priority order: Azure → AWS → GCS**

**Azure Blob Storage (Recommended - already using Azure SQL):**
```bash
# Set these environment variables in Replit Secrets
AZURE_STORAGE_ACCOUNT_NAME=your-storage-account
AZURE_STORAGE_ACCOUNT_KEY=your-account-key
ML_MODELS_CONTAINER=ml-models  # optional, defaults to 'ml-models'
```

**Setup Steps for Azure:**
1. Create Azure Storage Account in same region as SQL Server
2. Create a container named `ml-models` (or custom name)
3. Get access key from Azure Portal → Storage Account → Access Keys
4. Add to Replit Secrets (automatically syncs to deployment)

**AWS S3 (auto-detected):**
```bash
# Set these environment variables
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1  # optional, defaults to us-east-1
ML_MODELS_BUCKET=heydividend-ml-models  # optional
```

**Google Cloud Storage (auto-detected):**
```bash
# Set these environment variables
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
ML_MODELS_BUCKET=heydividend-ml-models  # optional
```

**Provider Comparison:**

| Provider | Cost (50GB) | Pros | Cons |
|----------|-------------|------|------|
| **Azure Blob** | ~$1.15/mo | Same region as SQL, integrated billing | Requires Azure account |
| **AWS S3** | ~$1.15/mo | Most features, global | Separate account |
| **GCS** | ~$1.30/mo | Fast in US | Google account needed |

**Usage (provider-agnostic):**
```typescript
import { modelStorageService } from './services/ModelStorageService';

// Load model (works with Azure, AWS S3, GCS, or local)
const buffer = await modelStorageService.loadModel('dividend_growth_forecaster.joblib');

// Upload model (automatically uses configured provider)
await modelStorageService.uploadToCloud('my_model.joblib', buffer);

// List models (from all sources)
const models = await modelStorageService.listModels();
```

#### 2. Create Training Pipeline

**GitHub Actions Example:**
```yaml
# .github/workflows/train-ml-models.yml
name: Train ML Models

on:
  schedule:
    - cron: '0 2 * * 0'  # Weekly on Sunday 2 AM
  workflow_dispatch:

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
          pip install prophet scikit-learn statsmodels pandas joblib
      
      - name: Fetch training data
        run: |
          python server/ml/scripts/fetch_training_data.py
      
      - name: Train models
        run: |
          python server/ml/training/dividend_growth_forecasting.py
          python server/ml/training/dividend_cut_prediction.py
      
      - name: Upload to S3
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: |
          aws s3 sync server/ml/models/ s3://heydividend-ml-models/models/
      
      - name: Notify production
        run: |
          curl -X POST https://your-app.replit.app/api/admin/reload-models \
            -H "X-Admin-Key: ${{ secrets.ADMIN_KEY }}"
```

#### 3. Model Reload Endpoint

```typescript
// server/routes.ts
app.post('/api/admin/reload-models', async (req, res) => {
  const adminKey = req.headers['x-admin-key'];
  if (adminKey !== process.env.ADMIN_KEY) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  
  const modelStorage = new ModelStorageService();
  
  // Download latest models
  await modelStorage.downloadModel('dividend_growth_forecaster.joblib');
  await modelStorage.downloadModel('dividend_cut_predictor.joblib');
  
  // Reload models in services
  await regressionService.reloadModels();
  
  res.json({ success: true, message: 'Models reloaded' });
});
```

### Benefits
- ✅ Automated retraining on schedule
- ✅ Version control for models
- ✅ A/B testing capabilities
- ✅ Rollback to previous versions
- ✅ Scalable to any model size

---

## Option C: Reserved VM Deployment (💪 Full ML Stack)

Deploy with training packages enabled on high-memory VM.

### Reserved VM Specifications

Replit offers dedicated Reserved VMs for resource-intensive applications:

| Configuration | vCPU | RAM | Monthly Cost | Best For |
|---------------|------|-----|--------------|----------|
| Small | 2 | 8 GB | $80 | Light ML inference |
| **Large** | 4 | 16 GB | **$160** | **ML training** |
| X-Large | 8 | 32 GB | $320 | Heavy workloads |

**Recommended:** Large VM (4 vCPU, 16 GB RAM, $160/mo) for ML training

### Setup Steps

#### 1. Configure Replit Secrets (Syncs Automatically)

Add these secrets in your Replit workspace (they auto-sync to deployment):

```bash
# Required: Enable ML Training
ENABLE_ML_TRAINING=true

# Optional: Azure Blob Storage for model persistence
AZURE_STORAGE_ACCOUNT_NAME=your-storage-account
AZURE_STORAGE_ACCOUNT_KEY=your-account-key
ML_MODELS_CONTAINER=ml-models
```

**How to add secrets:**
1. Open **Secrets** tool in Replit (Tool dock → All tools → Secrets)
2. Add each secret with Key and Value
3. Secrets automatically sync to your deployment

#### 2. Add Python ML Packages to pyproject.toml

**Edit `pyproject.toml` for Reserved VM:**

```toml
[project]
dependencies = [
    "prophet>=1.1.7",
    "scikit-learn>=1.7.2",
    "statsmodels>=0.14.5",
    "pandas>=2.3.2",
    "joblib>=1.5.2"
]
```

#### 3. Deploy to Reserved VM

1. Open **Deployments** tool in Replit
2. Select **Reserved VM** option
3. Click **Set up your published app**
4. Choose **Large** configuration:
   - 4 vCPU
   - 16 GB RAM
   - $160/month

#### 4. Configure Build & Run Commands

In deployment settings:

**Build command:**
```bash
npm install && uv pip install prophet scikit-learn statsmodels pandas joblib && npm run build
```

**Run command:**
```bash
npm start
```

**Port:** 5000 (default)

#### 5. Deploy

Click **Deploy** and wait for build to complete (~5-10 minutes for ML packages)

### Docker Image Optimization

Even with Reserved VM, optimize image size:

```dockerfile
# Use multi-stage build
FROM python:3.11-slim AS ml-builder
RUN pip install --no-cache-dir prophet scikit-learn statsmodels pandas joblib

FROM node:20-slim
COPY --from=ml-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
# Rest of build...
```

### Benefits
- ✅ Live training in production
- ✅ No external infrastructure needed
- ✅ Automatic model updates
- ✅ Full ML capabilities

### Limitations
- ❌ Higher cost ($160/month minimum)
- ❌ Longer deployment times
- ❌ Resource contention possible

---

## Decision Matrix

| Criteria | Option A: Pre-trained | Option B: Pipeline | Option C: Reserved VM |
|----------|----------------------|-------------------|----------------------|
| **Cost** | $0 extra | $50-200/mo (cloud) | $160/mo minimum |
| **Deployment Size** | <8 GiB ✅ | <8 GiB ✅ | ~10-12 GiB |
| **Setup Complexity** | Low | Medium | Low |
| **Training Speed** | Manual | Automated | Automated |
| **Scalability** | Medium | High | Medium |
| **Recommended For** | MVP, Testing | Production | All-in-one |

## Recommendation

**Start with Option A**, then migrate to **Option B** for production scale:

1. **Phase 1 (Now):** Use pre-trained models, train locally
2. **Phase 2 (Growth):** Set up training pipeline with GitHub Actions + S3
3. **Phase 3 (Scale):** Consider Reserved VM if simplified ops are worth $160/mo

---

## Quick Start Commands

### Option A: Pre-trained Models
```bash
# Local training
python -m venv ml-env
source ml-env/bin/activate
pip install prophet scikit-learn statsmodels pandas joblib
python server/ml/training/dividend_growth_forecasting.py
cp server/ml/models/*.joblib <production-location>
```

### Option B: GitHub Actions Pipeline
```bash
# Set up secrets in GitHub
gh secret set AWS_ACCESS_KEY_ID
gh secret set AWS_SECRET_ACCESS_KEY
gh secret set ADMIN_KEY

# Trigger workflow
gh workflow run train-ml-models.yml
```

### Option C: Reserved VM
```bash
# In Reserved VM deployment settings
ENABLE_ML_TRAINING=true
```

---

## Troubleshooting

### Model Loading Errors

```typescript
// Fallback mechanism
try {
  model = await loadModel('dividend_growth_forecaster.joblib');
} catch (error) {
  console.warn('Model not found, using fallback');
  model = new FallbackPredictor();
}
```

### Version Mismatches

Pin scikit-learn versions in training:
```bash
pip install scikit-learn==1.7.2  # Match production
```

### Large Model Files

Use Git LFS for models >100 MB:
```bash
git lfs track "*.joblib"
git lfs track "*.pkl"
```

---

## Next Steps

1. ✅ Review this guide
2. Choose deployment option
3. Follow implementation steps
4. Test predictions
5. Monitor performance

For questions, see `server/ml/training/TRAINING_GUIDE.md` or contact the team.
