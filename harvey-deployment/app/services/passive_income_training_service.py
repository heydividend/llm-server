"""
Passive Income Training Service
Processes specialized dividend investment training data for Harvey.
Includes 7,200+ questions focused on dividend strategies, yield analysis, and income optimization.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import re
from dataclasses import dataclass
from enum import Enum
import csv
from io import StringIO

logger = logging.getLogger("passive_income_training")


@dataclass
class DividendMetrics:
    """Metrics for dividend-paying securities."""
    ticker: str
    yield_pct: float
    dgr_5y: float  # 5-year dividend growth rate
    strategy: str  # organic, option-overlay, synthetic, etc.
    payout_frequency: str  # monthly, quarterly


@dataclass
class TrainingQuestion:
    """A dividend-focused training question."""
    query: str
    context: str
    metrics: Dict[str, DividendMetrics]
    payout_frequency: Dict[str, str]
    dividend_calendar_map: Dict[str, List[str]]
    category: str
    complexity: int


class DividendStrategy(Enum):
    """Types of dividend strategies."""
    ORGANIC = "organic"  # Traditional dividends (KO, SCHD, VIG)
    OPTION_OVERLAY = "option-overlay"  # Covered call ETFs (JEPI, JEPQ, XYLD)
    SYNTHETIC = "synthetic"  # YieldMax series (TSLY, NVDY, APLY)
    LEVERAGED_CREDIT = "leveraged-credit"  # CEFs with leverage (PDO)
    INFRA_CEF = "infra-CEF"  # Infrastructure CEFs (UTF)
    OPTION_CEF = "option-CEF"  # Option-based CEFs (ETY)


class PassiveIncomeTrainingService:
    """
    Comprehensive service for processing passive income training data.
    Specializes in dividend investing, yield strategies, and income optimization.
    """
    
    def __init__(self):
        """Initialize with evaluation targets and lesson plans."""
        self.evaluation_targets = {
            "global": {
                "clear_score_min": 0.9,
                "complete_score_min": 0.85,
                "actionable_score_min": 0.9
            },
            "per_level": {
                "beginner": {"clear_min": 0.92, "complete_min": 0.80, "actionable_min": 0.92},
                "intermediate": {"clear_min": 0.90, "complete_min": 0.86, "actionable_min": 0.90},
                "advanced": {"clear_min": 0.88, "complete_min": 0.90, "actionable_min": 0.88}
            }
        }
        
        self.auto_rewrite_prompts = {}
        self.lesson_modules = []
        self.training_questions = []
        
        logger.info("Passive Income Training Service initialized")
    
    def load_training_questions_jsonl(self, jsonl_content: str, dataset_name: str = "main") -> List[TrainingQuestion]:
        """
        Load training questions from JSONL format.
        
        Args:
            jsonl_content: JSONL string with training questions
            dataset_name: Name of the dataset (main or supplemental)
            
        Returns:
            List of parsed TrainingQuestion objects
        """
        questions = []
        lines = jsonl_content.strip().split('\n')
        
        for index, line in enumerate(lines):
            if not line.strip():
                continue
                
            try:
                data = json.loads(line)
                
                # Parse metrics for each ticker
                metrics = {}
                if "metrics" in data:
                    for ticker, ticker_metrics in data["metrics"].items():
                        metrics[ticker] = DividendMetrics(
                            ticker=ticker,
                            yield_pct=ticker_metrics.get("yield", 0.0),
                            dgr_5y=ticker_metrics.get("dgr_5y", 0.0),
                            strategy=ticker_metrics.get("strategy", "organic"),
                            payout_frequency=data.get("payout_frequency", {}).get(ticker, "quarterly")
                        )
                
                # Preserve existing category if present, otherwise use heuristic
                if "category" in data:
                    # Trust the provided category from curated data
                    category = data["category"]
                    logger.debug(f"Using provided category: {category}")
                elif "labels" in data and "category" in data["labels"]:
                    # Check if category is nested in labels
                    category = data["labels"]["category"]
                    logger.debug(f"Using category from labels: {category}")
                else:
                    # Fall back to heuristic only when category is missing
                    category = self._categorize_question(data.get("query", ""))
                    logger.debug(f"Using heuristic category: {category}")
                
                # Preserve existing complexity if present, otherwise use heuristic
                if "complexity" in data:
                    # Trust the provided complexity from curated data
                    complexity = data["complexity"]
                    logger.debug(f"Using provided complexity: {complexity}")
                elif "labels" in data and "complexity" in data["labels"]:
                    # Check if complexity is nested in labels
                    complexity = data["labels"]["complexity"]
                    logger.debug(f"Using complexity from labels: {complexity}")
                else:
                    # Fall back to heuristic only when complexity is missing
                    complexity = self._assess_complexity(data)
                    logger.debug(f"Using heuristic complexity: {complexity}")
                
                question = TrainingQuestion(
                    query=data.get("query", ""),
                    context=data.get("context", ""),
                    metrics=metrics,
                    payout_frequency=data.get("payout_frequency", {}),
                    dividend_calendar_map=data.get("dividend_calendar_map", {}),
                    category=category,
                    complexity=complexity
                )
                questions.append(question)
                
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing line {index} in {dataset_name}: {e}")
                continue
        
        logger.info(f"Loaded {len(questions)} training questions from {dataset_name}")
        return questions
    
    def load_lesson_plan(self, lesson_plan_json: str) -> Dict[str, Any]:
        """
        Load structured lesson plan for dividend education.
        
        Args:
            lesson_plan_json: JSON string with lesson modules
            
        Returns:
            Parsed lesson plan structure
        """
        try:
            lesson_data = json.loads(lesson_plan_json)
            self.lesson_modules = lesson_data.get("modules", [])
            
            # Extract key learning objectives
            learning_map = {}
            for module in self.lesson_modules:
                module_name = module.get("name", "")
                lessons = module.get("lessons", [])
                
                for lesson in lessons:
                    topic = lesson.get("topic", "")
                    learning_map[topic] = {
                        "objectives": lesson.get("objectives", []),
                        "examples": lesson.get("examples", []),
                        "practice_task": lesson.get("practice_task", ""),
                        "rubric": lesson.get("rubric_reference", {})
                    }
            
            logger.info(f"Loaded {len(self.lesson_modules)} lesson modules")
            return learning_map
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing lesson plan: {e}")
            return {}
    
    def load_auto_rewrite_prompts(self, prompts_json: str) -> None:
        """
        Load auto-rewrite prompts for quality improvement.
        
        Args:
            prompts_json: JSON string with rewrite prompts
        """
        try:
            prompts = json.loads(prompts_json)
            for prompt_data in prompts:
                criterion = prompt_data.get("criterion_failed", "")
                prompt = prompt_data.get("prompt", "")
                self.auto_rewrite_prompts[criterion] = prompt
            
            logger.info(f"Loaded {len(self.auto_rewrite_prompts)} auto-rewrite prompts")
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing auto-rewrite prompts: {e}")
    
    def _categorize_question(self, query: str) -> str:
        """
        Categorize a question based on its content.
        
        Args:
            query: The question text
            
        Returns:
            Category name
        """
        query_lower = query.lower()
        
        if "sustainable" in query_lower or "yield trap" in query_lower:
            return "yield_sustainability"
        elif "monthly income" in query_lower or "income plan" in query_lower:
            return "income_planning"
        elif "diversified" in query_lower or "sleeve" in query_lower:
            return "portfolio_construction"
        elif "tax" in query_lower or "after-tax" in query_lower:
            return "tax_optimization"
        elif "better for passive income" in query_lower:
            return "comparison"
        elif "where should i hold" in query_lower:
            return "account_location"
        else:
            return "general"
    
    def _assess_complexity(self, question_data: Dict) -> int:
        """
        Assess complexity of a question (1-5 scale).
        
        Args:
            question_data: Question dictionary
            
        Returns:
            Complexity score 1-5
        """
        complexity = 2  # Base complexity
        
        # More tickers = more complex
        num_tickers = len(question_data.get("metrics", {}))
        if num_tickers > 3:
            complexity += 2
        elif num_tickers > 2:
            complexity += 1
        
        # Synthetic/leveraged strategies are more complex
        metrics = question_data.get("metrics", {})
        for ticker_data in metrics.values():
            if ticker_data.get("strategy") in ["synthetic", "leveraged-credit"]:
                complexity += 1
                break
        
        # Tax questions are complex
        if "tax" in question_data.get("query", "").lower():
            complexity += 1
        
        return min(5, complexity)
    
    def generate_enhanced_training_questions(self, base_questions: List[TrainingQuestion]) -> List[Dict[str, Any]]:
        """
        Generate enhanced training questions with quality improvements.
        
        Args:
            base_questions: Base training questions
            
        Returns:
            Enhanced questions with additional context
        """
        enhanced_questions = []
        
        for question in base_questions[:100]:  # Process first 100 for demo
            enhanced = {
                "question": question.query,
                "context": question.context,
                "category": question.category,
                "complexity": question.complexity,
                "enhanced_answer_requirements": []
            }
            
            # Add specific requirements based on question type
            if question.category == "yield_sustainability":
                enhanced["enhanced_answer_requirements"].extend([
                    "Compare payout ratios or coverage metrics",
                    "Discuss NAV trend for yields >20%",
                    "Mention dividend growth history"
                ])
            
            elif question.category == "income_planning":
                enhanced["enhanced_answer_requirements"].extend([
                    "Create month-by-month income schedule",
                    "Calculate total portfolio yield",
                    "Address diversification across strategies"
                ])
            
            elif question.category == "tax_optimization":
                enhanced["enhanced_answer_requirements"].extend([
                    "Specify qualified vs ordinary income treatment",
                    "Recommend account placement (taxable/IRA/Roth)",
                    "Mention state tax considerations if relevant"
                ])
            
            # Add ticker-specific analysis
            for ticker, metrics in question.metrics.items():
                if metrics.yield_pct > 20:
                    enhanced["enhanced_answer_requirements"].append(
                        f"Flag {ticker} high yield ({metrics.yield_pct}%) sustainability concerns"
                    )
                if metrics.dgr_5y < 0:
                    enhanced["enhanced_answer_requirements"].append(
                        f"Note {ticker} negative dividend growth ({metrics.dgr_5y}%)"
                    )
            
            enhanced_questions.append(enhanced)
        
        return enhanced_questions
    
    def evaluate_response_quality(self, response: str, question_type: str) -> Dict[str, float]:
        """
        Evaluate response quality against passive income criteria.
        
        Args:
            response: Model response
            question_type: Type of question
            
        Returns:
            Quality scores
        """
        scores = {
            "yield_source_explained": 0.0,
            "nav_risk_addressed": 0.0,
            "payout_frequency_mentioned": 0.0,
            "tax_implications_covered": 0.0,
            "specific_tickers_analyzed": 0.0,
            "actionable_threshold_provided": 0.0
        }
        
        response_lower = response.lower()
        
        # Check yield source explanation
        yield_sources = ["dividend", "interest", "option premium", "capital gains", "return of capital"]
        if any(source in response_lower for source in yield_sources):
            scores["yield_source_explained"] = 1.0
        
        # Check NAV risk discussion
        nav_terms = ["nav", "principal", "erosion", "decay", "capital preservation"]
        if any(term in response_lower for term in nav_terms):
            scores["nav_risk_addressed"] = 1.0
        
        # Check payout frequency
        frequency_terms = ["monthly", "quarterly", "semi-annual", "annual"]
        if any(term in response_lower for term in frequency_terms):
            scores["payout_frequency_mentioned"] = 1.0
        
        # Check tax implications
        tax_terms = ["qualified", "ordinary income", "tax", "after-tax", "roc", "return of capital"]
        if any(term in response_lower for term in tax_terms):
            scores["tax_implications_covered"] = 1.0
        
        # Check for specific ticker analysis
        ticker_pattern = r'\b[A-Z]{2,5}\b'
        tickers_found = re.findall(ticker_pattern, response)
        if len(tickers_found) >= 2:
            scores["specific_tickers_analyzed"] = 1.0
        
        # Check for actionable thresholds
        threshold_patterns = [r'\d+%', r'\$\d+', r'ratio of \d+', r'coverage of \d+']
        if any(re.search(pattern, response) for pattern in threshold_patterns):
            scores["actionable_threshold_provided"] = 1.0
        
        return scores
    
    def create_dividend_calendar(self, tickers: List[Tuple[str, str]]) -> Dict[str, List[str]]:
        """
        Create a dividend payment calendar.
        
        Args:
            tickers: List of (ticker, frequency) tuples
            
        Returns:
            Monthly dividend calendar
        """
        calendar = {month: [] for month in [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
        ]}
        
        for ticker, frequency in tickers:
            if frequency == "monthly":
                # Monthly payers pay every month
                for month in calendar:
                    calendar[month].append(ticker)
            
            elif frequency == "quarterly":
                # Assume standard quarterly schedules
                if ticker in ["SCHD", "VIG", "VYM"]:
                    # Feb, May, Aug, Nov pattern
                    for month in ["Feb", "May", "Aug", "Nov"]:
                        calendar[month].append(ticker)
                elif ticker in ["HDV", "ARCC"]:
                    # Mar, Jun, Sep, Dec pattern
                    for month in ["Mar", "Jun", "Sep", "Dec"]:
                        calendar[month].append(ticker)
                else:
                    # Jan, Apr, Jul, Oct pattern (default)
                    for month in ["Jan", "Apr", "Jul", "Oct"]:
                        calendar[month].append(ticker)
        
        return calendar
    
    def analyze_strategy_mix(self, portfolio: List[DividendMetrics]) -> Dict[str, Any]:
        """
        Analyze the strategy mix of a portfolio.
        
        Args:
            portfolio: List of dividend metrics
            
        Returns:
            Analysis of strategy distribution and risk
        """
        strategy_counts = {strategy.value: 0 for strategy in DividendStrategy}
        total_yield = 0
        total_dgr = 0
        high_risk_count = 0
        
        for holding in portfolio:
            strategy_counts[holding.strategy] += 1
            total_yield += holding.yield_pct
            total_dgr += holding.dgr_5y
            
            # Flag high-risk holdings
            if holding.yield_pct > 20 or holding.dgr_5y < -10:
                high_risk_count += 1
        
        num_holdings = len(portfolio)
        
        return {
            "strategy_distribution": strategy_counts,
            "avg_yield": total_yield / num_holdings if num_holdings > 0 else 0,
            "avg_dgr": total_dgr / num_holdings if num_holdings > 0 else 0,
            "high_risk_percentage": (high_risk_count / num_holdings * 100) if num_holdings > 0 else 0,
            "diversification_score": self._calculate_diversification_score(strategy_counts),
            "sustainability_score": self._calculate_sustainability_score(portfolio)
        }
    
    def _calculate_diversification_score(self, strategy_counts: Dict[str, int]) -> float:
        """
        Calculate portfolio diversification score (0-100).
        
        Higher scores indicate better diversification across strategies.
        """
        total = sum(strategy_counts.values())
        if total == 0:
            return 0.0
        
        # Calculate entropy-based diversification
        entropy = 0
        for count in strategy_counts.values():
            if count > 0:
                prob = count / total
                entropy -= prob * (prob if prob > 0 else 0)
        
        # Normalize to 0-100 scale
        max_entropy = -(1/len(strategy_counts)) * len(strategy_counts) * (1/len(strategy_counts))
        return min(100, (entropy / max_entropy) * 100) if max_entropy != 0 else 0
    
    def _calculate_sustainability_score(self, portfolio: List[DividendMetrics]) -> float:
        """
        Calculate income sustainability score (0-100).
        
        Based on yield levels, dividend growth, and strategy types.
        """
        if not portfolio:
            return 0.0
        
        score = 100.0
        
        for holding in portfolio:
            # Penalize very high yields
            if holding.yield_pct > 30:
                score -= 20
            elif holding.yield_pct > 20:
                score -= 10
            elif holding.yield_pct > 15:
                score -= 5
            
            # Penalize negative dividend growth
            if holding.dgr_5y < -10:
                score -= 15
            elif holding.dgr_5y < -5:
                score -= 10
            elif holding.dgr_5y < 0:
                score -= 5
            
            # Penalize risky strategies
            if holding.strategy == "synthetic":
                score -= 10
            elif holding.strategy == "leveraged-credit":
                score -= 5
        
        return max(0, score)
    
    def export_training_data(self, questions: List[TrainingQuestion], format: str = "openai") -> List[Dict[str, Any]]:
        """
        Export training data in specified format.
        
        Args:
            questions: Training questions to export
            format: Export format (openai, jsonl, csv)
            
        Returns:
            Formatted training data
        """
        if format == "openai":
            # OpenAI fine-tuning format
            training_data = []
            for q in questions:
                training_data.append({
                    "messages": [
                        {"role": "system", "content": "You are Harvey, an expert dividend investment advisor."},
                        {"role": "user", "content": q.query},
                        {"role": "assistant", "content": self._generate_ideal_response(q)}
                    ]
                })
            return training_data
        
        elif format == "jsonl":
            # Standard JSONL format
            return [vars(q) for q in questions]
        
        else:
            # CSV format
            rows = []
            for q in questions:
                rows.append({
                    "query": q.query,
                    "context": q.context,
                    "category": q.category,
                    "complexity": q.complexity,
                    "num_tickers": len(q.metrics)
                })
            return rows
    
    def _generate_ideal_response(self, question: TrainingQuestion) -> str:
        """
        Generate an ideal response template for a training question.
        
        This would be enhanced by actual model responses in production.
        """
        response = f"Based on your {question.context}, here's my analysis:\n\n"
        
        # Add ticker-specific analysis
        for ticker, metrics in question.metrics.items():
            response += f"**{ticker}**: {metrics.yield_pct}% yield, "
            response += f"{metrics.dgr_5y}% 5-year dividend growth, "
            response += f"{metrics.strategy} strategy, {metrics.payout_frequency} payments\n"
        
        # Add recommendations based on question type
        if question.category == "yield_sustainability":
            response += "\n**Sustainability Analysis**: "
            response += "Consider payout ratios and NAV trends for high-yield positions.\n"
        
        elif question.category == "income_planning":
            response += "\n**Monthly Income Schedule**: "
            response += "Diversify across payment frequencies for stable cash flow.\n"
        
        return response


# Global instance
passive_income_trainer = PassiveIncomeTrainingService()