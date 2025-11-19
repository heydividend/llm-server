"""
RLHF Dataset Builder for Harvey Continuous Learning Pipeline

Converts analyzed feedback into fine-tuning datasets for OpenAI models.

Features:
- Build preference pairs (chosen vs rejected responses)
- Format for OpenAI fine-tuning API (JSONL)
- Create reward model training data
- Apply privacy filters (PII removal)
- Apply governance filters (toxic content)
- Quality checks and validation
"""

import logging
import json
import uuid
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from sqlalchemy import text
from app.core.database import engine

logger = logging.getLogger("rlhf_dataset_builder")


class RLHFDatasetBuilder:
    """
    Builds RLHF training datasets from analyzed feedback.
    
    Creates three types of training samples:
    1. Preference pairs: Chosen (positive) vs Rejected (negative) responses
    2. Demonstrations: High-quality positive examples only
    3. Rejections: Negative examples with improvement guidance
    """
    
    # PII patterns to detect and remove
    PII_PATTERNS = [
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),  # Email
        (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]'),  # Phone
        (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]'),  # SSN
        (r'\b\d{13,19}\b', '[CARD]'),  # Credit card
        (r'\b\d{5}(?:-\d{4})?\b', '[ZIP]'),  # ZIP code
    ]
    
    # Toxic keywords (basic filter)
    TOXIC_KEYWORDS = [
        'fuck', 'shit', 'damn', 'bitch', 'asshole', 'idiot', 'stupid',
        'kill yourself', 'kys', 'hate you'
    ]
    
    def __init__(self):
        self.logger = logger
    
    def build_preference_pair(
        self,
        positive_feedback: Dict[str, Any],
        negative_feedback: Dict[str, Any],
        positive_analysis: Optional[Dict[str, Any]] = None,
        negative_analysis: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Build a preference pair from positive and negative feedback.
        
        Args:
            positive_feedback: Positive feedback item
            negative_feedback: Negative feedback item
            positive_analysis: Gemini analysis of positive feedback
            negative_analysis: Gemini analysis of negative feedback
        
        Returns:
            Preference pair dictionary or None if filtered
        """
        try:
            # Extract prompts and responses
            chosen_prompt = positive_feedback.get('user_query', '')
            chosen_response = positive_feedback.get('harvey_response', '')
            rejected_prompt = negative_feedback.get('user_query', '')
            rejected_response = negative_feedback.get('harvey_response', '')
            
            # Apply privacy filtering
            chosen_prompt, chosen_pii = self._filter_pii(chosen_prompt)
            chosen_response, chosen_resp_pii = self._filter_pii(chosen_response)
            rejected_prompt, rejected_pii = self._filter_pii(rejected_prompt)
            rejected_response, rejected_resp_pii = self._filter_pii(rejected_response)
            
            pii_detected = chosen_pii or chosen_resp_pii or rejected_pii or rejected_resp_pii
            
            # Apply toxicity filtering
            toxic_chosen = self._check_toxicity(chosen_prompt + ' ' + chosen_response)
            toxic_rejected = self._check_toxicity(rejected_prompt + ' ' + rejected_response)
            toxic_detected = toxic_chosen or toxic_rejected
            
            # Quality checks
            if not chosen_prompt or not chosen_response:
                return None
            
            if not rejected_prompt or not rejected_response:
                return None
            
            # Calculate quality score
            quality_score = self._calculate_pair_quality(
                positive_feedback,
                negative_feedback,
                positive_analysis,
                negative_analysis
            )
            
            # Build preference pair
            pair = {
                'sample_type': 'preference_pair',
                'chosen_feedback_id': positive_feedback.get('feedback_id'),
                'chosen_prompt': chosen_prompt,
                'chosen_response': chosen_response,
                'chosen_rating': positive_feedback.get('rating', 5) / 5.0,
                'rejected_feedback_id': negative_feedback.get('feedback_id'),
                'rejected_prompt': rejected_prompt,
                'rejected_response': rejected_response,
                'rejected_rating': negative_feedback.get('rating', 1) / 5.0,
                'query_type': positive_feedback.get('query_type', 'unknown'),
                'category': positive_analysis.get('category') if positive_analysis else None,
                'quality_score': quality_score,
                'pii_filtered': pii_detected,
                'toxicity_filtered': toxic_detected,
                'ready_for_training': quality_score >= 0.6 and not toxic_detected
            }
            
            # Generate OpenAI format
            pair['openai_format'] = self._format_for_openai_preference(pair)
            
            return pair
        
        except Exception as e:
            self.logger.error(f"Failed to build preference pair: {e}")
            return None
    
    def build_demonstration(
        self,
        positive_feedback: Dict[str, Any],
        analysis: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Build a demonstration sample from positive feedback.
        
        Args:
            positive_feedback: Positive feedback item
            analysis: Gemini analysis
        
        Returns:
            Demonstration sample or None if filtered
        """
        try:
            prompt = positive_feedback.get('user_query', '')
            response = positive_feedback.get('harvey_response', '')
            
            # Apply filters
            prompt, pii_prompt = self._filter_pii(prompt)
            response, pii_response = self._filter_pii(response)
            pii_detected = pii_prompt or pii_response
            
            toxic_detected = self._check_toxicity(prompt + ' ' + response)
            
            # Quality checks
            if not prompt or not response:
                return None
            
            if len(prompt) < 10 or len(response) < 20:
                return None
            
            # Calculate quality
            rating = positive_feedback.get('rating', 5)
            training_worthiness = analysis.get('training_worthiness', 0.8) if analysis else 0.8
            quality_score = (rating / 5.0 + training_worthiness) / 2.0
            
            # Build demonstration
            demo = {
                'sample_type': 'demonstration',
                'chosen_feedback_id': positive_feedback.get('feedback_id'),
                'chosen_prompt': prompt,
                'chosen_response': response,
                'chosen_rating': rating / 5.0,
                'rejected_feedback_id': None,
                'rejected_prompt': None,
                'rejected_response': None,
                'rejected_rating': None,
                'query_type': positive_feedback.get('query_type', 'unknown'),
                'category': analysis.get('category') if analysis else None,
                'quality_score': quality_score,
                'pii_filtered': pii_detected,
                'toxicity_filtered': toxic_detected,
                'ready_for_training': quality_score >= 0.7 and not toxic_detected
            }
            
            # Generate OpenAI format
            demo['openai_format'] = self._format_for_openai_demonstration(demo)
            
            return demo
        
        except Exception as e:
            self.logger.error(f"Failed to build demonstration: {e}")
            return None
    
    def _filter_pii(self, text: str) -> Tuple[str, bool]:
        """
        Remove PII from text.
        
        Returns:
            (filtered_text, pii_detected)
        """
        if not text:
            return text, False
        
        pii_detected = False
        filtered = text
        
        for pattern, replacement in self.PII_PATTERNS:
            if re.search(pattern, filtered):
                pii_detected = True
                filtered = re.sub(pattern, replacement, filtered)
        
        return filtered, pii_detected
    
    def _check_toxicity(self, text: str) -> bool:
        """Check for toxic content (basic keyword filter)."""
        if not text:
            return False
        
        text_lower = text.lower()
        for keyword in self.TOXIC_KEYWORDS:
            if keyword in text_lower:
                return True
        
        return False
    
    def _calculate_pair_quality(
        self,
        positive: Dict[str, Any],
        negative: Dict[str, Any],
        pos_analysis: Optional[Dict[str, Any]],
        neg_analysis: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate quality score for a preference pair."""
        
        # Base quality from ratings
        pos_rating = positive.get('rating', 5) / 5.0
        neg_rating = negative.get('rating', 1) / 5.0
        rating_diff = pos_rating - neg_rating
        
        # Training worthiness from Gemini analysis
        pos_worthiness = pos_analysis.get('training_worthiness', 0.7) if pos_analysis else 0.7
        neg_worthiness = neg_analysis.get('training_worthiness', 0.3) if neg_analysis else 0.3
        
        # Quality is average of rating difference and training worthiness
        quality = (rating_diff + pos_worthiness + (1.0 - neg_worthiness)) / 3.0
        
        return round(quality, 3)
    
    def _format_for_openai_preference(self, pair: Dict[str, Any]) -> str:
        """
        Format preference pair for OpenAI fine-tuning API.
        
        Uses DPO (Direct Preference Optimization) format.
        """
        openai_obj = {
            "prompt": pair['chosen_prompt'],
            "chosen": pair['chosen_response'],
            "rejected": pair['rejected_response'],
            "metadata": {
                "query_type": pair.get('query_type'),
                "category": pair.get('category'),
                "quality_score": pair.get('quality_score')
            }
        }
        
        return json.dumps(openai_obj)
    
    def _format_for_openai_demonstration(self, demo: Dict[str, Any]) -> str:
        """Format demonstration for OpenAI fine-tuning API."""
        openai_obj = {
            "messages": [
                {"role": "user", "content": demo['chosen_prompt']},
                {"role": "assistant", "content": demo['chosen_response']}
            ],
            "metadata": {
                "query_type": demo.get('query_type'),
                "category": demo.get('category'),
                "quality_score": demo.get('quality_score')
            }
        }
        
        return json.dumps(openai_obj)
    
    def save_sample(self, sample: Dict[str, Any]) -> str:
        """
        Save training sample to database.
        
        Args:
            sample: Sample dictionary
        
        Returns:
            Sample ID
        """
        try:
            sample_id = f"sample_{uuid.uuid4().hex[:12]}"
            
            with engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO fine_tuning_samples (
                            sample_id, sample_type,
                            chosen_feedback_id, chosen_prompt, chosen_response, chosen_rating,
                            rejected_feedback_id, rejected_prompt, rejected_response, rejected_rating,
                            query_type, category,
                            quality_score, pii_filtered, toxicity_filtered, ready_for_training,
                            openai_format, created_at
                        ) VALUES (
                            :sample_id, :sample_type,
                            :chosen_feedback_id, :chosen_prompt, :chosen_response, :chosen_rating,
                            :rejected_feedback_id, :rejected_prompt, :rejected_response, :rejected_rating,
                            :query_type, :category,
                            :quality_score, :pii_filtered, :toxicity_filtered, :ready_for_training,
                            :openai_format, :created_at
                        )
                    """),
                    {
                        'sample_id': sample_id,
                        'sample_type': sample['sample_type'],
                        'chosen_feedback_id': sample.get('chosen_feedback_id'),
                        'chosen_prompt': sample.get('chosen_prompt'),
                        'chosen_response': sample.get('chosen_response'),
                        'chosen_rating': sample.get('chosen_rating'),
                        'rejected_feedback_id': sample.get('rejected_feedback_id'),
                        'rejected_prompt': sample.get('rejected_prompt'),
                        'rejected_response': sample.get('rejected_response'),
                        'rejected_rating': sample.get('rejected_rating'),
                        'query_type': sample.get('query_type'),
                        'category': sample.get('category'),
                        'quality_score': sample.get('quality_score'),
                        'pii_filtered': 1 if sample.get('pii_filtered') else 0,
                        'toxicity_filtered': 1 if sample.get('toxicity_filtered') else 0,
                        'ready_for_training': 1 if sample.get('ready_for_training') else 0,
                        'openai_format': sample.get('openai_format'),
                        'created_at': datetime.now()
                    }
                )
            
            self.logger.info(f"Saved {sample['sample_type']} sample {sample_id}")
            return sample_id
        
        except Exception as e:
            self.logger.error(f"Failed to save sample: {e}")
            return ""
    
    def export_for_fine_tuning(
        self,
        output_file: str,
        sample_type: Optional[str] = None,
        min_quality: float = 0.6,
        limit: Optional[int] = None
    ) -> int:
        """
        Export training samples to JSONL file for OpenAI fine-tuning.
        
        Args:
            output_file: Path to output JSONL file
            sample_type: Filter by sample type
            min_quality: Minimum quality score
            limit: Maximum samples to export
        
        Returns:
            Number of samples exported
        """
        try:
            # Build query
            where_clauses = [
                "ready_for_training = 1",
                "used_in_training = 0",
                f"quality_score >= {min_quality}"
            ]
            
            if sample_type:
                where_clauses.append(f"sample_type = '{sample_type}'")
            
            where_clause = " AND ".join(where_clauses)
            limit_clause = f"TOP {limit}" if limit else ""
            
            query = f"""
                SELECT {limit_clause} openai_format
                FROM fine_tuning_samples
                WHERE {where_clause}
                ORDER BY quality_score DESC, created_at DESC
            """
            
            with engine.connect() as conn:
                result = conn.execute(text(query))
                
                count = 0
                with open(output_file, 'w', encoding='utf-8') as f:
                    for row in result:
                        f.write(row[0] + '\n')
                        count += 1
                
                self.logger.info(f"Exported {count} samples to {output_file}")
                return count
        
        except Exception as e:
            self.logger.error(f"Failed to export samples: {e}")
            return 0
    
    def get_dataset_statistics(self) -> Dict[str, Any]:
        """Get statistics about available training samples."""
        try:
            query = """
                SELECT 
                    sample_type,
                    COUNT(*) as total,
                    SUM(CASE WHEN ready_for_training = 1 THEN 1 ELSE 0 END) as ready,
                    SUM(CASE WHEN used_in_training = 1 THEN 1 ELSE 0 END) as used,
                    AVG(quality_score) as avg_quality,
                    SUM(CASE WHEN pii_filtered = 1 THEN 1 ELSE 0 END) as pii_filtered,
                    SUM(CASE WHEN toxicity_filtered = 1 THEN 1 ELSE 0 END) as toxic_filtered
                FROM fine_tuning_samples
                GROUP BY sample_type
            """
            
            with engine.connect() as conn:
                result = conn.execute(text(query)).fetchall()
                
                stats = {
                    'by_type': {},
                    'total': 0,
                    'ready': 0,
                    'used': 0
                }
                
                for row in result:
                    sample_type = row[0]
                    stats['by_type'][sample_type] = {
                        'total': row[1],
                        'ready': row[2],
                        'used': row[3],
                        'avg_quality': round(float(row[4] or 0), 3),
                        'pii_filtered': row[5],
                        'toxic_filtered': row[6]
                    }
                    stats['total'] += row[1]
                    stats['ready'] += row[2]
                    stats['used'] += row[3]
                
                return stats
        
        except Exception as e:
            self.logger.error(f"Failed to get dataset statistics: {e}")
            return {}


# Global instance
rlhf_dataset_builder = RLHFDatasetBuilder()
