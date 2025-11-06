#!/bin/bash
# Azure VM Service Troubleshooting Script

echo "=========================================="
echo "🔍 Azure VM Harvey Service Troubleshooting"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo "1️⃣ Checking service status..."
echo "------------------------------------------"

# Check if services are actually running
if systemctl is-active --quiet harvey-backend; then
    echo -e "${GREEN}✅ harvey-backend is RUNNING${NC}"
else
    echo -e "${RED}❌ harvey-backend is NOT RUNNING${NC}"
    echo "Starting harvey-backend..."
    sudo systemctl start harvey-backend
    sleep 3
fi

if systemctl is-active --quiet harvey-ml; then
    echo -e "${GREEN}✅ harvey-ml is RUNNING${NC}"
else
    echo -e "${RED}❌ harvey-ml is NOT RUNNING${NC}"
    echo "Starting harvey-ml..."
    sudo systemctl start harvey-ml
    sleep 3
fi

echo ""
echo "2️⃣ Checking what's actually listening..."
echo "------------------------------------------"

# Check what's listening on the ports
echo "Port 8001 (Harvey API):"
sudo ss -tlnp | grep :8001 || echo "  ❌ Nothing listening on port 8001"

echo ""
echo "Port 9000 (ML Service):"
sudo ss -tlnp | grep :9000 || echo "  ❌ Nothing listening on port 9000"

echo ""
echo "3️⃣ Checking local firewall (ufw)..."
echo "------------------------------------------"

# Check Ubuntu firewall
sudo ufw status | grep -E "8001|9000" || echo "No specific rules for ports 8001/9000"

# If ufw is active, add rules
if sudo ufw status | grep -q "Status: active"; then
    echo -e "${YELLOW}UFW is active - adding port rules...${NC}"
    sudo ufw allow 8001/tcp
    sudo ufw allow 9000/tcp
    echo -e "${GREEN}✅ UFW rules added${NC}"
else
    echo -e "${GREEN}✅ UFW is inactive (good)${NC}"
fi

echo ""
echo "4️⃣ Testing local connectivity..."
echo "------------------------------------------"

# Test from localhost
echo "Testing Harvey API locally:"
if curl -s --max-time 2 http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Harvey API responding on localhost:8001${NC}"
else
    echo -e "${RED}❌ Harvey API NOT responding on localhost:8001${NC}"
fi

echo ""
echo "Testing ML Service locally:"
if curl -s --max-time 2 http://localhost:9000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ ML Service responding on localhost:9000${NC}"
else
    echo -e "${RED}❌ ML Service NOT responding on localhost:9000${NC}"
fi

echo ""
echo "5️⃣ Checking service configurations..."
echo "------------------------------------------"

# Check if services are binding to 0.0.0.0
echo "Harvey Backend service configuration:"
grep -E "ExecStart|--host" /etc/systemd/system/harvey-backend.service 2>/dev/null || echo "Service file not found"

echo ""
echo "ML Service configuration:"
grep -E "ExecStart|host" /etc/systemd/system/harvey-ml.service 2>/dev/null || echo "Service file not found"

echo ""
echo "6️⃣ Checking Python and dependencies..."
echo "------------------------------------------"

# Check Python installation
if [ -f /home/azureuser/miniconda3/bin/python ]; then
    echo -e "${GREEN}✅ Python found at /home/azureuser/miniconda3/bin/python${NC}"
else
    echo -e "${RED}❌ Python NOT found at expected location${NC}"
fi

# Check if main files exist
if [ -f /home/azureuser/harvey/main.py ]; then
    echo -e "${GREEN}✅ main.py exists${NC}"
else
    echo -e "${RED}❌ main.py NOT found${NC}"
fi

if [ -f /home/azureuser/harvey/ml_training/ml_api.py ]; then
    echo -e "${GREEN}✅ ml_api.py exists${NC}"
else
    echo -e "${RED}❌ ml_api.py NOT found${NC}"
fi

echo ""
echo "7️⃣ Checking recent logs..."
echo "------------------------------------------"

echo "Harvey Backend recent errors:"
sudo journalctl -u harvey-backend --no-pager -n 5 | grep -i error || echo "No recent errors"

echo ""
echo "ML Service recent errors:"
sudo journalctl -u harvey-ml --no-pager -n 5 | grep -i error || echo "No recent errors"

echo ""
echo "8️⃣ Network Interface Check..."
echo "------------------------------------------"

# Show network interfaces and IPs
echo "Network interfaces:"
ip addr show | grep -E "inet |state UP" | head -10

echo ""
echo "9️⃣ Testing external connectivity..."
echo "------------------------------------------"

# Get public IP
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')
echo "VM Public IP: $PUBLIC_IP"

echo ""
echo "=========================================="
echo "📊 DIAGNOSIS SUMMARY"
echo "=========================================="

# Summary
if sudo ss -tlnp | grep -q ":8001.*LISTEN" && sudo ss -tlnp | grep -q ":9000.*LISTEN"; then
    echo -e "${GREEN}✅ Services ARE listening on correct ports${NC}"
    echo ""
    echo "🔍 Possible issues:"
    echo "1. Services might be bound to localhost only (not 0.0.0.0)"
    echo "2. Azure NSG rules might not be applied yet (wait 1-2 minutes)"
    echo "3. There might be an additional firewall layer"
    echo ""
    echo "🔧 Try this fix:"
    echo "sudo systemctl stop harvey-backend harvey-ml"
    echo "cd /home/azureuser/harvey"
    echo "/home/azureuser/miniconda3/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8001"
else
    echo -e "${RED}❌ Services are NOT listening on the expected ports${NC}"
    echo ""
    echo "🔧 Manual start commands:"
    echo "cd /home/azureuser/harvey"
    echo "/home/azureuser/miniconda3/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8001 &"
    echo "cd /home/azureuser/harvey/ml_training"
    echo "/home/azureuser/miniconda3/bin/python ml_api.py &"
fi

echo ""
echo "=========================================="