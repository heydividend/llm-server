#!/usr/bin/env python3
"""Test Harvey API endpoints"""

import requests
import json
import time

BASE_URL = "http://20.81.210.213:8001"

def test_health():
    """Test health endpoint"""
    try:
        print("Testing health endpoint...")
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False
    return response.status_code == 200

def test_chat():
    """Test chat endpoint with various queries"""
    queries = [
        "What are the top 5 dividend stocks?",
        "Show me REITS with yields over 5%",
        "Analyze AAPL dividend history"
    ]
    
    for query in queries:
        print(f"\n📝 Testing query: '{query}'")
        try:
            response = requests.post(
                f"{BASE_URL}/api/chat",
                json={"query": query, "session_id": "test-session"},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                print("✅ Query successful")
                # Print first 500 chars of response
                result = response.json()
                if 'response' in result:
                    print(f"Response preview: {result['response'][:500]}...")
                if 'model_used' in result:
                    print(f"Model used: {result['model_used']}")
            else:
                print(f"❌ Query failed: Status {response.status_code}")
                print(f"Error: {response.text[:500]}")
                
        except requests.exceptions.Timeout:
            print("⏱️ Request timed out (30s)")
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
        
        time.sleep(2)  # Wait between requests

def test_dividend_endpoints():
    """Test specific dividend analysis endpoints if available"""
    endpoints = [
        "/api/dividends/analyze?symbol=AAPL",
        "/api/portfolio/projection",
        "/api/watchlist/optimize"
    ]
    
    for endpoint in endpoints:
        print(f"\n📊 Testing endpoint: {endpoint}")
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("✅ Endpoint accessible")
            else:
                print(f"⚠️ Status {response.status_code}: {response.text[:200]}")
        except:
            print("❌ Endpoint not available")

if __name__ == "__main__":
    print("=" * 50)
    print("🔧 Testing Harvey API on Azure VM")
    print(f"Target: {BASE_URL}")
    print("=" * 50)
    
    # Test health first
    if test_health():
        # If health passes, test chat
        test_chat()
        # Test dividend endpoints
        test_dividend_endpoints()
    else:
        print("\n⚠️ Harvey might not be accessible from this location")
        print("Please check:")
        print("1. Azure NSG has port 8001 open")
        print("2. Harvey service is running on the VM")
        print("3. No firewall blocking the connection")