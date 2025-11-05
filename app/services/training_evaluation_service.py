"""
Training Evaluation Service
Evaluates the quality of Harvey's responses based on defined metrics and targets.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import re
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("training_evaluation")


class ExpertiseLevel(Enum):
    """Investor expertise levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ScoreLabel(Enum):
    """Score quality labels."""
    EXCELLENT = "excellent"  # >= 0.90
    GOOD = "good"           # >= 0.80
    FAIR = "fair"           # >= 0.70
    POOR = "poor"           # < 0.70


@dataclass
class EvaluationMetrics:
    """Evaluation metrics for a response."""
    clarity_score: float
    completeness_score: float
    actionability_score: float
    overall_score: float
    label: ScoreLabel
    expertise_level: ExpertiseLevel
    passes_threshold: bool
    feedback: List[str]


class TrainingEvaluationService:
    """
    Evaluates training responses against quality targets.
    Ensures Harvey's responses meet high standards for clarity, completeness, and actionability.
    """
    
    def __init__(self):
        """Initialize with evaluation targets."""
        self.targets = {
            "global": {
                "clear_score_min": 0.9,
                "complete_score_min": 0.85,
                "actionable_score_min": 0.9
            },
            "per_level": {
                "beginner": {
                    "clear_min": 0.92,
                    "complete_min": 0.80,
                    "actionable_min": 0.92
                },
                "intermediate": {
                    "clear_min": 0.90,
                    "complete_min": 0.86,
                    "actionable_min": 0.90
                },
                "advanced": {
                    "clear_min": 0.88,
                    "complete_min": 0.90,
                    "actionable_min": 0.88
                }
            }
        }
        logger.info("Training Evaluation Service initialized with quality targets")
    
    def evaluate_response(
        self,
        question: str,
        response: str,
        expertise_level: ExpertiseLevel,
        model_name: str = None
    ) -> EvaluationMetrics:
        """
        Evaluate a single response against quality metrics.
        
        Args:
            question: The question that was asked
            response: The model's response
            expertise_level: Target expertise level
            model_name: Optional model that generated the response
            
        Returns:
            EvaluationMetrics with scores and feedback
        """
        # Calculate individual metrics
        clarity_score = self._evaluate_clarity(response, expertise_level)
        completeness_score = self._evaluate_completeness(question, response, expertise_level)
        actionability_score = self._evaluate_actionability(response, expertise_level)
        
        # Calculate overall score
        overall_score = (clarity_score * 0.3 + 
                        completeness_score * 0.35 + 
                        actionability_score * 0.35)
        
        # Determine label
        label = self._get_score_label(overall_score)
        
        # Check if passes thresholds
        level_targets = self.targets["per_level"][expertise_level.value]
        passes_threshold = (
            clarity_score >= level_targets["clear_min"] and
            completeness_score >= level_targets["complete_min"] and
            actionability_score >= level_targets["actionable_min"]
        )
        
        # Generate feedback
        feedback = self._generate_feedback(
            clarity_score, completeness_score, actionability_score,
            level_targets, expertise_level
        )
        
        # Log evaluation
        logger.debug(f"Evaluated response - Model: {model_name}, Overall: {overall_score:.2f}, "
                    f"Passes: {passes_threshold}")
        
        return EvaluationMetrics(
            clarity_score=clarity_score,
            completeness_score=completeness_score,
            actionability_score=actionability_score,
            overall_score=overall_score,
            label=label,
            expertise_level=expertise_level,
            passes_threshold=passes_threshold,
            feedback=feedback
        )
    
    def _evaluate_clarity(self, response: str, expertise_level: ExpertiseLevel) -> float:
        """
        Evaluate clarity of the response.
        
        Factors:
        - Clear structure and formatting
        - Appropriate language for expertise level
        - Logical flow
        - No jargon overload for beginners
        """
        score = 1.0
        
        # Check for structure (headers, bullets, numbered lists)
        has_structure = bool(re.search(r'(^#{1,3}\s|\n\d+\.\s|\n[-*]\s)', response, re.MULTILINE))
        if not has_structure:
            score -= 0.15
        
        # Check for clear sections
        has_sections = bool(re.search(r'(#{2,3}\s|\*\*[^*]+\*\*:)', response))
        if has_sections:
            score += 0.05
        
        # Check sentence complexity based on expertise level
        avg_sentence_length = len(response.split()) / max(len(response.split('.')), 1)
        
        if expertise_level == ExpertiseLevel.BEGINNER:
            if avg_sentence_length > 25:  # Too complex for beginners
                score -= 0.1
            # Check for unexplained jargon
            jargon_terms = ['yield curve', 'ex-dividend', 'payout ratio', 'P/E', 'DRIP', 'REITs']
            unexplained_jargon = sum(1 for term in jargon_terms if term in response and f"({term}" not in response)
            score -= min(unexplained_jargon * 0.05, 0.2)
            
        elif expertise_level == ExpertiseLevel.ADVANCED:
            if avg_sentence_length < 10:  # Too simple for advanced
                score -= 0.05
        
        # Check for formatting issues
        if '```' in response:  # Has code blocks
            score += 0.05
        if '|' in response and '---' in response:  # Has tables
            score += 0.05
        
        # Ensure score is within bounds
        return max(0.0, min(1.0, score))
    
    def _evaluate_completeness(self, question: str, response: str, expertise_level: ExpertiseLevel) -> float:
        """
        Evaluate completeness of the response.
        
        Factors:
        - Addresses all parts of the question
        - Provides sufficient detail for expertise level
        - Includes relevant examples
        - Covers risks/considerations
        """
        score = 1.0
        
        # Check response length relative to question complexity
        question_complexity = len(question.split())
        response_length = len(response.split())
        
        if expertise_level == ExpertiseLevel.BEGINNER:
            if response_length < question_complexity * 5:
                score -= 0.15
        elif expertise_level == ExpertiseLevel.INTERMEDIATE:
            if response_length < question_complexity * 7:
                score -= 0.1
        elif expertise_level == ExpertiseLevel.ADVANCED:
            if response_length < question_complexity * 10:
                score -= 0.1
        
        # Check for key dividend investing components
        key_components = {
            'yield': r'(yield|dividend yield|current yield)',
            'risk': r'(risk|volatility|drawdown|safety)',
            'growth': r'(growth|appreciation|compound)',
            'tax': r'(tax|qualified|ordinary income)',
            'strategy': r'(strategy|approach|portfolio|allocation)'
        }
        
        components_mentioned = sum(1 for pattern in key_components.values() 
                                   if re.search(pattern, response, re.IGNORECASE))
        
        # Expect more components for higher expertise levels
        expected_components = {
            ExpertiseLevel.BEGINNER: 2,
            ExpertiseLevel.INTERMEDIATE: 3,
            ExpertiseLevel.ADVANCED: 4
        }
        
        if components_mentioned < expected_components[expertise_level]:
            score -= 0.15
        
        # Check for examples or specific tickers
        has_examples = bool(re.search(r'\b[A-Z]{1,5}\b(?:\s|,|$)', response))  # Stock tickers
        if has_examples:
            score += 0.05
        
        # Check for numbers/data
        has_data = bool(re.search(r'\d+\.?\d*%|\$\d+', response))
        if has_data:
            score += 0.05
        
        # Check if risks are mentioned
        mentions_risks = bool(re.search(r'(risk|consideration|warning|caution|note)', response, re.IGNORECASE))
        if not mentions_risks and expertise_level == ExpertiseLevel.BEGINNER:
            score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def _evaluate_actionability(self, response: str, expertise_level: ExpertiseLevel) -> float:
        """
        Evaluate how actionable the response is.
        
        Factors:
        - Provides specific steps or recommendations
        - Includes concrete examples
        - Offers clear next actions
        - Appropriate complexity for expertise level
        """
        score = 1.0
        
        # Check for action words
        action_patterns = [
            r'(should|recommend|suggest|consider|start with|begin by)',
            r'(step \d+|first|second|then|next|finally)',
            r'(buy|sell|hold|allocate|invest|diversify)',
            r'(calculate|determine|evaluate|research|analyze)'
        ]
        
        action_count = sum(1 for pattern in action_patterns 
                          if re.search(pattern, response, re.IGNORECASE))
        
        if action_count < 2:
            score -= 0.2
        elif action_count >= 4:
            score += 0.05
        
        # Check for specific allocations or percentages
        has_allocations = bool(re.search(r'\d+%\s*(of|allocation|portfolio)', response))
        if has_allocations:
            score += 0.1
        
        # Check for timeline or milestones
        has_timeline = bool(re.search(r'(month|year|quarter|annual|timeline)', response, re.IGNORECASE))
        if has_timeline:
            score += 0.05
        
        # Expertise-specific checks
        if expertise_level == ExpertiseLevel.BEGINNER:
            # Should have simple, clear steps
            has_numbered_steps = bool(re.search(r'\n\d+\.', response))
            if has_numbered_steps:
                score += 0.1
            # Shouldn't be overwhelmingly complex
            if len(response.split('\n')) > 50:  # Too many points
                score -= 0.1
                
        elif expertise_level == ExpertiseLevel.ADVANCED:
            # Should have sophisticated strategies
            advanced_terms = ['correlation', 'beta', 'alpha', 'sharpe', 'option', 'derivative']
            has_advanced = any(term in response.lower() for term in advanced_terms)
            if has_advanced:
                score += 0.05
        
        # Check for tools/resources mentioned
        has_resources = bool(re.search(r'(calculator|screener|platform|broker|tool)', response, re.IGNORECASE))
        if has_resources:
            score += 0.05
        
        return max(0.0, min(1.0, score))
    
    def _get_score_label(self, score: float) -> ScoreLabel:
        """Convert numeric score to quality label."""
        if score >= 0.90:
            return ScoreLabel.EXCELLENT
        elif score >= 0.80:
            return ScoreLabel.GOOD
        elif score >= 0.70:
            return ScoreLabel.FAIR
        else:
            return ScoreLabel.POOR
    
    def _generate_feedback(
        self,
        clarity: float,
        completeness: float,
        actionability: float,
        targets: Dict[str, float],
        level: ExpertiseLevel
    ) -> List[str]:
        """Generate specific feedback for improvement."""
        feedback = []
        
        if clarity < targets["clear_min"]:
            feedback.append(f"Clarity ({clarity:.2f}) below target ({targets['clear_min']}). "
                          "Improve structure and use appropriate language for {level.value} level.")
        
        if completeness < targets["complete_min"]:
            feedback.append(f"Completeness ({completeness:.2f}) below target ({targets['complete_min']}). "
                          "Address all aspects of the question with sufficient detail.")
        
        if actionability < targets["actionable_min"]:
            feedback.append(f"Actionability ({actionability:.2f}) below target ({targets['actionable_min']}). "
                          "Provide more specific steps and recommendations.")
        
        if not feedback:
            feedback.append("Response meets all quality targets. Well done!")
        
        return feedback
    
    def evaluate_batch(
        self,
        responses: List[Dict[str, Any]],
        expertise_level: ExpertiseLevel = None
    ) -> Dict[str, Any]:
        """
        Evaluate a batch of responses and return aggregate statistics.
        
        Args:
            responses: List of response dictionaries with question, answer, model
            expertise_level: Optional level to evaluate at (otherwise auto-detect)
            
        Returns:
            Dictionary with aggregate statistics and individual evaluations
        """
        evaluations = []
        total_clarity = 0
        total_completeness = 0
        total_actionability = 0
        passing_count = 0
        
        for response_data in responses:
            # Determine expertise level
            level = expertise_level or self._detect_expertise_level(response_data.get("question", ""))
            
            # Evaluate
            metrics = self.evaluate_response(
                question=response_data.get("question", ""),
                response=response_data.get("answer", ""),
                expertise_level=level,
                model_name=response_data.get("model", "unknown")
            )
            
            evaluations.append({
                "question": response_data.get("question", "")[:100] + "...",
                "model": response_data.get("model", "unknown"),
                "metrics": metrics
            })
            
            # Aggregate scores
            total_clarity += metrics.clarity_score
            total_completeness += metrics.completeness_score
            total_actionability += metrics.actionability_score
            if metrics.passes_threshold:
                passing_count += 1
        
        # Calculate averages
        num_responses = len(responses)
        
        return {
            "summary": {
                "total_evaluated": num_responses,
                "passing_count": passing_count,
                "passing_rate": passing_count / num_responses if num_responses > 0 else 0,
                "avg_clarity": total_clarity / num_responses if num_responses > 0 else 0,
                "avg_completeness": total_completeness / num_responses if num_responses > 0 else 0,
                "avg_actionability": total_actionability / num_responses if num_responses > 0 else 0,
                "avg_overall": (total_clarity + total_completeness + total_actionability) / (3 * num_responses) 
                              if num_responses > 0 else 0
            },
            "by_model": self._aggregate_by_model(evaluations),
            "by_label": self._aggregate_by_label(evaluations),
            "evaluations": evaluations[:10]  # Return first 10 for inspection
        }
    
    def _detect_expertise_level(self, question: str) -> ExpertiseLevel:
        """Auto-detect expertise level from question content."""
        question_lower = question.lower()
        
        # Advanced indicators
        advanced_terms = ['correlation', 'beta', 'options', 'derivatives', 'tax loss', 'qualified dividends']
        if any(term in question_lower for term in advanced_terms):
            return ExpertiseLevel.ADVANCED
        
        # Beginner indicators
        beginner_terms = ['what is', 'how do i start', 'beginner', 'first time', 'new to']
        if any(term in question_lower for term in beginner_terms):
            return ExpertiseLevel.BEGINNER
        
        # Default to intermediate
        return ExpertiseLevel.INTERMEDIATE
    
    def _aggregate_by_model(self, evaluations: List[Dict]) -> Dict[str, Any]:
        """Aggregate evaluation results by model."""
        model_stats = {}
        
        for eval_data in evaluations:
            model = eval_data["model"]
            metrics = eval_data["metrics"]
            
            if model not in model_stats:
                model_stats[model] = {
                    "count": 0,
                    "passing": 0,
                    "total_clarity": 0,
                    "total_completeness": 0,
                    "total_actionability": 0
                }
            
            model_stats[model]["count"] += 1
            if metrics.passes_threshold:
                model_stats[model]["passing"] += 1
            model_stats[model]["total_clarity"] += metrics.clarity_score
            model_stats[model]["total_completeness"] += metrics.completeness_score
            model_stats[model]["total_actionability"] += metrics.actionability_score
        
        # Calculate averages
        for model, stats in model_stats.items():
            count = stats["count"]
            stats["passing_rate"] = stats["passing"] / count if count > 0 else 0
            stats["avg_clarity"] = stats["total_clarity"] / count if count > 0 else 0
            stats["avg_completeness"] = stats["total_completeness"] / count if count > 0 else 0
            stats["avg_actionability"] = stats["total_actionability"] / count if count > 0 else 0
            # Remove totals
            del stats["total_clarity"]
            del stats["total_completeness"]
            del stats["total_actionability"]
        
        return model_stats
    
    def _aggregate_by_label(self, evaluations: List[Dict]) -> Dict[str, int]:
        """Count evaluations by quality label."""
        label_counts = {
            ScoreLabel.EXCELLENT.value: 0,
            ScoreLabel.GOOD.value: 0,
            ScoreLabel.FAIR.value: 0,
            ScoreLabel.POOR.value: 0
        }
        
        for eval_data in evaluations:
            label = eval_data["metrics"].label.value
            label_counts[label] += 1
        
        return label_counts
    
    def export_high_quality_examples(
        self,
        evaluations: List[Dict],
        min_score: float = 0.9
    ) -> List[Dict[str, Any]]:
        """
        Export high-quality examples for fine-tuning.
        
        Args:
            evaluations: List of evaluated responses
            min_score: Minimum overall score to include
            
        Returns:
            List of high-quality Q&A pairs for training
        """
        high_quality = []
        
        for eval_data in evaluations:
            metrics = eval_data.get("metrics")
            if metrics and metrics.overall_score >= min_score:
                high_quality.append({
                    "question": eval_data.get("question"),
                    "answer": eval_data.get("answer"),
                    "model": eval_data.get("model"),
                    "score": metrics.overall_score,
                    "label": metrics.label.value,
                    "expertise_level": metrics.expertise_level.value
                })
        
        logger.info(f"Exported {len(high_quality)} high-quality examples (score >= {min_score})")
        return high_quality


# Global instance
training_evaluator = TrainingEvaluationService()