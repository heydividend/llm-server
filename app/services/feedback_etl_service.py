"""
Feedback ETL Service for Harvey Continuous Learning Pipeline

Extracts, Transforms, and Loads user feedback data from the database
for analysis by the Gemini-powered learning system.

Features:
- Extract feedback from conversation_feedback table
- Load full conversation context for each feedback
- Filter low-quality or spam feedback
- Track feedback metadata and user patterns
- Prepare data for Gemini analysis
"""

import logging
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import text
from app.core.database import engine

logger = logging.getLogger("feedback_etl")


class FeedbackETLService:
    """
    ETL service for extracting and preparing user feedback for learning pipeline.
    
    Responsibilities:
    - Extract feedback from database with conversation context
    - Filter out low-quality, spam, or duplicate feedback
    - Transform feedback into structured format for Gemini analysis
    - Track metadata for audit trail
    """
    
    def __init__(self):
        self.logger = logger
    
    def extract_feedback(
        self,
        days: int = 30,
        min_rating: Optional[int] = None,
        max_rating: Optional[int] = None,
        sentiment: Optional[str] = None,
        query_types: Optional[List[str]] = None,
        limit: Optional[int] = None,
        exclude_analyzed: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Extract feedback from database based on criteria.
        
        Args:
            days: Look back N days (default 30)
            min_rating: Minimum rating filter (1-5)
            max_rating: Maximum rating filter (1-5)
            sentiment: Filter by sentiment ('positive', 'negative', 'neutral')
            query_types: Filter by query types
            limit: Maximum number of feedback items to extract
            exclude_analyzed: Skip feedback already analyzed by Gemini
        
        Returns:
            List of feedback dictionaries with full context
        """
        try:
            # Build dynamic WHERE clause
            where_clauses = ["cf.created_at >= DATEADD(DAY, -:days, GETDATE())"]
            params = {"days": days}
            
            if min_rating is not None:
                where_clauses.append("cf.rating >= :min_rating")
                params["min_rating"] = min_rating
            
            if max_rating is not None:
                where_clauses.append("cf.rating <= :max_rating")
                params["max_rating"] = max_rating
            
            if sentiment:
                where_clauses.append("cf.sentiment = :sentiment")
                params["sentiment"] = sentiment
            
            if query_types:
                placeholders = ','.join([f":qt{i}" for i in range(len(query_types))])
                where_clauses.append(f"cf.query_type IN ({placeholders})")
                for i, qt in enumerate(query_types):
                    params[f"qt{i}"] = qt
            
            if exclude_analyzed:
                where_clauses.append("""
                    NOT EXISTS (
                        SELECT 1 FROM feedback_labels fl 
                        WHERE fl.feedback_id = cf.feedback_id
                    )
                """)
            
            where_clause = " AND ".join(where_clauses)
            limit_clause = f"TOP {limit}" if limit else ""
            
            query = f"""
                SELECT {limit_clause}
                    cf.feedback_id,
                    cf.request_id,
                    cf.response_id,
                    cf.session_id,
                    cf.conversation_id,
                    cf.rating,
                    cf.sentiment,
                    cf.feedback_type,
                    cf.user_comment,
                    cf.tags,
                    cf.user_query,
                    cf.harvey_response,
                    cf.response_metadata,
                    cf.query_type,
                    cf.action_taken,
                    cf.created_at
                FROM conversation_feedback cf
                WHERE {where_clause}
                ORDER BY cf.created_at DESC
            """
            
            with engine.connect() as conn:
                result = conn.execute(text(query), params)
                
                feedback_items = []
                for row in result:
                    feedback_items.append({
                        'feedback_id': row[0],
                        'request_id': row[1],
                        'response_id': row[2],
                        'session_id': row[3],
                        'conversation_id': row[4],
                        'rating': row[5],
                        'sentiment': row[6],
                        'feedback_type': row[7],
                        'user_comment': row[8],
                        'tags': row[9],
                        'user_query': row[10],
                        'harvey_response': row[11],
                        'response_metadata': row[12],
                        'query_type': row[13],
                        'action_taken': row[14],
                        'created_at': row[15]
                    })
            
            self.logger.info(f"Extracted {len(feedback_items)} feedback items (days={days}, filters applied)")
            return feedback_items
        
        except Exception as e:
            self.logger.error(f"Failed to extract feedback: {e}")
            return []
    
    def load_conversation_context(
        self,
        conversation_id: str,
        max_messages: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Load conversation history for context.
        
        Args:
            conversation_id: Conversation ID
            max_messages: Maximum messages to load
        
        Returns:
            List of message dictionaries (user/assistant pairs)
        """
        if not conversation_id:
            return []
        
        try:
            query = f"""
                SELECT TOP {max_messages}
                    message_id,
                    role,
                    content,
                    created_at
                FROM conversation_messages
                WHERE conversation_id = :conversation_id
                ORDER BY created_at ASC
            """
            
            with engine.connect() as conn:
                result = conn.execute(
                    text(query),
                    {"conversation_id": conversation_id}
                )
                
                messages = []
                for row in result:
                    messages.append({
                        'message_id': row[0],
                        'role': row[1],
                        'content': row[2],
                        'created_at': row[3]
                    })
                
                return messages
        
        except Exception as e:
            self.logger.warning(f"Failed to load conversation context for {conversation_id}: {e}")
            return []
    
    def transform_for_analysis(
        self,
        feedback_item: Dict[str, Any],
        include_conversation: bool = True
    ) -> Dict[str, Any]:
        """
        Transform raw feedback into structured format for Gemini analysis.
        
        Args:
            feedback_item: Raw feedback dictionary
            include_conversation: Include conversation context
        
        Returns:
            Transformed feedback ready for Gemini analysis
        """
        # Load conversation context if available
        conversation_context = []
        if include_conversation and feedback_item.get('conversation_id'):
            conversation_context = self.load_conversation_context(
                feedback_item['conversation_id'],
                max_messages=5
            )
        
        # Build transformed structure
        transformed = {
            'feedback_id': feedback_item['feedback_id'],
            'rating': feedback_item['rating'],
            'sentiment': feedback_item['sentiment'],
            'user_comment': feedback_item.get('user_comment', ''),
            'query': feedback_item['user_query'],
            'response': feedback_item['harvey_response'],
            'query_type': feedback_item.get('query_type', 'unknown'),
            'action_taken': feedback_item.get('action_taken', ''),
            'tags': feedback_item.get('tags', '').split(',') if feedback_item.get('tags') else [],
            'conversation_context': [
                {'role': msg['role'], 'content': msg['content']}
                for msg in conversation_context
            ],
            'timestamp': feedback_item['created_at'].isoformat() if feedback_item.get('created_at') else None
        }
        
        return transformed
    
    def filter_quality(
        self,
        feedback_items: List[Dict[str, Any]],
        min_query_length: int = 10,
        min_response_length: int = 20,
        require_rating: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Filter out low-quality feedback.
        
        Args:
            feedback_items: List of feedback items
            min_query_length: Minimum query length
            min_response_length: Minimum response length
            require_rating: Require numeric rating (not just sentiment)
        
        Returns:
            Filtered list of quality feedback
        """
        filtered = []
        
        for item in feedback_items:
            # Skip if missing essential fields
            if not item.get('user_query') or not item.get('harvey_response'):
                continue
            
            # Check lengths
            if len(item['user_query']) < min_query_length:
                continue
            
            if len(item['harvey_response']) < min_response_length:
                continue
            
            # Require rating if specified
            if require_rating and not item.get('rating'):
                continue
            
            # Skip likely spam (very short repeated patterns)
            query = item['user_query'].lower()
            if len(set(query.split())) < 3 and len(query) > 20:
                continue
            
            filtered.append(item)
        
        removed = len(feedback_items) - len(filtered)
        if removed > 0:
            self.logger.info(f"Filtered out {removed} low-quality feedback items")
        
        return filtered
    
    def get_feedback_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get statistics about available feedback.
        
        Args:
            days: Look back N days
        
        Returns:
            Statistics dictionary
        """
        try:
            query = """
                SELECT 
                    COUNT(*) as total_feedback,
                    SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) as positive,
                    SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) as negative,
                    SUM(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END) as neutral,
                    AVG(rating) as avg_rating,
                    COUNT(DISTINCT query_type) as unique_query_types,
                    COUNT(DISTINCT session_id) as unique_sessions,
                    SUM(CASE WHEN EXISTS (
                        SELECT 1 FROM feedback_labels fl 
                        WHERE fl.feedback_id = cf.feedback_id
                    ) THEN 1 ELSE 0 END) as already_analyzed
                FROM conversation_feedback cf
                WHERE cf.created_at >= DATEADD(DAY, -:days, GETDATE())
            """
            
            with engine.connect() as conn:
                result = conn.execute(text(query), {"days": days}).first()
                
                if result:
                    return {
                        'total_feedback': result[0] or 0,
                        'positive': result[1] or 0,
                        'negative': result[2] or 0,
                        'neutral': result[3] or 0,
                        'avg_rating': round(float(result[4] or 0), 2),
                        'unique_query_types': result[5] or 0,
                        'unique_sessions': result[6] or 0,
                        'already_analyzed': result[7] or 0,
                        'pending_analysis': (result[0] or 0) - (result[7] or 0)
                    }
            
            return {}
        
        except Exception as e:
            self.logger.error(f"Failed to get feedback statistics: {e}")
            return {}
    
    def extract_positive_negative_pairs(
        self,
        days: int = 30,
        same_query_type: bool = True,
        min_rating_diff: int = 2
    ) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """
        Extract pairs of positive and negative feedback for RLHF.
        
        Args:
            days: Look back N days
            same_query_type: Pair feedback from same query type
            min_rating_diff: Minimum rating difference between pairs
        
        Returns:
            List of (positive_feedback, negative_feedback) tuples
        """
        try:
            # Extract positive feedback (rating >= 4)
            positive = self.extract_feedback(
                days=days,
                min_rating=4,
                sentiment='positive',
                exclude_analyzed=False
            )
            
            # Extract negative feedback (rating <= 2)
            negative = self.extract_feedback(
                days=days,
                max_rating=2,
                sentiment='negative',
                exclude_analyzed=False
            )
            
            pairs = []
            
            # Simple pairing strategy: match by query type
            if same_query_type:
                # Group by query type
                pos_by_type: Dict[str, List[Dict]] = {}
                for p in positive:
                    qt = p.get('query_type', 'unknown')
                    if qt not in pos_by_type:
                        pos_by_type[qt] = []
                    pos_by_type[qt].append(p)
                
                neg_by_type: Dict[str, List[Dict]] = {}
                for n in negative:
                    qt = n.get('query_type', 'unknown')
                    if qt not in neg_by_type:
                        neg_by_type[qt] = []
                    neg_by_type[qt].append(n)
                
                # Create pairs from same query types
                for query_type in pos_by_type:
                    if query_type in neg_by_type:
                        pos_list = pos_by_type[query_type]
                        neg_list = neg_by_type[query_type]
                        
                        # Pair up (round-robin)
                        for i in range(min(len(pos_list), len(neg_list))):
                            pairs.append((pos_list[i], neg_list[i]))
            
            else:
                # Simple pairing: just zip positive and negative
                for i in range(min(len(positive), len(negative))):
                    pairs.append((positive[i], negative[i]))
            
            self.logger.info(f"Extracted {len(pairs)} positive/negative feedback pairs")
            return pairs
        
        except Exception as e:
            self.logger.error(f"Failed to extract feedback pairs: {e}")
            return []


# Global instance
feedback_etl_service = FeedbackETLService()
