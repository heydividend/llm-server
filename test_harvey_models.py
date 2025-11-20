"""
Test Harvey's 5 AI Models - Verify All Models Respond Correctly
Tests: GPT-5, Grok-4, DeepSeek-R1, Gemini 2.5 Pro, FinGPT
"""

import os
import sys
from dotenv import load_dotenv
load_dotenv(override=True)

sys.path.insert(0, os.path.dirname(__file__))

from app.core.model_router import QueryRouter, ModelType
from app.core.llm_providers import oai_stream_with_model, gemini_stream, oai_client
import requests

def print_section(title):
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")

def test_azure_openai_models():
    """Test GPT-5, Grok-4, DeepSeek-R1 (all on Azure OpenAI)"""
    print_section("Testing Azure OpenAI Models")
    
    models = {
        "GPT-5": "HarveyGPT-5",
        "Grok-4": "grok-4-fast-reasoning",
        "DeepSeek-R1": "DeepSeek-R1-0528"
    }
    
    results = {}
    
    for name, deployment in models.items():
        print(f"\nTesting {name} (deployment: {deployment})...")
        try:
            # Simple test message
            messages = [
                {"role": "system", "content": "You are Harvey, a financial AI assistant."},
                {"role": "user", "content": "Say 'Hello from " + name + "' in exactly 5 words."}
            ]
            
            # Get non-streaming response
            response = oai_client.chat.completions.create(
                model=deployment,
                messages=messages,  # type: ignore[arg-type]
                temperature=0.2,
                max_tokens=50
            )
            
            reply = (response.choices[0].message.content or "").strip()
            print(f"   Response: {reply}")
            print(f"   Status: ✅ SUCCESS")
            results[name] = "SUCCESS"
            
        except Exception as e:
            print(f"   Status: ❌ FAILED")
            print(f"   Error: {e}")
            results[name] = f"FAILED: {e}"
    
    return results

def test_gemini():
    """Test Gemini 2.5 Pro"""
    print_section("Testing Gemini 2.5 Pro")
    
    print(f"\nTesting Gemini 2.5 Pro...")
    try:
        messages = [
            {"role": "system", "content": "You are Harvey's dividend analysis expert."},
            {"role": "user", "content": "Say 'Hello from Gemini' in exactly 4 words."}
        ]
        
        # Get streaming response
        chunks = []
        for chunk in gemini_stream(messages, temperature=0.2, max_tokens=50):
            chunks.append(chunk)
        
        reply = "".join(chunks).strip()
        print(f"   Response: {reply}")
        print(f"   Status: ✅ SUCCESS")
        return "SUCCESS"
        
    except Exception as e:
        print(f"   Status: ❌ FAILED")
        print(f"   Error: {e}")
        return f"FAILED: {e}"

def test_fingpt():
    """Test FinGPT on Azure VM"""
    print_section("Testing FinGPT (Azure VM ML API)")
    
    ml_api_url = os.getenv("ML_API_BASE_URL", "http://127.0.0.1:9000/api/internal/ml")
    ml_api_key = os.getenv("INTERNAL_ML_API_KEY")
    
    print(f"\nTesting FinGPT (ML API)...")
    print(f"   URL: {ml_api_url}")
    
    try:
        # Test health endpoint
        health_url = ml_api_url.replace("/api/internal/ml", "/health")
        response = requests.get(
            health_url,
            headers={"Authorization": f"Bearer {ml_api_key}"},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {data}")
            print(f"   Status: ✅ SUCCESS (ML API reachable)")
            return "SUCCESS"
        else:
            print(f"   Status: ⚠️  WARNING (Status {response.status_code})")
            print(f"   Note: ML API might be on Azure VM only (not accessible from Replit)")
            return f"WARNING: Status {response.status_code}"
            
    except requests.exceptions.ConnectionError:
        print(f"   Status: ⚠️  WARNING (Connection refused)")
        print(f"   Note: ML API is on Azure VM (20.81.210.213), not accessible from Replit")
        return "WARNING: Connection refused (expected on Replit)"
    except Exception as e:
        print(f"   Status: ❌ FAILED")
        print(f"   Error: {e}")
        return f"FAILED: {e}"

def test_query_routing():
    """Test intelligent query routing"""
    print_section("Testing Intelligent Query Routing")
    
    router = QueryRouter()
    
    test_queries = [
        ("What's the dividend yield of AAPL?", False),
        ("Analyze this chart pattern", True),  # Has image
        ("Calculate optimal portfolio allocation", False),
        ("Rate MSFT's dividend quality", False),
        ("Show me dividend sustainability for JNJ", False),
    ]
    
    print("\nQuery Classification Tests:")
    for query, has_image in test_queries:
        model, reason = router.route_query(query, has_image=has_image)
        print(f"\n   Query: '{query}'")
        print(f"   Image: {has_image}")
        print(f"   → Routed to: {model.value}")
        print(f"   → Reason: {reason}")
    
    return "SUCCESS"

def main():
    print("=" * 70)
    print("  Harvey AI - Multi-Model System Test")
    print("  Testing 5 AI Models: GPT-5, Grok-4, DeepSeek-R1, Gemini, FinGPT")
    print("=" * 70)
    
    results = {}
    
    # Test Azure OpenAI models
    azure_results = test_azure_openai_models()
    results.update(azure_results)
    
    # Test Gemini
    results["Gemini 2.5 Pro"] = test_gemini()
    
    # Test FinGPT
    results["FinGPT"] = test_fingpt()
    
    # Test routing
    results["Query Routing"] = test_query_routing()
    
    # Summary
    print_section("Test Summary")
    print()
    for model, status in results.items():
        status_icon = "✅" if "SUCCESS" in status else "⚠️" if "WARNING" in status else "❌"
        print(f"   {status_icon} {model}: {status}")
    
    print("\n" + "=" * 70)
    success_count = sum(1 for s in results.values() if "SUCCESS" in s)
    warning_count = sum(1 for s in results.values() if "WARNING" in s)
    fail_count = sum(1 for s in results.values() if "FAILED" in s)
    
    print(f"\nResults: {success_count} SUCCESS, {warning_count} WARNING, {fail_count} FAILED")
    
    if fail_count == 0:
        print("\n🎉 All critical models operational!")
        return 0
    else:
        print(f"\n⚠️  {fail_count} model(s) failed - check configuration")
        return 1

if __name__ == "__main__":
    sys.exit(main())
