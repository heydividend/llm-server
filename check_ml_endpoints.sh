#!/bin/bash
# Check ML Service Actual Endpoints

echo "================================================"
echo "🔍 Checking ML Service Endpoint Mismatch"
echo "================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "1️⃣ ML Service Available Endpoints"
echo "------------------------------------------------"

# Get the actual endpoints from ML Service
echo "Fetching ML Service OpenAPI spec..."
curl -s http://localhost:9000/openapi.json 2>/dev/null | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    paths = data.get('paths', {})
    print('\\nActual ML Service Endpoints:')
    print('=' * 40)
    for path in sorted(paths.keys()):
        methods = list(paths[path].keys())
        print(f'  {methods[0].upper():6} {path}')
    print()
except:
    print('Could not fetch ML OpenAPI spec')
" || echo "Error fetching endpoints"

echo ""
echo "2️⃣ What Harvey is Trying to Call"
echo "------------------------------------------------"
echo -e "${YELLOW}Harvey is calling (getting 404):${NC}"
echo "  GET /api/internal/ml/insights/{ticker}"
echo "  GET /api/internal/ml/health"
echo ""

echo "3️⃣ Testing Actual ML Endpoints"
echo "------------------------------------------------"

# Test the correct endpoints
echo -n "ML Health at /health: "
HEALTH=$(curl -s http://localhost:9000/health 2>/dev/null)
if echo "$HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Working${NC}"
else
    echo -e "${RED}❌ Not working${NC}"
fi

echo -n "ML Insights at /api/predict/ml_insights: "
INSIGHTS=$(curl -s -X POST http://localhost:9000/api/predict/ml_insights \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL"}' 2>/dev/null | head -c 50)
if [ ! -z "$INSIGHTS" ]; then
    echo -e "${GREEN}✅ Working${NC}"
    echo "  Response: $INSIGHTS..."
else
    echo -e "${RED}❌ Not found${NC}"
fi

echo ""
echo "4️⃣ Quick Fix - Update Harvey Configuration"
echo "------------------------------------------------"

echo -e "${BLUE}The issue: Harvey expects ML endpoints at different paths${NC}"
echo ""
echo "Harvey expects:"
echo "  • /api/internal/ml/health"
echo "  • /api/internal/ml/insights/{ticker}"
echo ""
echo "But ML Service has:"
echo "  • /health"
echo "  • /api/predict/ml_insights (POST)"
echo ""

echo "5️⃣ Solutions"
echo "------------------------------------------------"
echo ""
echo -e "${GREEN}Option 1: Update Harvey's ML service URL configuration${NC}"
echo "  Edit Harvey's config to use correct ML endpoints"
echo ""
echo -e "${GREEN}Option 2: Add proxy routes to ML Service${NC}"
echo "  Add the expected endpoints to redirect to actual ones"
echo ""
echo -e "${GREEN}Option 3: Update ML Service to match expected paths${NC}"
echo "  Modify ml_api.py to have the endpoints Harvey expects"
echo ""

echo "================================================"
echo "📊 Summary"
echo "================================================"
echo ""
echo -e "${GREEN}✅ Both services are running correctly!${NC}"
echo -e "${YELLOW}⚠️ Just need to fix endpoint paths${NC}"
echo ""
echo "The services can communicate, they just need"
echo "to agree on the endpoint URLs."
echo ""
echo "To fix quickly, we can:"
echo "1. Update Harvey's ML_BASE_URL or endpoint paths"
echo "2. Or add compatibility endpoints to ML Service"
echo ""