#!/usr/bin/env python3
"""
Test ML Scheduler Endpoints with Real Ticker Symbols
"""

import requests
import json
from datetime import datetime

# Configuration
API_BASE = "http://20.81.210.213:8001"
API_KEY = "hh_live_X6SPcjPD5jZhTMw69_internal_api_key"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

def test_payout_ratings():
    """Test the payout ratings endpoint with popular dividend stocks"""
    print("\n" + "="*60)
    print("📊 Testing Payout Ratings Endpoint")
    print("="*60)
    
    tickers = ["AAPL", "JNJ", "KO", "PG", "XOM"]
    
    # Send all tickers at once as a list
    response = requests.post(
        f"{API_BASE}/v1/ml-schedulers/payout-ratings",
        headers=HEADERS,
        json=tickers  # Send as list directly
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Response received:")
        print(f"   Raw response type: {type(data)}")
        
        # Check if it's a dict with 'ratings' key or just a list
        if isinstance(data, dict) and "ratings" in data:
            ratings = data["ratings"]
            print(f"   Found {len(ratings)} ratings")
            
            # Handle both string and dict responses
            for i, rating in enumerate(ratings):
                if isinstance(rating, dict):
                    print(f"\n   {rating.get('ticker', f'Stock {i+1}')}:")
                    print(f"   - Rating: {rating.get('rating', 'N/A')}")
                    print(f"   - Confidence: {rating.get('confidence', 0)*100:.1f}%")
                    print(f"   - Analysis: {rating.get('analysis', 'N/A')[:100]}...")
                else:
                    print(f"   - {tickers[i] if i < len(tickers) else f'Stock {i+1}'}: {rating}")
        elif isinstance(data, list):
            print(f"   Received list of {len(data)} items")
            for i, item in enumerate(data):
                ticker = tickers[i] if i < len(tickers) else f"Stock {i+1}"
                print(f"   - {ticker}: {item}")
        else:
            print(f"   Unexpected response format: {json.dumps(data, indent=2)[:500]}")
    else:
        print(f"\n❌ Error {response.status_code}: {response.text[:200]}")

def test_dividend_calendar():
    """Test the dividend calendar endpoint"""
    print("\n" + "="*60)
    print("📅 Testing Dividend Calendar Endpoint")
    print("="*60)
    
    tickers = ["MSFT", "T", "VZ", "PEP", "MCD"]
    
    # Send all tickers as a list
    response = requests.post(
        f"{API_BASE}/v1/ml-schedulers/dividend-calendar",
        headers=HEADERS,
        json=tickers  # Send as list directly
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Response received:")
        print(f"   Raw response type: {type(data)}")
        
        if isinstance(data, dict) and "predictions" in data:
            predictions = data["predictions"]
            print(f"   Found {len(predictions)} predictions")
            
            for pred in predictions:
                if isinstance(pred, dict):
                    print(f"\n   {pred.get('ticker', 'N/A')}:")
                    print(f"   - Next Ex-Date: {pred.get('ex_date', 'N/A')}")
                    print(f"   - Payment Date: {pred.get('payment_date', 'N/A')}")
                    print(f"   - Est. Amount: ${pred.get('estimated_amount', 0):.2f}")
                    print(f"   - Confidence: {pred.get('confidence', 0)*100:.1f}%")
                else:
                    print(f"   - {pred}")
        elif isinstance(data, list):
            print(f"   Received list of {len(data)} items")
            for i, item in enumerate(data):
                ticker = tickers[i] if i < len(tickers) else f"Stock {i+1}"
                print(f"   - {ticker}: {item}")
        else:
            print(f"   Unexpected response format: {json.dumps(data, indent=2)[:500]}")
    else:
        print(f"\n❌ Error {response.status_code}: {response.text[:200]}")

def test_training_status():
    """Test the training status endpoint"""
    print("\n" + "="*60)
    print("🤖 Testing Training Status Endpoint")
    print("="*60)
    
    response = requests.get(
        f"{API_BASE}/v1/ml-schedulers/training-status",
        headers=HEADERS
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Training Status:")
        print(f"   Status: {data.get('status', 'N/A')}")
        print(f"   Last Run: {data.get('last_run', 'N/A')}")
        print(f"   Next Scheduled: {data.get('next_scheduled', 'N/A')}")
        
        if data.get("models"):
            print(f"\n   Model Performance:")
            for model in data["models"]:
                if isinstance(model, dict):
                    print(f"   - {model.get('name', 'N/A')}: {model.get('accuracy', 0)*100:.1f}% accuracy")
                else:
                    print(f"   - {model}")
    else:
        print(f"\n❌ Error {response.status_code}: {response.text[:200]}")

def test_admin_dashboard():
    """Test the admin dashboard endpoint"""
    print("\n" + "="*60)
    print("📊 Testing Admin Dashboard Endpoint")
    print("="*60)
    
    response = requests.get(
        f"{API_BASE}/v1/ml-schedulers/admin/dashboard",
        headers=HEADERS
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Admin Dashboard:")
        print(f"   Raw response: {json.dumps(data, indent=2)[:1000]}")
        
        if isinstance(data, dict):
            print(f"\n   Dashboard Metrics:")
            print(f"   - Total Runs: {data.get('total_runs', 0)}")
            print(f"   - Success Rate: {data.get('success_rate', 0)*100:.1f}%")
            print(f"   - Avg Processing Time: {data.get('avg_processing_time', 0):.2f}s")
            
            if data.get("recent_runs"):
                print(f"\n   Recent Runs:")
                for run in data["recent_runs"][:3]:
                    if isinstance(run, dict):
                        print(f"   - {run.get('scheduler', 'N/A')}: {run.get('status', 'N/A')} at {run.get('timestamp', 'N/A')}")
                    else:
                        print(f"   - {run}")
    else:
        print(f"\n❌ Error {response.status_code}: {response.text[:200]}")

if __name__ == "__main__":
    print("\n🚀 ML Scheduler Endpoints Test Suite")
    print("Testing with real dividend-paying stocks...\n")
    
    test_payout_ratings()
    test_dividend_calendar()
    test_training_status()
    test_admin_dashboard()
    
    print("\n" + "="*60)
    print("✅ Testing Complete!")
    print("="*60)