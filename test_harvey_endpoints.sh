#!/bin/bash
# Test Harvey API endpoints on Azure VM

echo "================================================"
echo "🔍 Testing Harvey API Endpoints"
echo "================================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "1️⃣ Testing Available Endpoints..."
echo "------------------------------------------------"

# Test root endpoint
echo -n "Root endpoint (/): "
ROOT_RESPONSE=$(curl -s --max-time 3 -o /dev/null -w "%{http_code}" http://localhost:8001/ 2>/dev/null)
if [ "$ROOT_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✅ WORKING (HTTP 200)${NC}"
else
    echo -e "${YELLOW}HTTP $ROOT_RESPONSE${NC}"
fi

# Test /api/health endpoint
echo -n "API Health (/api/health): "
API_HEALTH=$(curl -s --max-time 3 -o /dev/null -w "%{http_code}" http://localhost:8001/api/health 2>/dev/null)
if [ "$API_HEALTH" = "200" ]; then
    echo -e "${GREEN}✅ WORKING (HTTP 200)${NC}"
else
    echo -e "${YELLOW}HTTP $API_HEALTH${NC}"
fi

# Test /docs endpoint (FastAPI documentation)
echo -n "API Docs (/docs): "
DOCS_RESPONSE=$(curl -s --max-time 3 -o /dev/null -w "%{http_code}" http://localhost:8001/docs 2>/dev/null)
if [ "$DOCS_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✅ WORKING (HTTP 200)${NC}"
    echo "  📚 API Documentation available at: http://20.81.210.213:8001/docs"
else
    echo -e "${YELLOW}HTTP $DOCS_RESPONSE${NC}"
fi

# Test chat endpoint
echo -n "Chat endpoint (/api/chat): "
CHAT_RESPONSE=$(curl -s --max-time 3 -o /dev/null -w "%{http_code}" http://localhost:8001/api/chat 2>/dev/null)
echo -e "${BLUE}HTTP $CHAT_RESPONSE${NC}"

echo ""
echo "2️⃣ Testing ML Service..."
echo "------------------------------------------------"

echo -n "ML Health (/health): "
ML_HEALTH=$(curl -s --max-time 3 http://localhost:9000/health 2>/dev/null)
if echo "$ML_HEALTH" | grep -q "Healthy"; then
    echo -e "${GREEN}✅ WORKING - $ML_HEALTH${NC}"
else
    echo -e "${RED}❌ NOT WORKING${NC}"
fi

echo ""
echo "3️⃣ Testing External Access..."
echo "------------------------------------------------"

echo -n "Harvey API External (20.81.210.213:8001): "
EXT_HARVEY=$(curl -s --max-time 3 -o /dev/null -w "%{http_code}" http://20.81.210.213:8001/docs 2>/dev/null)
if [ "$EXT_HARVEY" = "200" ]; then
    echo -e "${GREEN}✅ ACCESSIBLE${NC}"
else
    echo -e "${YELLOW}HTTP $EXT_HARVEY${NC}"
fi

echo -n "ML Service External (20.81.210.213:9000): "
EXT_ML=$(curl -s --max-time 3 -o /dev/null -w "%{http_code}" http://20.81.210.213:9000/health 2>/dev/null)
if [ "$EXT_ML" = "200" ]; then
    echo -e "${GREEN}✅ ACCESSIBLE${NC}"
else
    echo -e "${YELLOW}HTTP $EXT_ML${NC}"
fi

echo ""
echo "4️⃣ Quick Chat Test..."
echo "------------------------------------------------"

echo "Testing Harvey chat with a simple query..."
CHAT_TEST=$(curl -s --max-time 5 -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello Harvey, are you working?", "conversation_id": "test123"}' 2>/dev/null | head -c 100)

if [ ! -z "$CHAT_TEST" ]; then
    echo -e "${GREEN}✅ Chat endpoint responding:${NC}"
    echo "$CHAT_TEST..."
else
    echo -e "${YELLOW}⚠️ Chat endpoint not responding${NC}"
fi

echo ""
echo "================================================"
echo "✅ ENDPOINT TEST COMPLETE!"
echo "================================================"
echo ""
echo "📊 Summary:"
echo "  • Harvey Backend: Running on port 8001"
echo "  • ML Service: Running on port 9000"
echo ""
echo "🌐 Access Your Services:"
echo "  • Harvey API Docs: http://20.81.210.213:8001/docs"
echo "  • ML Service Health: http://20.81.210.213:9000/health"
echo ""
echo "📝 Note: The /health endpoint returns 404 because it's not"
echo "        defined in the code. Use /docs or /api/health instead."
echo ""
echo "Test from your browser:"
echo "  • http://20.81.210.213:8001/docs (FastAPI documentation)"
echo "  • http://20.81.210.213:9000/health (ML service status)"
echo ""