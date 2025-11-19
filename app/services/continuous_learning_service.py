"""
Continuous Learning Orchestrator for Harvey

Coordinates the entire continuous learning pipeline:
1. Extract feedback (ETL)
2. Analyze with Gemini
3. Build RLHF datasets
4. Track metrics
5. Generate reports

Features:
- Schedule automatic feedback analysis
- Aggregate feedback across time periods
- Generate fine-tuning datasets
- Track learning metrics and trends
- Cost controls and rate limiting
"""

import logging
import uuid
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import text
from app.core.database import engine
from app.services.feedback_etl_service import feedback_etl_service
from app.services.gemini_feedback_analyzer import gemini_feedback_analyzer
from app.services.rlhf_dataset_builder import rlhf_dataset_builder

logger = logging.getLogger("continuous_learning")


class ContinuousLearningService:
    """
    Orchestrates the continuous learning pipeline.
    
    Workflow:
    1. Extract unanalyzed feedback from database
    2. Analyze feedback with Gemini (categorize, extract insights)
    3. Build training samples from analyzed feedback
    4. Track metrics and generate reports
    5. Export datasets for fine-tuning
    """
    
    def __init__(self, max_gemini_calls_per_run: int = 100):
        """
        Initialize continuous learning service.
        
        Args:
            max_gemini_calls_per_run: Cost control - max Gemini API calls per run
        """
        self.etl = feedback_etl_service
        self.analyzer = gemini_feedback_analyzer
        self.builder = rlhf_dataset_builder
        self.logger = logger
        self.max_gemini_calls = max_gemini_calls_per_run
    
    def run_learning_cycle(
        self,
        days: int = 7,
        max_feedback: Optional[int] = None,
        generate_datasets: bool = True
    ) -> Dict[str, Any]:
        """
        Run a complete learning cycle.
        
        Args:
            days: Analyze feedback from last N days
            max_feedback: Maximum feedback items to process (cost control)
            generate_datasets: Build training datasets after analysis
        
        Returns:
            Results summary
        """
        self.logger.info("=" * 80)
        self.logger.info(f"CONTINUOUS LEARNING CYCLE STARTED (days={days})")
        self.logger.info("=" * 80)
        
        start_time = datetime.now()
        results = {
            'started_at': start_time.isoformat(),
            'days': days,
            'phases': {}
        }
        
        try:
            # Phase 1: Extract feedback
            self.logger.info("\n[Phase 1/4] Extracting feedback from database...")
            feedback_stats = self.etl.get_feedback_statistics(days)
            self.logger.info(f"  Total feedback: {feedback_stats.get('total_feedback', 0)}")
            self.logger.info(f"  Pending analysis: {feedback_stats.get('pending_analysis', 0)}")
            
            # Extract unanalyzed feedback
            max_to_extract = max_feedback or self.max_gemini_calls
            feedback_items = self.etl.extract_feedback(
                days=days,
                exclude_analyzed=True,
                limit=max_to_extract
            )
            
            # Filter quality
            feedback_items = self.etl.filter_quality(
                feedback_items,
                min_query_length=10,
                min_response_length=20
            )
            
            results['phases']['extraction'] = {
                'total_extracted': len(feedback_items),
                'pending_before': feedback_stats.get('pending_analysis', 0)
            }
            
            if not feedback_items:
                self.logger.info("  No new feedback to analyze. Exiting.")
                results['status'] = 'no_new_feedback'
                return results
            
            # Phase 2: Analyze with Gemini
            self.logger.info(f"\n[Phase 2/4] Analyzing {len(feedback_items)} feedback items with Gemini...")
            transformed_feedback = [
                self.etl.transform_for_analysis(item)
                for item in feedback_items
            ]
            
            analyses = self.analyzer.analyze_batch(
                transformed_feedback,
                max_items=self.max_gemini_calls,
                save_results=True
            )
            
            successful_analyses = [a for a in analyses if not a.get('error')]
            
            results['phases']['analysis'] = {
                'total_analyzed': len(analyses),
                'successful': len(successful_analyses),
                'failed': len(analyses) - len(successful_analyses),
                'gemini_calls': self.analyzer.total_api_calls,
                'tokens_used': self.analyzer.total_tokens
            }
            
            self.logger.info(f"  Analyzed: {len(successful_analyses)}/{len(analyses)}")
            self.logger.info(f"  Gemini calls: {self.analyzer.total_api_calls}")
            self.logger.info(f"  Tokens used: {self.analyzer.total_tokens}")
            
            # Phase 3: Build training datasets
            if generate_datasets:
                self.logger.info("\n[Phase 3/4] Building RLHF training datasets...")
                datasets_generated = self._build_training_datasets(days)
                results['phases']['dataset_building'] = datasets_generated
            else:
                self.logger.info("\n[Phase 3/4] Skipping dataset generation (disabled)")
                results['phases']['dataset_building'] = {'skipped': True}
            
            # Phase 4: Track metrics
            self.logger.info("\n[Phase 4/4] Tracking learning metrics...")
            metrics = self._track_learning_metrics(
                period_type='weekly',
                days=days
            )
            results['phases']['metrics'] = metrics
            
            # Calculate estimated cost (Gemini pricing)
            # Assuming ~$0.10 per 1M tokens for Gemini 2.0 Flash
            estimated_cost = (self.analyzer.total_tokens / 1_000_000) * 0.10
            results['estimated_cost_usd'] = round(estimated_cost, 4)
            
            # Final status
            duration = (datetime.now() - start_time).total_seconds()
            results['completed_at'] = datetime.now().isoformat()
            results['duration_seconds'] = round(duration, 2)
            results['status'] = 'success'
            
            self.logger.info("\n" + "=" * 80)
            self.logger.info(f"CONTINUOUS LEARNING CYCLE COMPLETED ({duration:.1f}s)")
            self.logger.info(f"  Analyzed: {len(successful_analyses)} feedback items")
            self.logger.info(f"  Estimated cost: ${estimated_cost:.4f}")
            self.logger.info("=" * 80)
            
            return results
        
        except Exception as e:
            self.logger.error(f"Learning cycle failed: {e}")
            results['status'] = 'error'
            results['error'] = str(e)
            return results
    
    def _build_training_datasets(self, days: int) -> Dict[str, Any]:
        """Build training datasets from analyzed feedback."""
        
        # Extract positive/negative pairs
        pairs = self.etl.extract_positive_negative_pairs(
            days=days,
            same_query_type=True,
            min_rating_diff=2
        )
        
        self.logger.info(f"  Found {len(pairs)} positive/negative pairs")
        
        # Build preference pairs
        preference_pairs_created = 0
        for pos, neg in pairs:
            # Get analyses if available
            pos_analysis = self._get_analysis(pos['feedback_id'])
            neg_analysis = self._get_analysis(neg['feedback_id'])
            
            pair = self.builder.build_preference_pair(
                pos, neg, pos_analysis, neg_analysis
            )
            
            if pair and pair['ready_for_training']:
                self.builder.save_sample(pair)
                preference_pairs_created += 1
        
        # Build demonstrations from high-quality positive feedback
        positive_items = self.etl.extract_feedback(
            days=days,
            min_rating=4,
            sentiment='positive',
            limit=50,
            exclude_analyzed=False
        )
        
        demonstrations_created = 0
        for item in positive_items:
            analysis = self._get_analysis(item['feedback_id'])
            demo = self.builder.build_demonstration(item, analysis)
            
            if demo and demo['ready_for_training']:
                self.builder.save_sample(demo)
                demonstrations_created += 1
        
        self.logger.info(f"  Created {preference_pairs_created} preference pairs")
        self.logger.info(f"  Created {demonstrations_created} demonstrations")
        
        return {
            'preference_pairs': preference_pairs_created,
            'demonstrations': demonstrations_created,
            'total_samples': preference_pairs_created + demonstrations_created
        }
    
    def _get_analysis(self, feedback_id: str) -> Optional[Dict[str, Any]]:
        """Get Gemini analysis for feedback."""
        try:
            query = """
                SELECT category, sentiment_reason, improvement_suggestions,
                       response_strengths, response_weaknesses,
                       primary_topic, subtopics, training_worthiness
                FROM feedback_labels
                WHERE feedback_id = :feedback_id
            """
            
            with engine.connect() as conn:
                result = conn.execute(
                    text(query),
                    {"feedback_id": feedback_id}
                ).first()
                
                if result:
                    return {
                        'category': result[0],
                        'sentiment_reason': result[1],
                        'improvement_suggestions': result[2],
                        'response_strengths': json.loads(result[3] or '[]'),
                        'response_weaknesses': json.loads(result[4] or '[]'),
                        'primary_topic': result[5],
                        'subtopics': json.loads(result[6] or '[]'),
                        'training_worthiness': float(result[7] or 0)
                    }
            
            return None
        
        except Exception as e:
            self.logger.warning(f"Failed to get analysis for {feedback_id}: {e}")
            return None
    
    def _track_learning_metrics(
        self,
        period_type: str = 'weekly',
        days: int = 7
    ) -> Dict[str, Any]:
        """Track learning metrics for the period."""
        try:
            period_start = datetime.now() - timedelta(days=days)
            period_end = datetime.now()
            
            # Feedback metrics
            feedback_stats = self.etl.get_feedback_statistics(days)
            
            # Analysis metrics
            analysis_stats = self.analyzer.get_analysis_summary(days)
            
            # Dataset metrics
            dataset_stats = self.builder.get_dataset_statistics()
            
            # Category breakdown
            category_breakdown = analysis_stats.get('category_breakdown', {})
            
            # Calculate trends
            quality_trend = self._calculate_quality_trend(days)
            
            # Calculate estimated cost
            tokens_used = analysis_stats.get('total_tokens_used', 0)
            estimated_cost = (tokens_used / 1_000_000) * 0.10
            
            # Save to database
            metric_id = f"metric_{uuid.uuid4().hex[:12]}"
            
            with engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO learning_metrics (
                            metric_id, period_start, period_end, period_type,
                            total_feedback, positive_feedback, negative_feedback,
                            avg_rating, feedback_by_category,
                            samples_generated, high_quality_samples,
                            avg_quality_score, quality_trend,
                            gemini_api_calls, gemini_tokens_used, estimated_cost_usd,
                            created_at
                        ) VALUES (
                            :metric_id, :period_start, :period_end, :period_type,
                            :total_feedback, :positive_feedback, :negative_feedback,
                            :avg_rating, :feedback_by_category,
                            :samples_generated, :high_quality_samples,
                            :avg_quality_score, :quality_trend,
                            :gemini_api_calls, :gemini_tokens_used, :estimated_cost_usd,
                            :created_at
                        )
                    """),
                    {
                        'metric_id': metric_id,
                        'period_start': period_start,
                        'period_end': period_end,
                        'period_type': period_type,
                        'total_feedback': feedback_stats.get('total_feedback', 0),
                        'positive_feedback': feedback_stats.get('positive_count', 0),
                        'negative_feedback': feedback_stats.get('negative_count', 0),
                        'avg_rating': feedback_stats.get('avg_rating', 0),
                        'feedback_by_category': json.dumps(category_breakdown),
                        'samples_generated': dataset_stats.get('total', 0),
                        'high_quality_samples': dataset_stats.get('ready', 0),
                        'avg_quality_score': analysis_stats.get('avg_training_worthiness', 0),
                        'quality_trend': quality_trend,
                        'gemini_api_calls': self.analyzer.total_api_calls,
                        'gemini_tokens_used': tokens_used,
                        'estimated_cost_usd': estimated_cost,
                        'created_at': datetime.now()
                    }
                )
            
            self.logger.info(f"  Saved metrics as {metric_id}")
            
            return {
                'metric_id': metric_id,
                'feedback_count': feedback_stats.get('total_feedback', 0),
                'samples_generated': dataset_stats.get('total', 0),
                'quality_trend': quality_trend,
                'estimated_cost': estimated_cost
            }
        
        except Exception as e:
            self.logger.error(f"Failed to track metrics: {e}")
            return {}
    
    def _calculate_quality_trend(self, days: int) -> str:
        """Calculate quality trend (improving, stable, declining)."""
        try:
            # Compare current period vs previous period
            query = """
                SELECT 
                    AVG(CASE 
                        WHEN created_at >= DATEADD(DAY, -:half_days, GETDATE()) 
                        THEN training_worthiness 
                    END) as recent_quality,
                    AVG(CASE 
                        WHEN created_at < DATEADD(DAY, -:half_days, GETDATE())
                        AND created_at >= DATEADD(DAY, -:days, GETDATE())
                        THEN training_worthiness 
                    END) as previous_quality
                FROM feedback_labels
                WHERE created_at >= DATEADD(DAY, -:days, GETDATE())
            """
            
            with engine.connect() as conn:
                result = conn.execute(
                    text(query),
                    {"days": days, "half_days": days // 2}
                ).first()
                
                if result and result[0] and result[1]:
                    recent = float(result[0])
                    previous = float(result[1])
                    diff = recent - previous
                    
                    if diff > 0.05:
                        return 'improving'
                    elif diff < -0.05:
                        return 'declining'
                    else:
                        return 'stable'
            
            return 'stable'
        
        except Exception:
            return 'unknown'
    
    def generate_learning_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive learning report."""
        
        report = {
            'period_days': days,
            'generated_at': datetime.now().isoformat(),
            'feedback_overview': self.etl.get_feedback_statistics(days),
            'analysis_summary': self.analyzer.get_analysis_summary(days),
            'dataset_statistics': self.builder.get_dataset_statistics()
        }
        
        return report


# Global instance
continuous_learning_service = ContinuousLearningService()
