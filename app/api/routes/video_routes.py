"""
Video Routes - API endpoints for YouTube video search and recommendations
Endpoints for @heydividedtv integration
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
import logging

from app.services.video_answer_service import VideoAnswerService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/videos", tags=["videos"])

# Initialize service
video_service = VideoAnswerService()

class VideoSearchRequest(BaseModel):
    query: str
    max_results: Optional[int] = 3

class VideoSearchResponse(BaseModel):
    query: str
    videos: List[dict]
    total_results: int

class VideoTopicsResponse(BaseModel):
    topics: List[str]
    total_count: int

class VideoStatsResponse(BaseModel):
    total_videos: int
    total_topics: int
    total_keywords: int
    average_keywords_per_video: float

@router.post("/search", response_model=VideoSearchResponse)
async def search_videos(request: VideoSearchRequest):
    """
    Search for relevant YouTube videos from @heydividedtv channel
    
    Args:
        request: Search query and optional max results
        
    Returns:
        List of relevant videos with metadata
    """
    try:
        max_results = request.max_results if request.max_results is not None else 3
        videos = video_service.search_videos(
            query=request.query,
            max_results=max_results
        )
        
        return VideoSearchResponse(
            query=request.query,
            videos=videos,
            total_results=len(videos)
        )
        
    except Exception as e:
        logger.error(f"Error searching videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/topics", response_model=VideoTopicsResponse)
async def get_all_topics():
    """
    Get all available video topics
    
    Returns:
        List of all unique topics in the knowledge base
    """
    try:
        topics = video_service.get_all_topics()
        
        return VideoTopicsResponse(
            topics=topics,
            total_count=len(topics)
        )
        
    except Exception as e:
        logger.error(f"Error fetching topics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/topic/{topic}", response_model=VideoSearchResponse)
async def get_videos_by_topic(topic: str):
    """
    Get videos for a specific topic
    
    Args:
        topic: Topic name
        
    Returns:
        List of videos matching the topic
    """
    try:
        videos = video_service.get_video_by_topic(topic)
        
        return VideoSearchResponse(
            query=f"topic:{topic}",
            videos=videos,
            total_results=len(videos)
        )
        
    except Exception as e:
        logger.error(f"Error fetching videos by topic: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=VideoStatsResponse)
async def get_video_stats():
    """
    Get statistics about the video knowledge base
    
    Returns:
        Statistics including total videos, topics, and keywords
    """
    try:
        stats = video_service.get_video_stats()
        
        return VideoStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error fetching video stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recommend")
async def recommend_videos_for_query(request: VideoSearchRequest):
    """
    Get video recommendations with formatted markdown response
    
    Args:
        request: User query
        
    Returns:
        Formatted video recommendations
    """
    try:
        max_results = request.max_results if request.max_results is not None else 3
        videos = video_service.search_videos(request.query, max_results)
        formatted = video_service.format_video_recommendations(videos)
        
        return {
            "query": request.query,
            "videos": videos,
            "formatted_response": formatted
        }
        
    except Exception as e:
        logger.error(f"Error recommending videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))
