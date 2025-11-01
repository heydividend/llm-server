"""
Feedback Analytics Service

Analyzes user feedback to identify patterns, improve responses,
and generate insights for continuous learning.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import text
from app.core.database import engine

logger = logging.getLogger("feedback_analytics")


class FeedbackAnalytics:
    """
    Analytics service for feedback data analysis and insights.
    
    Features:
    - Identify top-performing query types
    - Detect low-performing responses
    - Track improvement over time
    - Generate recommendations for enhancement
    """
    
    def get_dashboard_metrics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get comprehensive dashboard metrics for feedback analysis.
        
        Returns:
            - Overall stats (total feedback, avg rating, success rate)
            - Top performing query types
            - Bottom performing query types
            - Trending patterns
            - Training data readiness
        """
        try:
            with engine.begin() as conn:
                # Overall stats
                overall = conn.execute(
                    text("""
                        SELECT 
                            COUNT(*) as total_feedback,
                            AVG(rating) as avg_rating,
                            SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) as positive_count,
                            SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) as negative_count,
                            COUNT(DISTINCT session_id) as unique_sessions,
                            COUNT(DISTINCT response_id) as unique_responses
                        FROM conversation_feedback
                        WHERE created_at >= DATEADD(DAY, -:days, GETDATE())
                    """),
                    {"days": days}
                ).first()
                
                if overall:
                    total = overall[0] or 0
                    overall_stats = {
                        "total_feedback": total,
                        "avg_rating": round(float(overall[1] or 0), 2),
                        "positive_count": overall[2] or 0,
                        "negative_count": overall[3] or 0,
                        "success_rate": round(100.0 * (overall[2] or 0) / total, 2) if total > 0 else 0,
                        "unique_sessions": overall[4] or 0,
                        "unique_responses": overall[5] or 0
                    }
                else:
                    overall_stats = {
                        "total_feedback": 0,
                        "avg_rating": 0.0,
                        "positive_count": 0,
                        "negative_count": 0,
                        "success_rate": 0.0,
                        "unique_sessions": 0,
                        "unique_responses": 0
                    }
                
                # Top performing query types
                top_performers = conn.execute(
                    text("""
                        SELECT TOP 10
                            query_type,
                            action_taken,
                            COUNT(*) as response_count,
                            AVG(rating) as avg_rating,
                            ROUND(100.0 * SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
                        FROM conversation_feedback
                        WHERE created_at >= DATEADD(DAY, -:days, GETDATE())
                          AND query_type IS NOT NULL
                        GROUP BY query_type, action_taken
                        HAVING COUNT(*) >= 3
                        ORDER BY avg_rating DESC, success_rate DESC
                    """),
                    {"days": days}
                ).fetchall()
                
                top_list = []
                for row in top_performers:
                    top_list.append({
                        "query_type": row[0],
                        "action_taken": row[1],
                        "response_count": row[2],
                        "avg_rating": round(float(row[3] or 0), 2),
                        "success_rate": float(row[4] or 0)
                    })
                
                # Bottom performing query types
                bottom_performers = conn.execute(
                    text("""
                        SELECT TOP 10
                            query_type,
                            action_taken,
                            COUNT(*) as response_count,
                            AVG(rating) as avg_rating,
                            ROUND(100.0 * SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) / COUNT(*), 2) as failure_rate
                        FROM conversation_feedback
                        WHERE created_at >= DATEADD(DAY, -:days, GETDATE())
                          AND query_type IS NOT NULL
                        GROUP BY query_type, action_taken
                        HAVING COUNT(*) >= 3
                        ORDER BY avg_rating ASC, failure_rate DESC
                    """),
                    {"days": days}
                ).fetchall()
                
                bottom_list = []
                for row in bottom_performers:
                    bottom_list.append({
                        "query_type": row[0],
                        "action_taken": row[1],
                        "response_count": row[2],
                        "avg_rating": round(float(row[3] or 0), 2),
                        "failure_rate": float(row[4] or 0)
                    })
                
                # Training data stats
                training_stats = conn.execute(
                    text("""
                        SELECT 
                            COUNT(*) as total_training_examples,
                            SUM(CASE WHEN is_high_quality = TRUE THEN 1 ELSE 0 END) as high_quality_count,
                            SUM(CASE WHEN used_in_training = FALSE THEN 1 ELSE 0 END) as unused_count,
                            AVG(quality_score) as avg_quality_score
                        FROM gpt_training_data
                    """)
                ).first()
                
                if training_stats:
                    training_data = {
                        "total_examples": training_stats[0] or 0,
                        "high_quality_count": training_stats[1] or 0,
                        "unused_count": training_stats[2] or 0,
                        "avg_quality_score": round(float(training_stats[3] or 0), 2),
                        "ready_for_finetuning": (training_stats[2] or 0) >= 100
                    }
                else:
                    training_data = {
                        "total_examples": 0,
                        "high_quality_count": 0,
                        "unused_count": 0,
                        "avg_quality_score": 0.0,
                        "ready_for_finetuning": False
                    }
                
                return {
                    "success": True,
                    "period_days": days,
                    "overall": overall_stats,
                    "top_performers": top_list,
                    "bottom_performers": bottom_list,
                    "training_data": training_data,
                    "generated_at": datetime.now().isoformat()
                }
        
        except Exception as e:
            logger.error(f"Failed to get dashboard metrics: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_improvement_suggestions(self) -> List[Dict[str, Any]]:
        """
        Generate actionable suggestions for improving Harvey's responses.
        
        Returns:
            List of suggestions with priority, affected query types, and recommendations
        """
        suggestions = []
        
        try:
            with engine.begin() as conn:
                # Find query types with low ratings
                low_rated = conn.execute(
                    text("""
                        SELECT 
                            query_type,
                            action_taken,
                            COUNT(*) as count,
                            AVG(rating) as avg_rating
                        FROM conversation_feedback
                        WHERE rating IS NOT NULL
                          AND created_at >= DATEADD(DAY, -30, GETDATE())
                        GROUP BY query_type, action_taken
                        HAVING AVG(rating) < 3.0 AND COUNT(*) >= 5
                        ORDER BY avg_rating ASC
                    """)
                ).fetchall()
                
                for row in low_rated:
                    suggestions.append({
                        "priority": "high",
                        "category": "low_rating",
                        "query_type": row[0],
                        "action_taken": row[1],
                        "affected_responses": row[2],
                        "avg_rating": round(float(row[3]), 2),
                        "recommendation": f"Investigate and improve {row[0]} responses using {row[1]}. Consider adding more context, ML predictions, or formatting enhancements.",
                        "potential_actions": [
                            "Review recent examples of this query type",
                            "Add ML predictions if not already included",
                            "Enhance response formatting with tables/charts",
                            "Add follow-up suggestions or related insights"
                        ]
                    })
                
                # Find query types with high negative feedback
                high_negative = conn.execute(
                    text("""
                        SELECT 
                            query_type,
                            COUNT(*) as total,
                            SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) as negative_count
                        FROM conversation_feedback
                        WHERE created_at >= DATEADD(DAY, -30, GETDATE())
                          AND query_type IS NOT NULL
                        GROUP BY query_type
                        HAVING SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) >= 3
                           AND ROUND(100.0 * SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) / COUNT(*), 2) > 30
                        ORDER BY negative_count DESC
                    """)
                ).fetchall()
                
                for row in high_negative:
                    suggestions.append({
                        "priority": "medium",
                        "category": "high_negative_feedback",
                        "query_type": row[0],
                        "total_responses": row[1],
                        "negative_count": row[2],
                        "negative_rate": round(100.0 * row[2] / row[1], 2),
                        "recommendation": f"Address recurring issues with {row[0]} queries. Review user comments for specific pain points.",
                        "potential_actions": [
                            "Analyze feedback comments for common complaints",
                            "Test responses with different approaches",
                            "Add self-healing/fallback mechanisms",
                            "Improve error messages if queries are failing"
                        ]
                    })
                
                # Check if we have enough training data
                training_check = conn.execute(
                    text("""
                        SELECT COUNT(*) 
                        FROM gpt_training_data 
                        WHERE is_high_quality = 1
                          AND used_in_training = 0
                    """)
                ).scalar()
                
                if training_check and training_check >= 1000:
                    suggestions.append({
                        "priority": "high",
                        "category": "training_ready",
                        "affected_responses": training_check,
                        "recommendation": f"You have {training_check} high-quality training examples ready! Consider fine-tuning GPT-4o to improve overall performance.",
                        "potential_actions": [
                            "Export training data via /v1/feedback/training-data/export",
                            "Prepare JSONL file for OpenAI fine-tuning",
                            "Submit fine-tuning job to OpenAI",
                            "Test fine-tuned model vs base model"
                        ]
                    })
                elif training_check and training_check >= 100:
                    suggestions.append({
                        "priority": "low",
                        "category": "training_progress",
                        "affected_responses": training_check,
                        "recommendation": f"Good progress! {training_check} high-quality examples collected. Target: 1000+ for effective fine-tuning.",
                        "potential_actions": [
                            "Continue collecting feedback",
                            "Encourage users to rate responses",
                            "Review and validate training examples"
                        ]
                    })
                
                return suggestions
        
        except Exception as e:
            logger.error(f"Failed to generate improvement suggestions: {e}")
            return [{
                "priority": "error",
                "category": "analytics_error",
                "error": str(e),
                "recommendation": "Fix analytics database connection"
            }]
    
    def get_feedback_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Get feedback trends over time to track improvement.
        
        Returns:
            Daily stats showing rating and sentiment trends
        """
        try:
            with engine.begin() as conn:
                daily_trends = conn.execute(
                    text("""
                        SELECT 
                            CAST(created_at AS DATE) as date,
                            COUNT(*) as feedback_count,
                            AVG(rating) as avg_rating,
                            SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) as positive,
                            SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) as negative
                        FROM conversation_feedback
                        WHERE created_at >= DATEADD(DAY, -:days, GETDATE())
                        GROUP BY CAST(created_at AS DATE)
                        ORDER BY date DESC
                    """),
                    {"days": days}
                ).fetchall()
                
                trends = []
                for row in daily_trends:
                    trends.append({
                        "date": str(row[0]),
                        "feedback_count": row[1],
                        "avg_rating": round(float(row[2] or 0), 2),
                        "positive": row[3],
                        "negative": row[4],
                        "success_rate": round(100.0 * (row[3] or 0) / (row[1] or 1), 2)
                    })
                
                return {
                    "success": True,
                    "period_days": days,
                    "daily_trends": trends
                }
        
        except Exception as e:
            logger.error(f"Failed to get feedback trends: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Global instance
feedback_analytics = FeedbackAnalytics()
