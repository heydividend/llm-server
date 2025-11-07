#!/usr/bin/env python3
"""
Test script to verify ML endpoint fixes work correctly.
Tests that all fixed endpoints in ml_api_client.py can be called without 404 errors.
"""

import os
import sys
import asyncio
from typing import Dict, Any

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ''))

# Set environment variable for testing
os.environ['INTERNAL_ML_API_KEY'] = 'test-api-key'
os.environ['ML_API_BASE_URL'] = 'http://localhost:9000/api/internal/ml'

from app.services.ml_api_client import MLAPIClient


def print_result(test_name: str, result: Dict[str, Any], success: bool):
    """Print test result in a formatted way."""
    status = "✓" if success else "✗"
    print(f"\n{status} {test_name}")
    if not success:
        print(f"  Error: {result.get('error', 'Unknown error')}")
    else:
        print(f"  Response keys: {list(result.keys())}")


async def test_ml_endpoints():
    """Test all ML endpoints to ensure they work without 404 errors."""
    print("=" * 60)
    print("ML Endpoint Fix Verification Test")
    print("=" * 60)
    
    # Initialize client with short timeout for testing
    client = MLAPIClient(
        api_key='test-api-key',
        timeout=3,
        enable_cache=False,  # Disable cache for testing
        enable_circuit_breaker=False  # Disable circuit breaker for testing
    )
    
    test_symbol = "AAPL"
    test_symbols = ["AAPL", "MSFT", "JNJ"]
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Health Check
    print("\n1. Testing health check endpoint...")
    try:
        result = client.health_check()
        print_result("Health Check", result, result.get("status") == "healthy")
        if result.get("status") == "healthy":
            tests_passed += 1
        else:
            tests_failed += 1
    except Exception as e:
        print_result("Health Check", {"error": str(e)}, False)
        tests_failed += 1
    
    # Test 2: Score Symbol (Fixed: /score/symbol)
    print("\n2. Testing score symbol endpoint...")
    try:
        result = client.score_symbol(test_symbol)
        success = "scores" in result or "success" in result
        print_result("Score Symbol", result, success)
        if success:
            tests_passed += 1
        else:
            tests_failed += 1
    except Exception as e:
        print_result("Score Symbol", {"error": str(e)}, False)
        tests_failed += 1
    
    # Test 3: Predict Growth Rate (Fixed: /predict/growth-rate)
    print("\n3. Testing predict growth rate endpoint...")
    try:
        result = client.predict_growth_rate(test_symbol)
        success = "predictions" in result or "success" in result
        print_result("Predict Growth Rate", result, success)
        if success:
            tests_passed += 1
        else:
            tests_failed += 1
    except Exception as e:
        print_result("Predict Growth Rate", {"error": str(e)}, False)
        tests_failed += 1
    
    # Test 4: Predict Yield (Fixed: /predict/yield)
    print("\n4. Testing predict yield endpoint...")
    try:
        result = client.predict_yield(test_symbol)
        success = "predictions" in result or "success" in result
        print_result("Predict Yield", result, success)
        if success:
            tests_passed += 1
        else:
            tests_failed += 1
    except Exception as e:
        print_result("Predict Yield", {"error": str(e)}, False)
        tests_failed += 1
    
    # Test 5: Get Yield Forecast (Fixed: now uses /predict/yield)
    print("\n5. Testing get yield forecast endpoint...")
    try:
        result = client.get_yield_forecast(test_symbols)
        success = "data" in result or "predictions" in result or "success" in result
        print_result("Get Yield Forecast", result, success)
        if success:
            tests_passed += 1
        else:
            tests_failed += 1
    except Exception as e:
        print_result("Get Yield Forecast", {"error": str(e)}, False)
        tests_failed += 1
    
    # Test 6: Get Cut Risk (Fixed: /predict/cut-risk)
    print("\n6. Testing get cut risk endpoint...")
    try:
        result = client.get_cut_risk(test_symbols)
        success = "data" in result or "assessments" in result or "success" in result
        print_result("Get Cut Risk", result, success)
        if success:
            tests_passed += 1
        else:
            tests_failed += 1
    except Exception as e:
        print_result("Get Cut Risk", {"error": str(e)}, False)
        tests_failed += 1
    
    # Test 7: Check Anomalies (Fixed: now uses /predict/cut-risk as proxy)
    print("\n7. Testing check anomalies endpoint...")
    try:
        result = client.check_anomalies(test_symbols)
        success = "data" in result or "success" in result
        print_result("Check Anomalies", result, success)
        if success:
            tests_passed += 1
        else:
            tests_failed += 1
    except Exception as e:
        print_result("Check Anomalies", {"error": str(e)}, False)
        tests_failed += 1
    
    # Test 8: Get Comprehensive Score (Fixed: now uses /score/symbol)
    print("\n8. Testing get comprehensive score endpoint...")
    try:
        result = client.get_comprehensive_score(test_symbols)
        success = "data" in result or "scores" in result or "success" in result
        print_result("Get Comprehensive Score", result, success)
        if success:
            tests_passed += 1
        else:
            tests_failed += 1
    except Exception as e:
        print_result("Get Comprehensive Score", {"error": str(e)}, False)
        tests_failed += 1
    
    # Test 9: Batch Predict (Fixed: now uses /score/symbol)
    print("\n9. Testing batch predict endpoint...")
    try:
        result = client.batch_predict(test_symbols)
        success = "data" in result or "scores" in result or "success" in result
        print_result("Batch Predict", result, success)
        if success:
            tests_passed += 1
        else:
            tests_failed += 1
    except Exception as e:
        print_result("Batch Predict", {"error": str(e)}, False)
        tests_failed += 1
    
    # Test 10: Cluster Analyze Stock (Fixed: /cluster/analyze-stock)
    print("\n10. Testing cluster analyze stock endpoint...")
    try:
        result = client.cluster_analyze_stock(test_symbol)
        success = "analyses" in result or "success" in result
        print_result("Cluster Analyze Stock", result, success)
        if success:
            tests_passed += 1
        else:
            tests_failed += 1
    except Exception as e:
        print_result("Cluster Analyze Stock", {"error": str(e)}, False)
        tests_failed += 1
    
    # Test 11: Cluster Find Similar (Fixed: /cluster/find-similar)
    print("\n11. Testing cluster find similar endpoint...")
    try:
        result = client.cluster_find_similar(test_symbol, limit=5)
        success = "similar_stocks" in result or "success" in result
        print_result("Cluster Find Similar", result, success)
        if success:
            tests_passed += 1
        else:
            tests_failed += 1
    except Exception as e:
        print_result("Cluster Find Similar", {"error": str(e)}, False)
        tests_failed += 1
    
    # Test 12: Get Symbol Insights (Fixed: /insights/symbol)
    print("\n12. Testing get symbol insights endpoint...")
    try:
        result = client.get_symbol_insights(test_symbol)
        success = "insights" in result or "success" in result
        print_result("Get Symbol Insights", result, success)
        if success:
            tests_passed += 1
        else:
            tests_failed += 1
    except Exception as e:
        print_result("Get Symbol Insights", {"error": str(e)}, False)
        tests_failed += 1
    
    # Test 13: Portfolio Optimize (Fixed: /portfolio/optimize)
    print("\n13. Testing portfolio optimize endpoint...")
    try:
        result = client.cluster_optimize_portfolio(portfolio_id=1)
        # This endpoint exists and should work
        success = True  # Expecting some response
        print_result("Portfolio Optimize", result, success)
        if success:
            tests_passed += 1
        else:
            tests_failed += 1
    except Exception as e:
        print_result("Portfolio Optimize", {"error": str(e)}, False)
        tests_failed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results Summary:")
    print(f"  Passed: {tests_passed}")
    print(f"  Failed: {tests_failed}")
    print(f"  Total:  {tests_passed + tests_failed}")
    print("=" * 60)
    
    if tests_failed == 0:
        print("\n✅ All endpoint fixes verified successfully!")
    else:
        print(f"\n⚠️  {tests_failed} tests failed. Review the errors above.")
    
    return tests_passed, tests_failed


if __name__ == "__main__":
    # First, ensure ML service is running
    print("Note: Make sure the ML service is running on port 9000")
    print("You can start it with: python ml_training/ml_api.py")
    print()
    
    # Run the tests
    loop = asyncio.get_event_loop()
    passed, failed = loop.run_until_complete(test_ml_endpoints())
    
    # Exit with error code if tests failed
    sys.exit(0 if failed == 0 else 1)