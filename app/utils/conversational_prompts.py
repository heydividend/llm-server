"""
Conversational AI prompts and utilities to make Harvey proactive and advisor-like.
"""

import re
from typing import Optional, Dict, List, Tuple, Any
from app.utils.dividend_analytics import calculate_next_declaration_date

FOLLOW_UP_PROMPTS = {
    "ml_analysis": "Would you like to see ML-powered quality scores and sustainability ratings for {tickers}?",
    "similar_stocks": "Interested in finding similar dividend stocks to {tickers} using ML clustering?",
    "ml_forecasting": "Would you like ML-powered yield and growth forecasts for {tickers}?",
    "cut_risk": "Want to check the ML-predicted dividend cut risk for {tickers}?",
    "portfolio_optimization": "Would you like me to analyze the diversification of your portfolio using ML clustering?",
    "cluster_dashboard": "Interested in viewing the dividend market landscape and ML-identified clusters (Aristocrats, High Yield, etc.)?",
    "batch_ml_scoring": "Want to see ML quality scores and recommendations for all {tickers} in a comparison table?",
    "forecasting": "Would you like to see dividend growth forecasts for {tickers}?",
    "watchlist": "Would you like to add {tickers} to a watchlist to monitor dividend changes and price movements?",
    "portfolio": "Do you own shares in any of these? I can calculate your TTM (trailing twelve months) income and track performance.",
    "alerts": "Would you like to set up alerts for dividend cuts, yield changes, or price targets on {tickers}?",
    "income_ladder": "Interested in building a monthly income ladder with these dividend payers?",
    "tax_optimization": "Would you like me to analyze tax implications and optimization strategies for your dividend income?"
}

SHARE_OWNERSHIP_PATTERNS = [
    r"(?:I\s+)?(?:own|have|hold|holding)\s+(\d+)\s+(?:shares?\s+(?:of\s+)?)?([A-Z]{1,5})",
    r"(\d+)\s+shares?\s+(?:of\s+)?([A-Z]{1,5})",
    r"(?:my\s+)?(\d+)\s+([A-Z]{1,5})\s+shares?",
    r"([A-Z]{1,5})\s+(\d+)\s+shares?",
    r"(\d+)\s+in\s+([A-Z]{1,5})",
    r"holding\s+([A-Z]{1,5})\s+(\d+)",
]


def detect_share_ownership(text: str) -> Optional[Dict[str, Any]]:
    """
    Detect share ownership patterns in user input.
    
    Returns dict with 'shares' (int) and 'ticker' (str) if detected, else None.
    
    Examples:
        "I own 200 shares of YMAX" -> {'shares': 200, 'ticker': 'YMAX'}
        "I have 100 TSLY" -> {'shares': 100, 'ticker': 'TSLY'}
        "My 500 shares of NVDY" -> {'shares': 500, 'ticker': 'NVDY'}
        "500 TSLY shares" -> {'shares': 500, 'ticker': 'TSLY'}
    """
    for pattern in SHARE_OWNERSHIP_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            
            shares_str = groups[0] if groups[0].isdigit() else groups[1] if len(groups) > 1 and groups[1].isdigit() else None
            ticker_str = groups[1] if groups[0].isdigit() else groups[0] if len(groups) > 0 else None
            
            if shares_str and ticker_str:
                try:
                    shares = int(shares_str.replace(',', ''))
                    ticker = ticker_str.upper()
                    if 1 <= len(ticker) <= 5 and shares > 0:
                        return {'shares': shares, 'ticker': ticker}
                except ValueError:
                    continue
    
    return None


