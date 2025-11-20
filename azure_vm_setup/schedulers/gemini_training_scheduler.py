#!/usr/bin/env python3
"""
Harvey AI - Gemini Training Data Scheduler
Automatically generates training data using Gemini 2.5 Pro on a weekly schedule
"""

import os
import sys
import json
import time
import logging
import schedule
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/harvey/gemini_training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('GeminiTrainingScheduler')


class GeminiTrainingScheduler:
    """Automated scheduler for Gemini training data generation."""
    
    def __init__(self, harvey_dir: str = "/home/azureuser/harvey"):
        """
        Initialize Gemini training scheduler.
        
        Args:
            harvey_dir: Base directory for Harvey backend
        """
        self.harvey_dir = harvey_dir
        self.scripts_dir = os.path.join(harvey_dir, "scripts")
        self.status_file = "/var/log/harvey/gemini_training_status.json"
        self.metrics_file = os.path.join(harvey_dir, "gemini_training_metrics.json")
        
        # Create directories
        os.makedirs(os.path.dirname(self.status_file), exist_ok=True)
        
        # Training configuration
        self.weekly_config = {
            "total_questions": 100,
            "categories": [
                "dividend_analysis",
                "income_strategies", 
                "technical_timing",
                "etf_funds",
                "tax_optimization",
                "risk_management",
                "market_analysis",
                "portfolio_construction",
                "dividend_sustainability",
                "global_dividend_markets"
            ]
        }
        
        logger.info(f"Gemini Training Scheduler initialized (harvey_dir: {harvey_dir})")
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met for training generation."""
        try:
            # Check if Harvey directory exists
            if not os.path.exists(self.harvey_dir):
                logger.error(f"Harvey directory not found: {self.harvey_dir}")
                return False
            
            # Check if training script exists
            script_path = os.path.join(self.scripts_dir, "generate_training_data.py")
            if not os.path.exists(script_path):
                logger.error(f"Training script not found: {script_path}")
                return False
            
            # Check if GEMINI_API_KEY is set
            result = subprocess.run(
                ["python", "-c", "import os; from dotenv import load_dotenv; load_dotenv(override=True); key = os.getenv('GEMINI_API_KEY'); print('OK' if key and len(key) == 39 else 'INVALID')"],
                cwd=self.harvey_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.stdout.strip() != "OK":
                logger.error("GEMINI_API_KEY not found or invalid")
                return False
            
            logger.info("✓ All prerequisites met")
            return True
            
        except Exception as e:
            logger.error(f"Prerequisites check failed: {e}")
            return False
    
    def generate_training_data(
        self,
        category: str = None,
        count: int = 100,
        to_database: bool = True
    ) -> Dict[str, Any]:
        """
        Generate training data using Gemini.
        
        Args:
            category: Specific category or None for all categories
            count: Number of questions to generate
            to_database: Whether to save to database
            
        Returns:
            Generation results dictionary
        """
        logger.info(f"Generating {count} training questions (category: {category or 'all'})")
        
        try:
            # Build command
            cmd = [
                "python",
                "scripts/generate_training_data.py",
                "--count", str(count),
                "--with-answers"
            ]
            
            if category:
                cmd.extend(["--category", category])
            else:
                cmd.append("--all-categories")
            
            if to_database:
                cmd.append("--to-database")
            
            # Run generation
            start_time = time.time()
            result = subprocess.run(
                cmd,
                cwd=self.harvey_dir,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout
            )
            
            duration = time.time() - start_time
            
            if result.returncode != 0:
                logger.error(f"Generation failed: {result.stderr}")
                return {
                    "status": "failed",
                    "error": result.stderr,
                    "duration": duration
                }
            
            # Parse output to count generated questions
            generated_count = self._parse_generated_count(result.stdout)
            
            logger.info(f"✓ Generated {generated_count} questions in {duration:.1f}s")
            
            return {
                "status": "success",
                "category": category or "all",
                "requested": count,
                "generated": generated_count,
                "duration": duration,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "output": result.stdout[-500:]  # Last 500 chars
            }
            
        except subprocess.TimeoutExpired:
            logger.error("Generation timeout")
            return {"status": "timeout", "category": category}
        except Exception as e:
            logger.error(f"Generation error: {e}")
            return {"status": "error", "error": str(e)}
    
    def _parse_generated_count(self, output: str) -> int:
        """Parse the number of generated questions from output."""
        try:
            # Look for "Generated X questions" in output
            for line in output.split('\n'):
                if 'Generated' in line and 'questions' in line:
                    # Extract number
                    words = line.split()
                    for i, word in enumerate(words):
                        if word == 'Generated' and i + 1 < len(words):
                            try:
                                return int(words[i + 1])
                            except ValueError:
                                pass
            return 0
        except:
            return 0
    
    def weekly_generation(self):
        """Run weekly training data generation."""
        logger.info("=" * 70)
        logger.info("WEEKLY GEMINI TRAINING DATA GENERATION")
        logger.info("=" * 70)
        
        # Check prerequisites
        if not self.check_prerequisites():
            logger.error("Prerequisites not met, skipping generation")
            self.save_status({"status": "skipped", "reason": "prerequisites_not_met"})
            return
        
        # Generate training data for all categories
        total_config = self.weekly_config
        questions_per_category = total_config["total_questions"] // len(total_config["categories"])
        
        results = {
            "start_time": datetime.now(timezone.utc).isoformat(),
            "categories": {},
            "total_requested": total_config["total_questions"],
            "total_generated": 0
        }
        
        # Generate for each category
        for category in total_config["categories"]:
            logger.info(f"\nGenerating {questions_per_category} questions for {category}...")
            
            result = self.generate_training_data(
                category=category,
                count=questions_per_category,
                to_database=True
            )
            
            results["categories"][category] = result
            
            if result["status"] == "success":
                results["total_generated"] += result.get("generated", 0)
            
            # Small delay between categories to respect rate limits
            time.sleep(5)
        
        results["end_time"] = datetime.now(timezone.utc).isoformat()
        results["success_rate"] = results["total_generated"] / results["total_requested"] if results["total_requested"] > 0 else 0
        
        # Save results
        self.save_metrics(results)
        self.save_status({
            "status": "completed",
            "total_generated": results["total_generated"],
            "last_run": results["end_time"]
        })
        
        logger.info("=" * 70)
        logger.info(f"Weekly generation complete: {results['total_generated']}/{results['total_requested']} questions")
        logger.info("=" * 70)
    
    def save_metrics(self, results: Dict[str, Any]):
        """Save training generation metrics to file."""
        try:
            # Load existing metrics
            existing_metrics = []
            if os.path.exists(self.metrics_file):
                with open(self.metrics_file, 'r') as f:
                    existing_metrics = json.load(f)
            
            # Append new results
            existing_metrics.append(results)
            
            # Keep only last 50 runs
            existing_metrics = existing_metrics[-50:]
            
            # Save
            with open(self.metrics_file, 'w') as f:
                json.dump(existing_metrics, f, indent=2)
            
            logger.info(f"Metrics saved to {self.metrics_file}")
            
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
    
    def save_status(self, status: Dict[str, Any]):
        """Save current status."""
        try:
            status["last_updated"] = datetime.now(timezone.utc).isoformat()
            
            with open(self.status_file, 'w') as f:
                json.dump(status, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save status: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current scheduler status."""
        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r') as f:
                    return json.load(f)
            return {"status": "never_run"}
        except:
            return {"status": "unknown"}
    
    def run_scheduled(self):
        """Run scheduled training generation."""
        logger.info("Starting Gemini Training Scheduler...")
        logger.info("Schedule: Every Sunday at 4:00 AM (after ML model training)")
        
        # Schedule weekly generation
        schedule.every().sunday.at("04:00").do(self.weekly_generation)
        
        logger.info("Scheduler is running. Press Ctrl+C to stop.")
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("Scheduler stopped by user")
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(300)  # Wait 5 minutes on error


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Gemini Training Data Scheduler')
    parser.add_argument('--mode', choices=['once', 'scheduled', 'test'],
                       default='scheduled', help='Execution mode')
    parser.add_argument('--harvey-dir', default='/home/azureuser/harvey',
                       help='Harvey backend directory')
    parser.add_argument('--count', type=int, default=100,
                       help='Number of questions to generate (once/test mode)')
    parser.add_argument('--category', type=str,
                       help='Specific category (once/test mode)')
    
    args = parser.parse_args()
    
    scheduler = GeminiTrainingScheduler(harvey_dir=args.harvey_dir)
    
    if args.mode == 'once':
        # Run generation once
        result = scheduler.generate_training_data(
            category=args.category,
            count=args.count,
            to_database=True
        )
        print(json.dumps(result, indent=2))
        
    elif args.mode == 'test':
        # Test with small count
        logger.info("Running test generation (5 questions)...")
        result = scheduler.generate_training_data(
            category=args.category or "dividend_analysis",
            count=5,
            to_database=False
        )
        print(json.dumps(result, indent=2))
        
    elif args.mode == 'scheduled':
        # Run scheduled mode
        scheduler.run_scheduled()


if __name__ == "__main__":
    main()
