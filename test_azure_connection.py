#!/usr/bin/env python3
"""Test Harvey Azure VM Deployment"""

import requests
import json
from datetime import datetime

def test_service(name, url, timeout=5):
    """Test a service endpoint"""
    print(f"\n{'='*50}")
    print(f"Testing {name}")
    print(f"URL: {url}")
    print(f"{'='*50}")
    
    try:
        response = requests.get(url, timeout=timeout)
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Response: {response.json()}")
        return True
    except requests.exceptions.ConnectTimeout:
        print(f"❌ Connection timeout - Port might be blocked by firewall")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection refused - Service might not be running")
        print(f"   Error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    print(f"\n🧪 Testing Harvey Azure VM Deployment")
    print(f"Time: {datetime.now()}")
    
    # Azure VM endpoints
    base_url = "20.81.210.213"
    
    services = [
        ("Harvey API", f"http://{base_url}:8001/health"),
        ("ML Service", f"http://{base_url}:9000/health"),
    ]
    
    results = []
    for name, url in services:
        success = test_service(name, url)
        results.append((name, success))
    
    # Summary
    print(f"\n{'='*50}")
    print("📊 Summary")
    print(f"{'='*50}")
    
    for name, success in results:
        status = "✅ ACCESSIBLE" if success else "❌ NOT ACCESSIBLE"
        print(f"{name}: {status}")
    
    if not all(r[1] for r in results):
        print("\n⚠️  AZURE NETWORK SECURITY GROUP (NSG) FIX REQUIRED:")
        print("1. Go to Azure Portal")
        print("2. Navigate to your VM → Networking")
        print("3. Add inbound port rules:")
        print("   - Port 8001 (Harvey API) - Priority 100")
        print("   - Port 9000 (ML Service) - Priority 110")
        print("4. Source: Any, Protocol: TCP")
        print("\nOr run this Azure CLI command:")
        print("az vm open-port --resource-group YOUR_RG --name YOUR_VM --port 8001 --priority 100")
        print("az vm open-port --resource-group YOUR_RG --name YOUR_VM --port 9000 --priority 110")

if __name__ == "__main__":
    main()