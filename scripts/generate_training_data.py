#!/usr/bin/env python3
"""
CLI Tool for Generating Training Data using Gemini 2.5 Pro

Usage:
    # Generate 10 dividend analysis questions
    python scripts/generate_training_data.py --category dividend_analysis --count 10
    
    # Generate 50 questions for all categories
    python scripts/generate_training_data.py --count 50 --all-categories
    
    # Generate and save to database
    python scripts/generate_training_data.py --category income_strategies --count 25 --to-database
    
    # Generate without answers
    python scripts/generate_training_data.py --category etf_funds --count 20 --no-answers
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv()

from app.services.gemini_training_generator import get_training_generator
from app.services.training_ingestion_service import training_ingestion


def print_banner():
    """Print CLI banner."""
    print("=" * 70)
    print("Harvey AI - Gemini Training Data Generator")
    print("=" * 70)
    print()


def print_progress(current: int, total: int, category: str):
    """Print progress bar."""
    percent = int((current / total) * 100)
    bar_length = 40
    filled = int((bar_length * current) / total)
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"\r{category}: [{bar}] {percent}% ({current}/{total})", end="", flush=True)


def save_to_json(data: Dict[str, Any], output_path: str) -> str:
    """Save generated data to JSON file."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return str(output_file)


def format_output(questions: List[Dict[str, Any]], format_type: str = "json") -> str:
    """Format questions for output."""
    if format_type == "json":
        return json.dumps(questions, indent=2, ensure_ascii=False)
    
    elif format_type == "jsonl":
        lines = [json.dumps(q, ensure_ascii=False) for q in questions]
        return "\n".join(lines)
    
    elif format_type == "text":
        output = []
        for i, q in enumerate(questions, 1):
            output.append(f"\n{'='*60}")
            output.append(f"Question {i} ({q.get('category', 'unknown')})")
            output.append('='*60)
            output.append(f"Q: {q['question']}")
            if 'answer' in q and q['answer']:
                output.append(f"\nA: {q['answer']}")
        return "\n".join(output)
    
    else:
        return json.dumps(questions, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(
        description="Generate training questions using Gemini 2.5 Pro",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--category',
        type=str,
        help='Category to generate questions for (e.g., dividend_analysis, income_strategies)',
        choices=[
            'dividend_analysis',
            'income_strategies', 
            'technical_timing',
            'etf_funds',
            'tax_optimization',
            'risk_management',
            'market_analysis',
            'portfolio_construction',
            'dividend_sustainability',
            'global_dividend_markets'
        ]
    )
    
    parser.add_argument(
        '--count',
        type=int,
        default=10,
        help='Number of questions to generate per category (default: 10)'
    )
    
    parser.add_argument(
        '--all-categories',
        action='store_true',
        help='Generate questions for all categories'
    )
    
    parser.add_argument(
        '--with-answers',
        action='store_true',
        default=True,
        help='Generate answers using Gemini (default: True)'
    )
    
    parser.add_argument(
        '--no-answers',
        action='store_true',
        help='Skip answer generation (questions only)'
    )
    
    parser.add_argument(
        '--output-format',
        type=str,
        default='json',
        choices=['json', 'jsonl', 'text'],
        help='Output format (default: json)'
    )
    
    parser.add_argument(
        '--output-file',
        type=str,
        help='Output file path (default: auto-generated in attached_assets/)'
    )
    
    parser.add_argument(
        '--to-database',
        action='store_true',
        help='Ingest generated questions into training database'
    )
    
    parser.add_argument(
        '--temperature',
        type=float,
        default=0.8,
        help='Sampling temperature for generation (0.0-1.0, default: 0.8)'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        default=True,
        help='Validate dividend relevance (default: True)'
    )
    
    parser.add_argument(
        '--no-validate',
        action='store_true',
        help='Skip validation of dividend relevance'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show generation statistics'
    )
    
    args = parser.parse_args()
    
    # Validation
    if not args.all_categories and not args.category:
        parser.error("Must specify either --category or --all-categories")
    
    # Determine answer generation
    with_answers = args.with_answers and not args.no_answers
    validate = args.validate and not args.no_validate
    
    print_banner()
    
    # Initialize generator
    print("Initializing Gemini Training Generator...")
    try:
        generator = get_training_generator()
        print("✓ Generator initialized successfully")
        print()
    except Exception as e:
        print(f"✗ Failed to initialize generator: {e}")
        sys.exit(1)
    
    # Generate questions
    all_questions = []
    
    if args.all_categories:
        categories = [
            'dividend_analysis', 'income_strategies', 'technical_timing',
            'etf_funds', 'tax_optimization', 'risk_management',
            'market_analysis', 'portfolio_construction', 
            'dividend_sustainability', 'global_dividend_markets'
        ]
        
        print(f"Generating {args.count} questions for {len(categories)} categories...")
        print()
        
        for i, category in enumerate(categories, 1):
            print(f"[{i}/{len(categories)}] Generating questions for: {category}")
            
            try:
                questions = generator.generate_questions(
                    category=category,
                    count=args.count,
                    with_answers=with_answers,
                    temperature=args.temperature,
                    validate=validate
                )
                
                all_questions.extend(questions)
                print(f" ✓ Generated {len(questions)} questions")
                
            except Exception as e:
                print(f" ✗ Failed: {e}")
        
        print()
    
    else:
        # Single category
        category = args.category
        print(f"Generating {args.count} questions for category: {category}")
        print()
        
        try:
            questions = generator.generate_questions(
                category=category,
                count=args.count,
                with_answers=with_answers,
                temperature=args.temperature,
                validate=validate
            )
            
            all_questions = questions
            print(f"✓ Generated {len(questions)} questions")
            print()
            
        except Exception as e:
            print(f"✗ Failed to generate questions: {e}")
            sys.exit(1)
    
    if not all_questions:
        print("No questions generated. Exiting.")
        sys.exit(1)
    
    # Show statistics
    if args.stats:
        print("\nGeneration Statistics:")
        print("-" * 60)
        stats = generator.get_statistics()
        print(f"  Total generated:      {stats['total_generated']}")
        print(f"  Total validated:      {stats['total_validated']}")
        print(f"  Total rejected:       {stats['total_rejected']}")
        print(f"  Duplicates filtered:  {stats['duplicates_filtered']}")
        print("\nBy category:")
        for cat, count in stats['by_category'].items():
            print(f"  {cat:25} {count:4} questions")
        print()
    
    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if args.output_file:
        output_path = args.output_file
    else:
        filename = f"gemini_training_data_{timestamp}.{args.output_format}"
        output_path = os.path.join("attached_assets", filename)
    
    print(f"Saving to file: {output_path}")
    
    try:
        data = {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "total_questions": len(all_questions),
                "categories": list(set(q['category'] for q in all_questions)),
                "with_answers": with_answers,
                "temperature": args.temperature,
                "validated": validate
            },
            "questions": all_questions
        }
        
        formatted_output = format_output(all_questions, args.output_format)
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            if args.output_format == 'text':
                f.write(formatted_output)
            else:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Saved {len(all_questions)} questions to {output_path}")
        print()
        
    except Exception as e:
        print(f"✗ Failed to save file: {e}")
    
    # Ingest to database
    if args.to_database:
        print("Ingesting questions into training database...")
        
        try:
            result = training_ingestion.ingest_gemini_questions(
                questions=all_questions,
                prevent_duplicates=True
            )
            
            if result.get('success'):
                print(f"✓ Ingested {result['ingested']} questions")
                print(f"  Duplicates skipped: {result['duplicates']}")
                print(f"  Errors: {result['errors']}")
            else:
                print(f"✗ Ingestion failed: {result.get('error', 'Unknown error')}")
            
            print()
            
        except Exception as e:
            print(f"✗ Failed to ingest to database: {e}")
    
    # Summary
    print("=" * 70)
    print("Generation Complete!")
    print("=" * 70)
    print(f"Total questions generated: {len(all_questions)}")
    print(f"Output saved to: {output_path}")
    
    if args.to_database:
        print(f"Database ingestion: {'✓ Complete' if result.get('success') else '✗ Failed'}")
    
    print()
    
    # Show sample questions
    if all_questions and not args.all_categories:
        print("Sample Questions:")
        print("-" * 70)
        for i, q in enumerate(all_questions[:3], 1):
            print(f"\n{i}. {q['question']}")
            if with_answers and 'answer' in q:
                answer_preview = q['answer'][:200] + "..." if len(q['answer']) > 200 else q['answer']
                print(f"   A: {answer_preview}")
        print()


if __name__ == "__main__":
    main()
