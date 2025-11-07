#!/usr/bin/env python3
"""
Harvey ML - Automated Training Pipeline
Runs continuous training with scheduling and monitoring
"""

import os
import sys
import time
import json
import logging
import argparse
import subprocess
from datetime import datetime, timedelta
from typing import Dict, Any, List
import schedule

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/harvey/ml_training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AutomatedTraining')


class MLTrainingPipeline:
    """Automated ML training pipeline with monitoring and notifications."""
    
    def __init__(self, base_dir: str = "/home/harvey/harvey-backend/ml_training"):
        """
        Initialize training pipeline.
        
        Args:
            base_dir: Base directory for ML training
        """
        self.base_dir = base_dir
        self.models_dir = os.path.join(base_dir, "models")
        self.metrics_file = os.path.join(base_dir, "training_metrics.json")
        self.status_file = "/var/log/harvey/training_status.json"
        
        # Create directories if they don't exist
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.status_file), exist_ok=True)
        
        self.models_to_train = [
            'dividend_scorer',
            'yield_predictor', 
            'growth_predictor',
            'payout_predictor',
            'cut_risk_analyzer',
            'anomaly_detector',
            'stock_clusterer'
        ]
        
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met for training."""
        try:
            # Check if database is accessible
            result = subprocess.run(
                ["python", "-c", "from data_extraction import DataExtractor; e = DataExtractor(); print('OK')"],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"Database connection failed: {result.stderr}")
                return False
                
            logger.info("✓ Database connection verified")
            
            # Check if training script exists
            train_script = os.path.join(self.base_dir, "train.py")
            if not os.path.exists(train_script):
                logger.error(f"Training script not found: {train_script}")
                return False
                
            logger.info("✓ Training scripts found")
            return True
            
        except Exception as e:
            logger.error(f"Prerequisites check failed: {e}")
            return False
    
    def train_model(self, model_name: str) -> Dict[str, Any]:
        """
        Train a specific model.
        
        Args:
            model_name: Name of the model to train
            
        Returns:
            Training results dictionary
        """
        logger.info(f"Starting training for {model_name}...")
        
        try:
            # Run training
            cmd = ["python", "train.py", "--model", model_name, "--save-dir", self.models_dir]
            result = subprocess.run(
                cmd,
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode != 0:
                logger.error(f"Training failed for {model_name}: {result.stderr}")
                return {"status": "failed", "error": result.stderr}
            
            logger.info(f"✓ {model_name} trained successfully")
            
            # Validate the model
            validation_result = self.validate_model(model_name)
            
            return {
                "status": "success",
                "model": model_name,
                "validation": validation_result,
                "timestamp": datetime.now().isoformat()
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"Training timeout for {model_name}")
            return {"status": "timeout", "model": model_name}
        except Exception as e:
            logger.error(f"Training error for {model_name}: {e}")
            return {"status": "error", "model": model_name, "error": str(e)}
    
    def validate_model(self, model_name: str) -> Dict[str, Any]:
        """
        Validate a trained model.
        
        Args:
            model_name: Name of the model to validate
            
        Returns:
            Validation results
        """
        try:
            cmd = ["python", "validate.py", "--model", model_name, "--model-dir", self.models_dir]
            result = subprocess.run(
                cmd,
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode == 0:
                # Parse validation output (assuming JSON output)
                try:
                    validation_data = json.loads(result.stdout)
                    return validation_data
                except:
                    return {"status": "validated", "output": result.stdout}
            else:
                return {"status": "validation_failed", "error": result.stderr}
                
        except Exception as e:
            logger.error(f"Validation error for {model_name}: {e}")
            return {"status": "validation_error", "error": str(e)}
    
    def train_all_models(self, force: bool = False) -> Dict[str, Any]:
        """
        Train all models in the pipeline.
        
        Args:
            force: Force retraining even if models exist
            
        Returns:
            Training results for all models
        """
        logger.info("=" * 60)
        logger.info("Starting Full Training Pipeline")
        logger.info("=" * 60)
        
        if not self.check_prerequisites():
            logger.error("Prerequisites not met, aborting training")
            return {"status": "prerequisites_failed"}
        
        results = {
            "start_time": datetime.now().isoformat(),
            "models": {}
        }
        
        for model in self.models_to_train:
            model_file = os.path.join(self.models_dir, f"{model}.pkl")
            
            # Check if model exists and skip if not forcing
            if os.path.exists(model_file) and not force:
                file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(model_file))
                if file_age.days < 7:  # Skip if model is less than 7 days old
                    logger.info(f"Skipping {model} - recently trained ({file_age.days} days old)")
                    results["models"][model] = {"status": "skipped", "age_days": file_age.days}
                    continue
            
            # Train the model
            result = self.train_model(model)
            results["models"][model] = result
            
            # Small delay between models
            time.sleep(5)
        
        results["end_time"] = datetime.now().isoformat()
        
        # Save results
        self.save_training_results(results)
        
        # Restart ML service if training was successful
        if self.should_restart_service(results):
            self.restart_ml_service()
        
        return results
    
    def save_training_results(self, results: Dict[str, Any]):
        """Save training results to file."""
        try:
            with open(self.metrics_file, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Training results saved to {self.metrics_file}")
            
            # Update status file
            status = {
                "last_training": results.get("end_time"),
                "models_trained": len([m for m in results["models"] if results["models"][m]["status"] == "success"]),
                "total_models": len(self.models_to_train),
                "status": "healthy" if self.is_training_healthy(results) else "needs_attention"
            }
            
            with open(self.status_file, 'w') as f:
                json.dump(status, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
    
    def is_training_healthy(self, results: Dict[str, Any]) -> bool:
        """Check if training results are healthy."""
        if "models" not in results:
            return False
            
        successful = sum(1 for m in results["models"].values() 
                        if m.get("status") in ["success", "skipped"])
        total = len(results["models"])
        
        return successful >= (total * 0.8)  # 80% success rate
    
    def should_restart_service(self, results: Dict[str, Any]) -> bool:
        """Determine if ML service should be restarted."""
        # Restart if any model was successfully trained
        return any(m.get("status") == "success" for m in results.get("models", {}).values())
    
    def restart_ml_service(self):
        """Restart the ML service to load new models."""
        try:
            logger.info("Restarting ML service to load new models...")
            subprocess.run(["sudo", "systemctl", "restart", "harvey-ml"], check=True)
            time.sleep(10)  # Wait for service to start
            
            # Check if service is running
            result = subprocess.run(
                ["systemctl", "is-active", "harvey-ml"],
                capture_output=True,
                text=True
            )
            
            if result.stdout.strip() == "active":
                logger.info("✓ ML service restarted successfully")
            else:
                logger.error("ML service restart failed")
                
        except Exception as e:
            logger.error(f"Failed to restart ML service: {e}")
    
    def incremental_training(self):
        """Perform incremental training on existing models."""
        logger.info("Starting incremental training...")
        
        # This would implement incremental/online learning
        # For now, we'll retrain models that are older than 3 days
        for model in self.models_to_train:
            model_file = os.path.join(self.models_dir, f"{model}.pkl")
            
            if os.path.exists(model_file):
                file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(model_file))
                if file_age.days >= 3:
                    logger.info(f"Retraining {model} (age: {file_age.days} days)")
                    self.train_model(model)
    
    def run_scheduled_training(self):
        """Run training on a schedule."""
        logger.info("Starting scheduled training service...")
        
        # Schedule daily training at 2 AM
        schedule.every().day.at("02:00").do(self.train_all_models)
        
        # Schedule incremental training every 6 hours
        schedule.every(6).hours.do(self.incremental_training)
        
        # Schedule validation every 12 hours
        schedule.every(12).hours.do(self.validate_all_models)
        
        logger.info("Scheduled tasks:")
        logger.info("- Full training: Daily at 2 AM")
        logger.info("- Incremental training: Every 6 hours")
        logger.info("- Validation: Every 12 hours")
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("Scheduled training stopped")
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(300)  # Wait 5 minutes on error
    
    def validate_all_models(self):
        """Validate all existing models."""
        logger.info("Validating all models...")
        
        for model in self.models_to_train:
            model_file = os.path.join(self.models_dir, f"{model}.pkl")
            if os.path.exists(model_file):
                result = self.validate_model(model)
                logger.info(f"{model}: {result.get('status', 'unknown')}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Harvey ML Automated Training')
    parser.add_argument('--mode', choices=['once', 'scheduled', 'incremental'],
                       default='once', help='Training mode')
    parser.add_argument('--force', action='store_true',
                       help='Force retraining of all models')
    parser.add_argument('--base-dir', default='/home/harvey/harvey-backend/ml_training',
                       help='Base directory for training')
    
    args = parser.parse_args()
    
    pipeline = MLTrainingPipeline(base_dir=args.base_dir)
    
    if args.mode == 'once':
        # Run training once
        results = pipeline.train_all_models(force=args.force)
        print(json.dumps(results, indent=2))
        
    elif args.mode == 'incremental':
        # Run incremental training
        pipeline.incremental_training()
        
    elif args.mode == 'scheduled':
        # Run scheduled training
        pipeline.run_scheduled_training()


if __name__ == "__main__":
    main()