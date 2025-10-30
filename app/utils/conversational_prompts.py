"""
Conversational AI prompts and utilities to make Harvey proactive and advisor-like.
"""

import re
from typing import Optional, Dict, List, Tuple, Any

FOLLOW_UP_PROMPTS = {
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


def get_follow_up_prompts(tickers: List[str], num_prompts: int = 3, exclude: Optional[List[str]] = None) -> List[str]:
    """
    Get relevant follow-up prompts for conversational advisor mode.
    
    Args:
        tickers: List of ticker symbols to include in prompts
        num_prompts: Number of prompts to return (default: 3)
        exclude: List of prompt types to exclude (optional)
    
    Returns:
        List of formatted follow-up questions
    """
    if exclude is None:
        exclude = []
    
    ticker_str = ", ".join(tickers) if tickers else "these tickers"
    
    prompts = []
    for key, template in FOLLOW_UP_PROMPTS.items():
        if key not in exclude:
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
