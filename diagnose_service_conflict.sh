#!/bin/bash
# Diagnose Harvey vs ML Service Conflict

echo "================================================"
echo "🔍 Diagnosing Service Conflict Issue"
echo "================================================"
echo "Problem: When ML starts, Harvey stops working"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "1️⃣ Current Service Status"
echo "------------------------------------------------"

# Check both services
echo -n "Harvey Backend: "
if systemctl is-active --quiet harvey-backend; then
    echo -e "${GREEN}✅ Active${NC}"
    HARVEY_PID=$(systemctl show harvey-backend --property=MainPID --value)
    echo "  PID: $HARVEY_PID"
else
    echo -e "${RED}❌ Inactive${NC}"
fi

echo -n "ML Service: "
if systemctl is-active --quiet harvey-ml; then
    echo -e "${GREEN}✅ Active${NC}"
    ML_PID=$(systemctl show harvey-ml --property=MainPID --value)
    echo "  PID: $ML_PID"
else
    echo -e "${RED}❌ Inactive${NC}"
fi

echo ""
echo "2️⃣ Memory Usage Check"
echo "------------------------------------------------"

# Check available memory
FREE_MEM=$(free -h | grep "^Mem:" | awk '{print $7}')
TOTAL_MEM=$(free -h | grep "^Mem:" | awk '{print $2}')
echo "System Memory: $FREE_MEM available of $TOTAL_MEM total"

# Check process memory usage
if [ ! -z "$HARVEY_PID" ] && [ "$HARVEY_PID" != "0" ]; then
    HARVEY_MEM=$(ps -o rss= -p $HARVEY_PID 2>/dev/null | awk '{print int($1/1024) " MB"}')
    echo "Harvey Backend Memory: $HARVEY_MEM"
fi

if [ ! -z "$ML_PID" ] && [ "$ML_PID" != "0" ]; then
    ML_MEM=$(ps -o rss= -p $ML_PID 2>/dev/null | awk '{print int($1/1024) " MB"}')
    echo "ML Service Memory: $ML_MEM"
fi

# Check if memory is low
AVAILABLE_MB=$(free -m | grep "^Mem:" | awk '{print $7}')
if [ $AVAILABLE_MB -lt 500 ]; then
    echo -e "${RED}⚠️ LOW MEMORY WARNING: Only ${AVAILABLE_MB}MB available${NC}"
    echo "This could cause services to crash!"
fi

echo ""
echo "3️⃣ Port Conflict Check"
echo "------------------------------------------------"

# Check what's on each port
echo "Port 8001 (Harvey):"
sudo lsof -i:8001 2>/dev/null | grep LISTEN || echo "  Nothing listening"

echo ""
echo "Port 9000 (ML):"
sudo lsof -i:9000 2>/dev/null | grep LISTEN || echo "  Nothing listening"

echo ""
echo "4️⃣ Service Logs Analysis"
echo "------------------------------------------------"

# Check for recent crashes
echo "Harvey Backend recent errors:"
sudo journalctl -u harvey-backend --since "10 minutes ago" 2>/dev/null | grep -E "(ERROR|killed|OOM|memory)" | tail -3 || echo "  No recent errors"

echo ""
echo "ML Service recent errors:"
sudo journalctl -u harvey-ml --since "10 minutes ago" 2>/dev/null | grep -E "(ERROR|killed|OOM|memory)" | tail -3 || echo "  No recent errors"

echo ""
echo "5️⃣ Testing Service Isolation"
echo "------------------------------------------------"

# Stop both services
echo "Stopping both services..."
sudo systemctl stop harvey-backend harvey-ml
sleep 3

# Start only Harvey
echo ""
echo -e "${BLUE}Starting ONLY Harvey Backend...${NC}"
sudo systemctl start harvey-backend
sleep 5

# Test Harvey
echo -n "Harvey API test: "
HARVEY_TEST=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 http://localhost:8001/docs)
if [ "$HARVEY_TEST" = "200" ]; then
    echo -e "${GREEN}✅ Working alone${NC}"
    HARVEY_WORKS_ALONE=true
else
    echo -e "${RED}❌ Not working even alone${NC}"
    HARVEY_WORKS_ALONE=false
fi

# Now start ML
echo ""
echo -e "${BLUE}Now starting ML Service...${NC}"
sudo systemctl start harvey-ml
sleep 5

# Test both
echo ""
echo "Testing with both running:"
echo -n "  Harvey API: "
HARVEY_WITH_ML=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 http://localhost:8001/docs)
if [ "$HARVEY_WITH_ML" = "200" ]; then
    echo -e "${GREEN}✅ Still working${NC}"
else
    echo -e "${RED}❌ Stopped working!${NC}"
fi

echo -n "  ML Service: "
ML_TEST=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 http://localhost:9000/health)
if [ "$ML_TEST" = "200" ]; then
    echo -e "${GREEN}✅ Working${NC}"
else
    echo -e "${RED}❌ Not working${NC}"
fi

echo ""
echo "6️⃣ Resource Limit Check"
echo "------------------------------------------------"

# Check systemd resource limits
echo "Harvey Backend limits:"
systemctl show harvey-backend | grep -E "(LimitNPROC|LimitNOFILE|MemoryLimit)" || echo "  No specific limits set"

echo ""
echo "ML Service limits:"
systemctl show harvey-ml | grep -E "(LimitNPROC|LimitNOFILE|MemoryLimit)" || echo "  No specific limits set"

echo ""
echo "================================================"
echo "📊 DIAGNOSIS RESULTS"
echo "================================================"
echo ""

# Determine the issue
if [ $AVAILABLE_MB -lt 500 ]; then
    echo -e "${RED}🔴 MEMORY EXHAUSTION DETECTED${NC}"
    echo ""
    echo "Solution: Your VM needs more RAM or optimize services"
    echo ""
    echo "Quick fixes:"
    echo "  1. Restart VM to clear memory: sudo reboot"
    echo "  2. Add swap space (temporary fix):"
    echo "     sudo fallocate -l 2G /swapfile"
    echo "     sudo chmod 600 /swapfile"
    echo "     sudo mkswap /swapfile"
    echo "     sudo swapon /swapfile"
    echo ""
    echo "  3. Run services one at a time"
elif [ "$HARVEY_WORKS_ALONE" = true ] && [ "$HARVEY_WITH_ML" != "200" ]; then
    echo -e "${YELLOW}🟡 SERVICE INTERFERENCE DETECTED${NC}"
    echo ""
    echo "Harvey works alone but fails when ML starts."
    echo "Possible causes:"
    echo "  • Shared resource conflict"
    echo "  • Environment variable conflict"
    echo "  • Database connection pool exhaustion"
else
    echo -e "${GREEN}🟢 Services appear compatible${NC}"
    echo "No obvious conflict detected"
fi

echo ""
echo "🔧 Recommended Actions:"
echo "  1. Increase VM memory if possible"
echo "  2. Run services with memory limits"
echo "  3. Monitor with: htop or top"
echo "  4. Check full logs: sudo journalctl -u harvey-backend -f"
echo ""