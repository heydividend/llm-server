#!/usr/bin/env python3
"""
CLI Tool for Harvey Continuous Learning Pipeline

Manual triggers for:
- Feedback analysis with Gemini
- Fine-tuning dataset generation
- Learning insights and reports
- Dataset export for OpenAI fine-tuning

Usage:
    python scripts/generate_learning_data.py --analyze-feedback --days 30
    python scripts/generate_learning_data.py --generate-dataset --min-quality 0.7
    python scripts/generate_learning_data.py --show-insights
    python scripts/generate_learning_data.py --export-dataset output.jsonl --limit 1000
    python scripts/generate_learning_data.py --full-cycle --days 7
"""

import sys
import os
import argparse
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.continuous_learning_service import continuous_learning_service
from app.services.feedback_etl_service import feedback_etl_service
from app.services.gemini_feedback_analyzer import gemini_feedback_analyzer
from app.services.rlhf_dataset_builder import rlhf_dataset_builder


def analyze_feedback(args):
    """Analyze feedback with Gemini."""
    print("=" * 80)
    print("FEEDBACK ANALYSIS")
    print("=" * 80)
    
    # Get feedback statistics
    stats = feedback_etl_service.get_feedback_statistics(args.days)
    print(f"\nFeedback Statistics (last {args.days} days):")
    print(f"  Total feedback: {stats.get('total_feedback', 0)}")
    print(f"  Positive: {stats.get('positive', 0)}")
    print(f"  Negative: {stats.get('negative', 0)}")
    print(f"  Avg rating: {stats.get('avg_rating', 0):.2f}/5")
    print(f"  Already analyzed: {stats.get('already_analyzed', 0)}")
    print(f"  Pending analysis: {stats.get('pending_analysis', 0)}")
    
    if stats.get('pending_analysis', 0) == 0:
        print("\n✓ No pending feedback to analyze!")
        return
    
    # Extract feedback
    print(f"\nExtracting feedback (limit: {args.limit})...")
    feedback_items = feedback_etl_service.extract_feedback(
        days=args.days,
        exclude_analyzed=True,
        limit=args.limit
    )
    
    # Filter quality
    feedback_items = feedback_etl_service.filter_quality(
        feedback_items,
        min_query_length=10,
        min_response_length=20
    )
    
    print(f"  Extracted {len(feedback_items)} quality feedback items")
    
    if not feedback_items:
        print("\n✓ No quality feedback to analyze!")
        return
    
    # Confirm with user
    if not args.yes:
        estimated_cost = (len(feedback_items) * 500) / 1_000_000 * 0.10  # Rough estimate
        print(f"\nThis will analyze {len(feedback_items)} items using Gemini.")
        print(f"Estimated cost: ${estimated_cost:.4f}")
        confirm = input("Continue? (y/n): ")
        if confirm.lower() != 'y':
            print("Aborted.")
            return
    
    # Transform and analyze
    print("\nAnalyzing feedback with Gemini...")
    transformed = [
        feedback_etl_service.transform_for_analysis(item)
        for item in feedback_items
    ]
    
    analyses = gemini_feedback_analyzer.analyze_batch(
        transformed,
        max_items=args.limit,
        save_results=True
    )
    
    successful = [a for a in analyses if not a.get('error')]
    
    print(f"\n✓ Analysis complete!")
    print(f"  Analyzed: {len(successful)}/{len(analyses)}")
    print(f"  Gemini calls: {gemini_feedback_analyzer.total_api_calls}")
    print(f"  Tokens used: {gemini_feedback_analyzer.total_tokens}")
    
    actual_cost = (gemini_feedback_analyzer.total_tokens / 1_000_000) * 0.10
    print(f"  Actual cost: ${actual_cost:.4f}")
    
    # Show category breakdown
    categories = {}
    for analysis in successful:
        cat = analysis.get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\nCategory Breakdown:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat}: {count}")


