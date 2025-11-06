#!/bin/bash
# Quick diagnostic for Harvey API on Azure VM

echo "================================================"
echo "🔍 Harvey API Diagnostic Check"
echo "================================================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo "1️⃣ Service Status:"
echo "------------------------------------------------"
systemctl is-active harvey-backend && echo -e "${GREEN}✅ harvey-backend is ACTIVE${NC}" || echo -e "${RED}❌ harvey-backend is INACTIVE${NC}"
systemctl is-active harvey-ml && echo -e "${GREEN}✅ harvey-ml is ACTIVE${NC}" || echo -e "${RED}❌ harvey-ml is INACTIVE${NC}"

echo ""
echo "2️⃣ Port Listening Status:"
echo "------------------------------------------------"
sudo ss -tlnp | grep :8001 && echo -e "${GREEN}✅ Port 8001 is listening${NC}" || echo -e "${RED}❌ Port 8001 NOT listening${NC}"
sudo ss -tlnp | grep :9000 && echo -e "${GREEN}✅ Port 9000 is listening${NC}" || echo -e "${RED}❌ Port 9000 NOT listening${NC}"

echo ""
echo "3️⃣ Recent Harvey Backend Errors:"
echo "------------------------------------------------"
sudo journalctl -u harvey-backend -n 20 --no-pager | grep -E "ERROR|FAILED|error|Error" | tail -5

echo ""
echo "4️⃣ Local Access Test:"
echo "------------------------------------------------"
echo -n "Harvey API (localhost:8001): "
curl -s --max-time 2 http://localhost:8001/health > /dev/null 2>&1 && echo -e "${GREEN}✅ WORKS LOCALLY${NC}" || echo -e "${RED}❌ NOT WORKING LOCALLY${NC}"

echo -n "ML Service (localhost:9000): "
curl -s --max-time 2 http://localhost:9000/health > /dev/null 2>&1 && echo -e "${GREEN}✅ WORKS LOCALLY${NC}" || echo -e "${RED}❌ NOT WORKING LOCALLY${NC}"

echo ""
echo "5️⃣ Last 10 Lines of Harvey Backend Log:"
echo "------------------------------------------------"
sudo journalctl -u harvey-backend -n 10 --no-pager

echo ""
echo "================================================"