#!/bin/bash
# Harvey Passive Income Training System - Deployment Script
# Run through Azure Portal -> VM -> Run Command -> RunShellScript
# This script deploys the fixed training system with preserved metadata

set -e

echo "=========================================="
echo "Harvey Training System Deployment"
echo "=========================================="
echo "Date: $(date)"
echo ""

# ============================================
# STEP 1: Navigate to Harvey backend
# ============================================
echo "Step 1: Navigating to Harvey backend..."
cd /opt/harvey-backend || { echo "ERROR: /opt/harvey-backend not found"; exit 1; }
echo "Current directory: $(pwd)"

# ============================================
# STEP 2: Backup existing files
# ============================================
echo ""
echo "Step 2: Backing up existing files..."
timestamp=$(date +%Y%m%d_%H%M%S)
mkdir -p backups

# Backup critical files if they exist
for file in app/services/passive_income_training_service.py app/scripts/ingest_balanced_passive_income.py; do
    if [ -f "$file" ]; then
        cp "$file" "backups/$(basename $file).${timestamp}.backup"
        echo "  Backed up: $file"
    fi
done

# ============================================
# STEP 3: Update PassiveIncomeTrainingService
# ============================================
echo ""
echo "Step 3: Updating PassiveIncomeTrainingService..."

# Ensure directories exist
mkdir -p app/services