def generate_dataset(args):
    """Generate fine-tuning datasets."""
    print("=" * 80)
    print("DATASET GENERATION")
    print("=" * 80)
    
    # Get current statistics
    stats = rlhf_dataset_builder.get_dataset_statistics()
    print(f"\nCurrent Dataset Statistics:")
    print(f"  Total samples: {stats.get('total', 0)}")
    print(f"  Ready for training: {stats.get('ready', 0)}")
    print(f"  Used in training: {stats.get('used', 0)}")
    
    if stats.get('by_type'):
        print("\nBy Type:")
        for sample_type, type_stats in stats['by_type'].items():
            print(f"  {sample_type}:")
            print(f"    Total: {type_stats['total']}")
            print(f"    Ready: {type_stats['ready']}")
            print(f"    Avg Quality: {type_stats['avg_quality']:.3f}")
    
    # Extract pairs and build datasets
    print(f"\nExtracting positive/negative pairs (days={args.days})...")
    pairs = feedback_etl_service.extract_positive_negative_pairs(
        days=args.days,
        same_query_type=True
    )
    
    print(f"  Found {len(pairs)} pairs")
    
    if not pairs:
        print("\n✓ No pairs available for dataset generation!")
        return
    
    # Build preference pairs
    print("\nBuilding preference pairs...")
    created = 0
    for pos, neg in pairs[:args.limit]:
        # Get analyses
        pos_analysis = continuous_learning_service._get_analysis(pos['feedback_id'])
        neg_analysis = continuous_learning_service._get_analysis(neg['feedback_id'])
        
        pair = rlhf_dataset_builder.build_preference_pair(
            pos, neg, pos_analysis, neg_analysis
        )
        
        if pair and pair['quality_score'] >= args.min_quality:
            if pair['ready_for_training']:
                rlhf_dataset_builder.save_sample(pair)
                created += 1
    
    print(f"  Created {created} preference pairs")
    
    # Build demonstrations
    print("\nBuilding demonstrations from positive feedback...")
    positive_items = feedback_etl_service.extract_feedback(
        days=args.days,
        min_rating=4,
        sentiment='positive',
        limit=args.limit,
        exclude_analyzed=False
    )
    
    demo_created = 0
    for item in positive_items:
        analysis = continuous_learning_service._get_analysis(item['feedback_id'])
        demo = rlhf_dataset_builder.build_demonstration(item, analysis)
        
        if demo and demo['quality_score'] >= args.min_quality:
            if demo['ready_for_training']:
                rlhf_dataset_builder.save_sample(demo)
                demo_created += 1
    
    print(f"  Created {demo_created} demonstrations")
    
    print(f"\n✓ Dataset generation complete!")
    print(f"  Total samples created: {created + demo_created}")


def export_dataset(args):
    """Export dataset to JSONL file."""
    print("=" * 80)
    print("DATASET EXPORT")
    print("=" * 80)
    
    output_file = args.output
    
    print(f"\nExporting to: {output_file}")
    print(f"  Sample type: {args.sample_type or 'all'}")
    print(f"  Min quality: {args.min_quality}")
    print(f"  Limit: {args.limit or 'unlimited'}")
    
    count = rlhf_dataset_builder.export_for_fine_tuning(
        output_file=output_file,
        sample_type=args.sample_type,
        min_quality=args.min_quality,
        limit=args.limit
    )
    
    if count > 0:
        print(f"\n✓ Exported {count} samples to {output_file}")
        
        # Show file info
        file_size = os.path.getsize(output_file)
        print(f"  File size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")
        
        # Show sample
        print("\nFirst sample (preview):")
        with open(output_file, 'r') as f:
            first_line = f.readline()
            sample = json.loads(first_line)
            print(json.dumps(sample, indent=2)[:500] + "...")
    else:
        print("\n✗ No samples exported (check filters)")


def show_insights(args):
    """Show learning insights and reports."""
    print("=" * 80)
    print("LEARNING INSIGHTS")
    print("=" * 80)
    
    # Generate comprehensive report
    report = continuous_learning_service.generate_learning_report(args.days)
    
    print(f"\nReport Period: Last {args.days} days")
    print(f"Generated: {report['generated_at']}")
    
    # Feedback overview
    feedback = report.get('feedback_overview', {})
    print("\n--- FEEDBACK OVERVIEW ---")
    print(f"Total feedback: {feedback.get('total_feedback', 0)}")
    print(f"  Positive: {feedback.get('positive_count', 0)} ({feedback.get('positive_count', 0) / max(feedback.get('total_feedback', 1), 1) * 100:.1f}%)")
    print(f"  Negative: {feedback.get('negative_count', 0)} ({feedback.get('negative_count', 0) / max(feedback.get('total_feedback', 1), 1) * 100:.1f}%)")
    print(f"  Avg rating: {feedback.get('avg_rating', 0):.2f}/5")
    print(f"  Pending analysis: {feedback.get('pending_analysis', 0)}")
    
    # Analysis summary
    analysis = report.get('analysis_summary', {})
    print("\n--- ANALYSIS SUMMARY ---")
    print(f"Total analyzed: {analysis.get('total_analyzed', 0)}")
    print(f"Avg training worthiness: {analysis.get('avg_training_worthiness', 0):.3f}")
    print(f"PII detected: {analysis.get('pii_detected_count', 0)}")
    print(f"Toxic content: {analysis.get('toxic_content_count', 0)}")
    
    if analysis.get('category_breakdown'):
        print("\nCategory Breakdown:")
        for cat, count in sorted(
            analysis['category_breakdown'].items(),
            key=lambda x: x[1],
            reverse=True
        ):
            print(f"  {cat}: {count}")
    
    # Dataset statistics
    dataset = report.get('dataset_statistics', {})
    print("\n--- DATASET STATISTICS ---")
    print(f"Total samples: {dataset.get('total', 0)}")
    print(f"Ready for training: {dataset.get('ready', 0)}")
    print(f"Used in training: {dataset.get('used', 0)}")
    
    if dataset.get('by_type'):
        print("\nBy Type:")
        for sample_type, stats in dataset['by_type'].items():
            print(f"  {sample_type}:")
            print(f"    Total: {stats['total']}")
            print(f"    Ready: {stats['ready']}")
            print(f"    Avg Quality: {stats['avg_quality']:.3f}")
    
    # Save report to file
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n✓ Full report saved to {args.output}")


