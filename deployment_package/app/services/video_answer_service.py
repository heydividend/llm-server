"""
Video Answer Service - YouTube @heydividedtv integration with semantic search
Searches Harvey's video knowledge base to find relevant YouTube videos for user questions
"""

import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class VideoAnswerService:
    """
    Service to search and recommend relevant YouTube videos from @heydividedtv channel
    """
    
    def __init__(self):
        self.video_knowledge_base = self._load_video_knowledge_base()
        self.search_index = self._build_search_index()
        
    def _load_video_knowledge_base(self) -> List[Dict[str, Any]]:
        """Load video knowledge base from JSON file"""
        try:
            kb_path = Path("app/data/video_knowledge_base.json")
            if kb_path.exists():
                with open(kb_path, 'r') as f:
                    return json.load(f)
            else:
                logger.warning("Video knowledge base file not found, using defaults")
                return self._get_default_videos()
        except Exception as e:
            logger.error(f"Error loading video knowledge base: {e}")
            return self._get_default_videos()
    
    def _get_default_videos(self) -> List[Dict[str, Any]]:
        """Default video content when file is not available"""
        return [
            {
                "video_id": "example1",
                "title": "Understanding Dividend Investing Basics",
                "url": "https://youtube.com/@heydividedtv",
                "duration": "10:30",
                "topics": ["dividend basics", "passive income", "investing 101"],
                "keywords": ["dividend", "income", "stocks", "basics", "beginner"],
                "description": "Introduction to dividend investing for beginners"
            }
        ]
    
    def _build_search_index(self) -> Dict[str, List[int]]:
        """Build keyword search index for fast lookup"""
        index = {}
        
        for idx, video in enumerate(self.video_knowledge_base):
            # Index keywords
            for keyword in video.get("keywords", []):
                keyword_lower = keyword.lower()
                if keyword_lower not in index:
                    index[keyword_lower] = []
                index[keyword_lower].append(idx)
            
            # Index topics
            for topic in video.get("topics", []):
                topic_lower = topic.lower()
                if topic_lower not in index:
                    index[topic_lower] = []
                index[topic_lower].append(idx)
        
        return index
    
    def _normalize_video_urls(self, video: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure video has canonical YouTube URLs
        
        Generates:
        - video_url: https://www.youtube.com/watch?v={video_id}
        - embed_url: https://www.youtube.com/embed/{video_id}
        - thumbnail_url: https://img.youtube.com/vi/{video_id}/maxresdefault.jpg
        
        Args:
            video: Video dictionary (must have video_id)
            
        Returns:
            Video dictionary with normalized URLs
        """
        video_id = video.get("video_id", "")
        
        if video_id:
            # Generate canonical YouTube watch URL
            video["video_url"] = f"https://www.youtube.com/watch?v={video_id}"
            
            # Generate embed URL for iframe embedding
            video["embed_url"] = f"https://www.youtube.com/embed/{video_id}"
            
            # Generate thumbnail URL (maxresdefault for highest quality)
            video["thumbnail_url"] = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
            
            # Keep original url field for backwards compatibility
            if "url" not in video or not video["url"].startswith("https://www.youtube.com/watch"):
                video["url"] = video["video_url"]
        
        return video
    
    def search_videos(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """
        Search for relevant videos based on user query
        
        Args:
            query: User's search query
            max_results: Maximum number of videos to return
            
        Returns:
            List of relevant video dictionaries with relevance scores and normalized URLs
        """
        query_lower = query.lower()
        query_terms = re.findall(r'\b\w+\b', query_lower)
        
        # Score each video based on keyword matches
        video_scores = {}
        
        for term in query_terms:
            if term in self.search_index:
                for video_idx in self.search_index[term]:
                    video_scores[video_idx] = video_scores.get(video_idx, 0) + 1
        
        # Additional scoring for exact phrase matches in title/description
        for idx, video in enumerate(self.video_knowledge_base):
            title_lower = video.get("title", "").lower()
            desc_lower = video.get("description", "").lower()
            
            # Boost score if query terms appear in title
            for term in query_terms:
                if term in title_lower:
                    video_scores[idx] = video_scores.get(idx, 0) + 3
                if term in desc_lower:
                    video_scores[idx] = video_scores.get(idx, 0) + 1
        
        # Sort by score and return top results
        sorted_videos = sorted(
            video_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:max_results]
        
        results = []
        for video_idx, score in sorted_videos:
            video = self.video_knowledge_base[video_idx].copy()
            video["relevance_score"] = score
            
            # FIX: Normalize URLs to include canonical YouTube watch/embed URLs
            video = self._normalize_video_urls(video)
            
            results.append(video)
        
        return results
    
    def format_video_recommendations(self, videos: List[Dict[str, Any]]) -> str:
        """
        Format video recommendations into user-friendly markdown
        
        Note: Frontend should render these with custom HeyDividendPlayer component
        
        Args:
            videos: List of video dictionaries with normalized metadata
            
        Returns:
            Formatted markdown string (frontend will inject video players)
        """
        if not videos:
            return ""
        
        response = "\n\n### 🎥 Related Videos from @heydividedtv\n\n"
        
        for video in videos:
            title = video.get("title", "Video")
            video_url = video.get("video_url", video.get("url", ""))
            duration = video.get("duration", "")
            description = video.get("description", "")
            
            response += f"**{title}**"
            if duration:
                response += f" ({duration})"
            response += "\n"
            response += f"🔗 {video_url}\n"
            if description:
                response += f"*{description}*\n"
            response += "\n"
        
        return response
    
    def get_video_by_topic(self, topic: str) -> List[Dict[str, Any]]:
        """
        Get videos by specific topic
        
        Args:
            topic: Topic to search for
            
        Returns:
            List of videos matching the topic
        """
        topic_lower = topic.lower()
        matching_videos = []
        
        for video in self.video_knowledge_base:
            video_topics = [t.lower() for t in video.get("topics", [])]
            if topic_lower in video_topics:
                matching_videos.append(video)
        
        return matching_videos
    
    def enhance_response_with_videos(self, user_query: str, response_text: str) -> Dict[str, Any]:
        """
        Enhance response with relevant video recommendations
        
        Returns structured video metadata for frontend rendering with HeyDividendPlayer
        
        Args:
            user_query: Original user query
            response_text: AI-generated response text
            
        Returns:
            Dictionary with enhanced response and structured video metadata
        """
        # Search for relevant videos
        videos = self.search_videos(user_query, max_results=3)
        
        # Only add videos if we found relevant matches
        if videos and videos[0].get("relevance_score", 0) >= 2:
            video_section = self.format_video_recommendations(videos)
            enhanced_response = response_text + video_section
            video_suffix = video_section  # Exact video section that was appended
        else:
            enhanced_response = response_text
            videos = []
            video_suffix = ""
        
        return {
            "original_response": response_text,
            "enhanced_response": enhanced_response,
            "video_suffix": video_suffix,  # NEW: Exact video section for streaming
            "videos_added": len(videos),
            "videos": videos,
            "video_metadata": self._extract_video_metadata(videos)
        }
    
    def _extract_video_metadata(self, videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract clean video metadata for frontend consumption
        
        Args:
            videos: List of video dictionaries
            
        Returns:
            List of clean metadata objects for HeyDividendPlayer component
        """
        metadata = []
        
        for video in videos:
            metadata.append({
                "video_id": video.get("video_id", ""),
                "title": video.get("title", ""),
                "description": video.get("description", ""),
                "duration": video.get("duration", ""),
                "thumbnail_url": video.get("thumbnail_url", ""),
                "video_url": video.get("video_url", ""),
                "embed_url": video.get("embed_url", ""),
                "channel_name": "@heydividedtv",
                "published_at": video.get("published_at", ""),
                "cta_copy": "Watch on YouTube"
            })
        
        return metadata
    
    def get_all_topics(self) -> List[str]:
        """Get list of all unique topics in the video knowledge base"""
        topics = set()
        for video in self.video_knowledge_base:
            topics.update(video.get("topics", []))
        return sorted(list(topics))
    
    def get_video_stats(self) -> Dict[str, Any]:
        """Get statistics about the video knowledge base"""
        return {
            "total_videos": len(self.video_knowledge_base),
            "total_topics": len(self.get_all_topics()),
            "total_keywords": len(self.search_index),
            "average_keywords_per_video": sum(len(v.get("keywords", [])) for v in self.video_knowledge_base) / max(len(self.video_knowledge_base), 1)
        }
