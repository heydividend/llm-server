#!/bin/bash

# Quick verification script for ML Scheduler deployment
# Run this after deploying to Azure VM

AZURE_VM_IP="20.81.210.213"

echo "=================================================="
echo "🔍 Verifying ML Scheduler Deployment"
echo "=================================================="
echo ""

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local method=${3:-GET}
    local data=$4
    local api_key=$5
    
    echo "Testing: $name"
    echo "URL: $url"
    
    if [ "$method" = "POST" ]; then
        if [ -n "$api_key" ]; then
            response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$url" \
                -H "Content-Type: application/json" \
                -H "Authorization: Bearer $api_key" \
                -d "$data" 2>/dev/null)
        else
            response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$url" \
                -H "Content-Type: application/json" \
                -d "$data" 2>/dev/null)
        fi
    else
        if [ -n "$api_key" ]; then
            response=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$url" \
                -H "Authorization: Bearer $api_key" 2>/dev/null)
        else
            response=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$url" 2>/dev/null)
        fi
    fi
    
    http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
    body=$(echo "$response" | grep -v "HTTP_CODE:")
    
    if [ "$http_code" = "200" ]; then
        echo "✅ Status: 200 OK"
        echo "$body" | python -m json.tool 2>/dev/null | head -n 10 || echo "$body" | head -n 3
    elif [ "$http_code" = "401" ]; then
        echo "🔐 Status: 401 - API Key Required"
    elif [ "$http_code" = "404" ]; then
        echo "❌ Status: 404 - Endpoint not found (not deployed yet)"
    else
        echo "⚠️  Status: $http_code"
        echo "$body" | head -n 3
    fi
    echo ""
}

# Check if API key is provided
if [ -n "$1" ]; then
    API_KEY="$1"
    echo "Using provided API key for authenticated endpoints"
else
    API_KEY=""
    echo "No API key provided - testing public endpoints only"
    echo "Usage: $0 YOUR_API_KEY"
fi
echo ""

# Test basic health endpoints
echo "=== Basic Health Checks ==="
echo ""
test_endpoint "Harvey API Health" "http://$AZURE_VM_IP:8001/healthz"
test_endpoint "ML Service Health" "http://$AZURE_VM_IP:9000/health"

# Test ML Scheduler endpoints
echo ""
echo "=== ML Scheduler Endpoints ==="
echo ""

test_endpoint "ML Schedulers Health" \
    "http://$AZURE_VM_IP:8001/v1/ml-schedulers/health" \
    "GET" "" "$API_KEY"

test_endpoint "Training Status" \
    "http://$AZURE_VM_IP:8001/v1/ml-schedulers/training-status" \
    "GET" "" "$API_KEY"

# Test with sample data if API key provided
if [ -n "$API_KEY" ]; then
    echo ""
    echo "=== Testing Data Endpoints ==="
    echo ""
    
    test_endpoint "Payout Ratings" \
        "http://$AZURE_VM_IP:8001/v1/ml-schedulers/payout-ratings" \
        "POST" \
        '{"symbols": ["AAPL", "MSFT"]}' \
        "$API_KEY"
    
    test_endpoint "Dividend Calendar" \
        "http://$AZURE_VM_IP:8001/v1/ml-schedulers/dividend-calendar" \
        "POST" \
        '{"symbols": ["O", "SCHD"], "months_ahead": 3}' \
        "$API_KEY"
fi

# Check service status on VM
echo ""
echo "=== Service Status on Azure VM ==="
echo ""
echo "To check service status, run:"
echo "  ssh azureuser@$AZURE_VM_IP 'sudo systemctl status harvey'"
echo "  ssh azureuser@$AZURE_VM_IP 'sudo systemctl status harvey-payout-rating.timer'"
echo "  ssh azureuser@$AZURE_VM_IP 'sudo systemctl status harvey-dividend-calendar.timer'"
echo ""

# Summary
echo "=================================================="
echo "📊 Verification Summary"
echo "=================================================="
echo ""
echo "If you see:"
echo "  ✅ 200 OK - Endpoint is working correctly"
echo "  🔐 401 - Endpoint requires API key (expected for protected endpoints)"
echo "  ❌ 404 - Endpoint not deployed yet (run deployment script)"
echo "  ⚠️  Other - Check logs for issues"
echo ""
echo "For full testing with API key, run:"
echo "  ./verify_ml_scheduler_deployment.sh YOUR_HARVEY_AI_API_KEY"
echo ""
echo "=================================================="