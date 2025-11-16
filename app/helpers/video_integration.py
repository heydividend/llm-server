"""
Video Integration Helper
Automatically enhances Harvey chat responses with relevant YouTube videos
"""

from app.services.video_answer_service import VideoAnswerService
from typing import Optional

video_service = VideoAnswerService()

def enhance_response_with_videos(user_query: str, ai_response: str, threshold: int = 2) -> str:
    """
    Enhance AI response with relevant videos from @heydividedtv
    
    Args:
        user_query: User's original question
        ai_response: Harvey's generated response
        threshold: Minimum relevance score to include videos (default: 2)
        
    Returns:
        Enhanced response with video recommendations appended
    """
    
    # Search for relevant videos
    videos = video_service.search_videos(user_query, max_results=2)
    
    # Only add videos if relevance score meets threshold
    if videos and videos[0].get("relevance_score", 0) >= threshold:
        video_section = video_service.format_video_recommendations(videos)
        return ai_response + video_section
    
    return ai_response


def get_video_recommendations(query: str, max_results: int = 2) -> Optional[str]:
    """
    Get formatted video recommendations for a query
    
    Args:
        query: Search query
        max_results: Maximum videos to return
        
    Returns:
        Formatted markdown string with videos, or None if no relevant videos
    """
    videos = video_service.search_videos(query, max_results=max_results)
    
    if videos and videos[0].get("relevance_score", 0) >= 2:
        return video_service.format_video_recommendations(videos)
    
    return None
