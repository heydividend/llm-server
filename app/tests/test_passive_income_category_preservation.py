#!/usr/bin/env python3
"""
Test that PassiveIncomeTrainingService preserves curated categories and complexities.
This ensures the balanced 5-category design is maintained.
"""

import json
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.passive_income_training_service import PassiveIncomeTrainingService


class TestCategoryPreservation(unittest.TestCase):
    """Test that curated categories and complexities are preserved."""
    
    def setUp(self):
        """Set up test service."""
        self.service = PassiveIncomeTrainingService()
    
    def test_preserves_provided_category(self):
        """Test that provided category fields are preserved, not overwritten."""
        # Create test data with explicit categories
        test_data = [
            {
                "query": "What's better for passive income, JEPI or JEPQ?",
                "context": "investor seeking monthly income",
                "category": "comparison",  # This should be preserved
                "complexity": 3,
                "metrics": {
                    "JEPI": {"yield": 7.5, "dgr_5y": 0, "strategy": "option-overlay"},
                    "JEPQ": {"yield": 9.2, "dgr_5y": 0, "strategy": "option-overlay"}
                },
                "payout_frequency": {"JEPI": "monthly", "JEPQ": "monthly"},
                "dividend_calendar_map": {}
            },
            {
                "query": "How should I build a portfolio for $5k monthly income?",
                "context": "retiree with $1.5M portfolio",
                "category": "portfolio-construction",  # This should be preserved
                "complexity": 4,
                "metrics": {
                    "SCHD": {"yield": 3.2, "dgr_5y": 8.5, "strategy": "organic"},
                    "O": {"yield": 5.8, "dgr_5y": 3.2, "strategy": "organic"}
                },
                "payout_frequency": {"SCHD": "quarterly", "O": "monthly"},
                "dividend_calendar_map": {}
            },
            {
                "query": "How can I optimize my dividend payment schedule?",
                "context": "investor wanting monthly income",
                "category": "payout_optimization",  # This should be preserved
                "complexity": 3,
                "metrics": {},
                "payout_frequency": {},
                "dividend_calendar_map": {}
            },
            {
                "query": "Is this 30% yield from TSLY sustainable?",
                "context": "aggressive investor",
                "category": "risk-check",  # This should be preserved
                "complexity": 5,
                "metrics": {
                    "TSLY": {"yield": 30.5, "dgr_5y": -15, "strategy": "synthetic"}
                },
                "payout_frequency": {"TSLY": "monthly"},
                "dividend_calendar_map": {}
            },
            {
                "query": "Where should I hold MLPs for tax efficiency?",
                "context": "high-income investor",
                "category": "tax-allocation",  # This should be preserved
                "complexity": 4,
                "metrics": {
                    "EPD": {"yield": 7.2, "dgr_5y": 5.1, "strategy": "organic"}
                },
                "payout_frequency": {"EPD": "quarterly"},
                "dividend_calendar_map": {}
            }
        ]
        
        # Convert to JSONL format
        jsonl_content = "\n".join([json.dumps(data) for data in test_data])
        
        # Load the questions
        questions = self.service.load_training_questions_jsonl(jsonl_content, "test_preservation")
        
        # Verify categories were preserved
        self.assertEqual(len(questions), 5)
        self.assertEqual(questions[0].category, "comparison")
        self.assertEqual(questions[1].category, "portfolio-construction")
        self.assertEqual(questions[2].category, "payout_optimization")
        self.assertEqual(questions[3].category, "risk-check")
        self.assertEqual(questions[4].category, "tax-allocation")
        
        # Verify complexities were preserved
        self.assertEqual(questions[0].complexity, 3)
        self.assertEqual(questions[1].complexity, 4)
        self.assertEqual(questions[2].complexity, 3)
        self.assertEqual(questions[3].complexity, 5)
        self.assertEqual(questions[4].complexity, 4)
    
    def test_preserves_labels_nested_category(self):
        """Test that categories nested in 'labels' field are preserved."""
        test_data = {
            "query": "Compare SCHD vs VIG for dividend growth",
            "context": "long-term investor",
            "labels": {
                "category": "comparison",  # Nested category should be preserved
                "complexity": 2
            },
            "metrics": {
                "SCHD": {"yield": 3.2, "dgr_5y": 8.5, "strategy": "organic"},
                "VIG": {"yield": 1.8, "dgr_5y": 9.2, "strategy": "organic"}
            },
            "payout_frequency": {"SCHD": "quarterly", "VIG": "quarterly"},
            "dividend_calendar_map": {}
        }
        
        jsonl_content = json.dumps(test_data)
        questions = self.service.load_training_questions_jsonl(jsonl_content, "test_nested")
        
        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0].category, "comparison")
        self.assertEqual(questions[0].complexity, 2)
    
    def test_falls_back_to_heuristic_when_missing(self):
        """Test that heuristic is used only when category/complexity are missing."""
        test_data = {
            "query": "What are sustainable yields for retirement income?",  # Contains "sustainable"
            "context": "retiree",
            # No category or complexity provided - should use heuristics
            "metrics": {
                "VYM": {"yield": 2.9, "dgr_5y": 7.1, "strategy": "organic"}
            },
            "payout_frequency": {"VYM": "quarterly"},
            "dividend_calendar_map": {}
        }
        
        jsonl_content = json.dumps(test_data)
        questions = self.service.load_training_questions_jsonl(jsonl_content, "test_heuristic")
        
        self.assertEqual(len(questions), 1)
        # Should use heuristic category (contains "sustainable")
        self.assertEqual(questions[0].category, "yield_sustainability")
        # Should use heuristic complexity (base 2, single ticker)
        self.assertEqual(questions[0].complexity, 2)
    
    def test_mixed_preservation_and_heuristics(self):
        """Test a mix of preserved and heuristic-based categorization."""
        test_data = [
            {
                "query": "Compare tax efficiency of qualified dividends",
                "category": "tax-allocation",  # Provided - should be preserved
                # No complexity - should use heuristic
                "context": "high earner",
                "metrics": {},
                "payout_frequency": {},
                "dividend_calendar_map": {}
            },
            {
                "query": "Build diversified monthly income portfolio",
                # No category - should use heuristic (contains "monthly income")
                "complexity": 5,  # Provided - should be preserved
                "context": "investor",
                "metrics": {},
                "payout_frequency": {},
                "dividend_calendar_map": {}
            }
        ]
        
        jsonl_content = "\n".join([json.dumps(data) for data in test_data])
        questions = self.service.load_training_questions_jsonl(jsonl_content, "test_mixed")
        
        self.assertEqual(len(questions), 2)
        
        # First question: preserved category, heuristic complexity
        self.assertEqual(questions[0].category, "tax-allocation")
        self.assertEqual(questions[0].complexity, 3)  # Heuristic: base 2 + 1 for tax
        
        # Second question: heuristic category, preserved complexity
        self.assertEqual(questions[1].category, "income_planning")  # Heuristic
        self.assertEqual(questions[1].complexity, 5)
    
    def test_category_distribution_preservation(self):
        """Test that category distribution is preserved across a larger dataset."""
        # Simulate balanced dataset with exact category counts
        categories_and_counts = [
            ("comparison", 1320),
            ("portfolio-construction", 1320),
            ("payout_optimization", 1320),
            ("risk-check", 1320),
            ("tax-allocation", 1320)
        ]
        
        test_records = []
        for category, count in categories_and_counts:
            for i in range(min(10, count)):  # Test with 10 samples per category
                test_records.append({
                    "query": f"Test question {i} for {category}",
                    "context": "test context",
                    "category": category,
                    "complexity": 3,
                    "metrics": {},
                    "payout_frequency": {},
                    "dividend_calendar_map": {}
                })
        
        jsonl_content = "\n".join([json.dumps(record) for record in test_records])
        questions = self.service.load_training_questions_jsonl(jsonl_content, "test_distribution")
        
        # Count categories
        category_counts = {}
        for q in questions:
            category_counts[q.category] = category_counts.get(q.category, 0) + 1
        
        # Verify balanced distribution is preserved
        self.assertEqual(len(category_counts), 5)
        for category in ["comparison", "portfolio-construction", "payout_optimization", 
                        "risk-check", "tax-allocation"]:
            self.assertEqual(category_counts[category], 10)
        
        print(f"✓ Category distribution preserved: {category_counts}")


if __name__ == "__main__":
    unittest.main(verbosity=2)