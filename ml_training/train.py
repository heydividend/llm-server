"""
Harvey Intelligence Engine - ML Training Pipeline

Main training script for all 7 dividend analysis models.
Supports training individual models or all models at once.
"""

import os
import sys
import argparse
import logging
import json
import signal
import time
import traceback
from datetime import datetime
from typing import List, Dict, Any, Optional
import psutil

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

TRAINING_STATUS = {
    'start_time': None,
    'models_completed': [],
    'models_failed': [],
    'metrics': {},
    'interrupted': False,
    'end_time': None
}

GLOBAL_SAVE_DIR = './models'

AVAILABLE_MODELS = {
    'dividend_scorer': DividendQualityScorer,
    'yield_predictor': YieldPredictor,
    'growth_predictor': GrowthRatePredictor,
    'payout_predictor': PayoutRatioPredictor,
    'cut_risk_analyzer': CutRiskAnalyzer,
    'anomaly_detector': AnomalyDetector,
    'stock_clusterer': StockClusterer
}


def log_memory_usage():
    """Log current memory usage."""
    process = psutil.Process()
    mem_info = process.memory_info()
    mem_mb = mem_info.rss / 1024 / 1024
    logger.info(f"Memory usage: {mem_mb:.1f} MB")


def save_training_status(save_dir: str):
    """Save training status to JSON file."""
    try:
        status_file = os.path.join(save_dir, 'training_status.json')
        with open(status_file, 'w') as f:
            json.dump(TRAINING_STATUS, f, indent=2, default=str)
        logger.info(f"Training status saved to: {status_file}")
    except Exception as e:
        logger.error(f"Failed to save training status: {e}")


def signal_handler(signum, frame):
    """Handle termination signals gracefully."""
    signal_name = signal.Signals(signum).name
    logger.warning(f"Received signal {signal_name}. Saving partial results...")
    TRAINING_STATUS['interrupted'] = True
    TRAINING_STATUS['end_time'] = datetime.now().isoformat()
    save_training_status(GLOBAL_SAVE_DIR)
    log_training_summary()
    sys.exit(130)


def log_training_summary():
    """Log comprehensive training summary."""
    logger.info("\n" + "=" * 80)
    logger.info("TRAINING SUMMARY")
    logger.info("=" * 80)
    
    if TRAINING_STATUS['start_time']:
        logger.info(f"Start time: {TRAINING_STATUS['start_time']}")
    if TRAINING_STATUS['end_time']:
        logger.info(f"End time: {TRAINING_STATUS['end_time']}")
    
    if TRAINING_STATUS['interrupted']:
        logger.warning("Training was interrupted before completion!")
    
    completed = TRAINING_STATUS['models_completed']
    failed = TRAINING_STATUS['models_failed']
    
    logger.info(f"\nModels completed: {len(completed)}")
    for model_name in completed:
        metrics = TRAINING_STATUS['metrics'].get(model_name, {})
        if 'test_r2' in metrics:
            logger.info(f"  ✓ {model_name}: R² = {metrics['test_r2']:.4f}")
        elif 'test_accuracy' in metrics:
            logger.info(f"  ✓ {model_name}: Accuracy = {metrics['test_accuracy']:.4f}")
        elif 'silhouette_score' in metrics:
            logger.info(f"  ✓ {model_name}: Silhouette = {metrics['silhouette_score']:.4f}")
        else:
            logger.info(f"  ✓ {model_name}: Trained successfully")
    
    logger.info(f"\nModels failed: {len(failed)}")
    for model_name in failed:
        error = TRAINING_STATUS['metrics'].get(model_name, {}).get('error', 'Unknown error')
        logger.error(f"  ✗ {model_name}: {error}")
    
    logger.info("=" * 80)


