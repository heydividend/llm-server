"""
Test the Training Data Ingestion System
Demonstrates how Harvey learns from 1,000+ dividend questions.
"""

import requests
import json
import time

# API configuration
BASE_URL = "http://localhost:5000/v1"
API_KEY = "test-key"  # Replace with actual key

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}


def test_training_categories():
    """Get list of training categories."""
    print("\n🔍 Getting Training Categories...")
    response = requests.get(
        f"{BASE_URL}/training/categories",
        headers=headers
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {len(data['categories'])} categories")
        print(f"📊 Total questions: {data['total_questions']}")
        for cat in data['categories']:
            print(f"  - {cat['name']}: {cat['question_count']} questions")
    else:
        print(f"❌ Error: {response.status_code}")
    return response.status_code == 200


def test_ingest_questions():
    """Ingest training questions into database."""
    print("\n📥 Ingesting Training Questions...")
    response = requests.post(
        f"{BASE_URL}/training/ingest",
        json={"batch_size": 50},
        headers=headers
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data['message']}")
        if 'category_counts' in data:
            for cat, count in data['category_counts'].items():
                print(f"  - {cat}: {count} questions")
    else:
        print(f"❌ Error: {response.status_code}")
    return response.status_code == 200


def test_process_batch():
    """Process questions through multi-model system."""
    print("\n⚙️ Processing Training Batch...")
    response = requests.post(
        f"{BASE_URL}/training/process",
        json={"batch_size": 5, "run_async": False},
        headers=headers
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data.get('message', 'Processing started')}")
        if 'processed_count' in data:
            print(f"  Processed: {data['processed_count']} questions")
    else:
        print(f"❌ Error: {response.status_code}")
    return response.status_code == 200


def test_training_status():
    """Check training system status."""
    print("\n📊 Getting Training Status...")
    response = requests.get(
        f"{BASE_URL}/training/status",
        headers=headers
    )
    if response.status_code == 200:
        data = response.json()
        stats = data.get('statistics', {})
        print("✅ Training Statistics:")
        print(f"  - Total Questions: {stats.get('total_questions', 0)}")
        print(f"  - Processed: {stats.get('processed_questions', 0)}")
        print(f"  - Total Responses: {stats.get('total_responses', 0)}")
        print(f"  - Training Examples: {stats.get('training_examples', 0)}")
        print(f"  - Exported: {stats.get('exported_examples', 0)}")
        print(f"  - Avg Quality Score: {stats.get('avg_quality_score', 0):.2f}")
        print(f"  - Processing Rate: {stats.get('processing_rate', '0%')}")
    else:
        print(f"❌ Error: {response.status_code}")
    return response.status_code == 200


def test_export_data():
    """Export training data for fine-tuning."""
    print("\n📤 Exporting Training Data...")
    response = requests.post(
        f"{BASE_URL}/training/export",
        params={"min_quality": 0.8},
        headers=headers
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data['message']}")
        if 'data' in data and len(data['data']) > 0:
            print(f"  Format: {data.get('format', 'unknown')}")
            print(f"  Sample:")
            sample = data['data'][0] if data['data'] else {}
            print(f"    {json.dumps(sample, indent=4)[:500]}...")
    else:
        print(f"❌ Error: {response.status_code}")
    return response.status_code == 200


def main():
    """Run all training system tests."""
    print("=" * 60)
    print("🧠 Harvey Training System Test")
    print("=" * 60)
    
    tests = [
        ("Categories", test_training_categories),
        ("Ingest", test_ingest_questions),
        ("Process", test_process_batch),
        ("Status", test_training_status),
        ("Export", test_export_data)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
            time.sleep(1)  # Small delay between tests
        except Exception as e:
            print(f"❌ {name} test failed: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {name}")
    
    all_passed = all(success for _, success in results)
    if all_passed:
        print("\n🎉 All tests passed! Harvey's training system is ready.")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")
    
    print("=" * 60)


if __name__ == "__main__":
    main()