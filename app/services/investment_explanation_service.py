"""
Investment Explanation Service for Harvey
Provides comprehensive Why/How/What explanations for investment research.
Makes Harvey an effective sub-agent in larger investment research initiatives.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from app.services.enhanced_logging_service import log_event

logger = logging.getLogger("investment_explanation")


class ExplanationType(Enum):
    """Types of explanations Harvey can provide"""
    METRIC = "metric"  # Explaining a financial metric
    STRATEGY = "strategy"  # Explaining an investment strategy
    RECOMMENDATION = "recommendation"  # Explaining a recommendation
    RISK = "risk"  # Explaining risk factors
    CALCULATION = "calculation"  # Explaining how something is calculated
    MARKET_CONTEXT = "market_context"  # Explaining market conditions
    TAX_IMPLICATION = "tax_implication"  # Explaining tax consequences


@dataclass
class ExplanationContext:
    """Context for generating explanations"""
    query: str
    symbol: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    investor_profile: Optional[str] = None  # conservative, moderate, aggressive
    time_horizon: Optional[str] = None  # short, medium, long
    research_context: Optional[str] = None


class InvestmentExplanationService:
    """
    Service to provide comprehensive investment explanations.
    Ensures Harvey explains the Why, How, and What of every analysis.
    """
    
    def __init__(self):
        self.explanation_templates = self._initialize_templates()
        logger.info("Investment Explanation Service initialized")
    
    def _initialize_templates(self) -> Dict[str, Dict[str, str]]:
        """Initialize explanation templates for different concepts"""
        return {
            "dividend_yield": {
                "what": "Dividend yield is the annual dividend payment divided by the stock price, expressed as a percentage.",
                "how": "Calculated as (Annual Dividend per Share / Current Stock Price) × 100",
                "why": "It shows the income return on your investment. Higher yields mean more income, but may signal risk or limited growth.",
                "context": "Compare yields to sector averages and consider sustainability."
            },
            "payout_ratio": {
                "what": "The percentage of earnings paid out as dividends to shareholders.",
                "how": "Calculated as (Dividends per Share / Earnings per Share) × 100",
                "why": "Shows dividend sustainability. <60% is healthy, >100% means paying more than earning (unsustainable).",
                "context": "REITs and utilities naturally have higher ratios; tech companies typically lower."
            },
            "dividend_growth": {
                "what": "The annualized rate at which a company's dividend payments have increased.",
                "how": "Calculated using CAGR formula: ((Ending Value/Beginning Value)^(1/Years)) - 1",
                "why": "Consistent growth protects against inflation and signals company health.",
                "context": "5-10% annual growth is excellent; aristocrats have 25+ years of increases."
            },
            "ex_dividend_date": {
                "what": "The date on which you must own the stock to receive the next dividend payment.",
                "how": "Set by the company; you must buy before this date to get the dividend.",
                "why": "Critical for dividend capture strategies and income planning.",
                "context": "Stock prices typically drop by dividend amount on ex-date."
            },
            "monthly_dividends": {
                "what": "Stocks or ETFs that pay dividends monthly rather than quarterly.",
                "how": "Companies structure payments to distribute 1/12 of annual dividend each month.",
                "why": "Provides more consistent income flow, easier budgeting, and faster compounding.",
                "context": "Common in REITs, BDCs, and covered call ETFs like YieldMax products."
            },
            "covered_call_etf": {
                "what": "ETFs that generate income by selling call options on their holdings.",
                "how": "Fund owns stocks and sells call options, collecting premiums as income.",
                "why": "Generates high current income but limits upside potential.",
                "context": "Best in flat/declining markets; underperforms in strong bull markets."
            },
            "nav_erosion": {
                "what": "The decline in Net Asset Value of high-yield funds over time.",
                "how": "Occurs when distributions exceed total returns from holdings.",
                "why": "Signals that high distributions may be unsustainable long-term.",
                "context": "Monitor NAV trends; consistent erosion means returning capital, not earnings."
            },
            "dividend_aristocrat": {
                "what": "S&P 500 companies with 25+ consecutive years of dividend increases.",
                "how": "Must meet market cap, liquidity, and consecutive increase requirements.",
                "why": "Demonstrates exceptional financial stability and shareholder commitment.",
                "context": "Only ~65 companies qualify; excellent for conservative portfolios."
            },
            "reits": {
                "what": "Real Estate Investment Trusts that own income-producing real estate.",
                "how": "Must distribute 90% of taxable income as dividends to maintain tax status.",
                "why": "Provides real estate exposure with high yields and liquidity.",
                "context": "Dividends taxed as ordinary income; sensitive to interest rates."
            },
            "qualified_dividends": {
                "what": "Dividends that qualify for lower capital gains tax rates.",
                "how": "Must hold stock 60+ days around ex-dividend date; from US companies.",
                "why": "Taxed at 0-20% instead of ordinary income rates up to 37%.",
                "context": "REIT and foreign dividends usually non-qualified."
            }
        }
    
    def explain_investment_concept(
        self,
        concept: str,
        context: Optional[ExplanationContext] = None
    ) -> Dict[str, str]:
        """
        Generate comprehensive explanation for an investment concept.
        
        Returns:
            Dictionary with 'what', 'how', 'why', and 'context' explanations
        """
        base_explanation = self.explanation_templates.get(concept, {})
        
        if not base_explanation:
            # Generate generic explanation structure
            return {
                "what": f"{concept} is a financial metric or concept used in investment analysis.",
                "how": "The specific calculation depends on the metric type.",
                "why": "Understanding this helps make informed investment decisions.",
                "context": "Consider this alongside other relevant factors."
            }
        
        # Customize based on context if provided
        if context and context.investor_profile:
            base_explanation = self._customize_for_profile(
                base_explanation,
                context.investor_profile
            )
        
        return base_explanation
    
    def _customize_for_profile(
        self,
        explanation: Dict[str, str],
        profile: str
    ) -> Dict[str, str]:
        """Customize explanation based on investor profile"""
        
        profile_adjustments = {
            "conservative": {
                "emphasis": "Focus on stability and capital preservation",
                "risk_note": "Prioritize sustainability over high yields"
            },
            "moderate": {
                "emphasis": "Balance income with growth potential",
                "risk_note": "Consider both yield and appreciation"
            },
            "aggressive": {
                "emphasis": "Maximize returns with calculated risks",
                "risk_note": "Higher yields acceptable with proper diversification"
            }
        }
        
        if profile in profile_adjustments:
            adjustment = profile_adjustments[profile]
            explanation["investor_note"] = (
                f"{adjustment['emphasis']}. {adjustment['risk_note']}."
            )
        
        return explanation
    
    def generate_recommendation_explanation(
        self,
        recommendation: str,
        reasoning: List[str],
        data: Dict[str, Any]
    ) -> str:
        """
        Generate comprehensive explanation for an investment recommendation.
        
        Args:
            recommendation: The recommendation being made
            reasoning: List of reasons supporting the recommendation
            data: Supporting data for the recommendation
        """
        explanation = []
        
        # WHAT - State the recommendation clearly
        explanation.append(f"**WHAT:** {recommendation}")
        
        # HOW - Explain the analysis process
        explanation.append("\n**HOW we determined this:**")
        for i, reason in enumerate(reasoning, 1):
            explanation.append(f"{i}. {reason}")
        
        # WHY - Explain the importance
        explanation.append("\n**WHY this matters:**")
        
        # Add context-specific why explanations
        if "yield" in str(data).lower():
            explanation.append("- Yield directly impacts your income return")
        
        if "payout_ratio" in str(data).lower():
            explanation.append("- Payout ratio indicates dividend sustainability")
        
        if "growth" in str(data).lower():
            explanation.append("- Growth protects purchasing power from inflation")
        
        if "risk" in str(data).lower():
            explanation.append("- Risk assessment prevents permanent capital loss")
        
        # Add data support
        if data:
            explanation.append("\n**Supporting Data:**")
            for key, value in data.items():
                if value is not None:
                    explanation.append(f"- {key}: {value}")
        
        return "\n".join(explanation)
    
    def explain_calculation(
        self,
        metric: str,
        formula: str,
        inputs: Dict[str, float],
        result: float
    ) -> str:
        """
        Explain how a calculation was performed.
        
        Args:
            metric: Name of the metric being calculated
            formula: Formula used
            inputs: Input values
            result: Calculated result
        """
        explanation = []
        
        explanation.append(f"**Calculating {metric}:**\n")
        
        # Show formula
        explanation.append(f"**Formula:** {formula}\n")
        
        # Show inputs
        explanation.append("**Inputs:**")
        for key, value in inputs.items():
            explanation.append(f"- {key}: {value}")
        
        # Show calculation
        explanation.append(f"\n**Calculation:**")
        # Create a readable calculation string
        calc_str = formula
        for key, value in inputs.items():
            calc_str = calc_str.replace(key, str(value))
        explanation.append(f"{calc_str} = {result}")
        
        # Explain what the result means
        explanation.append(f"\n**What this means:**")
        explanation.append(self._interpret_result(metric, result))
        
        return "\n".join(explanation)
    
    def _interpret_result(self, metric: str, result: float) -> str:
        """Interpret what a calculated result means"""
        
        interpretations = {
            "dividend_yield": {
                "ranges": [
                    (0, 2, "Low yield - growth-focused"),
                    (2, 4, "Moderate yield - balanced"),
                    (4, 6, "High yield - income-focused"),
                    (6, 10, "Very high yield - check sustainability"),
                    (10, 100, "Extremely high - possible risk signal")
                ]
            },
            "payout_ratio": {
                "ranges": [
                    (0, 30, "Conservative payout - room for growth"),
                    (30, 60, "Healthy payout - well-balanced"),
                    (60, 80, "High payout - limited growth potential"),
                    (80, 100, "Very high - sustainability concern"),
                    (100, 1000, "Unsustainable - paying more than earning")
                ]
            }
        }
        
        if metric in interpretations:
            for min_val, max_val, interpretation in interpretations[metric]["ranges"]:
                if min_val <= result < max_val:
                    return f"At {result:.2f}%: {interpretation}"
        
        return f"Result: {result:.2f}"
    
    def generate_market_context_explanation(
        self,
        topic: str,
        current_conditions: Dict[str, Any]
    ) -> str:
        """
        Explain current market context for investment decisions.
        """
        explanation = []
        
        explanation.append(f"**Market Context for {topic}:**\n")
        
        # Interest rate environment
        if "interest_rate" in current_conditions:
            rate = current_conditions["interest_rate"]
            explanation.append(f"**Interest Rates:** {rate}%")
            if rate > 4:
                explanation.append("- High rates make bonds competitive with dividend stocks")
                explanation.append("- REITs and utilities may face pressure")
            else:
                explanation.append("- Low rates favor dividend stocks over bonds")
                explanation.append("- 'TINA' effect (There Is No Alternative)")
        
        # Market volatility
        if "volatility" in current_conditions:
            vix = current_conditions["volatility"]
            explanation.append(f"\n**Market Volatility (VIX):** {vix}")
            if vix > 20:
                explanation.append("- High volatility favors quality dividend stocks")
                explanation.append("- Covered call strategies more profitable")
            else:
                explanation.append("- Low volatility supports dividend growth stocks")
                explanation.append("- Covered call strategies less effective")
        
        # Sector rotation
        if "sector_trend" in current_conditions:
            explanation.append(f"\n**Sector Trends:** {current_conditions['sector_trend']}")
        
        return "\n".join(explanation)
    
    def enhance_response_with_explanations(
        self,
        base_response: str,
        query: str,
        data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Enhance a base response with comprehensive explanations.
        
        This is the main method to ensure Harvey always explains
        the Why, How, and What of investment analysis.
        """
        enhanced = []
        
        # Add the base response
        enhanced.append(base_response)
        
        # Detect concepts mentioned and add explanations
        concepts_to_explain = []
        
        # Check for common investment concepts
        concept_keywords = {
            "yield": "dividend_yield",
            "payout ratio": "payout_ratio",
            "dividend growth": "dividend_growth",
            "ex-dividend": "ex_dividend_date",
            "monthly": "monthly_dividends",
            "covered call": "covered_call_etf",
            "nav": "nav_erosion",
            "aristocrat": "dividend_aristocrat",
            "reit": "reits",
            "qualified": "qualified_dividends"
        }
        
        query_lower = query.lower()
        response_lower = base_response.lower()
        
        for keyword, concept in concept_keywords.items():
            if keyword in query_lower or keyword in response_lower:
                concepts_to_explain.append(concept)
        
        # Add explanations for detected concepts
        if concepts_to_explain:
            enhanced.append("\n\n## 📚 **Understanding Key Concepts:**")
            
            for concept in concepts_to_explain[:3]:  # Limit to top 3 to avoid overwhelming
                explanation = self.explain_investment_concept(concept)
                enhanced.append(f"\n### {concept.replace('_', ' ').title()}:")
                enhanced.append(f"**What:** {explanation.get('what', '')}")
                enhanced.append(f"**How:** {explanation.get('how', '')}")
                enhanced.append(f"**Why it matters:** {explanation.get('why', '')}")
        
        # Add investment context
        enhanced.append("\n## 💡 **Investment Context:**")
        enhanced.append(self._generate_investment_wisdom(query, data))
        
        # Log the enhancement
        log_event("response_enhanced", {
            "concepts_explained": concepts_to_explain,
            "query_length": len(query),
            "response_length": len(base_response),
            "enhanced_length": len("\n".join(enhanced))
        })
        
        return "\n".join(enhanced)
    
    def _generate_investment_wisdom(
        self,
        query: str,
        data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate contextual investment wisdom"""
        
        wisdom = []
        
        # Add relevant investment principles
        if "dividend" in query.lower():
            wisdom.append("Remember: Total return = Dividend yield + Capital appreciation")
            wisdom.append("Consider tax implications of dividend income vs. capital gains")
        
        if "etf" in query.lower():
            wisdom.append("ETF advantages: Diversification, liquidity, and lower fees")
            wisdom.append("Check expense ratios and tracking error")
        
        if "risk" in query.lower():
            wisdom.append("Risk and return are related - higher yields often mean higher risk")
            wisdom.append("Diversification is the only free lunch in investing")
        
        if not wisdom:
            wisdom.append("Always consider your time horizon and risk tolerance")
            wisdom.append("Past performance doesn't guarantee future results")
        
        return "\n".join([f"• {w}" for w in wisdom])


# Global instance
investment_explainer = InvestmentExplanationService()


# Convenience functions
def explain_concept(concept: str, context: Optional[ExplanationContext] = None):
    return investment_explainer.explain_investment_concept(concept, context)

def explain_recommendation(recommendation: str, reasoning: List[str], data: Dict[str, Any]):
    return investment_explainer.generate_recommendation_explanation(
        recommendation, reasoning, data
    )

def explain_calculation(metric: str, formula: str, inputs: Dict[str, float], result: float):
    return investment_explainer.explain_calculation(metric, formula, inputs, result)

def enhance_response(base_response: str, query: str, data: Optional[Dict[str, Any]] = None):
    return investment_explainer.enhance_response_with_explanations(
        base_response, query, data
    )