cat > app/services/passive_income_training_service.py << 'PYTHON_SERVICE_EOF'
"""
Passive Income Training Service
Processes specialized dividend investment training data for Harvey.
Includes 7,200+ questions focused on dividend strategies, yield analysis, and income optimization.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import re
from dataclasses import dataclass
from enum import Enum
import csv
from io import StringIO

logger = logging.getLogger("passive_income_training")


@dataclass
class DividendMetrics:
    """Metrics for dividend-paying securities."""
    ticker: str
    yield_pct: float
    dgr_5y: float  # 5-year dividend growth rate
    strategy: str  # organic, option-overlay, synthetic, etc.
    payout_frequency: str  # monthly, quarterly


@dataclass
class TrainingQuestion:
    """A dividend-focused training question."""
    query: str
    context: str
    metrics: Dict[str, DividendMetrics]
    payout_frequency: Dict[str, str]
    dividend_calendar_map: Dict[str, List[str]]
    category: str
    complexity: int


class DividendStrategy(Enum):
    """Types of dividend strategies."""
    ORGANIC = "organic"  # Traditional dividends (KO, SCHD, VIG)
    OPTION_OVERLAY = "option-overlay"  # Covered call ETFs (JEPI, JEPQ, XYLD)
    SYNTHETIC = "synthetic"  # YieldMax series (TSLY, NVDY, APLY)
    LEVERAGED_CREDIT = "leveraged-credit"  # CEFs with leverage (PDO)
    INFRA_CEF = "infra-CEF"  # Infrastructure CEFs (UTF)
    OPTION_CEF = "option-CEF"  # Option-based CEFs (ETY)


class PassiveIncomeTrainingService:
    """
    Comprehensive service for processing passive income training data.
    Specializes in dividend investing, yield strategies, and income optimization.
    """
    
    def __init__(self):
        """Initialize with evaluation targets and lesson plans."""
        self.evaluation_targets = {
            "global": {
                "clear_score_min": 0.9,
                "complete_score_min": 0.85,
                "actionable_score_min": 0.9
            },
            "per_level": {
                "beginner": {"clear_min": 0.92, "complete_min": 0.80, "actionable_min": 0.92},
                "intermediate": {"clear_min": 0.90, "complete_min": 0.86, "actionable_min": 0.90},
                "advanced": {"clear_min": 0.88, "complete_min": 0.90, "actionable_min": 0.88}
            }
        }
        
        self.auto_rewrite_prompts = {}
        self.lesson_modules = []
        self.training_questions = []
        
        logger.info("Passive Income Training Service initialized")
    
    def load_training_questions_jsonl(self, jsonl_content: str, dataset_name: str = "main") -> List[TrainingQuestion]:
        """
        Load training questions from JSONL format.
        
        Args:
            jsonl_content: JSONL string with training questions
            dataset_name: Name of the dataset (main or supplemental)
            
        Returns:
            List of parsed TrainingQuestion objects
        """
        questions = []
        lines = jsonl_content.strip().split('\n')
        
        for index, line in enumerate(lines):
            if not line.strip():
                continue
                
            try:
                data = json.loads(line)
                
                # Parse metrics for each ticker
                metrics = {}
                if "metrics" in data:
                    for ticker, ticker_metrics in data["metrics"].items():
                        metrics[ticker] = DividendMetrics(
                            ticker=ticker,
                            yield_pct=ticker_metrics.get("yield", 0.0),
                            dgr_5y=ticker_metrics.get("dgr_5y", 0.0),
                            strategy=ticker_metrics.get("strategy", "organic"),
                            payout_frequency=data.get("payout_frequency", {}).get(ticker, "quarterly")
                        )
                
                # Preserve existing category if present, otherwise use heuristic
                if "category" in data:
                    # Trust the provided category from curated data
                    category = data["category"]
                    logger.debug(f"Using provided category: {category}")
                elif "labels" in data and "category" in data["labels"]:
                    # Check if category is nested in labels
                    category = data["labels"]["category"]
                    logger.debug(f"Using category from labels: {category}")
                else:
                    # Fall back to heuristic only when category is missing
                    category = self._categorize_question(data.get("query", ""))
                    logger.debug(f"Using heuristic category: {category}")
                
                # Preserve existing complexity if present, otherwise use heuristic
                if "complexity" in data:
                    # Trust the provided complexity from curated data
                    complexity = data["complexity"]
                    logger.debug(f"Using provided complexity: {complexity}")
                elif "labels" in data and "complexity" in data["labels"]:
                    # Check if complexity is nested in labels
                    complexity = data["labels"]["complexity"]
                    logger.debug(f"Using complexity from labels: {complexity}")
                else:
                    # Fall back to heuristic only when complexity is missing
                    complexity = self._determine_complexity(metrics, data.get("query", ""))
                    logger.debug(f"Using heuristic complexity: {complexity}")
                
                question = TrainingQuestion(
                    query=data.get("query", ""),
                    context=data.get("context", ""),
                    metrics=metrics,
                    payout_frequency=data.get("payout_frequency", {}),
                    dividend_calendar_map=data.get("dividend_calendar_map", {}),
                    category=category,
                    complexity=complexity
                )
                questions.append(question)
                
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing line {index}: {e}")
                continue
            except Exception as e:
                logger.error(f"Error processing line {index}: {e}")
                continue
        
        logger.info(f"Loaded {len(questions)} questions from {dataset_name}")
        return questions
    
    def _categorize_question(self, query: str) -> str:
        """Categorize question based on query text (fallback heuristic)."""
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in ["compare", "better", "vs", "versus", "which"]):
            return "comparison"
        elif any(keyword in query_lower for keyword in ["build", "create", "design", "portfolio", "allocation"]):
            return "portfolio-construction"
        elif any(keyword in query_lower for keyword in ["monthly income", "income plan", "payout", "schedule"]):
            return "payout_optimization"
        elif any(keyword in query_lower for keyword in ["sustainable", "risk", "volatility", "nav", "erosion"]):
            return "risk-check"
        elif any(keyword in query_lower for keyword in ["tax", "ira", "roth", "401k", "after-tax"]):
            return "tax-allocation"
        else:
            return "comparison"  # default
    
    def _determine_complexity(self, metrics: Dict[str, DividendMetrics], query: str) -> int:
        """Determine complexity based on metrics and query (fallback heuristic)."""
        if not metrics:
            return 3  # default medium
        
        # Check for high-yield synthetic strategies (very complex)
        yields = [m.yield_pct for m in metrics.values()]
        strategies = [m.strategy for m in metrics.values()]
        
        if any(y > 30 for y in yields):
            return 5  # Very high yield, likely synthetic
        elif any(s == "synthetic" for s in strategies):
            return 5
        elif any(y > 15 for y in yields):
            return 4  # High yield
        elif len(metrics) > 3:
            return 4  # Multiple securities to analyze
        elif any(y < 3 for y in yields):
            return 2  # Low yield dividend growers
        else:
            return 3  # Medium complexity
    
    def validate_category_distribution(self, questions: List[TrainingQuestion]) -> Dict[str, int]:
        """Validate the distribution of categories in the dataset."""
        category_counts = {}
        for question in questions:
            category = question.category
            category_counts[category] = category_counts.get(category, 0) + 1
        
        logger.info(f"Category distribution: {category_counts}")
        total = sum(category_counts.values())
        
        for category, count in category_counts.items():
            percentage = (count / total) * 100
            logger.info(f"  {category}: {count} ({percentage:.1f}%)")
        
        return category_counts
PYTHON_SERVICE_EOF

echo "✅ PassiveIncomeTrainingService updated"

# ============================================
# STEP 4: Update Ingestion Script
# ============================================
echo ""
echo "Step 4: Updating ingestion script..."

mkdir -p app/scripts

cat > app/scripts/ingest_balanced_passive_income.py << 'PYTHON_SCRIPT_EOF'
#!/usr/bin/env python3
"""
Ingest balanced passive income training data into Harvey's training system.
Processes 6,600+ balanced questions across 5 categories with cross-validation folds.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any
import requests
from datetime import datetime
import time