def train_dividend_scorer(extractor: DataExtractor, save_dir: str) -> Dict[str, Any]:
    """
    Train DividendQualityScorer model.
    
    Args:
        extractor: DataExtractor instance
        save_dir: Directory to save trained model
        
    Returns:
        Training metrics
    """
    start_time = time.time()
    logger.info("=" * 60)
    logger.info("Training Dividend Quality Scorer")
    logger.info("=" * 60)
    
    logger.info("Step 1/3: Loading training data from database...")
    log_memory_usage()
    features_df, _ = extractor.prepare_training_data()
    logger.info(f"Loaded {len(features_df)} samples in {time.time() - start_time:.1f}s")
    
    logger.info("Step 2/3: Training model...")
    log_memory_usage()
    model = DividendQualityScorer(n_estimators=100)
    metrics = model.train(features_df)
    
    logger.info("Step 3/3: Saving model...")
    model_path = model.save(save_dir)
    logger.info(f"Model saved to: {model_path}")
    
    elapsed = time.time() - start_time
    logger.info(f"Total training time: {elapsed:.1f}s")
    metrics['training_time_seconds'] = elapsed
    
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
    start_time = time.time()
    logger.info("=" * 60)
    logger.info(f"Training Yield Predictor ({horizon})")
    logger.info("=" * 60)
    
    logger.info("Step 1/3: Loading training data from database...")
    log_memory_usage()
    features_df, _ = extractor.prepare_training_data()
    logger.info(f"Loaded {len(features_df)} samples in {time.time() - start_time:.1f}s")
    
    logger.info("Step 2/3: Training model...")
    log_memory_usage()
    model = YieldPredictor(horizon=horizon)
    metrics = model.train(features_df)
    
    logger.info("Step 3/3: Saving model...")
    model_path = model.save(save_dir)
    logger.info(f"Model saved to: {model_path}")
    
    elapsed = time.time() - start_time
    logger.info(f"Total training time: {elapsed:.1f}s")
    metrics['training_time_seconds'] = elapsed
    
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
    start_time = time.time()
    logger.info("=" * 60)
    logger.info("Training Growth Rate Predictor")
    logger.info("=" * 60)
    
    logger.info("Step 1/3: Loading training data from database...")
    log_memory_usage()
    features_df, _ = extractor.prepare_training_data()
    logger.info(f"Loaded {len(features_df)} samples in {time.time() - start_time:.1f}s")
    
    logger.info("Step 2/3: Training model...")
    log_memory_usage()
    model = GrowthRatePredictor(n_estimators=100)
    metrics = model.train(features_df)
    
    logger.info("Step 3/3: Saving model...")
    model_path = model.save(save_dir)
    logger.info(f"Model saved to: {model_path}")
    
    elapsed = time.time() - start_time
    logger.info(f"Total training time: {elapsed:.1f}s")
    metrics['training_time_seconds'] = elapsed
    
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
    start_time = time.time()
    logger.info("=" * 60)
    logger.info("Training Payout Ratio Predictor")
    logger.info("=" * 60)
    
    logger.info("Step 1/3: Loading training data from database...")
    log_memory_usage()
    features_df, _ = extractor.prepare_training_data()
    logger.info(f"Loaded {len(features_df)} samples in {time.time() - start_time:.1f}s")
    
    logger.info("Step 2/3: Training model...")
    log_memory_usage()
    model = PayoutRatioPredictor()
    metrics = model.train(features_df)
    
    logger.info("Step 3/3: Saving model...")
    model_path = model.save(save_dir)
    logger.info(f"Model saved to: {model_path}")
    
    elapsed = time.time() - start_time
    logger.info(f"Total training time: {elapsed:.1f}s")
    metrics['training_time_seconds'] = elapsed
    
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
    start_time = time.time()
    logger.info("=" * 60)
    logger.info("Training Cut Risk Analyzer")
    logger.info("=" * 60)
    
    logger.info("Step 1/3: Loading training data from database...")
    log_memory_usage()
    features_df, _ = extractor.prepare_training_data()
    logger.info(f"Loaded {len(features_df)} samples in {time.time() - start_time:.1f}s")
    
    logger.info("Step 2/3: Training model...")
    log_memory_usage()
    model = CutRiskAnalyzer()
    metrics = model.train(features_df)
    
    logger.info("Step 3/3: Saving model...")
    model_path = model.save(save_dir)
    logger.info(f"Model saved to: {model_path}")
    
    elapsed = time.time() - start_time
    logger.info(f"Total training time: {elapsed:.1f}s")
    metrics['training_time_seconds'] = elapsed
    
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
    start_time = time.time()
    logger.info("=" * 60)
    logger.info("Training Anomaly Detector")
    logger.info("=" * 60)
    
    logger.info("Step 1/3: Loading training data from database...")
    log_memory_usage()
    features_df, _ = extractor.prepare_training_data()
    logger.info(f"Loaded {len(features_df)} samples in {time.time() - start_time:.1f}s")
    
    logger.info("Step 2/3: Training model...")
    log_memory_usage()
    model = AnomalyDetector(contamination=0.1)
    metrics = model.train(features_df)
    
    logger.info("Step 3/3: Saving model...")
    model_path = model.save(save_dir)
    logger.info(f"Model saved to: {model_path}")
    
    elapsed = time.time() - start_time
    logger.info(f"Total training time: {elapsed:.1f}s")
    metrics['training_time_seconds'] = elapsed
    
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
    start_time = time.time()
    logger.info("=" * 60)
    logger.info("Training Stock Clusterer")
    logger.info("=" * 60)
    
    logger.info("Step 1/3: Loading training data from database...")
    log_memory_usage()
    features_df, _ = extractor.prepare_training_data()
    logger.info(f"Loaded {len(features_df)} samples in {time.time() - start_time:.1f}s")
    
    logger.info("Step 2/3: Training model...")
    log_memory_usage()
    model = StockClusterer(n_clusters=8)
    metrics = model.train(features_df)
    
    logger.info("Step 3/3: Saving model...")
    model_path = model.save(save_dir)
    logger.info(f"Model saved to: {model_path}")
    
    elapsed = time.time() - start_time
    logger.info(f"Total training time: {elapsed:.1f}s")
    metrics['training_time_seconds'] = elapsed
    
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
    
    logger.info("\n" + "=" * 80)
    logger.info("HARVEY INTELLIGENCE ENGINE - FULL TRAINING PIPELINE")
    logger.info("=" * 80 + "\n")
    
    logger.info("Starting training of 7 models...")
    log_memory_usage()
    
    # Model 1: Dividend Scorer
    try:
        logger.info("\n[1/7] Starting Dividend Quality Scorer...")
        all_metrics['dividend_scorer'] = train_dividend_scorer(extractor, save_dir)
        TRAINING_STATUS['models_completed'].append('dividend_scorer')
        TRAINING_STATUS['metrics']['dividend_scorer'] = all_metrics['dividend_scorer']
        logger.info("[1/7] ✓ Dividend Quality Scorer completed")
    except Exception as e:
        logger.error(f"[1/7] ✗ Dividend Quality Scorer failed: {e}", exc_info=True)
        all_metrics['dividend_scorer'] = {'error': str(e)}
        TRAINING_STATUS['models_failed'].append('dividend_scorer')
        TRAINING_STATUS['metrics']['dividend_scorer'] = {'error': str(e)}
    
    # Model 2: Yield Predictor
    try:
        logger.info("\n[2/7] Starting Yield Predictor...")
        all_metrics['yield_predictor_12m'] = train_yield_predictor(extractor, save_dir, '12_months')
        TRAINING_STATUS['models_completed'].append('yield_predictor_12m')
        TRAINING_STATUS['metrics']['yield_predictor_12m'] = all_metrics['yield_predictor_12m']
        logger.info("[2/7] ✓ Yield Predictor completed")
    except Exception as e:
        logger.error(f"[2/7] ✗ Yield Predictor failed: {e}", exc_info=True)
        all_metrics['yield_predictor_12m'] = {'error': str(e)}
        TRAINING_STATUS['models_failed'].append('yield_predictor_12m')
        TRAINING_STATUS['metrics']['yield_predictor_12m'] = {'error': str(e)}
    
    # Model 3: Growth Predictor
    try:
        logger.info("\n[3/7] Starting Growth Rate Predictor...")
        all_metrics['growth_predictor'] = train_growth_predictor(extractor, save_dir)
        TRAINING_STATUS['models_completed'].append('growth_predictor')
        TRAINING_STATUS['metrics']['growth_predictor'] = all_metrics['growth_predictor']
        logger.info("[3/7] ✓ Growth Rate Predictor completed")
    except Exception as e:
        logger.error(f"[3/7] ✗ Growth Rate Predictor failed: {e}", exc_info=True)
        all_metrics['growth_predictor'] = {'error': str(e)}
        TRAINING_STATUS['models_failed'].append('growth_predictor')
        TRAINING_STATUS['metrics']['growth_predictor'] = {'error': str(e)}
    
    # Model 4: Payout Predictor
    try:
        logger.info("\n[4/7] Starting Payout Ratio Predictor...")
        all_metrics['payout_predictor'] = train_payout_predictor(extractor, save_dir)
        TRAINING_STATUS['models_completed'].append('payout_predictor')
        TRAINING_STATUS['metrics']['payout_predictor'] = all_metrics['payout_predictor']
        logger.info("[4/7] ✓ Payout Ratio Predictor completed")
    except Exception as e:
        logger.error(f"[4/7] ✗ Payout Ratio Predictor failed: {e}", exc_info=True)
        all_metrics['payout_predictor'] = {'error': str(e)}
        TRAINING_STATUS['models_failed'].append('payout_predictor')
        TRAINING_STATUS['metrics']['payout_predictor'] = {'error': str(e)}
    
    # Model 5: Cut Risk Analyzer
    try:
        logger.info("\n[5/7] Starting Cut Risk Analyzer...")
        all_metrics['cut_risk_analyzer'] = train_cut_risk_analyzer(extractor, save_dir)
        TRAINING_STATUS['models_completed'].append('cut_risk_analyzer')
        TRAINING_STATUS['metrics']['cut_risk_analyzer'] = all_metrics['cut_risk_analyzer']
        logger.info("[5/7] ✓ Cut Risk Analyzer completed")
    except Exception as e:
        logger.error(f"[5/7] ✗ Cut Risk Analyzer failed: {e}", exc_info=True)
        all_metrics['cut_risk_analyzer'] = {'error': str(e)}
        TRAINING_STATUS['models_failed'].append('cut_risk_analyzer')
        TRAINING_STATUS['metrics']['cut_risk_analyzer'] = {'error': str(e)}
    
    # Model 6: Anomaly Detector
    try:
        logger.info("\n[6/7] Starting Anomaly Detector...")
        all_metrics['anomaly_detector'] = train_anomaly_detector(extractor, save_dir)
        TRAINING_STATUS['models_completed'].append('anomaly_detector')
        TRAINING_STATUS['metrics']['anomaly_detector'] = all_metrics['anomaly_detector']
        logger.info("[6/7] ✓ Anomaly Detector completed")
    except Exception as e:
        logger.error(f"[6/7] ✗ Anomaly Detector failed: {e}", exc_info=True)
        all_metrics['anomaly_detector'] = {'error': str(e)}
        TRAINING_STATUS['models_failed'].append('anomaly_detector')
        TRAINING_STATUS['metrics']['anomaly_detector'] = {'error': str(e)}
    
    # Model 7: Stock Clusterer
    try:
        logger.info("\n[7/7] Starting Stock Clusterer...")
        all_metrics['stock_clusterer'] = train_stock_clusterer(extractor, save_dir)
        TRAINING_STATUS['models_completed'].append('stock_clusterer')
        TRAINING_STATUS['metrics']['stock_clusterer'] = all_metrics['stock_clusterer']
        logger.info("[7/7] ✓ Stock Clusterer completed")
    except Exception as e:
        logger.error(f"[7/7] ✗ Stock Clusterer failed: {e}", exc_info=True)
        all_metrics['stock_clusterer'] = {'error': str(e)}
        TRAINING_STATUS['models_failed'].append('stock_clusterer')
        TRAINING_STATUS['metrics']['stock_clusterer'] = {'error': str(e)}
    
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
    
    # Set global save directory for signal handler
    global GLOBAL_SAVE_DIR
    GLOBAL_SAVE_DIR = args.save_dir
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Initialize training status
    TRAINING_STATUS['start_time'] = datetime.now().isoformat()
    
    logger.info("=" * 80)
    logger.info("Initializing Harvey Intelligence Engine Training Pipeline")
    logger.info("=" * 80)
    logger.info(f"Timestamp: {TRAINING_STATUS['start_time']}")
    logger.info(f"Model: {args.model}")
    logger.info(f"Save directory: {args.save_dir}")
    logger.info(f"Process ID: {os.getpid()}")
    log_memory_usage()
    
    os.makedirs(args.save_dir, exist_ok=True)
    
    try:
        logger.info("\nInitializing database connection...")
        extractor = DataExtractor()
        logger.info("✓ Data extractor initialized successfully")
        log_memory_usage()
        
        if args.model == 'all':
            metrics = train_all_models(extractor, args.save_dir)
        elif args.model == 'dividend_scorer':
            model_name = 'dividend_scorer'
            metrics = train_dividend_scorer(extractor, args.save_dir)
            TRAINING_STATUS['models_completed'].append(model_name)
            TRAINING_STATUS['metrics'][model_name] = metrics
        elif args.model == 'yield_predictor':
            model_name = 'yield_predictor'
            metrics = train_yield_predictor(extractor, args.save_dir, args.horizon)
            TRAINING_STATUS['models_completed'].append(model_name)
            TRAINING_STATUS['metrics'][model_name] = metrics
        elif args.model == 'growth_predictor':
            model_name = 'growth_predictor'
            metrics = train_growth_predictor(extractor, args.save_dir)
            TRAINING_STATUS['models_completed'].append(model_name)
            TRAINING_STATUS['metrics'][model_name] = metrics
        elif args.model == 'payout_predictor':
            model_name = 'payout_predictor'
            metrics = train_payout_predictor(extractor, args.save_dir)
            TRAINING_STATUS['models_completed'].append(model_name)
            TRAINING_STATUS['metrics'][model_name] = metrics
        elif args.model == 'cut_risk_analyzer':
            model_name = 'cut_risk_analyzer'
            metrics = train_cut_risk_analyzer(extractor, args.save_dir)
            TRAINING_STATUS['models_completed'].append(model_name)
            TRAINING_STATUS['metrics'][model_name] = metrics
        elif args.model == 'anomaly_detector':
            model_name = 'anomaly_detector'
            metrics = train_anomaly_detector(extractor, args.save_dir)
            TRAINING_STATUS['models_completed'].append(model_name)
            TRAINING_STATUS['metrics'][model_name] = metrics
        elif args.model == 'stock_clusterer':
            model_name = 'stock_clusterer'
            metrics = train_stock_clusterer(extractor, args.save_dir)
            TRAINING_STATUS['models_completed'].append(model_name)
            TRAINING_STATUS['metrics'][model_name] = metrics
        else:
            logger.error(f"Unknown model: {args.model}")
            return 1
        
        TRAINING_STATUS['end_time'] = datetime.now().isoformat()
        
        logger.info("\n" + "=" * 80)
        logger.info("TRAINING PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        return 0
        
    except KeyboardInterrupt:
        logger.warning("\nTraining interrupted by user (Ctrl+C)")
        TRAINING_STATUS['interrupted'] = True
        TRAINING_STATUS['end_time'] = datetime.now().isoformat()
        return 130
    
    except Exception as e:
        logger.error(f"\nTraining pipeline failed with exception: {e}", exc_info=True)
        TRAINING_STATUS['end_time'] = datetime.now().isoformat()
        return 1
    
    finally:
        # Always log summary and save status, even if training failed
        TRAINING_STATUS['end_time'] = TRAINING_STATUS.get('end_time') or datetime.now().isoformat()
        log_training_summary()
        save_training_status(args.save_dir)
        log_memory_usage()
        logger.info("Training pipeline terminated.")


if __name__ == "__main__":
    sys.exit(main())
