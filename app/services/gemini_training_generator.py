"""
Gemini Training Data Generator for Harvey AI
Generates high-quality synthetic training questions and answers for Harvey's ML models
using Gemini 2.5 Pro with validation and deduplication.
"""

import logging
import hashlib
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from difflib import SequenceMatcher
from app.services.gemini_client import get_gemini_client

logger = logging.getLogger("gemini_training_generator")


class GeminiTrainingGenerator:
    """
    Generates dividend-focused training questions and answers using Gemini 2.5 Pro.
    
    Features:
    - Category-specific prompt engineering
    - Quality validation for dividend relevance
    - Deduplication of similar questions
    - Structured output formatting
    """
    
    # Category-specific prompts with examples
    CATEGORY_PROMPTS = {
        "dividend_analysis": {
            "description": "Financial analysis of dividend metrics, ratios, and sustainability",
            "examples": [
                "What is the 5-year dividend CAGR for AAPL?",
                "Calculate the dividend coverage ratio for JNJ",
                "What's the free cash flow payout ratio for KO?"
            ],
            "template": """Generate {count} unique, professional dividend analysis questions. Focus on:
- Dividend growth rates and CAGR calculations
- Payout ratios (earnings and free cash flow)
- Dividend coverage and sustainability metrics
- Historical dividend payment consistency
- Dividend aristocrats, kings, and champions
- Valuation models (DDM, Gordon Growth Model)
- Yield metrics and yield on cost

Examples:
{examples}

Requirements:
- Use real ticker symbols (AAPL, MSFT, JNJ, KO, PG, etc.)
- Include specific metrics and timeframes
- Make questions actionable and answerable
- Vary complexity from basic to advanced
- Focus on dividend investing fundamentals

Output format: Return ONLY a JSON array of question strings, no additional text."""
        },
        
        "income_strategies": {
            "description": "Portfolio construction strategies for passive income generation",
            "examples": [
                "Build a $50K portfolio targeting $500 monthly income",
                "Create a dividend ladder with weekly payments",
                "Design a portfolio with no overlapping ex-dates"
            ],
            "template": """Generate {count} unique dividend income strategy questions. Focus on:
- Portfolio construction for specific income targets
- Dividend payment frequency optimization (monthly, weekly)
- Tax-efficient income strategies
- REIT and MLPs for income generation
- Covered calls and cash-secured puts
- Income laddering and payment scheduling
- Risk-adjusted income strategies

Examples:
{examples}

Requirements:
- Specify investment amounts and income targets
- Include timeframes and constraints
- Cover different risk tolerance levels
- Address tax considerations
- Mix growth and income approaches
- Use realistic portfolio sizes ($10K-$1M)

Output format: Return ONLY a JSON array of question strings, no additional text."""
        },
        
        "technical_timing": {
            "description": "Timing analysis for dividend capture and announcement patterns",
            "examples": [
                "When does AAPL typically announce dividend increases?",
                "What's the best entry point before ex-dividend for KO?",
                "Show stocks going ex-dividend in next 3 days"
            ],
            "template": """Generate {count} unique dividend timing and technical analysis questions. Focus on:
- Ex-dividend date patterns and timing
- Dividend announcement schedules
- Dividend capture strategies and optimal holding periods
- Seasonal dividend patterns
- Price behavior around ex-dividend dates
- Dividend surprise and announcement reactions
- Calendar-based dividend opportunities

Examples:
{examples}

Requirements:
- Use specific tickers and timeframes
- Include calendar-based queries (next week, this month)
- Cover pattern recognition
- Address entry/exit timing
- Mix short-term and long-term perspectives

Output format: Return ONLY a JSON array of question strings, no additional text."""
        },
        
        "etf_funds": {
            "description": "Analysis of dividend ETFs, covered call ETFs, and fund strategies",
            "examples": [
                "Compare SCHD vs VIG for dividend growth investing",
                "What's the expense ratio impact on JEPI returns?",
                "Show all monthly paying dividend ETFs sorted by yield"
            ],
            "template": """Generate {count} unique dividend ETF and fund questions. Focus on:
- Popular dividend ETFs (SCHD, VIG, DVY, NOBL, VYM)
- Covered call ETFs (JEPI, JEPQ, QYLD, RYLD, XYLD)
- International dividend funds
- Sector-specific dividend ETFs
- Expense ratios and fee impact
- NAV erosion in covered call strategies
- Fund overlap and holdings analysis
- Distribution frequency (monthly, quarterly)

Examples:
{examples}

Requirements:
- Use actual ETF tickers
- Compare similar funds
- Address costs and efficiency
- Cover different dividend strategies
- Include yield and performance metrics

Output format: Return ONLY a JSON array of question strings, no additional text."""
        },
        
        "tax_optimization": {
            "description": "Tax-efficient dividend investing strategies and calculations",
            "examples": [
                "Calculate qualified dividend tax for $50K income",
                "What's the tax difference between ordinary and qualified dividends?",
                "How do I optimize dividend income in IRA vs taxable account?"
            ],
            "template": """Generate {count} unique dividend tax optimization questions. Focus on:
- Qualified vs ordinary dividend taxation
- Tax-advantaged account placement (IRA, Roth, 401k, taxable)
- Foreign tax credits and withholding
- NIIT (Net Investment Income Tax)
- Tax-loss harvesting with dividends
- REIT and MLP tax treatment
- Municipal bonds vs taxable dividends
- Stepped-up basis for inherited dividend stocks

Examples:
{examples}

Requirements:
- Include specific income levels for tax brackets
- Address different account types
- Cover international tax considerations
- Explain tax-efficient strategies
- Use realistic dollar amounts

Output format: Return ONLY a JSON array of question strings, no additional text."""
        },
        
        "risk_management": {
            "description": "Risk assessment and mitigation for dividend portfolios",
            "examples": [
                "What's the dividend cut probability for T based on debt?",
                "Show warning signs of unsustainable dividends",
                "Calculate the downside protection from KO dividends"
            ],
            "template": """Generate {count} unique dividend risk management questions. Focus on:
- Dividend cut probability and warning signs
- Payout ratio sustainability thresholds
- Debt-to-equity and interest coverage
- Sector-specific risks (utilities, REITs, energy)
- Dividend safety scoring models
- Portfolio diversification for dividend income
- Interest rate sensitivity
- Recession resilience of dividend stocks
- Volatility and drawdown analysis

Examples:
{examples}

Requirements:
- Use specific tickers and sectors
- Include quantitative risk metrics
- Address macroeconomic factors
- Cover defensive strategies
- Balance risk and return considerations

Output format: Return ONLY a JSON array of question strings, no additional text."""
        },
        
        "market_analysis": {
            "description": "Market conditions, trends, and sector analysis for dividends",
            "examples": [
                "How do rising interest rates affect REIT dividends?",
                "What sectors have the best dividend yields during recessions?",
                "Compare dividend growth in tech vs utilities over 10 years"
            ],
            "template": """Generate {count} unique market analysis questions for dividend investing. Focus on:
- Interest rate impact on dividend stocks
- Sector rotation and dividend performance
- Economic cycle effects on dividends
- Market cap considerations (large, mid, small)
- Geographic diversification (US vs international)
- Inflation impact on real dividend returns
- Market valuation and dividend yields
- Historical market patterns and dividends

Examples:
{examples}

Requirements:
- Address macroeconomic factors
- Compare sectors and market segments
- Include timeframes and cycles
- Use historical context
- Cover global markets

Output format: Return ONLY a JSON array of question strings, no additional text."""
        },
        
        "portfolio_construction": {
            "description": "Building and optimizing dividend-focused portfolios",
            "examples": [
                "Design a 20-stock dividend portfolio for maximum diversification",
                "Build a dividend portfolio with 4% yield and 7% growth",
                "Create a barbell strategy mixing high yield and growth"
            ],
            "template": """Generate {count} unique dividend portfolio construction questions. Focus on:
- Position sizing and allocation
- Diversification across sectors and geographies
- Balancing yield and growth
- Core/satellite portfolio approaches
- Rebalancing strategies
- Number of holdings optimization
- Factor tilts (value, quality, momentum)
- Risk-adjusted portfolio optimization

Examples:
{examples}

Requirements:
- Specify portfolio characteristics (size, yield, growth)
- Include diversification requirements
- Address rebalancing frequency
- Cover different strategies (barbell, dumbbell, equal-weight)
- Use realistic constraints

Output format: Return ONLY a JSON array of question strings, no additional text."""
        },
        
        "dividend_sustainability": {
            "description": "Analyzing long-term dividend sustainability and growth potential",
            "examples": [
                "Evaluate dividend sustainability for T based on FCF trends",
                "What metrics predict dividend cuts with 90% accuracy?",
                "Analyze the sustainability of XOM's dividend post-2020"
            ],
            "template": """Generate {count} unique dividend sustainability analysis questions. Focus on:
- Free cash flow coverage of dividends
- Earnings quality and dividend sustainability
- Capital allocation priorities
- Debt service capacity
- Industry headwinds and tailwinds
- Management dividend policy
- Dividend growth runway
- Competitive moat and pricing power

Examples:
{examples}

Requirements:
- Use specific companies and metrics
- Include fundamental analysis
- Address industry-specific factors
- Cover both strong and weak examples
- Include predictive elements

Output format: Return ONLY a JSON array of question strings, no additional text."""
        },
        
        "global_dividend_markets": {
            "description": "International dividend investing and global market opportunities",
            "examples": [
                "Compare dividend withholding taxes across UK, Canada, and Australia",
                "What are the best European dividend aristocrats?",
                "Analyze emerging market dividend opportunities and risks"
            ],
            "template": """Generate {count} unique global dividend market questions. Focus on:
- International dividend stocks and ADRs
- Foreign withholding taxes and tax treaties
- Currency risk in international dividends
- Regional dividend champions (Europe, Asia-Pacific, Canada)
- Emerging market dividend opportunities
- Developed vs emerging market dividend yields
- Global sector leaders in dividends
- Cross-border tax optimization

Examples:
{examples}

Requirements:
- Cover multiple geographies (Europe, Asia, Canada, Australia)
- Address tax and currency considerations
- Use specific international tickers or markets
- Compare global opportunities
- Include risk/reward trade-offs

Output format: Return ONLY a JSON array of question strings, no additional text."""
        }
    }
    
    def __init__(self):
        """Initialize the training generator."""
        self.client = get_gemini_client()
        self.generated_questions = set()  # For deduplication
        self.generation_stats = {
            'total_generated': 0,
            'total_validated': 0,
            'total_rejected': 0,
            'duplicates_filtered': 0,
            'by_category': {}
        }
        
        logger.info("Gemini Training Generator initialized")
    
    def generate_questions(
        self,
        category: str,
        count: int = 50,
        with_answers: bool = True,
        temperature: float = 0.8,
        validate: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generate training questions for a specific category.
        
        Args:
            category: Category name (must be in CATEGORY_PROMPTS)
            count: Number of questions to generate
            with_answers: Generate answers using Gemini
            temperature: Sampling temperature for creativity
            validate: Validate dividend relevance
        
        Returns:
            List of dicts with 'question', 'category', 'answer' (if with_answers)
        """
        if category not in self.CATEGORY_PROMPTS:
            raise ValueError(f"Unknown category: {category}. Valid: {list(self.CATEGORY_PROMPTS.keys())}")
        
        logger.info(f"Generating {count} questions for category: {category}")
        
        prompt_config = self.CATEGORY_PROMPTS[category]
        examples_text = "\n".join(f"- {ex}" for ex in prompt_config["examples"])
        
        prompt = prompt_config["template"].format(
            count=count,
            examples=examples_text
        )
        
        try:
            # Generate questions
            result = self.client.generate_text(
                prompt=prompt,
                temperature=temperature,
                max_tokens=4096,
                use_cache=False  # Don't cache training generation
            )
            
            # Parse JSON response
            questions_raw = self._parse_json_response(result['text'])
            
            if not questions_raw:
                logger.error(f"Failed to parse questions from response: {result['text'][:200]}")
                return []
            
            # Process and validate questions
            processed = []
            for question_text in questions_raw:
                # Skip empty or very short questions
                if not question_text or len(question_text) < 10:
                    continue
                
                # Check for duplicates
                if self._is_duplicate(question_text):
                    self.generation_stats['duplicates_filtered'] += 1
                    logger.debug(f"Filtered duplicate: {question_text[:50]}...")
                    continue
                
                # Validate dividend relevance
                if validate and not self._validate_dividend_relevance(question_text):
                    self.generation_stats['total_rejected'] += 1
                    logger.warning(f"Rejected non-dividend question: {question_text[:50]}...")
                    continue
                
                question_obj = {
                    'question': question_text.strip(),
                    'category': category,
                    'source': 'gemini_generated',
                    'generated_at': datetime.utcnow().isoformat()
                }
                
                # Generate answer if requested
                if with_answers:
                    answer = self._generate_answer(question_text, category)
                    question_obj['answer'] = answer
                
                processed.append(question_obj)
                self.generated_questions.add(question_text.lower())
                self.generation_stats['total_validated'] += 1
            
            self.generation_stats['total_generated'] += len(processed)
            self.generation_stats['by_category'][category] = \
                self.generation_stats['by_category'].get(category, 0) + len(processed)
            
            logger.info(f"Generated {len(processed)} validated questions for {category}")
            return processed
            
        except Exception as e:
            logger.error(f"Failed to generate questions for {category}: {e}")
            return []
    
    def generate_all_categories(
        self,
        questions_per_category: int = 50,
        with_answers: bool = True
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate questions for all categories.
        
        Args:
            questions_per_category: Number of questions per category
            with_answers: Generate answers
        
        Returns:
            Dict mapping category to list of question objects
        """
        logger.info(f"Generating {questions_per_category} questions for {len(self.CATEGORY_PROMPTS)} categories")
        
        all_questions = {}
        
        for category in self.CATEGORY_PROMPTS.keys():
            questions = self.generate_questions(
                category=category,
                count=questions_per_category,
                with_answers=with_answers
            )
            all_questions[category] = questions
        
        total = sum(len(q) for q in all_questions.values())
        logger.info(f"Generated {total} total questions across all categories")
        
        return all_questions
    
    def _parse_json_response(self, response_text: str) -> List[str]:
        """Parse JSON array from Gemini response."""
        try:
            # Try direct JSON parse
            cleaned = response_text.strip()
            
            # Remove markdown code blocks if present
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]
            
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            
            cleaned = cleaned.strip()
            
            # Parse JSON
            data = json.loads(cleaned)
            
            if isinstance(data, list):
                return [str(item) for item in data if item]
            else:
                logger.warning(f"Expected JSON array, got: {type(data)}")
                return []
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.debug(f"Response text: {response_text[:500]}")
            return []
    
    def _validate_dividend_relevance(self, question: str) -> bool:
        """
        Validate that question is relevant to dividend investing.
        
        Checks for dividend-related keywords and patterns.
        """
        question_lower = question.lower()
        
        # Required dividend keywords
        dividend_keywords = [
            'dividend', 'yield', 'payout', 'distribution', 'income',
            'aristocrat', 'king', 'champion', 'drip', 'ex-dividend',
            'ex-date', 'pay date', 'declaration', 'quarterly', 'monthly',
            'coverage ratio', 'fcf payout', 'earnings payout', 'sustainability'
        ]
        
        # Check if any dividend keyword is present
        has_dividend_keyword = any(kw in question_lower for kw in dividend_keywords)
        
        # Financial analysis keywords (weaker signal)
        financial_keywords = ['portfolio', 'strategy', 'etf', 'reit', 'tax', 'growth']
        has_financial_keyword = any(kw in question_lower for kw in financial_keywords)
        
        # Ticker pattern check
        has_ticker = bool(re.search(r'\b[A-Z]{1,5}\b', question))
        
        # Must have dividend keyword, or both financial keyword and ticker
        return has_dividend_keyword or (has_financial_keyword and has_ticker)
    
    def _is_duplicate(self, question: str, similarity_threshold: float = 0.85) -> bool:
        """
        Check if question is duplicate or too similar to existing questions.
        
        Args:
            question: Question text
            similarity_threshold: Minimum similarity ratio to consider duplicate
        
        Returns:
            True if duplicate
        """
        question_lower = question.lower()
        
        # Exact match
        if question_lower in self.generated_questions:
            return True
        
        # Fuzzy match against recent questions (sample for performance)
        sample_size = min(100, len(self.generated_questions))
        recent_questions = list(self.generated_questions)[-sample_size:]
        
        for existing in recent_questions:
            similarity = SequenceMatcher(None, question_lower, existing).ratio()
            if similarity >= similarity_threshold:
                logger.debug(f"Similar question found (similarity: {similarity:.2f})")
                return True
        
        return False
    
    def _generate_answer(self, question: str, category: str) -> str:
        """
        Generate a comprehensive answer for a question.
        
        Args:
            question: Question text
            category: Category for context
        
        Returns:
            Generated answer
        """
        category_context = self.CATEGORY_PROMPTS[category]["description"]
        
        prompt = f"""You are Harvey, an expert dividend investing AI assistant. 
Answer this {category} question with detailed, actionable information:

Question: {question}

Provide a comprehensive answer that includes:
- Direct answer to the question
- Relevant calculations or metrics (if applicable)
- Practical considerations for dividend investors
- Risk factors or caveats
- Specific examples with real tickers when possible

Keep the answer professional, accurate, and focused on dividend investing fundamentals.
Answer:"""
        
        try:
            result = self.client.generate_text(
                prompt=prompt,
                temperature=0.7,
                max_tokens=1024,
                use_cache=False
            )
            
            answer = result['text'].strip()
            logger.debug(f"Generated answer ({len(answer)} chars)")
            return answer
            
        except Exception as e:
            logger.error(f"Failed to generate answer: {e}")
            return "[Answer generation failed]"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get generation statistics."""
        return {
            **self.generation_stats,
            'gemini_stats': self.client.get_statistics()
        }
    
    def reset_statistics(self):
        """Reset generation statistics."""
        self.generation_stats = {
            'total_generated': 0,
            'total_validated': 0,
            'total_rejected': 0,
            'duplicates_filtered': 0,
            'by_category': {}
        }
        self.generated_questions.clear()
        logger.info("Statistics reset")


# Global shared instance
_generator: Optional[GeminiTrainingGenerator] = None


def get_training_generator() -> GeminiTrainingGenerator:
    """Get or create the global training generator instance."""
    global _generator
    
    if _generator is None:
        _generator = GeminiTrainingGenerator()
    
    return _generator
