"""
Harvey Hashtag API Routes

Provides endpoints for hashtag analytics, trending detection,
and user hashtag preferences.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import logging

from app.services.hashtag_analytics_service import get_hashtag_analytics_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/hashtags", tags=["hashtags"])

hashtag_service = get_hashtag_analytics_service()


class HashtagEventRequest(BaseModel):
    """Request model for tracking hashtag events"""
    hashtags: List[str] = Field(..., description="List of hashtags to track")
    user_id: Optional[str] = Field(None, description="User identifier")
    context: str = Field("chat", description="Context: chat, search, portfolio, watchlist")
    session_id: Optional[str] = Field(None, description="Session ID")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    metadata: Optional[Dict] = Field(None, description="Additional metadata")


class HashtagEventResponse(BaseModel):
    """Response model for hashtag tracking"""
    success: bool
    hashtags_tracked: Optional[int] = None
    timestamp: Optional[str] = None
    error: Optional[str] = None


class TrendingHashtagResponse(BaseModel):
    """Response model for trending hashtags"""
    hashtag: str
    count: int
    rank: int
    time_window_hours: int


class UserPreferenceResponse(BaseModel):
    """Response model for user hashtag preferences"""
    hashtag: str
    count: int
    rank: int


class CooccurrenceResponse(BaseModel):
    """Response model for hashtag co-occurrence"""
    related_hashtag: str
    cooccurrence_count: int
    rank: int


@router.post("/track", response_model=HashtagEventResponse)
async def track_hashtag_event(request: HashtagEventRequest):
    """
    Track a hashtag usage event
    
    Example:
    ```json
    {
        "hashtags": ["AAPL", "MSFT", "GOOGL"],
        "user_id": "user123",
        "context": "chat",
        "session_id": "session456",
        "conversation_id": "conv789"
    }
    ```
    """
    try:
        result = hashtag_service.track_hashtag_event(
            hashtags=request.hashtags,
            user_id=request.user_id,
            context=request.context,
            session_id=request.session_id,
            conversation_id=request.conversation_id,
            metadata=request.metadata
        )
        
        if result["success"]:
            return HashtagEventResponse(
                success=True,
                hashtags_tracked=result.get("hashtags_tracked"),
                timestamp=result.get("timestamp")
            )
        else:
            return HashtagEventResponse(
                success=False,
                error=result.get("reason") or result.get("error")
            )
            
    except Exception as e:
        logger.error(f"[HashtagAPI] Track event error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trending", response_model=List[TrendingHashtagResponse])
async def get_trending_hashtags(
    time_window_hours: int = Query(24, description="Time window in hours (24, 168, 720)"),
    limit: int = Query(10, description="Maximum number of trending hashtags"),
    min_count: int = Query(2, description="Minimum occurrence count")
):
    """
    Get trending hashtags within a time window
    
    Examples:
    - Last 24 hours: /api/hashtags/trending?time_window_hours=24&limit=10
    - Last 7 days: /api/hashtags/trending?time_window_hours=168&limit=20
    - Last 30 days: /api/hashtags/trending?time_window_hours=720&limit=50
    """
    try:
        trending = hashtag_service.get_trending_hashtags(
            time_window_hours=time_window_hours,
            limit=limit,
            min_count=min_count
        )
        
        return [TrendingHashtagResponse(**item) for item in trending]
        
    except Exception as e:
        logger.error(f"[HashtagAPI] Trending error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}/preferences", response_model=List[UserPreferenceResponse])
async def get_user_preferences(
    user_id: str,
    limit: int = Query(20, description="Maximum number of hashtags")
):
    """
    Get a user's most frequently used hashtags
    
    Example: /api/hashtags/user/user123/preferences?limit=20
    """
    try:
        preferences = hashtag_service.get_user_hashtag_preferences(
            user_id=user_id,
            limit=limit
        )
        
        return [UserPreferenceResponse(**item) for item in preferences]
        
    except Exception as e:
        logger.error(f"[HashtagAPI] User preferences error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/related/{hashtag}", response_model=List[CooccurrenceResponse])
async def get_related_hashtags(
    hashtag: str,
    limit: int = Query(10, description="Maximum number of related hashtags")
):
    """
    Find hashtags that commonly appear with the given hashtag
    
    Example: /api/hashtags/related/AAPL?limit=10
    """
    try:
        # Remove # symbol if present
        hashtag_clean = hashtag.replace("#", "").upper()
        
        related = hashtag_service.get_hashtag_cooccurrence(
            hashtag=hashtag_clean,
            limit=limit
        )
        
        return [CooccurrenceResponse(**item) for item in related]
        
    except Exception as e:
        logger.error(f"[HashtagAPI] Related hashtags error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_hashtag_stats(
    hashtag: Optional[str] = Query(None, description="Specific hashtag to analyze")
):
    """
    Get comprehensive statistics for a hashtag or all hashtags
    
    Examples:
    - All stats: /api/hashtags/stats
    - Specific: /api/hashtags/stats?hashtag=AAPL
    """
    try:
        hashtag_clean = hashtag.replace("#", "").upper() if hashtag else None
        
        stats = hashtag_service.get_hashtag_stats(hashtag_clean)
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"[HashtagAPI] Stats error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract")
async def extract_hashtags_from_text(
    text: str = Query(..., description="Text to extract hashtags from")
):
    """
    Extract all hashtags from a given text
    
    Example: /api/hashtags/extract?text=Check out #AAPL and #MSFT dividends
    """
    try:
        hashtags = hashtag_service.extract_hashtags(text)
        
        return {
            "success": True,
            "text": text,
            "hashtags": hashtags,
            "count": len(hashtags)
        }
        
    except Exception as e:
        logger.error(f"[HashtagAPI] Extract error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/user/{user_id}/data")
async def delete_user_data(user_id: str):
    """
    Delete all hashtag data for a specific user (GDPR compliance)
    
    This removes:
    - User hashtag preferences
    - All events associated with the user
    - User context entries
    
    Example: DELETE /api/hashtags/user/user123/data
    """
    try:
        result = hashtag_service.delete_user_data(user_id)
        
        if result["success"]:
            return {
                "success": True,
                "message": f"User data deleted successfully for {user_id}",
                "details": {
                    "hashtags_deleted": result.get("hashtags_deleted", 0),
                    "events_deleted": result.get("events_deleted", 0),
                    "contexts_cleaned": result.get("contexts_cleaned", 0)
                }
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail=result.get("error", "Unknown error during deletion")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[HashtagAPI] Delete user data error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
