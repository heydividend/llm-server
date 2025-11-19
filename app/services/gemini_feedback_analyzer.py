"""
Gemini Feedback Analyzer for Harvey Continuous Learning Pipeline

Uses Gemini 2.0 Flash to analyze user feedback and extract insights
for improving Harvey's responses.

Features:
- Analyze WHY feedback was positive or negative
- Categorize feedback by topic (accuracy, helpfulness, tone, etc.)
- Extract improvement suggestions
- Detect patterns in highly-rated vs poorly-rated responses
- Generate structured labels for supervised learning
- Privacy: Detect and flag PII
- Governance: Detect toxic/inappropriate content
"""

import logging
import json
import uuid
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy import text
from app.core.database import engine
from app.services.gemini_client import get_gemini_client

logger = logging.getLogger("gemini_feedback_analyzer")


class GeminiFeedbackAnalyzer:
    """
    Analyzes user feedback using Gemini AI to extract insights for learning.
    
    Uses structured prompts to:
    - Categorize feedback
    - Identify strengths and weaknesses
    - Generate improvement suggestions
    - Detect PII and toxic content
    - Assess training worthiness
    """
    
    def __init__(self):
        self.gemini_client = get_gemini_client()
        self.logger = logger
        
        # Cost tracking
        self.total_api_calls = 0
        self.total_tokens = 0
    
    def analyze_feedback(
        self,
        feedback_data: Dict[str, Any],
        include_conversation: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze a single feedback item using Gemini.
        
        Args:
            feedback_data: Feedback dictionary from ETL service
            include_conversation: Include conversation context in analysis
        
        Returns:
            Analysis results with categories, insights, and labels
        """
        try:
            # Build analysis prompt
            prompt = self._build_analysis_prompt(feedback_data, include_conversation)
            
            # Call Gemini
            self.total_api_calls += 1
            response = self.gemini_client.generate_text(
                prompt=prompt,
                temperature=0.3,  # Lower temperature for consistent analysis
                max_tokens=1024,
                use_cache=False  # Don't cache feedback analysis
            )
            
            # Track tokens
            self.total_tokens += response.get('usage', {}).get('total_tokens', 0)
            
            # Parse response
            analysis = self._parse_analysis_response(response['text'])
            
            # Add metadata
            analysis['feedback_id'] = feedback_data['feedback_id']
            analysis['analyzed_by'] = response['model']
            analysis['analysis_tokens'] = response.get('usage', {}).get('total_tokens', 0)
            analysis['analysis_latency_ms'] = response.get('latency_ms', 0)
            
            self.logger.info(
                f"Analyzed feedback {feedback_data['feedback_id']} "
                f"(category: {analysis.get('category')}, "
                f"training_worthiness: {analysis.get('training_worthiness')})"
            )
            
            return analysis
        
        except Exception as e:
            self.logger.error(f"Failed to analyze feedback {feedback_data.get('feedback_id')}: {e}")
            return {
                'error': str(e),
                'feedback_id': feedback_data.get('feedback_id')
            }
    
    def _build_analysis_prompt(
        self,
        feedback_data: Dict[str, Any],
        include_conversation: bool
    ) -> str:
        """Build structured prompt for Gemini analysis."""
        
        # Conversation context
        conversation_text = ""
        if include_conversation and feedback_data.get('conversation_context'):
            messages = feedback_data['conversation_context']
            conversation_text = "\n".join([
                f"{msg['role'].upper()}: {msg['content'][:200]}"
                for msg in messages[-5:]  # Last 5 messages
            ])
        
        prompt = f"""You are an AI feedback analyst for Harvey, a financial AI assistant specializing in dividend investing.

Analyze the following user feedback to understand why the user rated the response positively or negatively, and extract insights for improving Harvey's responses.

**USER QUERY:**
{feedback_data['query']}

**HARVEY'S RESPONSE:**
{feedback_data['response'][:1000]}

**FEEDBACK:**
- Sentiment: {feedback_data['sentiment']}
- Rating: {feedback_data.get('rating', 'N/A')}/5
- User Comment: {feedback_data.get('user_comment', 'None')}
- Tags: {', '.join(feedback_data.get('tags', []))}
- Query Type: {feedback_data.get('query_type', 'unknown')}
"""

        if conversation_text:
            prompt += f"""
**CONVERSATION CONTEXT:**
{conversation_text}
"""

        prompt += """
**ANALYSIS INSTRUCTIONS:**

Provide a structured analysis in the following JSON format:

{
  "category": "<primary category: accuracy | helpfulness | tone | completeness | relevance>",
  "sentiment_reason": "<Why was this feedback positive or negative? Be specific.>",
  "improvement_suggestions": "<Specific suggestions for improving this type of response>",
  "response_strengths": ["<strength1>", "<strength2>", ...],
  "response_weaknesses": ["<weakness1>", "<weakness2>", ...],
  "primary_topic": "<main topic: dividend_analysis | portfolio_advice | tax_planning | etc>",
  "subtopics": ["<subtopic1>", "<subtopic2>", ...],
  "training_worthiness": <0.0-1.0: how valuable is this feedback for training?>,
  "pii_detected": <true|false: does response contain personal info like emails, phone, SSN?>,
  "toxic_content": <true|false: does response contain toxic/inappropriate content?>
}

**GUIDELINES:**
1. Be objective and analytical
2. Focus on actionable insights
3. Consider context from the conversation
4. Identify specific patterns that led to the rating
5. Flag any privacy concerns (PII) or inappropriate content
6. Training worthiness: 1.0 = perfect training example, 0.0 = not useful

Provide ONLY the JSON response, no other text.
"""
        
        return prompt
    
    def _parse_analysis_response(self, text: str) -> Dict[str, Any]:
        """Parse Gemini's JSON response into structured analysis."""
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                # Try to find JSON object directly
                json_match = re.search(r'\{.*\}', text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(0)
                else:
                    json_text = text
            
            analysis = json.loads(json_text)
            
            # Validate required fields
            required = ['category', 'sentiment_reason', 'training_worthiness']
            for field in required:
                if field not in analysis:
                    self.logger.warning(f"Missing required field: {field}")
                    analysis[field] = None if field != 'training_worthiness' else 0.0
            
            # Ensure lists
            for list_field in ['response_strengths', 'response_weaknesses', 'subtopics']:
                if list_field not in analysis or not isinstance(analysis[list_field], list):
                    analysis[list_field] = []
            
            # Ensure booleans
            for bool_field in ['pii_detected', 'toxic_content']:
                if bool_field not in analysis:
                    analysis[bool_field] = False
            
            return analysis
        
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse Gemini JSON response: {e}")
            self.logger.debug(f"Raw response: {text}")
            
            # Return minimal valid structure
            return {
                'category': 'unknown',
                'sentiment_reason': 'Failed to parse analysis',
                'improvement_suggestions': '',
                'response_strengths': [],
                'response_weaknesses': [],
                'primary_topic': 'unknown',
                'subtopics': [],
                'training_worthiness': 0.0,
                'pii_detected': False,
                'toxic_content': False,
                'parse_error': str(e)
            }
    
    def save_analysis(self, analysis: Dict[str, Any]) -> str:
        """
        Save analysis to feedback_labels table.
        
        Args:
            analysis: Analysis results from analyze_feedback()
        
        Returns:
            Label ID
        """
        try:
            label_id = f"label_{uuid.uuid4().hex[:12]}"
            
            with engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO feedback_labels (
                            label_id, feedback_id, category, sentiment_reason,
                            improvement_suggestions, response_strengths, response_weaknesses,
                            primary_topic, subtopics, training_worthiness,
                            pii_detected, toxic_content, analyzed_by,
                            analysis_tokens, analysis_latency_ms, created_at
                        ) VALUES (
                            :label_id, :feedback_id, :category, :sentiment_reason,
                            :improvement_suggestions, :response_strengths, :response_weaknesses,
                            :primary_topic, :subtopics, :training_worthiness,
                            :pii_detected, :toxic_content, :analyzed_by,
                            :analysis_tokens, :analysis_latency_ms, :created_at
                        )
                    """),
                    {
                        'label_id': label_id,
                        'feedback_id': analysis['feedback_id'],
                        'category': analysis.get('category', 'unknown'),
                        'sentiment_reason': analysis.get('sentiment_reason', ''),
                        'improvement_suggestions': analysis.get('improvement_suggestions', ''),
                        'response_strengths': json.dumps(analysis.get('response_strengths', [])),
                        'response_weaknesses': json.dumps(analysis.get('response_weaknesses', [])),
                        'primary_topic': analysis.get('primary_topic', 'unknown'),
                        'subtopics': json.dumps(analysis.get('subtopics', [])),
                        'training_worthiness': analysis.get('training_worthiness', 0.0),
                        'pii_detected': 1 if analysis.get('pii_detected') else 0,
                        'toxic_content': 1 if analysis.get('toxic_content') else 0,
                        'analyzed_by': analysis.get('analyzed_by', 'gemini-2.0-flash-exp'),
                        'analysis_tokens': analysis.get('analysis_tokens', 0),
                        'analysis_latency_ms': analysis.get('analysis_latency_ms', 0),
                        'created_at': datetime.now()
                    }
                )
            
            self.logger.info(f"Saved analysis as {label_id}")
            return label_id
        
        except Exception as e:
            self.logger.error(f"Failed to save analysis: {e}")
            return ""
    
    def analyze_batch(
        self,
        feedback_items: List[Dict[str, Any]],
        max_items: Optional[int] = None,
        save_results: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple feedback items in batch.
        
        Args:
            feedback_items: List of feedback dictionaries
            max_items: Maximum items to analyze (cost control)
            save_results: Save analyses to database
        
        Returns:
            List of analysis results
        """
        if max_items:
            feedback_items = feedback_items[:max_items]
        
        self.logger.info(f"Starting batch analysis of {len(feedback_items)} feedback items")
        
        analyses = []
        for i, feedback in enumerate(feedback_items, 1):
            self.logger.info(f"Analyzing {i}/{len(feedback_items)}: {feedback.get('feedback_id')}")
            
            analysis = self.analyze_feedback(feedback)
            analyses.append(analysis)
            
            # Save if requested
            if save_results and not analysis.get('error'):
                self.save_analysis(analysis)
        
        self.logger.info(
            f"Batch analysis complete: {len(analyses)} items analyzed "
            f"({self.total_api_calls} API calls, {self.total_tokens} tokens)"
        )
        
        return analyses
    
    def get_analysis_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        Get summary of analyzed feedback.
        
        Args:
            days: Look back N days
        
        Returns:
            Summary statistics
        """
        try:
            query = """
                SELECT 
                    COUNT(*) as total_analyzed,
                    AVG(training_worthiness) as avg_training_worthiness,
                    COUNT(DISTINCT category) as unique_categories,
                    SUM(CASE WHEN pii_detected = 1 THEN 1 ELSE 0 END) as pii_count,
                    SUM(CASE WHEN toxic_content = 1 THEN 1 ELSE 0 END) as toxic_count,
                    SUM(analysis_tokens) as total_tokens
                FROM feedback_labels
                WHERE created_at >= DATEADD(DAY, -:days, GETDATE())
            """
            
            with engine.connect() as conn:
                result = conn.execute(text(query), {"days": days}).first()
                
                if result:
                    # Get category breakdown
                    category_query = """
                        SELECT category, COUNT(*) as count
                        FROM feedback_labels
                        WHERE created_at >= DATEADD(DAY, -:days, GETDATE())
                        GROUP BY category
                        ORDER BY count DESC
                    """
                    category_result = conn.execute(text(category_query), {"days": days}).fetchall()
                    
                    return {
                        'total_analyzed': result[0] or 0,
                        'avg_training_worthiness': round(float(result[1] or 0), 3),
                        'unique_categories': result[2] or 0,
                        'pii_detected_count': result[3] or 0,
                        'toxic_content_count': result[4] or 0,
                        'total_tokens_used': result[5] or 0,
                        'category_breakdown': {
                            row[0]: row[1] for row in category_result
                        }
                    }
            
            return {}
        
        except Exception as e:
            self.logger.error(f"Failed to get analysis summary: {e}")
            return {}


# Global instance
gemini_feedback_analyzer = GeminiFeedbackAnalyzer()
