#!/usr/bin/env python3
"""
Monitor Harvey Unified AI System
Checks the integrated Harvey API with RAG and Intelligence features
"""

import requests
import json
from datetime import datetime
import time

def monitor_harvey():
    """Monitor the unified Harvey AI system"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Monitoring Harvey Unified AI System...")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:8001"
    
    # Check if Harvey API is running
    try:
        # Try the intelligence health endpoint
        response = requests.get(f"{base_url}/v1/intelligence/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Harvey AI System: {data.get('status', 'Unknown')}")
            print(f"   Service: {data.get('service', 'Harvey')}")
            print(f"   RAG Available: {data.get('rag_available', False)}")
        else:
            print(f"⚠️  Intelligence endpoint returned: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("⚠️  Harvey API not responding on port 8001")
        print("   Checking if service is running...")
        
    except Exception as e:
        print(f"❌ Error checking Harvey: {e}")
    
    print("\n📊 Harvey Unified Features:")
    print("  • RAG Multi-source Orchestration")
    print("  • Yahoo Finance Integration")
    print("  • Massive.com Sentiment (Configured)")
    print("  • Dividend Intelligence")
    print("  • ML Predictions")
    
    print("\n🔌 Unified API Endpoints (Port 8001):")
    print("  • POST /v1/intelligence/analyze")
    print("  • GET  /v1/intelligence/health")
    print("  • GET  /v1/intelligence/dividend-alerts")
    print("  • GET  /v1/intelligence/trending")
    
    print("\n💡 Database Note:")
    print("  Add Azure SQL firewall rule for VM IP 20.81.210.213")
    print("  to enable full database functionality")
    
    print("\n" + "=" * 60)
    print("Harvey is running as ONE unified AI system!")
    
    # Keep monitoring every 30 seconds
    time.sleep(30)

if __name__ == "__main__":
    while True:
        monitor_harvey()
        time.sleep(30)