"""
Feedback API Routes

Endpoints for collecting user feedback on Harvey's responses
and accessing feedback analytics.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from app.services.feedback_service import feedback_service

logger = logging.getLogger("feedback_routes")

router = APIRouter()


class FeedbackRequest(BaseModel):
    """Request model for submitting feedback"""
    response_id: str = Field(..., description="ID of the response being rated")
    sentiment: str = Field(..., description="Sentiment: positive, negative, or neutral")
    rating: Optional[int] = Field(None, ge=1, le=5, description="1-5 star rating")
    comment: Optional[str] = Field(None, description="User's text comment")
    tags: Optional[List[str]] = Field(None, description="Feedback tags (accurate, helpful, etc.)")
    
    # Optional context (usually provided by system, not user)
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    user_query: Optional[str] = None
    harvey_response: Optional[str] = None
    response_metadata: Optional[dict] = None
    query_type: Optional[str] = None
    action_taken: Optional[str] = None


@router.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest, request: Request):
    """
    Submit feedback on a Harvey response.
    
    **Quick feedback options:**
    - Thumbs up: `{"response_id": "resp_123", "sentiment": "positive"}`
    - Thumbs down: `{"response_id": "resp_123", "sentiment": "negative"}`
    - Rating: `{"response_id": "resp_123", "sentiment": "positive", "rating": 5}`
    - Comment: `{"response_id": "resp_123", "sentiment": "positive", "rating": 4, "comment": "Great analysis!"}`
    
    **Returns:**
    - feedback_id: Unique ID for this feedback entry
    - success: True if recorded successfully
    """
    try:
        # Get user context
        user_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # Record feedback
        result = feedback_service.record_feedback(
            response_id=feedback.response_id,
            sentiment=feedback.sentiment,
            request_id=feedback.request_id,
            session_id=feedback.session_id,
            conversation_id=feedback.conversation_id,
            rating=feedback.rating,
            comment=feedback.comment,
            tags=feedback.tags,
            user_query=feedback.user_query,
            harvey_response=feedback.harvey_response,
            response_metadata=feedback.response_metadata,
            query_type=feedback.query_type,
            action_taken=feedback.action_taken,
            user_ip=user_ip,
            user_agent=user_agent
        )
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to record feedback"))
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Feedback submission error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback/{response_id}/{sentiment}")
async def submit_simple_feedback(response_id: str, sentiment: str, request: Request):
    """
    Quick feedback endpoint - just thumbs up/down.
    
    **Usage:**
    - Thumbs up: `POST /v1/feedback/resp_123/positive`
    - Thumbs down: `POST /v1/feedback/resp_123/negative`
    
    **Returns:**
    - feedback_id: Unique ID for this feedback entry
    - success: True if recorded successfully
    """
    try:
        user_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        result = feedback_service.record_feedback(
            response_id=response_id,
            sentiment=sentiment,
            user_ip=user_ip,
            user_agent=user_agent
        )
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to record feedback"))
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Simple feedback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback/summary")
async def get_feedback_summary(days: int = 7):
    """
    Get feedback summary for the last N days.
    
    **Query Parameters:**
    - days: Number of days to analyze (default: 7)
    
    **Returns:**
    - total_feedback: Total number of feedback entries
    - avg_rating: Average star rating
    - positive_count: Number of positive feedback
    - negative_count: Number of negative feedback
    - success_rate: Percentage of positive feedback
    """
    try:
        summary = feedback_service.get_feedback_summary(days=days)
        return summary
    except Exception as e:
        logger.error(f"Error getting feedback summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback/training-data/export")
async def export_training_data(limit: int = 1000, min_quality: float = 0.8):
    """
    Export high-quality training data for GPT-4o fine-tuning.
    
    **Query Parameters:**
    - limit: Maximum number of examples to export (default: 1000)
    - min_quality: Minimum quality score 0.0-1.0 (default: 0.8)
    
    **Returns:**
    - Array of training examples in OpenAI fine-tuning format
    - Each example: `{"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}`
    
    **Usage:**
    Save output to `training_data.jsonl` for GPT-4o fine-tuning:
    ```bash
    curl http://localhost:5000/v1/feedback/training-data/export?limit=5000 > training_data.json
    ```
    """
    try:
        training_data = feedback_service.export_training_data(
            limit=limit,
            min_quality=min_quality
        )
        
        return {
            "success": True,
            "count": len(training_data),
            "training_data": training_data,
            "format": "openai_finetuning",
            "instructions": "Save to .jsonl file (one example per line) for OpenAI fine-tuning"
        }
    except Exception as e:
        logger.error(f"Error exporting training data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback/analytics/patterns")
async def get_response_patterns(min_responses: int = 10):
    """
    Get successful response patterns analytics.
    
    **Query Parameters:**
    - min_responses: Minimum number of responses to include pattern (default: 10)
    
    **Returns:**
    - Array of response patterns with success rates
    """
    try:
        from app.core.database import engine
        from sqlalchemy import text
        
        with engine.begin() as conn:
            results = conn.execute(
                text("""
                    SELECT 
                        pattern_id,
                        query_type,
                        action_type,
                        avg_rating,
                        positive_feedback_count,
                        negative_feedback_count,
                        total_responses,
                        success_rate,
                        last_updated
                    FROM successful_response_patterns
                    WHERE total_responses >= :min_responses
                    ORDER BY success_rate DESC, avg_rating DESC
                """),
                {"min_responses": min_responses}
            ).fetchall()
            
            patterns = []
            for row in results:
                patterns.append({
                    "pattern_id": row[0],
                    "query_type": row[1],
                    "action_type": row[2],
                    "avg_rating": float(row[3]) if row[3] else None,
                    "positive_feedback_count": row[4],
                    "negative_feedback_count": row[5],
                    "total_responses": row[6],
                    "success_rate": float(row[7]) if row[7] else 0,
                    "last_updated": str(row[8]) if row[8] else None
                })
            
            return {
                "success": True,
                "patterns": patterns,
                "count": len(patterns)
            }
    
    except Exception as e:
        logger.error(f"Error getting response patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback/analytics/dashboard")
async def get_analytics_dashboard(days: int = 7):
    """
    Get comprehensive feedback analytics dashboard.
    
    **Query Parameters:**
    - days: Number of days to analyze (default: 7)
    
    **Returns:**
    - Overall feedback statistics
    - Top and bottom performing query types
    - Training data readiness
    - Improvement suggestions
    """
    from app.services.feedback_analytics import feedback_analytics
    
    try:
        metrics = feedback_analytics.get_dashboard_metrics(days=days)
        suggestions = feedback_analytics.get_improvement_suggestions()
        
        return {
            **metrics,
            "improvement_suggestions": suggestions
        }
    except Exception as e:
        logger.error(f"Error getting analytics dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback/analytics/trends")
async def get_feedback_trends(days: int = 30):
    """
    Get feedback trends over time.
    
    **Query Parameters:**
    - days: Number of days to analyze (default: 30)
    
    **Returns:**
    - Daily feedback statistics
    - Rating and sentiment trends
    """
    from app.services.feedback_analytics import feedback_analytics
    
    try:
        trends = feedback_analytics.get_feedback_trends(days=days)
        return trends
    except Exception as e:
        logger.error(f"Error getting feedback trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))
