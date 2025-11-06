#!/bin/bash
# Verify and Fix ML Service Access

echo "================================================"
echo "🔍 Service Verification & ML Fix"
echo "================================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "1️⃣ Current Service Status"
echo "------------------------------------------------"

# Check what's actually listening
echo "Services listening on ports:"
sudo netstat -tlpn | grep -E ":8001|:9000"

echo ""
echo "2️⃣ Testing Local Access"
echo "------------------------------------------------"

# Test Harvey
echo -n "Harvey API (localhost:8001/docs): "
HARVEY_LOCAL=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 http://localhost:8001/docs)
if [ "$HARVEY_LOCAL" = "200" ]; then
    echo -e "${GREEN}✅ WORKING (HTTP 200)${NC}"
else
    echo -e "${RED}❌ NOT WORKING (HTTP $HARVEY_LOCAL)${NC}"
fi

# Test ML Service
echo -n "ML Service (localhost:9000/health): "
ML_LOCAL=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 http://localhost:9000/health)
if [ "$ML_LOCAL" = "200" ]; then
    echo -e "${GREEN}✅ WORKING (HTTP 200)${NC}"
else
    echo -e "${RED}❌ NOT WORKING (HTTP $ML_LOCAL)${NC}"
fi

echo ""
echo "3️⃣ Testing External Access"
echo "------------------------------------------------"

# Test from VM using public IP
echo -n "Harvey API (20.81.210.213:8001): "
HARVEY_EXT=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://20.81.210.213:8001/docs)
if [ "$HARVEY_EXT" = "200" ]; then
    echo -e "${GREEN}✅ EXTERNALLY ACCESSIBLE${NC}"
else
    echo -e "${RED}❌ BLOCKED (HTTP $HARVEY_EXT)${NC}"
fi

echo -n "ML Service (20.81.210.213:9000): "
ML_EXT=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://20.81.210.213:9000/health)
if [ "$ML_EXT" = "200" ]; then
    echo -e "${GREEN}✅ EXTERNALLY ACCESSIBLE${NC}"
else
    echo -e "${RED}❌ BLOCKED (HTTP $ML_EXT)${NC}"
fi

echo ""
echo "4️⃣ Ubuntu Firewall Check"
echo "------------------------------------------------"

# Check UFW
UFW_STATUS=$(sudo ufw status 2>/dev/null | grep -E "Status:")
echo "UFW Firewall: $UFW_STATUS"

if echo "$UFW_STATUS" | grep -q "active"; then
    echo "Adding port 9000 to UFW..."
    sudo ufw allow 9000/tcp
    echo -e "${GREEN}✅ Port 9000 added to UFW${NC}"
fi

# Check iptables
echo ""
echo "IPTables rules for our ports:"
sudo iptables -L INPUT -n -v | grep -E "dpt:(8001|9000)" || echo "No specific rules found"

echo ""
echo "5️⃣ ML Service Details"
echo "------------------------------------------------"

# Check if ML service is actually running
if systemctl is-active --quiet harvey-ml; then
    echo -e "${GREEN}✅ harvey-ml service is ACTIVE${NC}"
    
    # Show process details
    ML_PID=$(systemctl show harvey-ml --property=MainPID --value)
    if [ "$ML_PID" != "0" ]; then
        echo "  Process ID: $ML_PID"
        echo "  Memory: $(ps -o rss= -p $ML_PID | awk '{print int($1/1024) " MB"}' 2>/dev/null)"
    fi
else
    echo -e "${RED}❌ harvey-ml service is NOT ACTIVE${NC}"
    echo "Starting ML service..."
    sudo systemctl start harvey-ml
    sleep 3
fi

echo ""
echo "================================================"
echo "🔐 AZURE NSG CONFIGURATION REQUIRED"
echo "================================================"
echo ""
echo -e "${YELLOW}⚠️ Port 9000 is BLOCKED by Azure Network Security Group${NC}"
echo ""
echo "To fix this, add the following rule in Azure Portal:"
echo ""
echo -e "${BLUE}1. Go to Azure Portal → Your VM → Networking${NC}"
echo -e "${BLUE}2. Click 'Add inbound port rule'${NC}"
echo -e "${BLUE}3. Configure as follows:${NC}"
echo ""
echo "   Source: Any"
echo "   Source port ranges: *"
echo "   Destination: Any"
echo "   Service: Custom"
echo "   Destination port ranges: 9000"
echo "   Protocol: TCP"
echo "   Action: Allow"
echo "   Priority: 1002"
echo "   Name: Allow-ML-Service-9000"
echo ""
echo -e "${BLUE}4. Click 'Add' and wait 1-2 minutes${NC}"
echo ""
echo "================================================"
echo ""
echo "📊 Current Status Summary:"
echo ""
if [ "$HARVEY_LOCAL" = "200" ] && [ "$HARVEY_EXT" = "200" ]; then
    echo "  🟢 Harvey API (8001): Fully Working!"
else
    echo "  🔴 Harvey API (8001): Issue detected"
fi

if [ "$ML_LOCAL" = "200" ]; then
    if [ "$ML_EXT" = "200" ]; then
        echo "  🟢 ML Service (9000): Fully Working!"
    else
        echo "  🟡 ML Service (9000): Working locally, blocked externally"
        echo "      → Add Azure NSG rule for port 9000"
    fi
else
    echo "  🔴 ML Service (9000): Not working"
fi

echo ""
echo "🌐 Once Azure NSG rule is added, test with:"
echo "  curl http://20.81.210.213:8001/docs"
echo "  curl http://20.81.210.213:9000/health"
echo ""