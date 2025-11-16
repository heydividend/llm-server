"""
Investor Education Service - Detects and corrects investment misconceptions
Addresses common errors like confusing CUSIP with ticker symbols and distribution vs dividend misunderstandings
"""

import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import re

logger = logging.getLogger(__name__)

class InvestorEducationService:
    """
    Service to detect common investor misconceptions and provide educational corrections
    """
    
    def __init__(self):
        self.education_content = self._load_education_content()
        self.misconception_patterns = self._compile_patterns()
        
    def _load_education_content(self) -> Dict[str, Any]:
        """Load investor education content from JSON file"""
        try:
            content_path = Path("app/data/investor_education_content.json")
            if content_path.exists():
                with open(content_path, 'r') as f:
                    return json.load(f)
            else:
                logger.warning("Investor education content file not found, using defaults")
                return self._get_default_content()
        except Exception as e:
            logger.error(f"Error loading investor education content: {e}")
            return self._get_default_content()
    
    def _get_default_content(self) -> Dict[str, Any]:
        """Default education content when file is not available"""
        return {
            "misconceptions": {
                "cusip_vs_ticker": {
                    "title": "CUSIP vs Ticker Symbol",
                    "description": "CUSIP numbers and ticker symbols are different identifiers for securities",
                    "examples": [
                        "CUSIP is a 9-character alphanumeric code (e.g., 037833100 for Apple)",
                        "Ticker is a short abbreviation (e.g., AAPL for Apple)",
                        "You cannot trade using CUSIP numbers - use ticker symbols instead"
                    ]
                },
                "distribution_vs_dividend": {
                    "title": "Distribution vs Dividend",
                    "description": "Distributions and dividends have important tax differences",
                    "examples": [
                        "Dividends: Taxable income from corporations (qualified or ordinary)",
                        "Distributions: Payments from REITs, MLPs, or funds (may include return of capital)",
                        "Return of capital: Not immediately taxable, reduces cost basis"
                    ]
                }
            }
        }
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for detecting misconceptions"""
        return {
            "cusip_as_ticker": re.compile(r'\b[A-Z0-9]{9}\b', re.IGNORECASE),
            "cusip_mention": re.compile(r'\bcusip\b', re.IGNORECASE),
            "distribution_confusion": re.compile(r'\b(distribution|ROC|return of capital)\b', re.IGNORECASE),
            "dividend_mention": re.compile(r'\bdividend\b', re.IGNORECASE)
        }
    
    def detect_misconceptions(self, user_query: str) -> List[Dict[str, Any]]:
        """
        Detect potential misconceptions in user query
        
        Args:
            user_query: User's question or statement
            
        Returns:
            List of detected misconceptions with educational content
        """
        detected = []
        
        # Check for CUSIP confusion
        if self._detect_cusip_confusion(user_query):
            detected.append({
                "type": "cusip_vs_ticker",
                "severity": "high",
                "content": self.education_content["misconceptions"].get("cusip_vs_ticker", {}),
                "recommendation": "Use ticker symbols (e.g., AAPL, MSFT) instead of CUSIP numbers for stock queries"
            })
        
        # Check for distribution vs dividend confusion
        if self._detect_distribution_confusion(user_query):
            detected.append({
                "type": "distribution_vs_dividend",
                "severity": "medium",
                "content": self.education_content["misconceptions"].get("distribution_vs_dividend", {}),
                "recommendation": "Be aware of tax differences between qualified dividends and distributions (including ROC)"
            })
        
        return detected
    
    def _detect_cusip_confusion(self, query: str) -> bool:
        """Detect if user is confusing CUSIP with ticker"""
        has_cusip_pattern = bool(self.misconception_patterns["cusip_as_ticker"].search(query))
        mentions_cusip = bool(self.misconception_patterns["cusip_mention"].search(query))
        
        # If they mention CUSIP or use a 9-char alphanumeric code, flag it
        return has_cusip_pattern or mentions_cusip
    
    def _detect_distribution_confusion(self, query: str) -> bool:
        """Detect if user might be confused about distributions vs dividends"""
        has_distribution = bool(self.misconception_patterns["distribution_confusion"].search(query))
        has_dividend = bool(self.misconception_patterns["dividend_mention"].search(query))
        
        # If both terms appear, there might be confusion
        return has_distribution and has_dividend
    
    def get_educational_snippet(self, misconception_type: str) -> Optional[Dict[str, Any]]:
        """
        Get educational content for a specific misconception type
        
        Args:
            misconception_type: Type of misconception (e.g., 'cusip_vs_ticker')
            
        Returns:
            Educational content dictionary or None
        """
        return self.education_content["misconceptions"].get(misconception_type)
    
    def format_education_response(self, misconceptions: List[Dict[str, Any]]) -> str:
        """
        Format detected misconceptions into a user-friendly response
        
        Args:
            misconceptions: List of detected misconceptions
            
        Returns:
            Formatted markdown string
        """
        if not misconceptions:
            return ""
        
        response = "\n\n### 📚 Educational Notes\n\n"
        
        for item in misconceptions:
            content = item.get("content", {})
            title = content.get("title", "Important Note")
            description = content.get("description", "")
            examples = content.get("examples", [])
            recommendation = item.get("recommendation", "")
            
            response += f"**{title}**\n\n"
            response += f"{description}\n\n"
            
            if examples:
                response += "Key points:\n"
                for example in examples:
                    response += f"- {example}\n"
                response += "\n"
            
            if recommendation:
                response += f"💡 *{recommendation}*\n\n"
        
        return response
    
    def enhance_query_with_education(self, user_query: str) -> Dict[str, Any]:
        """
        Analyze query and return both the query and any educational notes
        
        Args:
            user_query: Original user query
            
        Returns:
            Dictionary with query analysis and educational content
        """
        misconceptions = self.detect_misconceptions(user_query)
        
        return {
            "original_query": user_query,
            "has_misconceptions": len(misconceptions) > 0,
            "misconceptions": misconceptions,
            "educational_response": self.format_education_response(misconceptions) if misconceptions else None
        }
