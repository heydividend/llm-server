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
API_BASE_URL = "http://localhost:5000"
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
        status, result = ingest_batch(
            request_data,
            "/v1/training/passive-income"
        )
        
        if status == 200:
            print(f"✓ Successfully ingested {fold_name}:")
            if "statistics" in result:
                stats = result["statistics"]
                print(f"  - Total questions: {stats.get('total_questions', 0)}")
                print(f"  - Categories: {stats.get('categories', {})}")
                print(f"  - Complexity distribution: {stats.get('complexity_distribution', {})}")
        else:
            print(f"✗ Failed to ingest {fold_name}: {result}")
        
        # Small delay between batches
        time.sleep(1)

def ingest_train_val_test(train_file: str, val_file: str, test_file: str):
    """Ingest standard train/val/test splits."""
    splits = [
        ("train", train_file),
        ("validation", val_file),
        ("test", test_file)
    ]
    
    for split_name, filepath in splits:
        print(f"\nProcessing {split_name} split...")
        
        # Load data
        records = load_jsonl(filepath)
        
        # Prepare batch
        batch_data = prepare_training_batch(records, f"balanced_{split_name}")
        
        # Convert to JSONL format
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
        
        request_data = {
            "training_data": jsonl_content,
            "dataset_name": batch_data["dataset_name"]
        }
        
        # Ingest
        status, result = ingest_batch(
            request_data,
            "/v1/training/passive-income"
        )
        
        if status == 200:
            print(f"✓ Successfully ingested {split_name}:")
            if "statistics" in result:
                stats = result["statistics"]
                print(f"  - Total questions: {stats.get('total_questions', 0)}")
                print(f"  - Categories: {stats.get('categories', {})}")
        else:
            print(f"✗ Failed to ingest {split_name}: {result}")
        
        time.sleep(1)

def get_statistics():
    """Get passive income training statistics."""
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    response = requests.get(
        f"{API_BASE_URL}/v1/training/passive-income/stats",
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        return result.get("statistics", {})
    return None

def main():
    """Main ingestion process."""
    print("=" * 60)
    print("Harvey Balanced Passive Income Training Data Ingestion")
    print("=" * 60)
    
    # Check for files
    base_dir = "attached_assets"
    
    # Load category weights
    weights_file = os.path.join(base_dir, "category_weights_1762253797688.json")
    if os.path.exists(weights_file):
        weights = load_category_weights(weights_file)
        print("\nCategory weights loaded:")
        for cat, weight in weights.get("class_weights", {}).items():
            count = weights.get("counts", {}).get(cat, 0)
            print(f"  {cat}: {count} samples, weight={weight:.3f}")
    
    # Process cross-validation folds
    fold_files = [
        os.path.join(base_dir, f"full6k_balanced_fold{i}_1762253797688.jsonl")
        for i in range(1, 6)
    ]
    
    existing_folds = [f for f in fold_files if os.path.exists(f)]
    if existing_folds:
        print(f"\nFound {len(existing_folds)} cross-validation folds")
        process_fold_files(existing_folds)
    
    # Process train/val/test splits
    train_file = os.path.join(base_dir, "balanced_train_1762253775286.jsonl")
    val_file = os.path.join(base_dir, "balanced_val_1762253775286.jsonl")
    test_file = os.path.join(base_dir, "balanced_test_1762253775286.jsonl")
    
    if all(os.path.exists(f) for f in [train_file, val_file, test_file]):
        print("\nProcessing balanced train/val/test splits...")
        ingest_train_val_test(train_file, val_file, test_file)
    
    # Get final statistics
    print("\n" + "=" * 60)
    print("Final Statistics")
    print("=" * 60)
    
    stats = get_statistics()
    if stats:
        print(f"\nTotal training questions: {stats.get('total_questions', 0)}")
        print(f"Datasets: {stats.get('datasets', {})}")
        print(f"\nStrategy types covered:")
        for strategy, desc in stats.get("strategy_types", {}).items():
            print(f"  - {strategy}: {desc}")
        print(f"\nQuestion categories:")
        for cat, count in stats.get("question_categories", {}).items():
            print(f"  - {cat}: {count}")
        print(f"\nKey tickers: {', '.join(stats.get('key_tickers_covered', []))}")
    
    print("\n✓ Balanced passive income training data ingestion complete!")

if __name__ == "__main__":
    main()