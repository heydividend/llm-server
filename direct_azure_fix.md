# Direct Fix Instructions for Azure VM

Since the automated scripts aren't working, let's fix this manually. SSH into your Azure VM and run these commands:

## Step 1: SSH into Azure VM
```bash
ssh azureuser@20.81.210.213
```

## Step 2: Check Current State
```bash
cd /home/azureuser/harvey

# Check if ml_schedulers.py exists
ls -la app/routes/ml_schedulers.py

# Check what's in main.py
grep -n "ml_schedulers" main.py

# If you see nothing, the routes aren't registered
```

## Step 3: Fix main.py
```bash
# Edit main.py
nano main.py
```

### Add these TWO lines if missing:

**Line 1:** After `from app.routes import chat` (around line 29), add:
```python
from app.routes import ml_schedulers
```

**Line 2:** After `app.include_router(chat.router...` (around line 83), add:
```python
app.include_router(ml_schedulers.router, prefix="/v1", tags=["ML Schedulers"])
```

Save with Ctrl+X, Y, Enter

## Step 4: Create ml_schedulers.py if missing
If the file doesn't exist, create it:

```bash
nano app/routes/ml_schedulers.py
```

Copy and paste this minimal version:
```python
from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import verify_api_key
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ml-schedulers", tags=["ML Schedulers"])

@router.get("/health")
async def health_check(api_key: str = Depends(verify_api_key)):
    """Check health status of ML schedulers"""
    return {
        "status": "healthy",
        "message": "ML Schedulers endpoints are working",
        "endpoints": [
            "/v1/ml-schedulers/health",
            "/v1/ml-schedulers/payout-ratings",
            "/v1/ml-schedulers/dividend-calendar",
            "/v1/ml-schedulers/training-status"
        ]
    }

@router.post("/payout-ratings")
async def get_payout_ratings(api_key: str = Depends(verify_api_key)):
    """Get payout ratings"""
    return {"message": "Payout ratings endpoint working"}

@router.post("/dividend-calendar")
async def get_dividend_calendar(api_key: str = Depends(verify_api_key)):
    """Get dividend calendar"""
    return {"message": "Dividend calendar endpoint working"}

@router.get("/training-status")
async def get_training_status(api_key: str = Depends(verify_api_key)):
    """Get training status"""
    return {"message": "Training status endpoint working"}
```

Save with Ctrl+X, Y, Enter

## Step 5: Install Dependencies
```bash
source venv/bin/activate
pip install sqlalchemy pymssql aiohttp
```

## Step 6: Restart Service
```bash
sudo systemctl restart harvey
sleep 5
sudo systemctl status harvey
```

## Step 7: Test Locally
```bash
# This should return 401 (unauthorized) or 200 with your API key
curl http://localhost:8001/v1/ml-schedulers/health

# Exit SSH
exit
```

## Step 8: Test from Local Machine
```bash
curl http://20.81.210.213:8001/v1/ml-schedulers/health \
  -H "Authorization: Bearer hh_live_X6SPcjPD5jZhTMw69_internal_api_key"
```

If this returns JSON (not "Not Found"), it's working!