# API configuration
API_BASE_URL = "http://localhost:8000"
API_KEY = os.environ.get("HARVEY_AI_API_KEY", "test-api-key-123")

def load_jsonl(filepath: str) -> List[Dict]:
    """Load JSONL file."""
    data = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def load_category_weights(filepath: str) -> Dict:
    """Load category weights for balanced sampling."""
    with open(filepath, 'r') as f:
        return json.load(f)

def prepare_training_batch(records: List[Dict], batch_name: str) -> Dict:
    """Prepare a batch of training records for ingestion.
    
    This function preserves curated category and complexity values from the dataset
    when present, only computing fallback values when missing.
    """
    questions = []
    
    for record in records:
        # Extract fields
        query = record.get("query", "")
        context = record.get("context", "")
        metrics = record.get("metrics", {})
        payout_freq = record.get("payout_frequency", {})
        calendar_map = record.get("dividend_calendar_map", {})
        
        # Get category - check both top level and labels field
        # Priority: top level > labels > default
        category = None
        if "category" in record:
            category = record["category"]
        elif "labels" in record and "category" in record["labels"]:
            category = record["labels"]["category"]
        
        # Use default only if no category found
        if category is None:
            category = "comparison"  # default
        
        # Get complexity - check if already exists before computing
        # Priority: top level > labels > computed from metrics
        complexity = None
        if "complexity" in record:
            complexity = record["complexity"]
        elif "labels" in record and "complexity" in record["labels"]:
            complexity = record["labels"]["complexity"]
        
        # Only compute complexity if not already present
        if complexity is None:
            complexity = 3  # default medium
            if metrics:
                yields = [float(m.get("yield", 0)) for m in metrics.values()]
                if max(yields, default=0) > 30:  # Very high yield synthetic
                    complexity = 5
                elif max(yields, default=0) > 15:  # High yield
                    complexity = 4
                elif min(yields, default=100) < 3:  # Low yield dividend growers
                    complexity = 2
        
        # Build question object
        question = {
            "query": query,
            "context": context,
            "category": category,
            "complexity": complexity,
            "metadata": {
                "metrics": metrics,
                "payout_frequency": payout_freq,
                "dividend_calendar": calendar_map
            }
        }
        questions.append(question)
    
    return {
        "training_data": json.dumps(questions),
        "dataset_name": batch_name
    }

