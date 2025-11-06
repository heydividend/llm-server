"""
Harvey Intelligence Engine - Model Validation

Validates trained models against accuracy thresholds:
- Regression models: R² > 0.7
- Classification models: Accuracy > 0.80
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_extraction import DataExtractor
from models.dividend_scorer import DividendQualityScorer
from models.yield_predictor import YieldPredictor
from models.growth_predictor import GrowthRatePredictor
from models.payout_predictor import PayoutRatioPredictor
from models.cut_risk_analyzer import CutRiskAnalyzer
from models.anomaly_detector import AnomalyDetector
from models.stock_clusterer import StockClusterer


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


REGRESSION_R2_THRESHOLD = 0.7
CLASSIFICATION_ACCURACY_THRESHOLD = 0.80
CLUSTERING_SILHOUETTE_THRESHOLD = 0.3


class ModelValidator:
    """Validates trained ML models against performance thresholds."""
    
    def __init__(self, model_dir: str):
        """
        Initialize model validator.
        
        Args:
            model_dir: Directory containing trained models
        """
        self.model_dir = model_dir
        self.extractor = DataExtractor()
        self.validation_results = {}
    
    def validate_dividend_scorer(self) -> Dict[str, Any]:
        """
        Validate DividendQualityScorer model.
        
        Returns:
            Validation results with pass/fail status
        """
        logger.info("=" * 60)
        logger.info("Validating Dividend Quality Scorer")
        logger.info("=" * 60)
        
        model_path = os.path.join(self.model_dir, "dividend_quality_scorer.pkl")
        
        if not os.path.exists(model_path):
            return {
                'status': 'FAILED',
                'error': f'Model file not found: {model_path}'
            }
        
        try:
            model = DividendQualityScorer()
            model.load(model_path)
            
            metrics = model.training_metrics
            test_r2 = metrics.get('test_r2', 0)
            
            passed = test_r2 > REGRESSION_R2_THRESHOLD
            
            result = {
                'status': 'PASSED' if passed else 'FAILED',
                'model_type': 'regression',
                'test_r2': test_r2,
                'threshold': REGRESSION_R2_THRESHOLD,
                'test_rmse': metrics.get('test_rmse', 0),
                'test_mae': metrics.get('test_mae', 0),
                'n_samples': metrics.get('n_samples', 0),
                'n_features': metrics.get('n_features', 0)
            }
            
            logger.info(f"Status: {result['status']}")
            logger.info(f"R² Score: {test_r2:.4f} (threshold: {REGRESSION_R2_THRESHOLD})")
            
            return result
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {
                'status': 'FAILED',
                'error': str(e)
            }
    
    def validate_yield_predictor(self, horizon: str = '12_months') -> Dict[str, Any]:
        """
        Validate YieldPredictor model.
        
        Args:
            horizon: Prediction horizon
            
        Returns:
            Validation results with pass/fail status
        """
        logger.info("=" * 60)
        logger.info(f"Validating Yield Predictor ({horizon})")
        logger.info("=" * 60)
        
        model_path = os.path.join(self.model_dir, f"yield_predictor_{horizon}.pkl")
        
        if not os.path.exists(model_path):
            return {
                'status': 'FAILED',
                'error': f'Model file not found: {model_path}'
            }
        
        try:
            model = YieldPredictor(horizon=horizon)
            model.load(model_path)
            
            metrics = model.training_metrics
            test_r2 = metrics.get('test_r2', 0)
            
            passed = test_r2 > REGRESSION_R2_THRESHOLD
            
            result = {
                'status': 'PASSED' if passed else 'FAILED',
                'model_type': 'regression',
                'horizon': horizon,
                'test_r2': test_r2,
                'threshold': REGRESSION_R2_THRESHOLD,
                'test_rmse': metrics.get('test_rmse', 0),
                'test_mae': metrics.get('test_mae', 0),
                'n_samples': metrics.get('n_samples', 0)
            }
            
            logger.info(f"Status: {result['status']}")
            logger.info(f"R² Score: {test_r2:.4f} (threshold: {REGRESSION_R2_THRESHOLD})")
            
            return result
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {
                'status': 'FAILED',
                'error': str(e)
            }
    
    def validate_growth_predictor(self) -> Dict[str, Any]:
        """
        Validate GrowthRatePredictor model.
        
        Returns:
            Validation results with pass/fail status
        """
        logger.info("=" * 60)
        logger.info("Validating Growth Rate Predictor")
        logger.info("=" * 60)
        
        model_path = os.path.join(self.model_dir, "growth_rate_predictor.pkl")
        
        if not os.path.exists(model_path):
            return {
                'status': 'FAILED',
                'error': f'Model file not found: {model_path}'
            }
        
        try:
            model = GrowthRatePredictor()
            model.load(model_path)
            
            metrics = model.training_metrics
            test_r2 = metrics.get('test_r2', 0)
            
            passed = test_r2 > REGRESSION_R2_THRESHOLD
            
            result = {
                'status': 'PASSED' if passed else 'FAILED',
                'model_type': 'regression',
                'test_r2': test_r2,
                'threshold': REGRESSION_R2_THRESHOLD,
                'test_rmse': metrics.get('test_rmse', 0),
                'test_mae': metrics.get('test_mae', 0),
                'n_samples': metrics.get('n_samples', 0)
            }
            
            logger.info(f"Status: {result['status']}")
            logger.info(f"R² Score: {test_r2:.4f} (threshold: {REGRESSION_R2_THRESHOLD})")
            
            return result
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {
                'status': 'FAILED',
                'error': str(e)
            }
    
    def validate_payout_predictor(self) -> Dict[str, Any]:
        """
        Validate PayoutRatioPredictor model.
        
        Returns:
            Validation results with pass/fail status
        """
        logger.info("=" * 60)
        logger.info("Validating Payout Ratio Predictor")
        logger.info("=" * 60)
        
        model_path = os.path.join(self.model_dir, "payout_ratio_predictor.pkl")
        
        if not os.path.exists(model_path):
            return {
                'status': 'FAILED',
                'error': f'Model file not found: {model_path}'
            }
        
        try:
            model = PayoutRatioPredictor()
            model.load(model_path)
            
            metrics = model.training_metrics
            test_r2 = metrics.get('test_r2', 0)
            
            passed = test_r2 > REGRESSION_R2_THRESHOLD
            
            result = {
                'status': 'PASSED' if passed else 'FAILED',
                'model_type': 'regression',
                'test_r2': test_r2,
                'threshold': REGRESSION_R2_THRESHOLD,
                'test_rmse': metrics.get('test_rmse', 0),
                'test_mae': metrics.get('test_mae', 0),
                'n_samples': metrics.get('n_samples', 0),
                'sustainability_pct': metrics.get('test_sustainable_pct', 0)
            }
            
            logger.info(f"Status: {result['status']}")
            logger.info(f"R² Score: {test_r2:.4f} (threshold: {REGRESSION_R2_THRESHOLD})")
            logger.info(f"Sustainability: {result['sustainability_pct']:.1f}%")
            
            return result
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {
                'status': 'FAILED',
                'error': str(e)
            }
    
    def validate_cut_risk_analyzer(self) -> Dict[str, Any]:
        """
        Validate CutRiskAnalyzer model.
        
        Returns:
            Validation results with pass/fail status
        """
        logger.info("=" * 60)
        logger.info("Validating Cut Risk Analyzer")
        logger.info("=" * 60)
        
        model_path = os.path.join(self.model_dir, "cut_risk_analyzer.pkl")
        
        if not os.path.exists(model_path):
            return {
                'status': 'FAILED',
                'error': f'Model file not found: {model_path}'
            }
        
        try:
            model = CutRiskAnalyzer()
            model.load(model_path)
            
            metrics = model.training_metrics
            test_accuracy = metrics.get('test_accuracy', 0)
            
            passed = test_accuracy > CLASSIFICATION_ACCURACY_THRESHOLD
            
            result = {
                'status': 'PASSED' if passed else 'FAILED',
                'model_type': 'classification',
                'test_accuracy': test_accuracy,
                'threshold': CLASSIFICATION_ACCURACY_THRESHOLD,
                'test_precision': metrics.get('test_precision', 0),
                'test_recall': metrics.get('test_recall', 0),
                'test_f1': metrics.get('test_f1', 0),
                'test_auc': metrics.get('test_auc', 0),
                'n_samples': metrics.get('n_samples', 0)
            }
            
            logger.info(f"Status: {result['status']}")
            logger.info(f"Accuracy: {test_accuracy:.4f} (threshold: {CLASSIFICATION_ACCURACY_THRESHOLD})")
            logger.info(f"F1 Score: {result['test_f1']:.4f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {
                'status': 'FAILED',
                'error': str(e)
            }
    
    def validate_anomaly_detector(self) -> Dict[str, Any]:
        """
        Validate AnomalyDetector model.
        
        Returns:
            Validation results with pass/fail status
        """
        logger.info("=" * 60)
        logger.info("Validating Anomaly Detector")
        logger.info("=" * 60)
        
        model_path = os.path.join(self.model_dir, "anomaly_detector.pkl")
        
        if not os.path.exists(model_path):
            return {
                'status': 'FAILED',
                'error': f'Model file not found: {model_path}'
            }
        
        try:
            model = AnomalyDetector()
            model.load(model_path)
            
            metrics = model.training_metrics
            anomaly_pct = metrics.get('test_anomaly_pct', 0)
            
            passed = 5 <= anomaly_pct <= 20
            
            result = {
                'status': 'PASSED' if passed else 'FAILED',
                'model_type': 'anomaly_detection',
                'test_anomaly_pct': anomaly_pct,
                'expected_range': '5-20%',
                'contamination': metrics.get('contamination', 0),
                'n_samples': metrics.get('n_samples', 0)
            }
            
            logger.info(f"Status: {result['status']}")
            logger.info(f"Anomaly %: {anomaly_pct:.1f}% (expected: 5-20%)")
            
            return result
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {
                'status': 'FAILED',
                'error': str(e)
            }
    
    def validate_stock_clusterer(self) -> Dict[str, Any]:
        """
        Validate StockClusterer model.
        
        Returns:
            Validation results with pass/fail status
        """
        logger.info("=" * 60)
        logger.info("Validating Stock Clusterer")
        logger.info("=" * 60)
        
        model_path = os.path.join(self.model_dir, "stock_clusterer.pkl")
        
        if not os.path.exists(model_path):
            return {
                'status': 'FAILED',
                'error': f'Model file not found: {model_path}'
            }
        
        try:
            model = StockClusterer()
            model.load(model_path)
            
            metrics = model.training_metrics
            silhouette_score = metrics.get('silhouette_score', 0)
            
            passed = silhouette_score > CLUSTERING_SILHOUETTE_THRESHOLD
            
            result = {
                'status': 'PASSED' if passed else 'FAILED',
                'model_type': 'clustering',
                'silhouette_score': silhouette_score,
                'threshold': CLUSTERING_SILHOUETTE_THRESHOLD,
                'davies_bouldin_score': metrics.get('davies_bouldin_score', 0),
                'n_clusters': metrics.get('n_clusters', 0),
                'n_samples': metrics.get('n_samples', 0)
            }
            
            logger.info(f"Status: {result['status']}")
            logger.info(f"Silhouette Score: {silhouette_score:.4f} (threshold: {CLUSTERING_SILHOUETTE_THRESHOLD})")
            
            return result
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {
                'status': 'FAILED',
                'error': str(e)
            }
    
    def validate_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Validate all trained models.
        
        Returns:
            Dictionary mapping model names to validation results
        """
        logger.info("\n" + "=" * 60)
        logger.info("HARVEY INTELLIGENCE ENGINE - MODEL VALIDATION")
        logger.info("=" * 60 + "\n")
        
        results = {}
        
        results['dividend_scorer'] = self.validate_dividend_scorer()
        results['yield_predictor_12m'] = self.validate_yield_predictor('12_months')
        results['growth_predictor'] = self.validate_growth_predictor()
        results['payout_predictor'] = self.validate_payout_predictor()
        results['cut_risk_analyzer'] = self.validate_cut_risk_analyzer()
        results['anomaly_detector'] = self.validate_anomaly_detector()
        results['stock_clusterer'] = self.validate_stock_clusterer()
        
        logger.info("\n" + "=" * 60)
        logger.info("VALIDATION SUMMARY")
        logger.info("=" * 60)
        
        passed_count = 0
        failed_count = 0
        
        for model_name, result in results.items():
            status = result.get('status', 'UNKNOWN')
            if status == 'PASSED':
                passed_count += 1
                logger.info(f"✓ {model_name}: PASSED")
            else:
                failed_count += 1
                error = result.get('error', 'Unknown error')
                logger.error(f"✗ {model_name}: FAILED - {error}")
        
        logger.info(f"\nTotal: {passed_count + failed_count} models")
        logger.info(f"Passed: {passed_count}")
        logger.info(f"Failed: {failed_count}")
        
        return results


