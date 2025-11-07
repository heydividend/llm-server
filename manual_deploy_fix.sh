#!/bin/bash

# Manual deployment fix for ML Scheduler endpoints
# This script directly copies and registers the routes

AZURE_VM_IP="20.81.210.213"
AZURE_USER="azureuser"

echo "=================================================="
echo "🔧 Manual ML Scheduler Deployment Fix"
echo "=================================================="
echo ""

# Check SSH connection
echo "1. Testing SSH connection..."
if ! ssh -o ConnectTimeout=5 $AZURE_USER@$AZURE_VM_IP "echo 'Connected'" > /dev/null 2>&1; then
    echo "❌ Cannot connect via SSH. Do you have SSH access configured?"
    echo "You need to:"
    echo "1. Have your SSH key configured for azureuser@20.81.210.213"
    echo "2. Or manually copy files to the VM"
    exit 1
fi
echo "✅ SSH connection successful"
echo ""

# Create the files directly on the VM
echo "2. Creating ML scheduler files directly on VM..."

# Create ml_schedulers.py route file
ssh $AZURE_USER@$AZURE_VM_IP 'cat > /home/azureuser/harvey/app/routes/ml_schedulers.py << '\''EOF'\''
"""ML Schedulers API Routes"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.core.auth import verify_api_key
from app.services.ml_schedulers_service import MLSchedulersService
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

# Initialize service
ml_schedulers_service = MLSchedulersService(
    ml_api_base_url=settings.ML_API_BASE_URL,
    ml_api_key=settings.INTERNAL_ML_API_KEY
)

@router.get("/ml-schedulers/health")
async def health_check(api_key: str = Depends(verify_api_key)):
    """Check health status of ML schedulers"""
    try:
        status = await ml_schedulers_service.get_health_status()
        return status
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ml-schedulers/training-status")
async def get_training_status(api_key: str = Depends(verify_api_key)):
    """Get the current ML training status"""
    try:
        status = await ml_schedulers_service.get_training_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get training status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ml-schedulers/payout-ratings")
async def get_payout_ratings(
    symbols: List[str],
    api_key: str = Depends(verify_api_key)
):
    """Get payout ratings for specified symbols"""
    try:
        if not symbols:
            raise HTTPException(status_code=400, detail="No symbols provided")
        
        request_data = {"symbols": symbols}
        ratings = await ml_schedulers_service.get_payout_ratings(request_data)
        return ratings
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get payout ratings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ml-schedulers/dividend-calendar") 
async def get_dividend_calendar(
    symbols: List[str],
    months_ahead: int = 3,
    api_key: str = Depends(verify_api_key)
):
    """Get dividend calendar predictions for specified symbols"""
    try:
        if not symbols:
            raise HTTPException(status_code=400, detail="No symbols provided")
        
        request_data = {
            "symbols": symbols,
            "months_ahead": months_ahead
        }
        calendar = await ml_schedulers_service.get_dividend_calendar(request_data)
        return calendar
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dividend calendar: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ml-schedulers/admin/dashboard")
async def admin_dashboard(api_key: str = Depends(verify_api_key)):
    """Get admin dashboard with all scheduler metrics"""
    try:
        dashboard = await ml_schedulers_service.get_admin_dashboard()
        return dashboard
    except Exception as e:
        logger.error(f"Failed to get admin dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
EOF'

echo "✅ Created ml_schedulers.py"

# Check if ml_schedulers_service.py exists, if not create a minimal version
ssh $AZURE_USER@$AZURE_VM_IP 'if [ ! -f /home/azureuser/harvey/app/services/ml_schedulers_service.py ]; then
cat > /home/azureuser/harvey/app/services/ml_schedulers_service.py << '\''EOF'\''
"""ML Schedulers Service"""
import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
from app.services.ml_api_client import MLAPIClient

logger = logging.getLogger(__name__)

class MLSchedulersService:
    """Service for ML scheduler operations"""
    
    def __init__(self, ml_api_base_url: str, ml_api_key: str):
        self.ml_client = MLAPIClient(ml_api_base_url, ml_api_key)
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of ML schedulers"""
        loop = asyncio.get_event_loop()
        ml_health = await loop.run_in_executor(None, self.ml_client.health_check)
        
        return {
            "status": "healthy" if ml_health.get("status") == "healthy" else "degraded",
            "ml_service": ml_health,
            "schedulers": {
                "payout_rating": {"schedule": "Daily 1:00 AM UTC"},
                "dividend_calendar": {"schedule": "Sunday 2:00 AM UTC"},
                "ml_training": {"schedule": "Sunday 3:00 AM UTC"}
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_training_status(self) -> Dict[str, Any]:
        """Get ML training status"""
        loop = asyncio.get_event_loop()
        try:
            status = await loop.run_in_executor(None, self.ml_client.get_training_status)
            return status
        except:
            return {
                "status": "unknown",
                "message": "Training status not available",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_payout_ratings(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get payout ratings for symbols"""
        loop = asyncio.get_event_loop()
        try:
            ratings = await loop.run_in_executor(
                None, 
                self.ml_client.get_payout_ratings,
                request_data
            )
            return ratings
        except Exception as e:
            logger.error(f"Failed to get payout ratings: {str(e)}")
            raise
    
    async def get_dividend_calendar(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get dividend calendar predictions"""
        loop = asyncio.get_event_loop()
        try:
            calendar = await loop.run_in_executor(
                None,
                self.ml_client.get_dividend_calendar, 
                request_data
            )
            return calendar
        except Exception as e:
            logger.error(f"Failed to get dividend calendar: {str(e)}")
            raise
    
    async def get_admin_dashboard(self) -> Dict[str, Any]:
        """Get admin dashboard data"""
        health = await self.get_health_status()
        training = await self.get_training_status()
        
        return {
            "health": health,
            "training": training,
            "cache_stats": {
                "enabled": True,
                "ttl_seconds": 3600
            },
            "timestamp": datetime.utcnow().isoformat()
        }
EOF
fi'

echo "✅ Verified ml_schedulers_service.py"

# Update main.py to register the route
echo ""
echo "3. Updating main.py to register ML scheduler routes..."

# First, backup main.py
ssh $AZURE_USER@$AZURE_VM_IP 'cp /home/azureuser/harvey/main.py /home/azureuser/harvey/main.py.backup_ml_scheduler'

# Check if route is already registered
if ssh $AZURE_USER@$AZURE_VM_IP 'grep -q "ml_schedulers" /home/azureuser/harvey/main.py'; then
    echo "⚠️  ML schedulers already mentioned in main.py, updating..."
else
    echo "Adding ML schedulers to main.py..."
fi

# Add the import and route registration using Python
ssh $AZURE_USER@$AZURE_VM_IP 'python3 << '\''PYTHON'\''
import re

# Read main.py
with open("/home/azureuser/harvey/main.py", "r") as f:
    content = f.read()

# Check if import exists, if not add it
if "from app.routes import ml_schedulers" not in content:
    # Find where other routes are imported and add our import
    import_pattern = r"(from app\.routes import.*)"
    match = re.search(import_pattern, content)
    if match:
        last_import = match.group(1)
        new_import = last_import + "\nfrom app.routes import ml_schedulers"
        content = content.replace(last_import, new_import)
        print("✅ Added ml_schedulers import")
    else:
        print("⚠️  Could not find route imports section")

# Check if route is registered, if not add it  
if 'ml_schedulers.router' not in content:
    # Find where other routers are included and add ours
    router_pattern = r"(app\.include_router\(.*?router.*?\))"
    matches = re.findall(router_pattern, content)
    if matches:
        last_router = matches[-1]
        # Find the position after the last router
        pos = content.rfind(last_router) + len(last_router)
        # Add our router registration
        new_router = '\napp.include_router(ml_schedulers.router, prefix="/v1", tags=["ML Schedulers"])'
        content = content[:pos] + new_router + content[pos:]
        print("✅ Added ml_schedulers router registration")
    else:
        print("⚠️  Could not find router registration section")

# Write the updated content
with open("/home/azureuser/harvey/main.py", "w") as f:
    f.write(content)
    
print("✅ main.py updated")
PYTHON'

echo ""
echo "4. Installing dependencies..."
ssh $AZURE_USER@$AZURE_VM_IP 'cd /home/azureuser/harvey && source venv/bin/activate && pip install aiohttp --quiet'
echo "✅ Dependencies installed"

echo ""
echo "5. Restarting Harvey service..."
ssh $AZURE_USER@$AZURE_VM_IP 'sudo systemctl restart harvey'
sleep 5

# Check if service is running
echo ""
echo "6. Checking service status..."
if ssh $AZURE_USER@$AZURE_VM_IP 'sudo systemctl is-active --quiet harvey'; then
    echo "✅ Harvey service is running"
else
    echo "❌ Harvey service failed to start. Checking logs..."
    ssh $AZURE_USER@$AZURE_VM_IP 'sudo journalctl -u harvey -n 30 --no-pager | grep -E "ERROR|Error|Failed|ImportError"'
fi

echo ""
echo "7. Testing endpoints..."
echo "------------------------"

# Test health endpoint
response=$(curl -s -o /dev/null -w "%{http_code}" http://$AZURE_VM_IP:8001/v1/ml-schedulers/health 2>/dev/null)
if [ "$response" = "200" ] || [ "$response" = "401" ]; then
    echo "✅ ML Scheduler endpoint is now available (HTTP $response)"
    if [ "$response" = "401" ]; then
        echo "   Note: Requires API key for full access"
    fi
else
    echo "❌ ML Scheduler endpoint still not working (HTTP $response)"
    echo ""
    echo "Checking what routes are registered..."
    curl -s http://$AZURE_VM_IP:8001/docs | grep -o '"path":"[^"]*"' | head -20
fi

echo ""
echo "=================================================="
echo "📋 Manual Fix Complete"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Test with your API key:"
echo "   curl http://$AZURE_VM_IP:8001/v1/ml-schedulers/health \\"
echo "     -H 'Authorization: Bearer YOUR_API_KEY'"
echo ""
echo "2. If still not working, check full logs:"
echo "   ssh $AZURE_USER@$AZURE_VM_IP 'sudo journalctl -u harvey -n 100'"
echo ""
echo "3. Verify the route registration:"
echo "   ssh $AZURE_USER@$AZURE_VM_IP 'grep ml_schedulers /home/azureuser/harvey/main.py'"
echo ""
echo "=================================================="