def get_follow_up_prompts(tickers: List[str], num_prompts: int = 3, exclude: Optional[List[str]] = None, prioritize_ml: bool = True) -> List[str]:
    """
    Get relevant follow-up prompts for conversational advisor mode.
    
    Args:
        tickers: List of ticker symbols to include in prompts
        num_prompts: Number of prompts to return (default: 3)
        exclude: List of prompt types to exclude (optional)
        prioritize_ml: Whether to prioritize ML-powered prompts (default: True)
    
    Returns:
        List of formatted follow-up questions
    """
    if exclude is None:
        exclude = []
    
    ticker_str = ", ".join(tickers) if tickers else "these tickers"
    
    ml_prompt_keys = ["ml_analysis", "similar_stocks", "ml_forecasting", "cut_risk", "portfolio_optimization"]
    
    prompts = []
    
    if prioritize_ml:
        for key in ml_prompt_keys:
            if key not in exclude and key in FOLLOW_UP_PROMPTS:
                template = FOLLOW_UP_PROMPTS[key]
                if "{tickers}" in template:
                    prompts.append(template.format(tickers=ticker_str))
                else:
                    prompts.append(template)
    
    for key, template in FOLLOW_UP_PROMPTS.items():
        if key not in exclude and key not in ml_prompt_keys:
            if "{tickers}" in template:
                prompts.append(template.format(tickers=ticker_str))
            else:
                prompts.append(template)
    
    return prompts[:num_prompts]


def format_ttm_message(shares: int, ticker: str, ttm_total: float, monthly_avg: float) -> str:
    """
    Format TTM (trailing twelve months) income message.
    
    Args:
        shares: Number of shares owned
        ticker: Ticker symbol
        ttm_total: Total TTM distributions
        monthly_avg: Monthly average distribution
    
    Returns:
        Formatted message string
    """
    return (
        f"💰 **With {shares:,} shares of {ticker}, you received ${ttm_total:,.2f} "
        f"in the last 12 months (${monthly_avg:,.2f} per month on average)**"
    )


def is_dividend_query(text: str) -> bool:
    """
    Detect if the query is dividend-related.
    
    Args:
        text: User query text
    
    Returns:
        True if dividend-related, False otherwise
    """
    dividend_keywords = [
        "dividend", "distribution", "payout", "yield", 
        "ex-div", "ex date", "payment date", "record date",
        "income", "passive income", "monthly income"
    ]
    
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in dividend_keywords)


def is_dividend_distribution_query(text: str) -> bool:
    """
    Detect if the query is specifically about dividend distribution/declaration dates.
    
    Args:
        text: User query text
    
    Returns:
        True if asking about dividend distribution/declaration, False otherwise
    """
    distribution_patterns = [
        r"what.*is.*(?:the\s+)?dividend(?:\s+distribution)?",
        r"when.*(?:is|does|will).*(?:dividend|distribution|payout)",
        r"(?:dividend|distribution).*(?:schedule|date|timing)",
        r"(?:next|upcoming).*(?:dividend|distribution|ex-div|ex date)",
        r"declaration.*date",
        r"when.*(?:declare|announcing|announce).*dividend"
    ]
    
    text_lower = text.lower()
    return any(re.search(pattern, text_lower) for pattern in distribution_patterns)


def format_next_dividend_alert_suggestion(
    ticker: str,
    distributions: List[Dict],
    include_declaration_info: bool = True
) -> Optional[str]:
    """
    Generate proactive alert suggestion for next dividend declaration.
    
    Args:
        ticker: Ticker symbol
        distributions: List of distribution records
        include_declaration_info: Whether to include declaration date info
    
    Returns:
        Formatted alert suggestion string, or None if unable to predict
    """
    if not distributions:
        return None
    
    next_div_info = calculate_next_declaration_date(distributions, ticker)
    
    if not next_div_info or not next_div_info.get("has_prediction"):
        return None
    
    if not include_declaration_info:
        return f"💡 **Tip:** Would you like to set up an alert for {ticker}'s next dividend announcement?"
    
    alert_text = next_div_info.get("alert_suggestion", "")
    
    days_until = next_div_info.get("days_until", 0)
    if days_until <= 7:
        urgency = "🔔 **Coming Soon!** "
    elif days_until <= 30:
        urgency = "📅 "
    else:
        urgency = ""
    
    return f"\n\n---\n\n{urgency}{alert_text}"


def should_show_conversational_prompts(text: str, has_dividend_data: bool) -> bool:
    """
    Determine if conversational follow-up prompts should be shown.
    
    Args:
        text: User query text
        has_dividend_data: Whether dividend data was returned
    
    Returns:
        True if prompts should be shown, False otherwise
    """
    if not has_dividend_data:
        return False
    
    if is_dividend_query(text):
        return True
    
    return False
