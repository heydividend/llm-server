import json
import os
import unittest
from pathlib import Path

# Update BASE to point to our attached_assets directory
BASE = "attached_assets"

REQUIRED_KEYS = [
    "query",
    "context",
    "metrics",
    "payout_frequency",
    "dividend_calendar_map",
]

# Labels are optional in our structure but when present should have these
LABEL_KEYS = ["category"]

def load_jsonl(path, max_rows=None):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if not line.strip():
                continue
            rows.append(json.loads(line))
            if max_rows and i+1 >= max_rows:
                break
    return rows

class TestDatasetIntegrity(unittest.TestCase):

    def test_files_exist(self):
        """Test that key training files exist."""
        must_exist = [
            # Cross-validation folds
            "full6k_balanced_fold1_1762253797688.jsonl",
            "full6k_balanced_fold2_1762253797687.jsonl",
            "full6k_balanced_fold3_1762253797688.jsonl",
            "full6k_balanced_fold4_1762253797688.jsonl",
            "full6k_balanced_fold5_1762253797688.jsonl",
            # Category weights
            "category_weights_1762253797688.json",
            # Config
            "config_1762253797688.yaml",
            # Python modules
            "hf_loader_1762253797688.py",
            "hf_trainer_1762253797687.py",
            "lightning_trainer_1762253797688.py",
            "torchmetrics_eval_1762253797688.py",
            # README
            "README_passive_income_suite_1762253797687.md",
        ]
        
        missing = []
        for name in must_exist:
            path = os.path.join(BASE, name)
            if not os.path.exists(path):
                missing.append(name)
        
        if missing:
            print(f"Missing files: {missing}")
        
        # Check at least some files exist
        found = len(must_exist) - len(missing)
        self.assertGreater(found, 0, f"No training files found in {BASE}")

    def test_basic_schema_fold1(self):
        """Test the schema of fold 1 data."""
        path = os.path.join(BASE, "full6k_balanced_fold1_1762253797688.jsonl")
        
        if not os.path.exists(path):
            self.skipTest(f"File not found: {path}")
        
        rows = load_jsonl(path, max_rows=200)  # sample to keep fast
        self.assertGreater(len(rows), 0, "Fold 1 is empty")
        
        for i, rec in enumerate(rows[:10]):  # Check first 10 records
            # Check required keys
            for k in REQUIRED_KEYS:
                self.assertIn(k, rec, f"Row {i}: Missing key {k}")
            
            # Type checks
            self.assertIsInstance(rec["metrics"], dict, f"Row {i}: metrics should be dict")
            self.assertIsInstance(rec["payout_frequency"], dict, f"Row {i}: payout_frequency should be dict")
            self.assertIsInstance(rec["dividend_calendar_map"], dict, f"Row {i}: dividend_calendar_map should be dict")
            
            # Check metrics structure
            if rec["metrics"]:
                for ticker, vals in rec["metrics"].items():
                    self.assertIn("yield", vals, f"Row {i}: Missing yield for {ticker}")
                    self.assertIn("dgr_5y", vals, f"Row {i}: Missing dgr_5y for {ticker}")
                    self.assertIn("strategy", vals, f"Row {i}: Missing strategy for {ticker}")

    def test_category_weights_json(self):
        """Test category weights file structure."""
        path = os.path.join(BASE, "category_weights_1762253797688.json")
        
        if not os.path.exists(path):
            self.skipTest(f"File not found: {path}")
        
        with open(path, "r", encoding="utf-8") as f:
            w = json.load(f)
        
        self.assertIn("counts", w, "Missing counts in category_weights")
        self.assertIn("class_weights", w, "Missing class_weights in category_weights")
        
        # Check expected categories
        expected_cats = {"comparison", "portfolio-construction", "payout_optimization", "risk-check", "tax-allocation"}
        actual_cats = set(w["counts"].keys())
        
        self.assertEqual(actual_cats, expected_cats, f"Category mismatch. Expected: {expected_cats}, Got: {actual_cats}")
        
        # Verify weights are calculated correctly (inverse frequency)
        total = sum(w["counts"].values())
        for cat, count in w["counts"].items():
            expected_weight = total / (len(w["counts"]) * count)
            actual_weight = w["class_weights"][cat]
            self.assertAlmostEqual(actual_weight, expected_weight, places=4, 
                                 msg=f"Weight calculation error for {cat}")

    def test_fold_consistency(self):
        """Test that all folds have similar structure."""
        fold_files = [
            f"full6k_balanced_fold{i}_1762253797688.jsonl" if i != 2 
            else f"full6k_balanced_fold2_1762253797687.jsonl"
            for i in range(1, 6)
        ]
        
        fold_sizes = []
        for fold_file in fold_files:
            path = os.path.join(BASE, fold_file)
            if os.path.exists(path):
                rows = load_jsonl(path, max_rows=None)
                fold_sizes.append(len(rows))
                print(f"{fold_file}: {len(rows)} records")
        
        if fold_sizes:
            # Check that folds are roughly equal in size
            avg_size = sum(fold_sizes) / len(fold_sizes)
            for i, size in enumerate(fold_sizes):
                deviation = abs(size - avg_size) / avg_size
                self.assertLess(deviation, 0.1, 
                              f"Fold {i+1} has unusual size: {size} (avg: {avg_size:.1f})")

    def test_strategy_distribution(self):
        """Test that various dividend strategies are represented."""
        path = os.path.join(BASE, "full6k_balanced_fold1_1762253797688.jsonl")
        
        if not os.path.exists(path):
            self.skipTest(f"File not found: {path}")
        
        rows = load_jsonl(path, max_rows=500)
        
        strategies = set()
        for rec in rows:
            for ticker_data in rec.get("metrics", {}).values():
                strategies.add(ticker_data.get("strategy", "unknown"))
        
        # Check for key strategy types
        expected_strategies = {"organic", "option-overlay", "synthetic"}
        found_strategies = strategies & expected_strategies
        
        self.assertGreater(len(found_strategies), 0, 
                          f"No standard strategies found. Got: {strategies}")
        
        print(f"Found strategies: {sorted(strategies)}")

    def test_ticker_coverage(self):
        """Test that common dividend tickers are covered."""
        path = os.path.join(BASE, "full6k_balanced_fold1_1762253797688.jsonl")
        
        if not os.path.exists(path):
            self.skipTest(f"File not found: {path}")
        
        rows = load_jsonl(path, max_rows=500)
        
        tickers = set()
        for rec in rows:
            tickers.update(rec.get("metrics", {}).keys())
        
        # Check for some common dividend tickers
        common_tickers = {"JEPI", "JEPQ", "SCHD", "O", "MAIN", "RYLD", "XYLD"}
        found_tickers = tickers & common_tickers
        
        self.assertGreater(len(found_tickers), 3, 
                          f"Too few common tickers found. Expected some of {common_tickers}, got {found_tickers}")
        
        print(f"Total unique tickers: {len(tickers)}")
        print(f"Sample tickers: {sorted(list(tickers)[:20])}")

if __name__ == "__main__":
    unittest.main(verbosity=2)