#!/usr/bin/env python3
"""
Quick test script to verify ETF provider integration works
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.harvey_intelligence import HarveyIntelligence


async def test_provider_queries():
    """Test various provider queries"""
    harvey = HarveyIntelligence()
    
    # Test queries
    queries = [
        "What are the latest distribution amounts for YieldMax ETFs?",
        "Show me all Vanguard ETFs distributions",
        "List all Global X funds",
        "What is TSLY distribution?",  # Single ETF (should not trigger provider)
    ]
    
    for query in queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)
        
        try:
            result = await harvey.analyze_dividend(query)
            
            # Show key results
            print(f"Provider Detected: {result.get('provider_detected', False)}")
            if result.get('provider_detected'):
                print(f"Provider: {result.get('provider_name', 'Unknown')}")
                print(f"ETFs Count: {result.get('etfs_count', 0)}")
                print(f"Frequency: {result.get('distribution_frequency', 'Unknown')}")
            else:
                print(f"Model Used: {result.get('model_used', 'Unknown')}")
                print(f"Routing Reason: {result.get('routing_reason', 'Unknown')}")
            
            # Show first 500 chars of response
            if result.get('ai_response'):
                response_preview = result['ai_response'][:500]
                print(f"\nResponse Preview:\n{response_preview}...")
                
        except Exception as e:
            print(f"ERROR: {e}")
    
    print("\n" + "="*60)
    print("ETF Provider Integration Test Complete!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_provider_queries())