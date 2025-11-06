#!/bin/bash
# Fix External Access and Service Issues on Azure VM

echo "================================================"
echo "🔧 Fixing External Access & Service Issues"
echo "================================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "1️⃣ Checking Firewall Rules (ufw)..."
echo "------------------------------------------------"

# Check if ufw is active
if sudo ufw status | grep -q "Status: active"; then
    echo -e "${YELLOW}UFW firewall is active. Adding rules...${NC}"
    
    # Allow ports
    sudo ufw allow 8001/tcp
    sudo ufw allow 9000/tcp
    sudo ufw allow 22/tcp  # Keep SSH open
    
    echo -e "${GREEN}✅ Firewall rules added for ports 8001 and 9000${NC}"
else
    echo -e "${GREEN}✅ UFW firewall is inactive (good for testing)${NC}"
fi

echo ""
echo "2️⃣ Checking iptables Rules..."
echo "------------------------------------------------"

# Check if there are blocking rules
IPTABLES_COUNT=$(sudo iptables -L -n | grep -E "(8001|9000)" | wc -l)
if [ $IPTABLES_COUNT -gt 0 ]; then
    echo -e "${YELLOW}Found iptables rules for our ports${NC}"
    sudo iptables -L -n | grep -E "(8001|9000)"
else
    echo -e "${GREEN}✅ No blocking iptables rules found${NC}"
fi

# Add explicit allow rules if needed
sudo iptables -I INPUT -p tcp --dport 8001 -j ACCEPT 2>/dev/null
sudo iptables -I INPUT -p tcp --dport 9000 -j ACCEPT 2>/dev/null

echo ""
echo "3️⃣ Checking Service Bindings..."
echo "------------------------------------------------"

# Check what's actually listening on the ports
echo "Services listening on ports:"
sudo netstat -tlpn | grep -E "(8001|9000)"

echo ""
echo "4️⃣ Restarting ML Service..."
echo "------------------------------------------------"

# Restart ML service which seems to be having issues
sudo systemctl restart harvey-ml
sleep 5

if systemctl is-active --quiet harvey-ml; then
    echo -e "${GREEN}✅ harvey-ml restarted successfully${NC}"
else
    echo -e "${RED}❌ harvey-ml failed to start${NC}"
    echo "Recent error logs:"
    sudo journalctl -u harvey-ml -n 10 --no-pager | grep -i error
fi

echo ""
echo "5️⃣ Testing Local Endpoints..."
echo "------------------------------------------------"

# Test Harvey locally
echo -n "Harvey API (localhost:8001): "
if curl -s --max-time 3 http://localhost:8001/docs -o /dev/null; then
    echo -e "${GREEN}✅ WORKING${NC}"
else
    echo -e "${RED}❌ NOT WORKING${NC}"
fi

# Test ML service locally  
echo -n "ML Service (localhost:9000): "
ML_RESPONSE=$(curl -s --max-time 3 http://localhost:9000/health 2>/dev/null)
if echo "$ML_RESPONSE" | grep -q "Healthy"; then
    echo -e "${GREEN}✅ WORKING - $ML_RESPONSE${NC}"
else
    echo -e "${RED}❌ NOT WORKING${NC}"
    # Try alternative endpoints
    echo "  Trying /api/health..."
    curl -s --max-time 3 http://localhost:9000/api/health
fi

echo ""
echo "6️⃣ Testing External Access (from VM)..."
echo "------------------------------------------------"

# Test using public IP from the VM itself
echo -n "Harvey via Public IP: "
if curl -s --max-time 5 http://20.81.210.213:8001/docs -o /dev/null; then
    echo -e "${GREEN}✅ ACCESSIBLE${NC}"
else
    echo -e "${RED}❌ NOT ACCESSIBLE${NC}"
fi

echo -n "ML Service via Public IP: "
if curl -s --max-time 5 http://20.81.210.213:9000/health -o /dev/null; then
    echo -e "${GREEN}✅ ACCESSIBLE${NC}"
else
    echo -e "${RED}❌ NOT ACCESSIBLE${NC}"
fi

echo ""
echo "7️⃣ Azure NSG Rules Check..."
echo "------------------------------------------------"

echo -e "${BLUE}Azure Network Security Group Rules:${NC}"
echo ""
echo "You need to verify in Azure Portal that NSG has these rules:"
echo "  • Port 8001: Allow inbound from any source (or your IP)"
echo "  • Port 9000: Allow inbound from any source (or your IP)"
echo ""
echo "To check/add in Azure Portal:"
echo "1. Go to your VM in Azure Portal"
echo "2. Click on 'Networking' in the left menu"
echo "3. Check 'Inbound port rules'"
echo "4. Add rules if missing:"
echo "   - Name: Allow-8001"
echo "   - Port: 8001"
echo "   - Protocol: TCP"
echo "   - Source: Any"
echo "   - Action: Allow"
echo ""

echo ""
echo "8️⃣ Testing Alternative Endpoints..."
echo "------------------------------------------------"

# Find the actual endpoints available
echo "Checking available Harvey endpoints..."
curl -s http://localhost:8001/openapi.json 2>/dev/null | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    paths = data.get('paths', {})
    print('Available endpoints:')
    for path in paths.keys():
        print(f'  • {path}')
except:
    print('Could not fetch OpenAPI spec')
" 2>/dev/null

echo ""
echo "================================================"
echo "✅ DIAGNOSTICS COMPLETE!"
echo "================================================"
echo ""
echo "📊 Summary:"

# Final status check
HARVEY_LOCAL=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/docs)
ML_LOCAL=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/health)
HARVEY_EXT=$(timeout 3 curl -s -o /dev/null -w "%{http_code}" http://20.81.210.213:8001/docs 2>/dev/null)
ML_EXT=$(timeout 3 curl -s -o /dev/null -w "%{http_code}" http://20.81.210.213:9000/health 2>/dev/null)

echo "  Local Access:"
echo "    • Harvey (8001): $([[ "$HARVEY_LOCAL" == "200" ]] && echo "✅ WORKING" || echo "❌ HTTP $HARVEY_LOCAL")"
echo "    • ML Service (9000): $([[ "$ML_LOCAL" == "200" ]] && echo "✅ WORKING" || echo "❌ HTTP $ML_LOCAL")"
echo ""
echo "  External Access:"
echo "    • Harvey (8001): $([[ "$HARVEY_EXT" == "200" ]] && echo "✅ WORKING" || echo "❌ HTTP $HARVEY_EXT (timeout/blocked)")"
echo "    • ML Service (9000): $([[ "$ML_EXT" == "200" ]] && echo "✅ WORKING" || echo "❌ HTTP $ML_EXT (timeout/blocked)")"

echo ""
echo "🔧 If external access is still blocked:"
echo "  1. Check Azure NSG rules in Portal"
echo "  2. Ensure VM public IP hasn't changed"
echo "  3. Try from different network/device"
echo "  4. Check if Azure has any DDoS protection blocking"
echo ""
echo "📝 Quick test from your local machine:"
echo "  curl http://20.81.210.213:8001/docs"
echo "  curl http://20.81.210.213:9000/health"
echo ""