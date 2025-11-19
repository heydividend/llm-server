"""
Quick test script for Gemini ML Evaluator
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.gemini_ml_evaluator import GeminiMLEvaluator, ModelType


def test_evaluator():
    """Test the ML evaluator with sample predictions."""
    print("="*80)
    print("Testing Gemini ML Model Evaluator")
    print("="*80)
    
    evaluator = GeminiMLEvaluator()
    
    print("\n1️⃣  Testing Dividend Scorer Evaluation...")
    result = evaluator.evaluate_prediction(
        model_type=ModelType.DIVIDEND_SCORER,
        ticker="AAPL",
        prediction_value=85.5,
        model_metadata={
            "grade": "A",
            "confidence": 0.92
        },
        save_to_db=False
    )
    
    if result.get('success'):
        print(f"   ✅ Evaluation successful!")
        print(f"   Ticker: {result['ticker']}")
        print(f"   Validation: {result['validation']}")
        print(f"   Confidence: {result['confidence_score']:.2f}")
        print(f"   Explanation: {result['explanation'][:100]}...")
    else:
        print(f"   ❌ Evaluation failed: {result.get('error')}")
    
    print("\n2️⃣  Testing Yield Predictor Evaluation...")
    result2 = evaluator.evaluate_prediction(
        model_type=ModelType.YIELD_PREDICTOR,
        ticker="JNJ",
        prediction_value=3.2,
        model_metadata={
            "confidence": 0.88,
            "current_yield": 3.0
        },
        save_to_db=False
    )
    
    if result2.get('success'):
        print(f"   ✅ Evaluation successful!")
        print(f"   Ticker: {result2['ticker']}")
        print(f"   Validation: {result2['validation']}")
        print(f"   Confidence: {result2['confidence_score']:.2f}")
        print(f"   Anomaly Detected: {result2.get('anomaly_detected', False)}")
    else:
        print(f"   ❌ Evaluation failed: {result2.get('error')}")
    
    print("\n3️⃣  Testing Batch Evaluation...")
    batch_predictions = [
        {
            'model_type': 'dividend_scorer',
            'ticker': 'MSFT',
            'prediction_value': 78.5,
            'metadata': {'grade': 'B+', 'confidence': 0.85},
            'save_to_db': False
        },
        {
            'model_type': 'growth_predictor',
            'ticker': 'KO',
            'prediction_value': 5.5,
            'metadata': {'confidence': 0.80},
            'save_to_db': False
        }
    ]
    
    batch_results = evaluator.evaluate_batch(
        predictions=batch_predictions,
        batch_size=2
    )
    
    successful = sum(1 for r in batch_results if r.get('success'))
    print(f"   Batch completed: {successful}/{len(batch_predictions)} successful")
    
    print("\n4️⃣  Testing Model Comparison...")
    comparison = evaluator.compare_models(
        ticker="PG",
        predictions={
            'dividend_scorer': 82.0,
            'yield_predictor': 2.8,
            'growth_predictor': 6.2
        }
    )
    
    if comparison:
        print(f"   ✅ Comparison complete!")
        print(f"   Models evaluated: {comparison['models_evaluated']}")
        print(f"   Agreement rate: {comparison['agreement_rate']*100:.1f}%")
        print(f"   Avg confidence: {comparison['avg_confidence']:.2f}")
        print(f"   Anomalies detected: {comparison['anomalies_detected']}")
    
    print("\n" + "="*80)
    print("✅ All tests completed!")
    print("="*80)
    
    return True


if __name__ == '__main__':
    try:
        test_evaluator()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
