#!/usr/bin/env python3
"""
CLI Tool for Evaluating ML Predictions using Gemini
Part of Phase 4: Gemini ML Model Evaluator

Usage Examples:
    # Evaluate a single ticker
    python scripts/evaluate_ml_predictions.py --ticker AAPL --model dividend_scorer

    # Batch evaluate recent predictions (last 7 days)
    python scripts/evaluate_ml_predictions.py --batch --days 7 --limit 100

    # Generate evaluation report
    python scripts/evaluate_ml_predictions.py --report --model all

    # Evaluate specific model type
    python scripts/evaluate_ml_predictions.py --ticker MSFT --model yield_predictor

    # Batch evaluate with specific model
    python scripts/evaluate_ml_predictions.py --batch --model growth_predictor --limit 50
"""

import sys
import os
import argparse
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from tabulate import tabulate
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.gemini_ml_evaluator import GeminiMLEvaluator, ModelType
from app.services.ml_api_client import get_ml_client
from app.core.database import get_db_connection

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("evaluate_ml_predictions")


class MLPredictionEvaluator:
    """CLI tool for evaluating ML predictions using Gemini."""
    
    def __init__(self):
        """Initialize evaluator and ML client."""
        self.evaluator = GeminiMLEvaluator()
        self.ml_client = get_ml_client()
        logger.info("ML Prediction Evaluator initialized")
    
    def evaluate_ticker(self, ticker: str, model_type: str) -> Dict[str, Any]:
        """
        Evaluate ML prediction for a specific ticker and model.
        
        Args:
            ticker: Stock ticker symbol
            model_type: Model type (e.g., 'dividend_scorer')
        
        Returns:
            Evaluation result
        """
        logger.info(f"Evaluating {model_type} prediction for {ticker}")
        
        try:
            model_enum = ModelType(model_type)
        except ValueError:
            logger.error(f"Invalid model type: {model_type}")
            logger.info(f"Valid model types: {[m.value for m in ModelType]}")
            return {"success": False, "error": f"Invalid model type: {model_type}"}
        
        prediction_value, metadata = self._get_ml_prediction(ticker, model_enum)
        
        if prediction_value is None:
            logger.error(f"Could not get ML prediction for {ticker}")
            return {"success": False, "error": "ML prediction unavailable"}
        
        logger.info(f"Got ML prediction: {prediction_value} for {ticker}")
        
        result = self.evaluator.evaluate_prediction(
            model_type=model_enum,
            ticker=ticker,
            prediction_value=prediction_value,
            model_metadata=metadata,
            save_to_db=True
        )
        
        return result
    
    def evaluate_batch(
        self,
        days: int = 7,
        limit: int = 100,
        model_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Batch evaluate recent ML predictions.
        
        Args:
            days: Look back N days for predictions (default: 7)
            limit: Maximum number to evaluate (default: 100)
            model_type: Optional specific model to evaluate
        
        Returns:
            List of evaluation results
        """
        logger.info(f"Batch evaluating predictions from last {days} days (limit: {limit})")
        
        recent_predictions = self._get_recent_predictions(days, limit, model_type)
        
        if not recent_predictions:
            logger.warning("No recent predictions found to evaluate")
            return []
        
        logger.info(f"Found {len(recent_predictions)} predictions to evaluate")
        
        predictions_to_evaluate = []
        for pred in recent_predictions:
            predictions_to_evaluate.append({
                'model_type': pred['model_type'],
                'ticker': pred['ticker'],
                'prediction_value': pred['prediction_value'],
                'metadata': pred.get('metadata'),
                'save_to_db': True
            })
        
        results = self.evaluator.evaluate_batch(
            predictions=predictions_to_evaluate,
            batch_size=5,
            delay_between_batches=1.0
        )
        
        return results
    
    def generate_report(
        self,
        model_type: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate evaluation report for model performance.
        
        Args:
            model_type: Specific model type or 'all' (default: all)
            days: Report period in days (default: 30)
        
        Returns:
            Report with statistics and insights
        """
        logger.info(f"Generating evaluation report for last {days} days")
        
        stats = self.evaluator.get_evaluation_statistics(days=days)
        
        if model_type and model_type != 'all':
            stats['models'] = [m for m in stats['models'] if m['model_name'] == model_type]
        
        return stats
    
    def _get_ml_prediction(
        self,
        ticker: str,
        model_type: ModelType
    ) -> tuple[Optional[float], Optional[Dict[str, Any]]]:
        """
        Get ML prediction value and metadata for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            model_type: Model type enum
        
        Returns:
            Tuple of (prediction_value, metadata)
        """
        try:
            if model_type == ModelType.DIVIDEND_SCORER:
                result = self.ml_client.score_symbol(ticker)
                if result.get('success'):
                    data = result.get('data', {})
                    return data.get('overall_score'), {
                        'grade': data.get('grade'),
                        'confidence': data.get('confidence')
                    }
            
            elif model_type == ModelType.YIELD_PREDICTOR:
                result = self.ml_client.predict_yield(ticker, horizon="12_months")
                if result.get('success'):
                    data = result.get('data', {})
                    return data.get('predicted_yield'), {
                        'confidence': data.get('confidence'),
                        'current_yield': data.get('current_yield')
                    }
            
            elif model_type == ModelType.GROWTH_PREDICTOR:
                result = self.ml_client.predict_growth_rate(ticker)
                if result.get('success'):
                    data = result.get('data', {})
                    return data.get('predicted_growth_rate'), {
                        'confidence': data.get('confidence'),
                        'historical_growth': data.get('historical_growth')
                    }
            
            elif model_type == ModelType.PAYOUT_PREDICTOR:
                result = self.ml_client.predict_payout_ratio(ticker)
                if result.get('success'):
                    data = result.get('data', {})
                    return data.get('predicted_payout_ratio'), {
                        'confidence': data.get('confidence'),
                        'current_payout': data.get('current_payout')
                    }
            
            elif model_type == ModelType.CUT_RISK_ANALYZER:
                result = self.ml_client.analyze_cut_risk(ticker)
                if result.get('success'):
                    data = result.get('data', {})
                    return data.get('cut_risk_score'), {
                        'risk_level': data.get('risk_level'),
                        'confidence': data.get('confidence')
                    }
            
            elif model_type == ModelType.ANOMALY_DETECTOR:
                result = self.ml_client.detect_anomaly(ticker)
                if result.get('success'):
                    data = result.get('data', {})
                    return data.get('anomaly_score'), {
                        'is_anomalous': data.get('is_anomalous'),
                        'anomaly_type': data.get('anomaly_type')
                    }
            
            elif model_type == ModelType.STOCK_CLUSTERER:
                result = self.ml_client.cluster_analyze_stock(ticker)
                if result.get('success'):
                    data = result.get('data', {})
                    return float(data.get('cluster_id', 0)), {
                        'cluster_name': data.get('cluster_name'),
                        'cluster_characteristics': data.get('characteristics')
                    }
        
        except Exception as e:
            logger.error(f"Failed to get ML prediction: {e}")
        
        return None, None
    
    def _get_recent_predictions(
        self,
        days: int,
        limit: int,
        model_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent ML predictions from database (if stored) or make fresh predictions.
        
        For this implementation, we'll make fresh predictions on popular tickers.
        
        Args:
            days: Look back period (not used in this implementation)
            limit: Maximum predictions to return
            model_type: Optional specific model type
        
        Returns:
            List of predictions
        """
        popular_tickers = [
            'AAPL', 'MSFT', 'JNJ', 'PG', 'KO', 'PEP', 'WMT', 'VZ', 'T',
            'XOM', 'CVX', 'MO', 'PM', 'O', 'MAIN', 'STAG', 'GLAD',
            'SCHD', 'VYM', 'DGRO', 'NOBL', 'SDY', 'DVY', 'VIG'
        ]
        
        tickers = popular_tickers[:min(limit, len(popular_tickers))]
        
        predictions = []
        
        model_types = [model_type] if model_type else [
            'dividend_scorer', 'yield_predictor', 'growth_predictor'
        ]
        
        for ticker in tickers:
            for mt in model_types:
                try:
                    model_enum = ModelType(mt)
                    pred_value, metadata = self._get_ml_prediction(ticker, model_enum)
                    
                    if pred_value is not None:
                        predictions.append({
                            'ticker': ticker,
                            'model_type': mt,
                            'prediction_value': pred_value,
                            'metadata': metadata
                        })
                        
                        if len(predictions) >= limit:
                            return predictions
                
                except Exception as e:
                    logger.debug(f"Skipping {ticker}/{mt}: {e}")
        
        return predictions


def print_evaluation_result(result: Dict[str, Any]):
    """Pretty print evaluation result."""
    if not result.get('success'):
        print(f"\n❌ Evaluation failed: {result.get('error')}")
        return
    
    print("\n" + "="*80)
    print(f"📊 ML Prediction Evaluation for {result['ticker']}")
    print("="*80)
    
    print(f"\n🤖 Model: {result['model_type']}")
    print(f"📈 Prediction Value: {result['prediction_value']:.2f}")
    
    validation_emoji = {
        'agree': '✅',
        'disagree': '❌',
        'uncertain': '❓',
        'partially_agree': '⚠️'
    }
    
    print(f"\n{validation_emoji.get(result['validation'], '❓')} Gemini Validation: {result['validation'].upper()}")
    print(f"🎯 Confidence Score: {result['confidence_score']:.2f}")
    
    if result.get('anomaly_detected'):
        print(f"⚠️  Anomaly Detected: {result['anomaly_risk']} risk")
    
    print(f"\n💬 Explanation:")
    print(f"   {result['explanation']}")
    
    if result.get('key_factors'):
        print(f"\n📌 Key Factors:")
        for i, factor in enumerate(result['key_factors'], 1):
            print(f"   {i}. {factor}")
    
    print("\n" + "="*80)


def print_batch_summary(results: List[Dict[str, Any]]):
    """Print batch evaluation summary."""
    successful = [r for r in results if r.get('success')]
    failed = [r for r in results if not r.get('success')]
    
    print("\n" + "="*80)
    print(f"📊 Batch Evaluation Summary")
    print("="*80)
    
    print(f"\n✅ Successful: {len(successful)}")
    print(f"❌ Failed: {len(failed)}")
    
    if successful:
        validations = {}
        for r in successful:
            val = r.get('validation', 'unknown')
            validations[val] = validations.get(val, 0) + 1
        
        print(f"\n📋 Validation Breakdown:")
        for val, count in validations.items():
            print(f"   {val}: {count}")
        
        avg_confidence = sum(r.get('confidence_score', 0) for r in successful) / len(successful)
        print(f"\n🎯 Average Confidence: {avg_confidence:.2f}")
        
        anomalies = sum(1 for r in successful if r.get('anomaly_detected'))
        print(f"⚠️  Anomalies Detected: {anomalies}")
    
    print("\n" + "="*80)


def print_report(report: Dict[str, Any]):
    """Print evaluation report."""
    print("\n" + "="*80)
    print(f"📈 ML Model Evaluation Report ({report['period_days']} days)")
    print("="*80)
    
    print(f"\n📊 Overall Statistics:")
    print(f"   Total Evaluations: {report['total_evaluations']}")
    print(f"   Agreement Rate: {report['overall_agreement_rate']*100:.1f}%")
    print(f"   Average Confidence: {report['overall_avg_confidence']:.2f}")
    print(f"   Total Anomalies: {report['total_anomalies']}")
    
    if report.get('models'):
        print(f"\n🤖 Model Performance:")
        
        table_data = []
        for model in report['models']:
            table_data.append([
                model['model_name'],
                model['total_evaluations'],
                f"{model['agreement_rate']*100:.1f}%",
                f"{model['avg_confidence']:.2f}",
                model['anomaly_count']
            ])
        
        headers = ['Model', 'Evaluations', 'Agreement', 'Avg Confidence', 'Anomalies']
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
    
    print("\n" + "="*80)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Evaluate ML predictions using Gemini AI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--ticker',
        type=str,
        help='Stock ticker to evaluate (e.g., AAPL)'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        choices=[m.value for m in ModelType] + ['all'],
        help='ML model type to evaluate'
    )
    
    parser.add_argument(
        '--batch',
        action='store_true',
        help='Batch evaluate recent predictions'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Number of days to look back (default: 7)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=100,
        help='Maximum predictions to evaluate (default: 100)'
    )
    
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate evaluation report'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    evaluator = MLPredictionEvaluator()
    
    try:
        if args.report:
            report = evaluator.generate_report(
                model_type=args.model,
                days=args.days
            )
            print_report(report)
        
        elif args.batch:
            results = evaluator.evaluate_batch(
                days=args.days,
                limit=args.limit,
                model_type=args.model
            )
            print_batch_summary(results)
        
        elif args.ticker and args.model:
            result = evaluator.evaluate_ticker(args.ticker, args.model)
            print_evaluation_result(result)
        
        else:
            parser.print_help()
            print("\n❌ Error: Specify --ticker and --model, --batch, or --report")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
