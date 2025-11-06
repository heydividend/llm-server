#!/usr/bin/env python3
"""
Test that the ingestion script preserves curated metadata from balanced datasets.

This test verifies that the prepare_training_batch function in 
app/scripts/ingest_balanced_passive_income.py properly preserves 
category and complexity values when they exist in the input data.
"""

import json
import sys
import unittest
from pathlib import Path

# Add parent directory to path to import the ingestion script
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.scripts.ingest_balanced_passive_income import prepare_training_batch


class TestIngestionMetadataPreservation(unittest.TestCase):
    """Test metadata preservation in the ingestion script."""
    
    def test_preserves_category_from_labels(self):
        """Test that category is preserved from labels field."""
        records = [
            {
                "query": "Which is better for income: JEPI or SCHD?",
                "context": "Investor seeks monthly income",
                "metrics": {"JEPI": {"yield": 8.5}, "SCHD": {"yield": 3.2}},
                "payout_frequency": {"JEPI": "monthly", "SCHD": "quarterly"},
                "dividend_calendar_map": {"Jan": ["JEPI"], "Feb": ["JEPI"], "Mar": ["JEPI", "SCHD"]},
                "labels": {
                    "category": "comparison",
                    "income_focus": "monthly"
                }
            },
            {
                "query": "How should I allocate between dividend ETFs in a taxable account?",
                "context": "Tax-efficient income strategy",
                "metrics": {"SCHD": {"yield": 3.2}, "DVY": {"yield": 3.8}},
                "payout_frequency": {"SCHD": "quarterly", "DVY": "quarterly"},
                "dividend_calendar_map": {"Mar": ["SCHD", "DVY"]},
                "labels": {
                    "category": "tax-allocation",
                    "tax_focus": "efficiency"
                }
            }
        ]
        
        result = prepare_training_batch(records, "test_batch")
        questions = json.loads(result["training_data"])
        
        # Verify categories are preserved from labels
        self.assertEqual(questions[0]["category"], "comparison")
        self.assertEqual(questions[1]["category"], "tax-allocation")
        
    def test_preserves_category_from_top_level(self):
        """Test that category at top level takes precedence."""
        records = [
            {
                "query": "Build a portfolio for $50K passive income",
                "context": "Portfolio construction request",
                "category": "portfolio-construction",  # Top level
                "metrics": {"JEPI": {"yield": 8.5}},
                "payout_frequency": {"JEPI": "monthly"},
                "dividend_calendar_map": {"Jan": ["JEPI"]},
                "labels": {
                    "category": "comparison",  # Should be overridden
                    "income_focus": "monthly"
                }
            }
        ]
        
        result = prepare_training_batch(records, "test_batch")
        questions = json.loads(result["training_data"])
        
        # Top level category should take precedence
        self.assertEqual(questions[0]["category"], "portfolio-construction")
        
    def test_default_category_when_missing(self):
        """Test that default category is used when not present."""
        records = [
            {
                "query": "What's the yield on JEPI?",
                "context": "Simple query",
                "metrics": {"JEPI": {"yield": 8.5}},
                "payout_frequency": {"JEPI": "monthly"},
                "dividend_calendar_map": {"Jan": ["JEPI"]}
                # No category field at all
            }
        ]
        
        result = prepare_training_batch(records, "test_batch")
        questions = json.loads(result["training_data"])
        
        # Should use default category
        self.assertEqual(questions[0]["category"], "comparison")
        
    def test_preserves_complexity_from_top_level(self):
        """Test that complexity is preserved when present at top level."""
        records = [
            {
                "query": "Advanced tax optimization strategy",
                "context": "Complex scenario",
                "complexity": 5,  # Explicitly set
                "metrics": {"JEPI": {"yield": 8.5}},  # Would compute to 3
                "payout_frequency": {"JEPI": "monthly"},
                "dividend_calendar_map": {"Jan": ["JEPI"]},
                "labels": {"category": "tax-allocation"}
            }
        ]
        
        result = prepare_training_batch(records, "test_batch")
        questions = json.loads(result["training_data"])
        
        # Should preserve explicit complexity
        self.assertEqual(questions[0]["complexity"], 5)
        
    def test_preserves_complexity_from_labels(self):
        """Test that complexity is preserved from labels field."""
        records = [
            {
                "query": "Simple comparison",
                "context": "Basic query",
                "metrics": {"JEPI": {"yield": 8.5}},  # Would compute to 3
                "payout_frequency": {"JEPI": "monthly"},
                "dividend_calendar_map": {"Jan": ["JEPI"]},
                "labels": {
                    "category": "comparison",
                    "complexity": 1  # Explicitly set in labels
                }
            }
        ]
        
        result = prepare_training_batch(records, "test_batch")
        questions = json.loads(result["training_data"])
        
        # Should preserve complexity from labels
        self.assertEqual(questions[0]["complexity"], 1)
        
    def test_computes_complexity_when_missing(self):
        """Test that complexity is computed based on yields when not present."""
        test_cases = [
            # Low yield (< 3%) -> complexity 2
            {
                "query": "Low yield growth stock",
                "metrics": {"PG": {"yield": 2.5}},
                "expected_complexity": 2
            },
            # Medium yield (3-15%) -> complexity 3 (default)
            {
                "query": "Normal dividend stock",
                "metrics": {"SCHD": {"yield": 3.5}},
                "expected_complexity": 3
            },
            # High yield (15-30%) -> complexity 4
            {
                "query": "High yield fund",
                "metrics": {"RYLD": {"yield": 18.0}},
                "expected_complexity": 4
            },
            # Very high yield (>30%) -> complexity 5
            {
                "query": "Synthetic high yield",
                "metrics": {"SYNTHETIC": {"yield": 35.0}},
                "expected_complexity": 5
            }
        ]
        
        for test_case in test_cases:
            records = [{
                "query": test_case["query"],
                "context": "Test context",
                "metrics": test_case["metrics"],
                "payout_frequency": {"TEST": "monthly"},
                "dividend_calendar_map": {"Jan": ["TEST"]}
            }]
            
            result = prepare_training_batch(records, "test_batch")
            questions = json.loads(result["training_data"])
            
            self.assertEqual(
                questions[0]["complexity"], 
                test_case["expected_complexity"],
                f"Failed for query: {test_case['query']}"
            )
    
    def test_all_five_categories_preserved(self):
        """Test that all 5 balanced categories are preserved correctly."""
        categories = [
            "comparison",
            "portfolio-construction", 
            "payout_optimization",
            "risk-check",
            "tax-allocation"
        ]
        
        records = []
        for cat in categories:
            records.append({
                "query": f"Test query for {cat}",
                "context": f"Context for {cat}",
                "metrics": {"TEST": {"yield": 5.0}},
                "payout_frequency": {"TEST": "quarterly"},
                "dividend_calendar_map": {"Jan": ["TEST"]},
                "labels": {"category": cat}
            })
        
        result = prepare_training_batch(records, "test_batch")
        questions = json.loads(result["training_data"])
        
        # Verify all categories are preserved
        result_categories = [q["category"] for q in questions]
        self.assertEqual(result_categories, categories)
        
    def test_metadata_structure_preserved(self):
        """Test that all metadata fields are properly preserved in output."""
        record = {
            "query": "Full metadata test",
            "context": "Complete record",
            "metrics": {
                "JEPI": {"yield": 8.5, "dgr_5y": 0.0, "strategy": "option-overlay"},
                "SCHD": {"yield": 3.2, "dgr_5y": 8.5, "strategy": "organic"}
            },
            "payout_frequency": {"JEPI": "monthly", "SCHD": "quarterly"},
            "dividend_calendar_map": {
                "Jan": ["JEPI"],
                "Mar": ["JEPI", "SCHD"],
                "Jun": ["JEPI", "SCHD"]
            },
            "labels": {"category": "comparison"}
        }
        
        result = prepare_training_batch([record], "test_batch")
        questions = json.loads(result["training_data"])
        question = questions[0]
        
        # Verify structure
        self.assertEqual(question["query"], "Full metadata test")
        self.assertEqual(question["context"], "Complete record")
        self.assertEqual(question["category"], "comparison")
        self.assertIn("complexity", question)
        
        # Verify metadata
        self.assertIn("metadata", question)
        metadata = question["metadata"]
        self.assertEqual(metadata["metrics"], record["metrics"])
        self.assertEqual(metadata["payout_frequency"], record["payout_frequency"])
        self.assertEqual(metadata["dividend_calendar"], record["dividend_calendar_map"])


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)