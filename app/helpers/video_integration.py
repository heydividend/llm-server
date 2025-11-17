"""
Video Integration Helper
Automatically enhances Harvey chat responses with relevant YouTube videos
Supports hashtag-based video discovery for better recommendations
"""

from app.services.video_answer_service import VideoAnswerService
from app.services.hashtag_analytics_service import get_hashtag_analytics_service
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

video_service = VideoAnswerService()
hashtag_service = get_hashtag_analytics_service()


def enhance_response_with_videos(user_query: str, ai_response: str, threshold: int = 2, detected_tickers: Optional[List[str]] = None) -> str:
    """
    Enhance AI response with relevant videos from @heydividedtv
    
    Args:
        user_query: User's original question
        ai_response: Harvey's generated response
        threshold: Minimum relevance score to include videos (default: 2)
        detected_tickers: Optional list of detected tickers/hashtags
        
    Returns:
        Enhanced response with video recommendations appended
    """
    
    # Enhance query with detected tickers for better video matching
    enhanced_query = user_query
    if detected_tickers:
        ticker_terms = " ".join([f"#{ticker}" for ticker in detected_tickers[:3]])
        enhanced_query = f"{user_query} {ticker_terms}"
        logger.debug(f"[VideoIntegration] Enhanced query with tickers: {ticker_terms}")
    
    # Search for relevant videos
    videos = video_service.search_videos(enhanced_query, max_results=2)
    
    # Only add videos if relevance score meets threshold
    if videos and videos[0].get("relevance_score", 0) >= threshold:
        video_section = video_service.format_video_recommendations(videos)
        return ai_response + video_section
    
    return ai_response


def get_video_recommendations(query: str, max_results: int = 2, detected_tickers: Optional[List[str]] = None) -> Optional[str]:
    """
    Get formatted video recommendations for a query
    
    Args:
        query: Search query
        max_results: Maximum videos to return
        detected_tickers: Optional list of detected tickers/hashtags to enhance search
        
    Returns:
        Formatted markdown string with videos, or None if no relevant videos
    """
    # Enhance query with detected tickers for better video matching
    enhanced_query = query
    if detected_tickers:
        ticker_terms = " ".join([f"#{ticker}" for ticker in detected_tickers[:3]])
        enhanced_query = f"{query} {ticker_terms}"
        logger.debug(f"[VideoIntegration] Enhanced query with tickers: {ticker_terms}")
    
    videos = video_service.search_videos(enhanced_query, max_results=max_results)
    
    if videos and videos[0].get("relevance_score", 0) >= 2:
        return video_service.format_video_recommendations(videos)
    
    return None


def get_videos_by_hashtag(hashtag: str, max_results: int = 5) -> Optional[str]:
    """
    Get videos related to a specific hashtag/ticker
    
    Args:
        hashtag: Ticker symbol (e.g., "AAPL" or "#AAPL")
        max_results: Maximum videos to return
        
    Returns:
        Formatted markdown string with videos, or None if no relevant videos
    """
    # Remove # symbol if present
    clean_hashtag = hashtag.replace("#", "").upper()
    
    # Search for videos about this specific ticker
    search_query = f"#{clean_hashtag} dividend stock analysis"
    videos = video_service.search_videos(search_query, max_results=max_results)
    
    if videos:
        return video_service.format_video_recommendations(videos)
    
    return None


def get_trending_hashtag_videos(limit: int = 5) -> Optional[str]:
    """
    Get videos for currently trending hashtags
    
    Args:
        limit: Number of trending hashtags to get videos for
        
    Returns:
        Formatted markdown string with videos for trending topics
    """
    try:
        # Get trending hashtags from analytics service
        trending = hashtag_service.get_trending_hashtags(
            time_window_hours=24,
            limit=limit,
            min_count=2
        )
        
        if not trending:
            return None
        
        # Get the top trending hashtag
        top_hashtag = trending[0]["hashtag"]
        
        logger.info(f"[VideoIntegration] Getting videos for trending #{top_hashtag}")
        return get_videos_by_hashtag(top_hashtag, max_results=3)
        
    except Exception as e:
        logger.error(f"[VideoIntegration] Trending video error: {str(e)}")
        return None
