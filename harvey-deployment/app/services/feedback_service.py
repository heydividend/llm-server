"""
Feedback Collection & Learning Service

Handles user feedback on Harvey's responses and builds training data
for continuous improvement and GPT-4o fine-tuning.
"""

import uuid
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy import text
from app.core.database import engine

logger = logging.getLogger("feedback_service")


class FeedbackService:
    """
    Service for collecting and analyzing user feedback on Harvey's responses.
    
    Features:
    - Record thumbs up/down feedback
    - Track 1-5 star ratings
    - Capture user comments
    - Analyze response patterns
    - Generate training data for GPT-4o fine-tuning
    """
    
    def __init__(self):
        self.ensure_tables_exist()
    
    def ensure_tables_exist(self):
        """Ensure feedback tables exist (run schema if needed)"""
        try:
            with engine.begin() as conn:
                conn.execute(text("SELECT TOP 1 1 FROM conversation_feedback"))
            logger.info("Feedback tables verified")
        except Exception as e:
            logger.warning(f"Feedback tables may not exist: {e}")
            logger.info("Run feedback_schema.sql to create tables")
    
    def record_feedback(
        self,
        response_id: str,
        sentiment: str,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        rating: Optional[int] = None,
        comment: Optional[str] = None,
        tags: Optional[List[str]] = None,
        user_query: Optional[str] = None,
        harvey_response: Optional[str] = None,
        response_metadata: Optional[Dict[str, Any]] = None,
        query_type: Optional[str] = None,
        action_taken: Optional[str] = None,
        user_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record user feedback on a Harvey response.
        
        Args:
            response_id: Unique ID of the response being rated
            sentiment: 'positive', 'negative', or 'neutral'
            request_id: Original request ID
            session_id: User session ID
            conversation_id: Conversation thread ID
            rating: 1-5 star rating (optional)
            comment: User's text comment (optional)
            tags: List of feedback tags (e.g., ['accurate', 'helpful'])
            user_query: Original user question
            harvey_response: Harvey's response text
            response_metadata: Dict with response context (tickers, ML predictions, etc.)
            query_type: Type of query (dividend_history, portfolio_analysis, etc.)
            action_taken: Action Harvey took (sql_query, web_search, ml_prediction)
            user_ip: User's IP address
            user_agent: User's browser/client info
        
        Returns:
            Dict with feedback_id and success status
        """
        feedback_id = f"fb_{uuid.uuid4().hex[:12]}"
        
        try:
            # Validate sentiment
            if sentiment not in ['positive', 'negative', 'neutral']:
                raise ValueError(f"Invalid sentiment: {sentiment}")
            
            # Validate rating if provided
            if rating is not None and (rating < 1 or rating > 5):
                raise ValueError(f"Rating must be between 1 and 5, got: {rating}")
            
            # Determine feedback type
            feedback_type = self._determine_feedback_type(rating, sentiment, comment)
            
            # Convert tags list to comma-separated string
            tags_str = ','.join(tags) if tags else None
            
            # Convert response_metadata to JSON string
            metadata_str = json.dumps(response_metadata) if response_metadata else None
            
            # Insert feedback
            with engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO conversation_feedback (
                            feedback_id, request_id, response_id, session_id, conversation_id,
                            rating, sentiment, feedback_type, user_comment, tags,
                            user_query, harvey_response, response_metadata,
                            query_type, action_taken, user_ip, user_agent,
                            created_at
                        ) VALUES (
                            :feedback_id, :request_id, :response_id, :session_id, :conversation_id,
                            :rating, :sentiment, :feedback_type, :user_comment, :tags,
                            :user_query, :harvey_response, :response_metadata,
                            :query_type, :action_taken, :user_ip, :user_agent,
                            :created_at
                        )
                    """),
                    {
                        "feedback_id": feedback_id,
                        "request_id": request_id or response_id,
                        "response_id": response_id,
                        "session_id": session_id,
                        "conversation_id": conversation_id,
                        "rating": rating,
                        "sentiment": sentiment,
                        "feedback_type": feedback_type,
                        "user_comment": comment,
                        "tags": tags_str,
                        "user_query": user_query,
                        "harvey_response": harvey_response,
                        "response_metadata": metadata_str,
                        "query_type": query_type,
                        "action_taken": action_taken,
                        "user_ip": user_ip,
                        "user_agent": user_agent,
                        "created_at": datetime.now()
                    }
                )
            
            logger.info(f"Recorded feedback: {feedback_id} (response: {response_id}, sentiment: {sentiment}, rating: {rating})")
            
            # If high quality, create training data entry
            if rating and rating >= 4 and user_query and harvey_response:
                self._create_training_data_entry(
                    feedback_id=feedback_id,
                    user_query=user_query,
                    harvey_response=harvey_response,
                    rating=rating,
                    query_type=query_type
                )
            
            # Update response patterns
            if query_type and action_taken:
                self._update_response_patterns(
                    query_type=query_type,
                    action_taken=action_taken,
                    sentiment=sentiment,
                    rating=rating
                )
            
            return {
                "success": True,
                "feedback_id": feedback_id,
                "message": "Feedback recorded successfully"
            }
        
        except Exception as e:
            logger.error(f"Failed to record feedback: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _determine_feedback_type(self, rating: Optional[int], sentiment: str, comment: Optional[str]) -> str:
        """Determine the type of feedback based on provided data"""
        if rating:
            return "rating"
        elif comment:
            return "comment"
        elif sentiment == "positive":
            return "thumbs_up"
        elif sentiment == "negative":
            return "thumbs_down"
        else:
            return "general"
    
    def _create_training_data_entry(
        self,
        feedback_id: str,
        user_query: str,
        harvey_response: str,
        rating: int,
        query_type: Optional[str] = None
    ):
        """Create a training data entry for high-quality responses"""
        try:
            training_id = f"train_{uuid.uuid4().hex[:12]}"
            quality_score = rating / 5.0  # Normalize to 0.0-1.0
            
            with engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO gpt_training_data (
                            training_id, feedback_id, user_message, assistant_message,
                            quality_score, is_high_quality, query_type, created_at
                        ) VALUES (
                            :training_id, :feedback_id, :user_message, :assistant_message,
                            :quality_score, :is_high_quality, :query_type, :created_at
                        )
                    """),
                    {
                        "training_id": training_id,
                        "feedback_id": feedback_id,
                        "user_message": user_query,
                        "assistant_message": harvey_response,
                        "quality_score": quality_score,
                        "is_high_quality": 1,  # BIT type: 1 for True
                        "query_type": query_type,
                        "created_at": datetime.now()
                    }
                )
            
            logger.info(f"Created training data entry: {training_id} (quality: {quality_score})")
        
        except Exception as e:
            logger.warning(f"Failed to create training data entry: {e}")
    
    def _update_response_patterns(
        self,
        query_type: str,
        action_taken: str,
        sentiment: str,
        rating: Optional[int] = None
    ):
        """Update successful response patterns analytics"""
        try:
            pattern_id = f"{query_type}_{action_taken}".replace(" ", "_").lower()
            
            with engine.begin() as conn:
                # Check if pattern exists
                result = conn.execute(
                    text("SELECT pattern_id FROM successful_response_patterns WHERE pattern_id = :pattern_id"),
                    {"pattern_id": pattern_id}
                ).first()
                
                if result:
                    # Update existing pattern
                    conn.execute(
                        text("""
                            UPDATE successful_response_patterns
                            SET positive_feedback_count = positive_feedback_count + :pos_inc,
                                negative_feedback_count = negative_feedback_count + :neg_inc,
                                total_responses = total_responses + 1,
                                last_updated = :now,
                                last_positive_feedback = CASE WHEN :is_positive THEN :now ELSE last_positive_feedback END
                            WHERE pattern_id = :pattern_id
                        """),
                        {
                            "pattern_id": pattern_id,
                            "pos_inc": 1 if sentiment == 'positive' else 0,
                            "neg_inc": 1 if sentiment == 'negative' else 0,
                            "is_positive": sentiment == 'positive',
                            "now": datetime.now()
                        }
                    )
                else:
                    # Create new pattern
                    conn.execute(
                        text("""
                            INSERT INTO successful_response_patterns (
                                pattern_id, query_type, action_type,
                                positive_feedback_count, negative_feedback_count, total_responses,
                                first_seen, last_updated
                            ) VALUES (
                                :pattern_id, :query_type, :action_type,
                                :pos_count, :neg_count, 1,
                                :now, :now
                            )
                        """),
                        {
                            "pattern_id": pattern_id,
                            "query_type": query_type,
                            "action_type": action_taken,
                            "pos_count": 1 if sentiment == 'positive' else 0,
                            "neg_count": 1 if sentiment == 'negative' else 0,
                            "now": datetime.now()
                        }
                    )
                
                # Update success rate
                conn.execute(
                    text("""
                        UPDATE successful_response_patterns
                        SET success_rate = ROUND(100.0 * positive_feedback_count / NULLIF(total_responses, 0), 2),
                            avg_rating = (
                                SELECT AVG(rating)
                                FROM conversation_feedback
                                WHERE query_type = :query_type AND action_taken = :action_taken AND rating IS NOT NULL
                            )
                        WHERE pattern_id = :pattern_id
                    """),
                    {
                        "pattern_id": pattern_id,
                        "query_type": query_type,
                        "action_taken": action_taken
                    }
                )
        
        except Exception as e:
            logger.warning(f"Failed to update response patterns: {e}")
    
    def get_feedback_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get feedback summary for the last N days"""
        try:
            with engine.begin() as conn:
                result = conn.execute(
                    text("""
                        SELECT 
                            COUNT(*) as total_feedback,
                            AVG(rating) as avg_rating,
                            SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) as positive_count,
                            SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) as negative_count,
                            SUM(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END) as neutral_count
                        FROM conversation_feedback
                        WHERE created_at >= DATEADD(DAY, -:days, GETDATE())
                    """),
                    {"days": days}
                ).first()
                
                if result:
                    total = result[0] or 0
                    return {
                        "total_feedback": total,
                        "avg_rating": round(float(result[1] or 0), 2),
                        "positive_count": result[2] or 0,
                        "negative_count": result[3] or 0,
                        "neutral_count": result[4] or 0,
                        "success_rate": round(100.0 * (result[2] or 0) / total, 2) if total > 0 else 0
                    }
                
                return {"total_feedback": 0}
        
        except Exception as e:
            logger.error(f"Failed to get feedback summary: {e}")
            return {"error": str(e)}
    
    def export_training_data(self, limit: int = 1000, min_quality: float = 0.8) -> List[Dict[str, Any]]:
        """
        Export high-quality training data for GPT-4o fine-tuning.
        
        Returns data in OpenAI fine-tuning format:
        {"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
        """
        try:
            with engine.begin() as conn:
                results = conn.execute(
                    text("""
                        SELECT TOP :limit user_message, assistant_message, quality_score, query_type
                        FROM gpt_training_data
                        WHERE is_high_quality = 1
                          AND used_in_training = 0
                          AND quality_score >= :min_quality
                        ORDER BY quality_score DESC, created_at DESC
                    """),
                    {"min_quality": min_quality, "limit": limit}
                ).fetchall()
                
                training_data = []
                for row in results:
                    training_data.append({
                        "messages": [
                            {"role": "user", "content": row[0]},
                            {"role": "assistant", "content": row[1]}
                        ],
                        "metadata": {
                            "quality_score": float(row[2]),
                            "query_type": row[3]
                        }
                    })
                
                logger.info(f"Exported {len(training_data)} training examples")
                return training_data
        
        except Exception as e:
            logger.error(f"Failed to export training data: {e}")
            return []


# Global instance
feedback_service = FeedbackService()