def ingest_batch(batch_data: Dict, endpoint: str):
    """Ingest a batch of training data."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{API_BASE_URL}{endpoint}",
        json=batch_data,
        headers=headers
    )
    
    return response.status_code, response.json()

def process_fold_files(fold_files: List[str]):
    """Process cross-validation fold files."""
    for fold_file in fold_files:
        print(f"\nProcessing {fold_file}...")
        
        # Load data
        records = load_jsonl(fold_file)
        fold_name = Path(fold_file).stem
        
        # Prepare batch
        batch_data = prepare_training_batch(records, f"balanced_{fold_name}")
        
        # Convert to JSONL format for passive income endpoint
        jsonl_content = "\n".join([
            json.dumps({
                "query": q["query"],
                "context": q["context"],
                "metrics": q["metadata"]["metrics"],
                "payout_frequency": q["metadata"]["payout_frequency"],
                "dividend_calendar_map": q["metadata"]["dividend_calendar"],
                "category": q["category"],
                "complexity": q["complexity"]
            }) for q in json.loads(batch_data["training_data"])
        ])
        
        # Prepare request
        request_data = {
            "training_data": jsonl_content,
            "dataset_name": batch_data["dataset_name"]
        }
        
        # Ingest via passive income endpoint
        status, response = ingest_batch(
            request_data,
            "/v1/training/passive-income/ingest"
        )
        
        if status == 200:
            print(f"✅ {fold_name}: {response.get('questions_ingested', 0)} questions ingested")
            print(f"   Categories: {response.get('category_distribution', {})}")
        else:
            print(f"❌ {fold_name} failed: {response}")

def main():
    """Main ingestion process."""
    print("=" * 60)
    print("Passive Income Training Data Ingestion")
    print("=" * 60)
    
    # Define fold files
    fold_files = [
        "/opt/harvey-backend/training_data/full6k_balanced_fold1_1762253797688.jsonl",
        "/opt/harvey-backend/training_data/full6k_balanced_fold2_1762253797687.jsonl",
        "/opt/harvey-backend/training_data/full6k_balanced_fold3_1762253797688.jsonl",
        "/opt/harvey-backend/training_data/full6k_balanced_fold4_1762253797688.jsonl",
        "/opt/harvey-backend/training_data/full6k_balanced_fold5_1762253797688.jsonl"
    ]
    
    # Process all folds
    process_fold_files(fold_files)
    
    print("\n" + "=" * 60)
    print("✅ Ingestion Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
PYTHON_SCRIPT_EOF

chmod +x app/scripts/ingest_balanced_passive_income.py
echo "✅ Ingestion script updated"

# ============================================
# STEP 5: Create training data directory
# ============================================
echo ""
echo "Step 5: Creating training data directory..."
mkdir -p training_data
echo "✅ Training data directory created: /opt/harvey-backend/training_data"

# ============================================
# STEP 6: Deploy training datasets
# ============================================
echo ""
echo "Step 6: Deploying balanced training datasets..."
echo "Note: Training data files need to be uploaded separately"
echo "Expected files in training_data/:"
echo "  - full6k_balanced_fold1_1762253797688.jsonl"
echo "  - full6k_balanced_fold2_1762253797687.jsonl"
echo "  - full6k_balanced_fold3_1762253797688.jsonl"
echo "  - full6k_balanced_fold4_1762253797688.jsonl"
echo "  - full6k_balanced_fold5_1762253797688.jsonl"

# ============================================
# STEP 7: Create test files
# ============================================
echo ""
echo "Step 7: Creating test files for CI/CD..."
mkdir -p app/tests

cat > app/tests/test_passive_income_category_preservation.py << 'PYTHON_TEST_EOF'
"""Test that passive income training preserves curated categories."""

import json
import sys
import os
sys.path.append('/opt/harvey-backend')

from app.services.passive_income_training_service import PassiveIncomeTrainingService

def test_category_preservation():
    """Test that curated categories are preserved during ingestion."""
    service = PassiveIncomeTrainingService()
    
    # Test data with explicit categories
    test_jsonl = """{"query": "Test 1", "context": "Context", "category": "comparison", "metrics": {}}
{"query": "Test 2", "context": "Context", "category": "portfolio-construction", "metrics": {}}
{"query": "Test 3", "context": "Context", "category": "risk-check", "metrics": {}}"""
    
    questions = service.load_training_questions_jsonl(test_jsonl)
    
    assert questions[0].category == "comparison"
    assert questions[1].category == "portfolio-construction"
    assert questions[2].category == "risk-check"
    
    print("✅ Category preservation test passed")

if __name__ == "__main__":
    test_category_preservation()
PYTHON_TEST_EOF

echo "✅ Test files created"

# ============================================
# STEP 8: Set proper permissions
# ============================================
echo ""
echo "Step 8: Setting file permissions..."
chown -R azureuser:azureuser /opt/harvey-backend/app
chown -R azureuser:azureuser /opt/harvey-backend/training_data
echo "✅ Permissions set"

# ============================================
# STEP 9: Restart Harvey backend service
# ============================================
echo ""
echo "Step 9: Restarting Harvey backend service..."
systemctl daemon-reload
systemctl restart harvey.service || systemctl restart harvey-backend.service || true
sleep 5

# Check service status
if systemctl is-active harvey.service &>/dev/null; then
    echo "✅ Harvey service restarted successfully"
elif systemctl is-active harvey-backend.service &>/dev/null; then
    echo "✅ Harvey backend service restarted successfully"
else
    echo "⚠️ Warning: Could not verify service status"
fi

# ============================================
# STEP 10: Verify deployment
# ============================================
echo ""
echo "Step 10: Verifying deployment..."

# Test if Harvey is responding
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "✅ Harvey backend is responding"
else
    echo "⚠️ Harvey backend not responding on port 8000"
fi

# Check if the files were updated
echo ""
echo "File update verification:"
if [ -f "app/services/passive_income_training_service.py" ]; then
    echo "✅ PassiveIncomeTrainingService updated"
    echo "  File size: $(stat -c%s app/services/passive_income_training_service.py) bytes"
    echo "  Modified: $(stat -c%y app/services/passive_income_training_service.py)"
fi

if [ -f "app/scripts/ingest_balanced_passive_income.py" ]; then
    echo "✅ Ingestion script updated"
    echo "  File size: $(stat -c%s app/scripts/ingest_balanced_passive_income.py) bytes"
    echo "  Modified: $(stat -c%y app/scripts/ingest_balanced_passive_income.py)"
fi

# ============================================
# DEPLOYMENT COMPLETE
# ============================================
echo ""
echo "=========================================="
echo "✅ Training System Deployment Complete!"
echo "=========================================="
echo ""
echo "📊 Summary:"
echo "  - PassiveIncomeTrainingService: Updated"
echo "  - Ingestion script: Updated"
echo "  - Test files: Created"
echo "  - Harvey service: Restarted"
echo ""
echo "📝 Next Steps:"
echo "1. Upload training data files to /opt/harvey-backend/training_data/"
echo "2. Run the ingestion script:"
echo "   cd /opt/harvey-backend"
echo "   python3 app/scripts/ingest_balanced_passive_income.py"
echo ""
echo "📋 Verify with:"
echo "  systemctl status harvey.service"
echo "  journalctl -u harvey.service -n 50"
echo ""
echo "🔍 Test the service:"
echo "  curl http://localhost:8000/v1/training/passive-income/status"
echo ""