def run_full_cycle(args):
    """Run complete learning cycle."""
    print("=" * 80)
    print("FULL LEARNING CYCLE")
    print("=" * 80)
    
    if not args.yes:
        print("\nThis will:")
        print("  1. Analyze unanalyzed feedback with Gemini")
        print("  2. Build RLHF training datasets")
        print("  3. Track learning metrics")
        print(f"\nPeriod: Last {args.days} days")
        print(f"Max feedback to analyze: {args.limit}")
        
        confirm = input("\nContinue? (y/n): ")
        if confirm.lower() != 'y':
            print("Aborted.")
            return
    
    # Run learning cycle
    results = continuous_learning_service.run_learning_cycle(
        days=args.days,
        max_feedback=args.limit,
        generate_datasets=True
    )
    
    # Display results
    print("\n" + "=" * 80)
    print("CYCLE RESULTS")
    print("=" * 80)
    
    print(f"\nStatus: {results.get('status')}")
    print(f"Duration: {results.get('duration_seconds', 0):.1f}s")
    print(f"Estimated cost: ${results.get('estimated_cost_usd', 0):.4f}")
    
    if results.get('phases'):
        phases = results['phases']
        
        if 'extraction' in phases:
            print(f"\nExtraction:")
            print(f"  Extracted: {phases['extraction'].get('total_extracted', 0)}")
        
        if 'analysis' in phases:
            print(f"\nAnalysis:")
            print(f"  Analyzed: {phases['analysis'].get('successful', 0)}/{phases['analysis'].get('total_analyzed', 0)}")
            print(f"  Gemini calls: {phases['analysis'].get('gemini_calls', 0)}")
            print(f"  Tokens: {phases['analysis'].get('tokens_used', 0)}")
        
        if 'dataset_building' in phases:
            print(f"\nDataset Building:")
            print(f"  Preference pairs: {phases['dataset_building'].get('preference_pairs', 0)}")
            print(f"  Demonstrations: {phases['dataset_building'].get('demonstrations', 0)}")
        
        if 'metrics' in phases:
            print(f"\nMetrics:")
            print(f"  Metric ID: {phases['metrics'].get('metric_id', 'N/A')}")
            print(f"  Quality trend: {phases['metrics'].get('quality_trend', 'unknown')}")
    
    # Save results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n✓ Results saved to {args.output}")


def main():
    parser = argparse.ArgumentParser(
        description="Harvey Continuous Learning Pipeline CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze feedback from last 30 days
  python scripts/generate_learning_data.py --analyze-feedback --days 30
  
  # Generate datasets with minimum quality 0.7
  python scripts/generate_learning_data.py --generate-dataset --min-quality 0.7
  
  # Export dataset to JSONL file
  python scripts/generate_learning_data.py --export-dataset output.jsonl --limit 1000
  
  # Show learning insights
  python scripts/generate_learning_data.py --show-insights --days 30
  
  # Run full learning cycle
  python scripts/generate_learning_data.py --full-cycle --days 7 --limit 100
        """
    )
    
    # Main actions
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('--analyze-feedback', action='store_true',
                             help='Analyze feedback with Gemini')
    action_group.add_argument('--generate-dataset', action='store_true',
                             help='Generate RLHF training datasets')
    action_group.add_argument('--export-dataset', metavar='FILE',
                             help='Export dataset to JSONL file')
    action_group.add_argument('--show-insights', action='store_true',
                             help='Show learning insights and reports')
    action_group.add_argument('--full-cycle', action='store_true',
                             help='Run complete learning cycle')
    
    # Common options
    parser.add_argument('--days', type=int, default=30,
                       help='Look back N days (default: 30)')
    parser.add_argument('--limit', type=int, default=100,
                       help='Maximum items to process (default: 100)')
    parser.add_argument('--min-quality', type=float, default=0.6,
                       help='Minimum quality score (default: 0.6)')
    parser.add_argument('--sample-type', choices=['preference_pair', 'demonstration', 'rejection'],
                       help='Filter by sample type (export only)')
    parser.add_argument('--output', metavar='FILE',
                       help='Output file for results/reports')
    parser.add_argument('--yes', '-y', action='store_true',
                       help='Skip confirmation prompts')
    
    args = parser.parse_args()
    
    try:
        if args.analyze_feedback:
            analyze_feedback(args)
        elif args.generate_dataset:
            generate_dataset(args)
        elif args.export_dataset:
            args.output = args.export_dataset
            export_dataset(args)
        elif args.show_insights:
            show_insights(args)
        elif args.full_cycle:
            run_full_cycle(args)
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
