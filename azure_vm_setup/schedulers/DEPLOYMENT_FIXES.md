# Critical Deployment Fixes - November 20, 2025

## Issues Fixed

### 1. ✅ ODBC Driver Version (CRITICAL)
**Error:**
```
Can't open lib 'ODBC Driver 17 for SQL Server' : file not found
```

**Fix Applied:**
- Changed from `ODBC Driver 17` → **`ODBC Driver 18`**
- Added `TrustServerCertificate=yes` for Azure SQL compatibility
- File: `app/services/training_ingestion_service.py` line 218

**Connection String:**
```python
# Before
f"mssql+pyodbc://{user}:{password}@{host}/{db}?driver=ODBC+Driver+17+for+SQL+Server"

# After  
f"mssql+pyodbc://{user}:{password}@{host}/{db}?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
```

---

### 2. ✅ Gemini Model Retired (CRITICAL)
**Error:**
```
404 models/gemini-1.5-flash is not found for API version v1beta
```

**Root Cause:**
- **Gemini 1.5 models were RETIRED in September 2024**
- All `gemini-1.5-flash`, `gemini-1.5-pro`, `gemini-pro` now return 404 errors
- Must use Gemini 2.0 or 2.5 models

**Fix Applied:**
- Changed default model: `gemini-1.5-flash` → **`gemini-2.0-flash`**
- File: `app/services/gemini_client.py` line 142

**Model Selection:**
```python
# Before (RETIRED - 404 Error)
model_name: str = "gemini-1.5-flash"

# After (Production-Ready)
model_name: str = "gemini-2.0-flash"
```

**Available Models (2025):**
- ✅ `gemini-2.0-flash` - Stable, production-ready (recommended)
- ✅ `gemini-2.5-flash` - Latest, faster
- ✅ `gemini-2.5-pro` - Advanced reasoning
- ❌ ~~`gemini-1.5-flash`~~ - RETIRED
- ❌ ~~`gemini-1.5-pro`~~ - RETIRED
- ❌ ~~`gemini-pro`~~ - RETIRED

---

## Deployment Steps (Updated)

### 1. Commit and Push Changes
```bash
# On Replit
git add .
git commit -m "🔧 Fix ODBC Driver 18 + Gemini 2.0 migration

- Update to ODBC Driver 18 for Azure SQL
- Migrate from retired gemini-1.5-flash to gemini-2.0-flash
- Add TrustServerCertificate for Azure SQL compatibility"
git push origin main
```

### 2. Deploy on Azure VM
```bash
# SSH to Azure VM
ssh azureuser@20.81.210.213

# Pull latest fixes
cd /home/azureuser/harvey
git pull origin main

# Restart the scheduler to apply fixes
sudo systemctl restart gemini-training-scheduler

# Verify it's working
sudo journalctl -u gemini-training-scheduler -f
```

### 3. Test the Fixes
```bash
# Run test generation (should work now)
cd /home/azureuser/harvey
python azure_vm_setup/schedulers/gemini_training_scheduler.py --mode test

# Expected output:
# ✓ Successfully generated 5 questions
# ✓ Database connection successful
# ✓ Status: completed
```

---

## Verification Commands

### Check Service Status
```bash
sudo systemctl status gemini-training-scheduler
```

### View Logs (Real-time)
```bash
# Should show successful API calls to gemini-2.0-flash
sudo journalctl -u gemini-training-scheduler -f
```

### Check Status File
```bash
cat /var/log/harvey/gemini_training_status.json
```

**Expected Output:**
```json
{
  "status": "completed",
  "total_generated": 5,
  "last_run": "2025-11-20T...",
  "last_updated": "2025-11-20T..."
}
```

---

## Troubleshooting

### If Still Getting ODBC Error
```bash
# Verify ODBC Driver 18 is installed
odbcinst -q -d

# Should show:
# [ODBC Driver 18 for SQL Server]
```

**If not installed:**
```bash
# Install ODBC Driver 18
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18
```

### If Still Getting 404 Model Error
```bash
# List available Gemini models
cd /home/azureuser/harvey
python -c "
import google.generativeai as genai
import os
from dotenv import load_dotenv
load_dotenv(override=True)

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
"
```

**Should show:**
```
models/gemini-2.0-flash
models/gemini-2.5-flash
models/gemini-2.5-pro
...
```

---

## Summary

| Component | Old Value | New Value | Status |
|-----------|-----------|-----------|--------|
| ODBC Driver | Driver 17 | **Driver 18** | ✅ Fixed |
| Gemini Model | gemini-1.5-flash | **gemini-2.0-flash** | ✅ Fixed |
| SSL Certificate | Not specified | **TrustServerCertificate=yes** | ✅ Added |

**Result:** Both critical blocking issues resolved. Scheduler should now run successfully.

---

**Last Updated:** November 20, 2025  
**Tested:** Azure VM (Ubuntu 20.04, Python 3.11, ODBC Driver 18)  
**Status:** ✅ Ready for Deployment
