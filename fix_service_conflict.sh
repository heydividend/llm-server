#!/bin/bash
# Fix Harvey and ML Service Conflict on Well-Resourced VM

echo "================================================"
echo "🔧 Fixing Harvey/ML Service Conflict"
echo "================================================"
echo "VM Resources: 27GB RAM (20GB free) - Not a memory issue!"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "1️⃣ Checking Current Service Status"
echo "------------------------------------------------"

# Check both services
systemctl status harvey-backend --no-pager | head -5
echo ""
systemctl status harvey-ml --no-pager | head -5

echo ""
echo "2️⃣ Looking for Port Conflicts"
echo "------------------------------------------------"

# Check all listening ports
echo "Services on our ports:"
sudo ss -tlnp | grep -E ":(8001|9000)"

echo ""
echo "3️⃣ Checking for Process Crashes"
echo "------------------------------------------------"

# Look for OOM kills or crashes
echo "Checking for service crashes in last hour:"
sudo journalctl --since "1 hour ago" | grep -E "(harvey-backend|harvey-ml).*(Stopped|Failed|killed)" | tail -5

echo ""
echo "4️⃣ Fixing Service Configuration"
echo "------------------------------------------------"

# Update Harvey Backend service with better configuration
sudo tee /etc/systemd/system/harvey-backend.service > /dev/null << 'EOF'
[Unit]
Description=Harvey Backend API
After=network.target
Wants=harvey-ml.service

[Service]
Type=simple
User=azureuser
WorkingDirectory=/home/azureuser/harvey
Environment="ODBCSYSINI=/home/azureuser"
Environment="PATH=/home/azureuser/miniconda3/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
EnvironmentFile=/home/azureuser/harvey/.env
ExecStart=/home/azureuser/miniconda3/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8001 --workers 1
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Update ML Service configuration
sudo tee /etc/systemd/system/harvey-ml.service > /dev/null << 'EOF'
[Unit]
Description=Harvey ML Service
After=network.target

[Service]
Type=simple
User=azureuser
WorkingDirectory=/home/azureuser/harvey/ml_training
Environment="PATH=/home/azureuser/miniconda3/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
EnvironmentFile=/home/azureuser/harvey/.env
ExecStart=/home/azureuser/miniconda3/bin/python -m uvicorn ml_api:app --host 0.0.0.0 --port 9000 --workers 1
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✅ Service configurations updated${NC}"

echo ""
echo "5️⃣ Reloading and Restarting Services"
echo "------------------------------------------------"

# Reload systemd
sudo systemctl daemon-reload

# Stop both services completely
sudo systemctl stop harvey-backend harvey-ml
sleep 3

# Kill any lingering processes
sudo pkill -f "uvicorn.*8001" 2>/dev/null
sudo pkill -f "uvicorn.*9000" 2>/dev/null
sleep 2

# Start ML first
echo "Starting ML Service first..."
sudo systemctl start harvey-ml
sleep 5

# Check if ML started
if systemctl is-active --quiet harvey-ml; then
    echo -e "${GREEN}✅ ML Service started successfully${NC}"
else
    echo -e "${RED}❌ ML Service failed to start${NC}"
    sudo journalctl -u harvey-ml -n 20 --no-pager
fi

# Start Harvey
echo "Starting Harvey Backend..."
sudo systemctl start harvey-backend
sleep 5

# Check if Harvey started
if systemctl is-active --quiet harvey-backend; then
    echo -e "${GREEN}✅ Harvey Backend started successfully${NC}"
else
    echo -e "${RED}❌ Harvey Backend failed to start${NC}"
    sudo journalctl -u harvey-backend -n 20 --no-pager
fi

echo ""
echo "6️⃣ Testing Both Services"
echo "------------------------------------------------"

# Test Harvey
echo -n "Harvey API (localhost:8001): "
HARVEY_TEST=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 http://localhost:8001/docs)
if [ "$HARVEY_TEST" = "200" ]; then
    echo -e "${GREEN}✅ WORKING${NC}"
else
    echo -e "${RED}❌ NOT WORKING (HTTP $HARVEY_TEST)${NC}"
fi

# Test ML
echo -n "ML Service (localhost:9000): "
ML_TEST=$(curl -s --max-time 3 http://localhost:9000/health 2>/dev/null)
if echo "$ML_TEST" | grep -q "Healthy"; then
    echo -e "${GREEN}✅ WORKING${NC}"
else
    echo -e "${RED}❌ NOT WORKING${NC}"
fi

echo ""
echo "7️⃣ External Access Test"
echo "------------------------------------------------"

echo -n "Harvey External (20.81.210.213:8001): "
HARVEY_EXT=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://20.81.210.213:8001/docs)
if [ "$HARVEY_EXT" = "200" ]; then
    echo -e "${GREEN}✅ ACCESSIBLE${NC}"
else
    echo -e "${YELLOW}⚠️ NOT ACCESSIBLE (HTTP $HARVEY_EXT)${NC}"
fi

echo -n "ML External (20.81.210.213:9000): "
ML_EXT=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://20.81.210.213:9000/health)
if [ "$ML_EXT" = "200" ]; then
    echo -e "${GREEN}✅ ACCESSIBLE${NC}"
else
    echo -e "${YELLOW}⚠️ NOT ACCESSIBLE (HTTP $ML_EXT)${NC}"
    echo "  → Add Azure NSG rule for port 9000"
fi

echo ""
echo "8️⃣ Checking for Specific Errors"
echo "------------------------------------------------"

# Check if Harvey is trying to connect to ML and failing
echo "Checking Harvey->ML connection attempts:"
sudo journalctl -u harvey-backend --since "5 minutes ago" 2>/dev/null | grep -i "ml.*service\|9000\|connection" | tail -3

echo ""
echo "================================================"
echo "✅ SERVICE CONFLICT FIX COMPLETE"
echo "================================================"
echo ""

# Final status
if [ "$HARVEY_TEST" = "200" ] && echo "$ML_TEST" | grep -q "Healthy"; then
    echo -e "${GREEN}🎉 SUCCESS! Both services are running together!${NC}"
    echo ""
    echo "Services are working at:"
    echo "  • Harvey API: http://localhost:8001 (and http://20.81.210.213:8001)"
    echo "  • ML Service: http://localhost:9000"
    echo ""
    echo "Note: ML Service external access needs Azure NSG rule for port 9000"
else
    echo -e "${YELLOW}⚠️ One or both services still having issues${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check logs: sudo journalctl -u harvey-backend -f"
    echo "  2. Check processes: ps aux | grep uvicorn"
    echo "  3. Restart VM if needed: sudo reboot"
fi

echo ""
echo "📊 Resource Usage:"
free -h | grep "^Mem:"
echo ""