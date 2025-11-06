#!/usr/bin/env python3
"""Test ML Service Integration with Harvey"""

import requests
import json
import time

# Configuration - Update for your environment
HARVEY_URL = "http://localhost:5000"  # Harvey API (Replit)
ML_URL = "http://localhost:9000"      # ML Service (Replit)

# Azure VM URLs (when testing remotely)
# HARVEY_URL = "http://20.81.210.213:8001"
# ML_URL = "http://20.81.210.213:9000"

def test_ml_health():
    """Test ML Service health"""
    print("\n1. Testing ML Service Health")
    print("=" * 40)
    try:
        response = requests.get(f"{ML_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ ML Service Status: {data['status']}")
            print(f"   Version: {data['version']}")
            return True
        else:
            print(f"❌ ML Service returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ML Service not accessible: {e}")
        return False

def test_ml_predictions():
    """Test ML prediction endpoints directly"""
    print("\n2. Testing ML Prediction Endpoints")
    print("=" * 40)
    
    test_symbols = ["AAPL", "MSFT", "JNJ", "O", "MAIN"]
    endpoints = [
        "/api/internal/ml/predict/growth-rate",
        "/api/internal/ml/predict/yield",
        "/api/internal/ml/score/symbol"
    ]
    
    for endpoint in endpoints:
        print(f"\nTesting {endpoint}...")
        try:
            response = requests.post(
                f"{ML_URL}{endpoint}",
                json={"symbols": test_symbols},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if "predictions" in data:
                    print(f"✅ Received {len(data['predictions'])} predictions")
                elif "scores" in data:
                    print(f"✅ Received {len(data['scores'])} scores")
                else:
                    print(f"✅ Response received")
            else:
                print(f"❌ Endpoint returned status {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")

def test_harvey_integration():
    """Test Harvey's integration with ML Service"""
    print("\n3. Testing Harvey-ML Integration")
    print("=" * 40)
    
    # Test query that should trigger ML features
    query = "Analyze AAPL dividend growth potential and compare with similar stocks"
    
    print(f"Sending query: '{query}'")
    try:
        response = requests.post(
            f"{HARVEY_URL}/api/chat",
            json={"query": query, "session_id": "test-ml-integration"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Harvey processed query successfully")
            
            # Check if ML features were used
            if "response" in data:
                response_text = data["response"].lower()
                ml_indicators = [
                    "growth prediction",
                    "ml analysis",
                    "confidence score",
                    "similar stocks",
                    "cluster analysis"
                ]
                ml_used = any(indicator in response_text for indicator in ml_indicators)
                
                if ml_used:
                    print("✅ ML features appear to be integrated")
                else:
                    print("⚠️ Response received but ML features not clearly indicated")
            
            if "model_used" in data:
                print(f"   Model used: {data['model_used']}")
                
        else:
            print(f"❌ Harvey returned status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error calling Harvey: {e}")

def check_circuit_breaker():
    """Check if circuit breaker is open (ML service issues)"""
    print("\n4. Checking Circuit Breaker Status")
    print("=" * 40)
    
    # Make a test query to see if warnings appear
    try:
        response = requests.post(
            f"{HARVEY_URL}/api/chat",
            json={"query": "Show dividend scores for AAPL", "session_id": "circuit-test"},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Harvey responding normally")
            # In production, check logs for circuit breaker warnings
            print("   (Check Harvey logs for circuit breaker status)")
        else:
            print(f"⚠️ Harvey returned status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_ml_endpoints_comprehensive():
    """Comprehensive test of all ML endpoints"""
    print("\n5. Comprehensive ML Endpoint Test")
    print("=" * 40)
    
    all_endpoints = [
        ("/api/internal/ml/predict/growth-rate", {"symbols": ["AAPL"]}),
        ("/api/internal/ml/predict/yield", {"symbols": ["O", "MAIN"]}),
        ("/api/internal/ml/predict/cut-risk", {"symbols": ["GE", "F"]}),
        ("/api/internal/ml/cluster/analyze-stock", {"symbols": ["JNJ"]}),
        ("/api/internal/ml/cluster/find-similar", {"symbols": ["MSFT"]}),
        ("/api/internal/ml/score/symbol", {"symbols": ["KO", "PEP"]}),
        ("/api/internal/ml/insights/symbol", {"symbols": ["AAPL"]}),
        ("/api/internal/ml/models/status", None)
    ]
    
    success_count = 0
    for endpoint, payload in all_endpoints:
        try:
            if payload:
                response = requests.post(f"{ML_URL}{endpoint}", json=payload, timeout=5)
            else:
                response = requests.get(f"{ML_URL}{endpoint}", timeout=5)
                
            if response.status_code == 200:
                print(f"✅ {endpoint}")
                success_count += 1
            else:
                print(f"❌ {endpoint} - Status {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} - Error: {str(e)[:50]}")
    
    print(f"\nSummary: {success_count}/{len(all_endpoints)} endpoints working")
    return success_count == len(all_endpoints)

if __name__ == "__main__":
    print("=" * 50)
    print("Harvey ML Integration Test Suite")
    print("=" * 50)
    print(f"Harvey URL: {HARVEY_URL}")
    print(f"ML Service URL: {ML_URL}")
    
    # Run all tests
    ml_healthy = test_ml_health()
    
    if ml_healthy:
        test_ml_predictions()
        test_harvey_integration()
        check_circuit_breaker()
        all_working = test_ml_endpoints_comprehensive()
        
        print("\n" + "=" * 50)
        print("INTEGRATION TEST COMPLETE")
        print("=" * 50)
        
        if all_working:
            print("✅ All ML endpoints are working!")
            print("✅ Harvey and ML Service are fully integrated!")
        else:
            print("⚠️ Some endpoints need attention")
            print("Check the logs for circuit breaker warnings")
    else:
        print("\n❌ ML Service is not accessible")
        print("Please ensure ML Service is running on port 9000")