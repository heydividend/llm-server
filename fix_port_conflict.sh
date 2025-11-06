#!/bin/bash
# Fix port 8001 conflict on Azure VM

echo "=========================================="
echo "🔧 Fixing Port 8001 Conflict"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo "1️⃣ Finding what's using port 8001..."
echo "------------------------------------------"

# Find process using port 8001
PORT_PID=$(sudo lsof -t -i:8001)

if [ -z "$PORT_PID" ]; then
    echo -e "${GREEN}✅ Port 8001 is free${NC}"
else
    echo -e "${RED}❌ Port 8001 is being used by PID: $PORT_PID${NC}"
    
    # Show process details
    echo "Process details:"
    ps aux | grep $PORT_PID | grep -v grep
    
    echo ""
    echo "Killing process $PORT_PID..."
    sudo kill -9 $PORT_PID
    sleep 2
    
    # Verify it's killed
    if sudo lsof -t -i:8001 > /dev/null 2>&1; then
        echo -e "${RED}❌ Failed to kill process${NC}"
    else
        echo -e "${GREEN}✅ Process killed successfully${NC}"
    fi
fi

echo ""
echo "2️⃣ Stopping harvey-backend service..."
echo "------------------------------------------"

# Stop the service
sudo systemctl stop harvey-backend
sleep 2

echo ""
echo "3️⃣ Starting harvey-backend service..."
echo "------------------------------------------"

# Start the service
sudo systemctl start harvey-backend
sleep 5

# Check status
if systemctl is-active --quiet harvey-backend; then
    echo -e "${GREEN}✅ harvey-backend is now RUNNING${NC}"
else
    echo -e "${RED}❌ harvey-backend failed to start${NC}"
    echo ""
    echo "Checking logs:"
    sudo journalctl -u harvey-backend -n 20 --no-pager
fi

echo ""
echo "4️⃣ Verifying services..."
echo "------------------------------------------"

# Check what's listening now
echo "Port 8001:"
sudo ss -tlnp | grep :8001 || echo "  ❌ Nothing listening on port 8001"

echo ""
echo "Port 9000:"
sudo ss -tlnp | grep :9000 || echo "  ✅ ML Service on port 9000"

echo ""
echo "5️⃣ Testing endpoints..."
echo "------------------------------------------"

# Test Harvey API
echo -n "Harvey API (8001): "
if curl -s --max-time 2 http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ WORKING${NC}"
    curl -s http://localhost:8001/health | python3 -m json.tool
else
    echo -e "${RED}❌ NOT RESPONDING${NC}"
fi

echo ""
echo -n "ML Service (9000): "
if curl -s --max-time 2 http://localhost:9000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ WORKING${NC}"
else
    echo -e "${RED}❌ NOT RESPONDING${NC}"
fi

echo ""
echo "=========================================="
echo "🎯 ALTERNATIVE: Change Harvey to port 8002"
echo "=========================================="
echo ""
echo "If port 8001 keeps being occupied, change to 8002:"
echo ""
echo "1. Edit service file:"
echo "   sudo nano /etc/systemd/system/harvey-backend.service"
echo "   Change: --port 8001 → --port 8002"
echo ""
echo "2. Reload and restart:"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl restart harvey-backend"
echo ""
echo "3. Update Azure NSG to allow port 8002"
echo ""
echo "=========================================="