#!/usr/bin/env python
"""
Simple test for ML scheduler integration
"""

import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing ML Scheduler Integration...")

# Test basic imports
try:
    from app.services.ml_api_client import MLAPIClient
    print("✓ MLAPIClient imported")
except Exception as e:
    print(f"✗ Failed to import MLAPIClient: {e}")

try:
    from app.services.ml_schedulers_service import MLSchedulersService
    print("✓ MLSchedulersService imported")
except Exception as e:
    print(f"✗ Failed to import MLSchedulersService: {e}")

# Test creating instances
try:
    client = MLAPIClient()
    print("✓ MLAPIClient instance created")
    
    # Test new methods exist
    if hasattr(client, 'get_dividend_calendar'):
        print("✓ get_dividend_calendar method exists")
    if hasattr(client, 'get_training_status'):
        print("✓ get_training_status method exists")
    if hasattr(client, 'get_payout_ratings'):
        print("✓ get_payout_ratings method exists")
        
except Exception as e:
    print(f"✗ Failed to create MLAPIClient: {e}")

try:
    service = MLSchedulersService()
    print("✓ MLSchedulersService instance created")
except Exception as e:
    print(f"✗ Failed to create MLSchedulersService: {e}")

# Test ML integration
try:
    from app.services.ml_integration import get_ml_integration
    ml_integration = get_ml_integration()
    print("✓ ML integration instance created")
    
    # Test new methods exist
    if hasattr(ml_integration, 'get_scheduled_payout_ratings'):
        print("✓ get_scheduled_payout_ratings method exists")
    if hasattr(ml_integration, 'get_dividend_calendar_predictions'):
        print("✓ get_dividend_calendar_predictions method exists")
    if hasattr(ml_integration, 'get_ml_training_status'):
        print("✓ get_ml_training_status method exists")
    if hasattr(ml_integration, 'get_scheduler_health'):
        print("✓ get_scheduler_health method exists")
        
except Exception as e:
    print(f"✗ Failed to create ML integration: {e}")

print("\nIntegration test complete!")