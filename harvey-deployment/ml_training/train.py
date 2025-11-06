"""
Harvey Intelligence Engine - ML Training Pipeline

Main training script for all 7 dividend analysis models.
Supports training individual models or all models at once.
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_extraction import DataExtractor
from models import ModelRegistry
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


AVAILABLE_MODELS = {
    'dividend_scorer': DividendQualityScorer,
    'yield_predictor': YieldPredictor,
    'growth_predictor': GrowthRatePredictor,
    'payout_predictor': PayoutRatioPredictor,
    'cut_risk_analyzer': CutRiskAnalyzer,
    'anomaly_detector': AnomalyDetector,
    'stock_clusterer': StockClusterer
}


def train_dividend_scorer(extractor: DataExtractor, save_dir: str) -> Dict[str, Any]:
    """
    Train DividendQualityScorer model.
    
    Args:
        extractor: DataExtractor instance
        save_dir: Directory to save trained model
        
    Returns:
        Training metrics
    """
    logger.info("=" * 60)
    logger.info("Training Dividend Quality Scorer")
    logger.info("=" * 60)
    
    features_df, _ = extractor.prepare_training_data()
    
    model = DividendQualityScorer(n_estimators=100)
    metrics = model.train(features_df)
    
    model_path = model.save(save_dir)
    logger.info(f"Model saved to: {model_path}")
    
    return metrics


def train_yield_predictor(extractor: DataExtractor, save_dir: str, horizon: str = '12_months') -> Dict[str, Any]:
    """
    Train YieldPredictor model.
    
    Args:
        extractor: DataExtractor instance
        save_dir: Directory to save trained model
        horizon: Prediction horizon (3_months, 6_months, 12_months, 24_months)
        
    Returns:
        Training metrics
    """
    logger.info("=" * 60)
    logger.info(f"Training Yield Predictor ({horizon})")
    logger.info("=" * 60)
    
    features_df, _ = extractor.prepare_training_data()
    
    model = YieldPredictor(horizon=horizon)
    metrics = model.train(features_df)
    
    model_path = model.save(save_dir)
    logger.info(f"Model saved to: {model_path}")
    
    return metrics


def train_growth_predictor(extractor: DataExtractor, save_dir: str) -> Dict[str, Any]:
    """
    Train GrowthRatePredictor model.
    
    Args:
        extractor: DataExtractor instance
        save_dir: Directory to save trained model
        
    Returns:
        Training metrics
    """
    logger.info("=" * 60)
    logger.info("Training Growth Rate Predictor")
    logger.info("=" * 60)
    
    features_df, _ = extractor.prepare_training_data()
    
    model = GrowthRatePredictor(n_estimators=100)
    metrics = model.train(features_df)
    
    model_path = model.save(save_dir)
    logger.info(f"Model saved to: {model_path}")
    
    return metrics


def train_payout_predictor(extractor: DataExtractor, save_dir: str) -> Dict[str, Any]:
    """
    Train PayoutRatioPredictor model.
    
    Args:
        extractor: DataExtractor instance
        save_dir: Directory to save trained model
        
    Returns:
        Training metrics
    """
    logger.info("=" * 60)
    logger.info("Training Payout Ratio Predictor")
    logger.info("=" * 60)
    
    features_df, _ = extractor.prepare_training_data()
    
    model = PayoutRatioPredictor()
    metrics = model.train(features_df)
    
    model_path = model.save(save_dir)
    logger.info(f"Model saved to: {model_path}")
    
    return metrics


def train_cut_risk_analyzer(extractor: DataExtractor, save_dir: str) -> Dict[str, Any]:
    """
    Train CutRiskAnalyzer model.
    
    Args:
        extractor: DataExtractor instance
        save_dir: Directory to save trained model
        
    Returns:
        Training metrics
    """
    logger.info("=" * 60)
    logger.info("Training Cut Risk Analyzer")
    logger.info("=" * 60)
    
    features_df, _ = extractor.prepare_training_data()
    
    model = CutRiskAnalyzer()
    metrics = model.train(features_df)
    
    model_path = model.save(save_dir)
    logger.info(f"Model saved to: {model_path}")
    
    return metrics


def train_anomaly_detector(extractor: DataExtractor, save_dir: str) -> Dict[str, Any]:
    """
    Train AnomalyDetector model.
    
    Args:
        extractor: DataExtractor instance
        save_dir: Directory to save trained model
        
    Returns:
        Training metrics
    """
    logger.info("=" * 60)
    logger.info("Training Anomaly Detector")
    logger.info("=" * 60)
    
    features_df, _ = extractor.prepare_training_data()
    
    model = AnomalyDetector(contamination=0.1)
    metrics = model.train(features_df)
    
    model_path = model.save(save_dir)
    logger.info(f"Model saved to: {model_path}")
    
    return metrics


def train_stock_clusterer(extractor: DataExtractor, save_dir: str) -> Dict[str, Any]:
    """
    Train StockClusterer model.
    
    Args:
        extractor: DataExtractor instance
        save_dir: Directory to save trained model
        
    Returns:
        Training metrics
    """
    logger.info("=" * 60)
    logger.info("Training Stock Clusterer")
    logger.info("=" * 60)
    
    features_df, _ = extractor.prepare_training_data()
    
    model = StockClusterer(n_clusters=8)
    metrics = model.train(features_df)
    
    model_path = model.save(save_dir)
    logger.info(f"Model saved to: {model_path}")
    
    return metrics


def train_all_models(extractor: DataExtractor, save_dir: str) -> Dict[str, Dict[str, Any]]:
    """
    Train all 7 models in the Harvey Intelligence Engine.
    
    Args:
        extractor: DataExtractor instance
        save_dir: Directory to save trained models
        
    Returns:
        Dictionary mapping model names to their training metrics
    """
    all_metrics = {}
    
    logger.info("\n" + "=" * 60)
    logger.info("HARVEY INTELLIGENCE ENGINE - FULL TRAINING PIPELINE")
    logger.info("=" * 60 + "\n")
    
    try:
        all_metrics['dividend_scorer'] = train_dividend_scorer(extractor, save_dir)
    except Exception as e:
        logger.error(f"Failed to train dividend_scorer: {e}")
        all_metrics['dividend_scorer'] = {'error': str(e)}
    
    try:
        all_metrics['yield_predictor_12m'] = train_yield_predictor(extractor, save_dir, '12_months')
    except Exception as e:
        logger.error(f"Failed to train yield_predictor: {e}")
        all_metrics['yield_predictor_12m'] = {'error': str(e)}
    
    try:
        all_metrics['growth_predictor'] = train_growth_predictor(extractor, save_dir)
    except Exception as e:
        logger.error(f"Failed to train growth_predictor: {e}")
        all_metrics['growth_predictor'] = {'error': str(e)}
    
    try:
        all_metrics['payout_predictor'] = train_payout_predictor(extractor, save_dir)
    except Exception as e:
        logger.error(f"Failed to train payout_predictor: {e}")
        all_metrics['payout_predictor'] = {'error': str(e)}
    
    try:
        all_metrics['cut_risk_analyzer'] = train_cut_risk_analyzer(extractor, save_dir)
    except Exception as e:
        logger.error(f"Failed to train cut_risk_analyzer: {e}")
        all_metrics['cut_risk_analyzer'] = {'error': str(e)}
    
    try:
        all_metrics['anomaly_detector'] = train_anomaly_detector(extractor, save_dir)
    except Exception as e:
        logger.error(f"Failed to train anomaly_detector: {e}")
        all_metrics['anomaly_detector'] = {'error': str(e)}
    
    try:
        all_metrics['stock_clusterer'] = train_stock_clusterer(extractor, save_dir)
    except Exception as e:
        logger.error(f"Failed to train stock_clusterer: {e}")
        all_metrics['stock_clusterer'] = {'error': str(e)}
    
    logger.info("\n" + "=" * 60)
    logger.info("TRAINING COMPLETE - Summary")
    logger.info("=" * 60)
    
    for model_name, metrics in all_metrics.items():
        if 'error' in metrics:
            logger.error(f"{model_name}: FAILED - {metrics['error']}")
        else:
            if 'test_r2' in metrics:
                logger.info(f"{model_name}: R² = {metrics['test_r2']:.4f}")
            elif 'test_accuracy' in metrics:
                logger.info(f"{model_name}: Accuracy = {metrics['test_accuracy']:.4f}")
            elif 'silhouette_score' in metrics:
                logger.info(f"{model_name}: Silhouette = {metrics['silhouette_score']:.4f}")
            else:
                logger.info(f"{model_name}: Trained successfully")
    
    return all_metrics


def main():
    """Main training pipeline entry point."""
    parser = argparse.ArgumentParser(
        description='Harvey Intelligence Engine - ML Training Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Train all models
  python train.py
  
  # Train specific model
  python train.py --model dividend_scorer
  
  # Train with custom save directory
  python train.py --save-dir ./trained_models
  
  # Train yield predictor with specific horizon
  python train.py --model yield_predictor --horizon 24_months
  
Available models:
  - dividend_scorer: Dividend quality scoring (0-100)
  - yield_predictor: Future yield prediction (3/6/12/24 months)
  - growth_predictor: Annual growth rate prediction
  - payout_predictor: Payout ratio prediction with sustainability
  - cut_risk_analyzer: Dividend cut risk classification
  - anomaly_detector: Unusual pattern detection
  - stock_clusterer: Similar stock grouping (8 clusters)
        """
    )
    
    parser.add_argument(
        '--model',
        type=str,
        choices=list(AVAILABLE_MODELS.keys()) + ['all'],
        default='all',
        help='Model to train (default: all)'
    )
    
    parser.add_argument(
        '--save-dir',
        type=str,
        default='./models',
        help='Directory to save trained models (default: ./models)'
    )
    
    parser.add_argument(
        '--horizon',
        type=str,
        choices=['3_months', '6_months', '12_months', '24_months'],
        default='12_months',
        help='Yield prediction horizon (default: 12_months)'
    )
    
    parser.add_argument(
        '--min-history-days',
        type=int,
        default=365,
        help='Minimum payment history in days (default: 365)'
    )
    
    args = parser.parse_args()
    
    logger.info("Initializing Harvey Intelligence Engine Training Pipeline")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"Model: {args.model}")
    logger.info(f"Save directory: {args.save_dir}")
    
    os.makedirs(args.save_dir, exist_ok=True)
    
    try:
        extractor = DataExtractor()
        logger.info("Data extractor initialized successfully")
        
        if args.model == 'all':
            metrics = train_all_models(extractor, args.save_dir)
        elif args.model == 'dividend_scorer':
            metrics = train_dividend_scorer(extractor, args.save_dir)
        elif args.model == 'yield_predictor':
            metrics = train_yield_predictor(extractor, args.save_dir, args.horizon)
        elif args.model == 'growth_predictor':
            metrics = train_growth_predictor(extractor, args.save_dir)
        elif args.model == 'payout_predictor':
            metrics = train_payout_predictor(extractor, args.save_dir)
        elif args.model == 'cut_risk_analyzer':
            metrics = train_cut_risk_analyzer(extractor, args.save_dir)
        elif args.model == 'anomaly_detector':
            metrics = train_anomaly_detector(extractor, args.save_dir)
        elif args.model == 'stock_clusterer':
            metrics = train_stock_clusterer(extractor, args.save_dir)
        else:
            logger.error(f"Unknown model: {args.model}")
            return 1
        
        logger.info("\n" + "=" * 60)
        logger.info("TRAINING PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        return 0
        
    except KeyboardInterrupt:
        logger.warning("\nTraining interrupted by user")
        return 130
    
    except Exception as e:
        logger.error(f"\nTraining pipeline failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
