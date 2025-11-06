#!/bin/bash
# Manual fix for ML endpoints on Azure VM
# Run this on your Azure VM to manually apply the fixes

echo "================================================"
echo "🔧 Manually Fixing ML Endpoint Paths"
echo "================================================"
echo ""

# Navigate to Harvey directory
cd /home/azureuser/harvey

# Backup original file
cp app/services/ml_api_client.py app/services/ml_api_client.py.backup

# Fix the get_symbol_insights method
echo "Fixing get_symbol_insights endpoint..."
sed -i 's|url = f"{self.base_url}/insights/{symbol}"|url = f"{self.base_url}/insights/symbol"|' app/services/ml_api_client.py
sed -i 's|response = self.client.get(url, headers=self._get_headers())|data = {"symbol": symbol}\n            response = self.client.post(url, json=data, headers=self._get_headers())|' app/services/ml_api_client.py

# Fix the health_check method
echo "Fixing health_check endpoint..."
sed -i 's|url = f"{self.base_url}/health"|ml_root = self.base_url.replace("/api/internal/ml", "")\n            url = f"{ml_root}/health"|' app/services/ml_api_client.py

echo ""
echo "✅ Endpoints fixed!"
echo ""
echo "Restarting Harvey Backend..."
sudo systemctl restart harvey-backend

echo ""
echo "Testing services..."
sleep 5

# Check if Harvey is running
if systemctl is-active --quiet harvey-backend; then
    echo "✅ Harvey Backend is running"
    
    # Check logs for 404 errors
    echo ""
    echo "Checking for endpoint errors in last 10 seconds..."
    if sudo journalctl -u harvey-backend --since "10 seconds ago" | grep -q "404"; then
        echo "⚠️ Still seeing 404 errors - may need manual edit"
    else
        echo "✅ No 404 errors detected!"
    fi
else
    echo "❌ Harvey Backend failed to start"
fi

echo ""
echo "================================================"
echo "Manual fix complete!"
echo "================================================"
echo ""
echo "If this doesn't work, manually edit:"
echo "  nano /home/azureuser/harvey/app/services/ml_api_client.py"
echo ""
echo "Change line ~695:"
echo "  FROM: url = f\"{self.base_url}/insights/{symbol}\""
echo "        response = self.client.get(url, headers=self._get_headers())"
echo ""
echo "  TO:   url = f\"{self.base_url}/insights/symbol\""
echo "        data = {\"symbol\": symbol}"
echo "        response = self.client.post(url, json=data, headers=self._get_headers())"
echo ""
echo "Change line ~744:"
echo "  FROM: url = f\"{self.base_url}/health\""
echo ""
echo "  TO:   ml_root = self.base_url.replace('/api/internal/ml', '')"
echo "        url = f\"{ml_root}/health\""
echo ""