def main():
    """Main validation pipeline entry point."""
    parser = argparse.ArgumentParser(
        description='Harvey Intelligence Engine - Model Validation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate all models
  python validate.py
  
  # Validate specific model
  python validate.py --model dividend_scorer
  
  # Validate with custom model directory
  python validate.py --model-dir ./trained_models
  
Validation Thresholds:
  - Regression models: R² > 0.7
  - Classification models: Accuracy > 0.80
  - Clustering models: Silhouette > 0.3
  - Anomaly detection: 5-20% anomaly rate
        """
    )
    
    parser.add_argument(
        '--model',
        type=str,
        choices=['dividend_scorer', 'yield_predictor', 'growth_predictor', 
                'payout_predictor', 'cut_risk_analyzer', 'anomaly_detector', 
                'stock_clusterer', 'all'],
        default='all',
        help='Model to validate (default: all)'
    )
    
    parser.add_argument(
        '--model-dir',
        type=str,
        default='./models',
        help='Directory containing trained models (default: ./models)'
    )
    
    args = parser.parse_args()
    
    logger.info("Initializing Harvey Intelligence Engine Validation")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"Model directory: {args.model_dir}")
    
    if not os.path.exists(args.model_dir):
        logger.error(f"Model directory not found: {args.model_dir}")
        return 1
    
    try:
        validator = ModelValidator(args.model_dir)
        
        if args.model == 'all':
            results = validator.validate_all()
            failed_count = sum(1 for r in results.values() if r.get('status') != 'PASSED')
            return 0 if failed_count == 0 else 1
        elif args.model == 'dividend_scorer':
            result = validator.validate_dividend_scorer()
        elif args.model == 'yield_predictor':
            result = validator.validate_yield_predictor()
        elif args.model == 'growth_predictor':
            result = validator.validate_growth_predictor()
        elif args.model == 'payout_predictor':
            result = validator.validate_payout_predictor()
        elif args.model == 'cut_risk_analyzer':
            result = validator.validate_cut_risk_analyzer()
        elif args.model == 'anomaly_detector':
            result = validator.validate_anomaly_detector()
        elif args.model == 'stock_clusterer':
            result = validator.validate_stock_clusterer()
        else:
            logger.error(f"Unknown model: {args.model}")
            return 1
        
        return 0 if result.get('status') == 'PASSED' else 1
        
    except KeyboardInterrupt:
        logger.warning("\nValidation interrupted by user")
        return 130
    
    except Exception as e:
        logger.error(f"\nValidation failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
