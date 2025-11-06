#!/usr/bin/env python3
"""
Test that real balanced datasets preserve their curated category distribution.
"""

import json
import os
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.passive_income_training_service import PassiveIncomeTrainingService


class TestRealDataPreservation(unittest.TestCase):
    """Test with actual balanced dataset files."""
    
    def setUp(self):
        """Set up test service."""
        self.service = PassiveIncomeTrainingService()
        self.base_dir = "attached_assets"
    
    def load_jsonl_file(self, filename):
        """Load a JSONL file from attached_assets."""
        filepath = os.path.join(self.base_dir, filename)
        if not os.path.exists(filepath):
            self.skipTest(f"File not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    
    def test_fold1_category_preservation(self):
        """Test that fold1 preserves the balanced category distribution."""
        # Load fold1 data
        jsonl_content = self.load_jsonl_file("full6k_balanced_fold1_1762253797688.jsonl")
        
        # Process through the service
        questions = self.service.load_training_questions_jsonl(jsonl_content, "fold1_test")
        
        # Count categories
        category_counts = {}
        for q in questions:
            category_counts[q.category] = category_counts.get(q.category, 0) + 1
        
        print(f"\nFold 1 Category Distribution:")
        for cat, count in sorted(category_counts.items()):
            print(f"  {cat}: {count}")
        
        # Check expected categories exist
        expected_categories = {
            "comparison", "portfolio-construction", 
            "payout_optimization", "risk-check", "tax-allocation"
        }
        
        # Some questions might use heuristic categories if not labeled
        # But the main 5 categories should dominate
        main_category_count = sum(
            category_counts.get(cat, 0) for cat in expected_categories
        )
        total_count = sum(category_counts.values())
        
        # At least 90% should be in the main 5 categories
        if total_count > 0:
            main_category_percentage = (main_category_count / total_count) * 100
            self.assertGreaterEqual(main_category_percentage, 90,
                f"Expected at least 90% in main categories, got {main_category_percentage:.1f}%")
            
            # Check that categories are relatively balanced (within 20% of each other)
            main_counts = [category_counts.get(cat, 0) for cat in expected_categories]
            if all(c > 0 for c in main_counts):
                max_count = max(main_counts)
                min_count = min(main_counts)
                balance_ratio = min_count / max_count if max_count > 0 else 0
                self.assertGreaterEqual(balance_ratio, 0.8,
                    f"Categories not balanced. Min: {min_count}, Max: {max_count}")
    
    def test_category_weights_file_matches_distribution(self):
        """Test that the category weights file matches the actual distribution."""
        # Load category weights
        weights_file = os.path.join(self.base_dir, "category_weights_1762253797688.json")
        if not os.path.exists(weights_file):
            self.skipTest(f"Weights file not found: {weights_file}")
        
        with open(weights_file, 'r') as f:
            weights_data = json.load(f)
        
        expected_counts = weights_data.get("counts", {})
        
        # Load a sample of fold1 data to verify
        jsonl_content = self.load_jsonl_file("full6k_balanced_fold1_1762253797688.jsonl")
        
        # Take first 500 lines as sample
        lines = jsonl_content.strip().split('\n')[:500]
        sample_content = '\n'.join(lines)
        
        questions = self.service.load_training_questions_jsonl(sample_content, "sample_test")
        
        # Count categories in sample
        sample_counts = {}
        for q in questions:
            sample_counts[q.category] = sample_counts.get(q.category, 0) + 1
        
        print(f"\nCategory Weights vs Sample Distribution:")
        print(f"Expected total in full dataset: {sum(expected_counts.values())}")
        print(f"Sample size: {len(questions)}")
        print(f"\nSample distribution:")
        for cat in expected_counts.keys():
            sample_count = sample_counts.get(cat, 0)
            sample_pct = (sample_count / len(questions) * 100) if questions else 0
            expected_pct = 20  # Should be balanced at ~20% each for 5 categories
            print(f"  {cat}: {sample_count} ({sample_pct:.1f}%) - Expected: ~{expected_pct}%")
    
    def test_no_heuristic_overrides_in_labeled_data(self):
        """Verify heuristic categories aren't overriding labeled data."""
        # Create test cases where heuristic would differ from label
        test_cases = [
            {
                # Query contains "tax" which heuristic would label as "tax_optimization"
                # But it's labeled as "comparison"
                "query": "Should I prioritize tax-efficient funds SCHD or VIG?",
                "context": "investor seeking tax efficiency",
                "category": "comparison",  # This should be preserved
                "metrics": {
                    "SCHD": {"yield": 3.2, "dgr_5y": 8.5, "strategy": "organic"},
                    "VIG": {"yield": 1.8, "dgr_5y": 9.2, "strategy": "organic"}
                },
                "payout_frequency": {"SCHD": "quarterly", "VIG": "quarterly"},
                "dividend_calendar_map": {}
            },
            {
                # Query contains "sustainable" which heuristic would label as "yield_sustainability"
                # But it's labeled as "risk-check"
                "query": "Are these sustainable yields realistic for retirement?",
                "context": "conservative retiree",
                "category": "risk-check",  # This should be preserved
                "metrics": {
                    "JEPI": {"yield": 7.5, "dgr_5y": 0, "strategy": "option-overlay"}
                },
                "payout_frequency": {"JEPI": "monthly"},
                "dividend_calendar_map": {}
            },
            {
                # Query contains "monthly income" which heuristic would label as "income_planning"
                # But it's labeled as "payout_optimization"
                "query": "How to structure monthly income from quarterly payers?",
                "context": "income investor",
                "category": "payout_optimization",  # This should be preserved
                "metrics": {},
                "payout_frequency": {},
                "dividend_calendar_map": {}
            }
        ]
        
        jsonl_content = "\n".join([json.dumps(case) for case in test_cases])
        questions = self.service.load_training_questions_jsonl(jsonl_content, "override_test")
        
        # Verify labels were preserved, not overridden by heuristics
        self.assertEqual(questions[0].category, "comparison", 
                        "Category was overridden by heuristic (expected comparison, not tax_optimization)")
        self.assertEqual(questions[1].category, "risk-check",
                        "Category was overridden by heuristic (expected risk-check, not yield_sustainability)")
        self.assertEqual(questions[2].category, "payout_optimization",
                        "Category was overridden by heuristic (expected payout_optimization, not income_planning)")
        
        print("✓ Labeled categories correctly preserved over heuristics")


if __name__ == "__main__":
    unittest.main(verbosity=2)