"""
Context-Aware Status Message Detection for Harvey AI

Analyzes incoming queries and returns appropriate status messages
to display during streaming responses.
"""

import re
import logging

logger = logging.getLogger(__name__)

# Status message mappings based on query keywords
# NOTE: Order matters! More specific terms should come first
STATUS_MAPPINGS = {
    # ===== DIVIDEND ARISTOCRATS/KINGS/CHAMPIONS (very specific) =====
    "dividend aristocrat": "Finding dividend aristocrats...",
    "aristocrat": "Finding dividend aristocrats...",
    "dividend king": "Finding dividend kings...",
    "king": "Finding dividend kings...",
    "dividend champion": "Finding dividend champions...",
    "champion": "Finding dividend champions...",
    
    # ===== TIMING & CALENDAR =====
    "ex-dividend": "Finding ex-dividend dates...",
    "ex dividend": "Finding ex-dividend dates...",
    "when pay": "Checking payment schedules...",
    "payment date": "Checking payment schedules...",
    "payment schedule": "Checking payment schedules...",
    "monthly payer": "Finding monthly payers...",
    "quarterly": "Checking payment frequencies...",
    "annual": "Checking payment frequencies...",
    
    # ===== DIVIDEND SAFETY & RISK =====
    "dividend safety": "Evaluating dividend safety...",
    "dividend cut": "Assessing cut risk...",
    "cut risk": "Assessing cut risk...",
    "suspend": "Evaluating dividend safety...",
    "at risk": "Assessing cut risk...",
    "sustainable": "Evaluating dividend sustainability...",
    "coverage": "Checking coverage ratios...",
    
    # ===== ML & AI FEATURES =====
    "predict": "Running ML models...",
    "forecast": "Running ML models...",
    "machine learning": "Running ML models...",
    "model": "Running ML models...",
    "score": "Calculating AI scores...",
    "rating": "Generating ratings...",
    "backtest": "Running backtests...",
    "ai": "Processing with Harvey AI...",
    
    # ===== PORTFOLIO & STRATEGY =====
    "rebalance": "Balancing portfolio...",
    "balance portfolio": "Balancing portfolio...",
    "optimize allocation": "Optimizing allocations...",
    "optimize": "Optimizing allocations...",
    "allocation": "Optimizing allocations...",
    "diversif": "Assessing diversification...",
    "portfolio": "Scanning portfolios...",
    "watchlist": "Analyzing watchlist...",
    "position": "Reviewing positions...",
    "holdings": "Reviewing holdings...",
    "risk": "Assessing risk levels...",
    "volatility": "Analyzing volatility...",
    "strategy": "Analyzing strategies...",
    
    # ===== COMPARISON & SCREENING =====
    "compare": "Comparing options...",
    "versus": "Comparing alternatives...",
    " vs ": "Comparing alternatives...",
    "screen": "Screening stocks...",
    "filter": "Filtering results...",
    "find stocks": "Searching for stocks...",
    "search for": "Searching database...",
    
    # ===== INCOME PLANNING =====
    "income ladder": "Building income ladder...",
    "monthly income": "Calculating monthly income...",
    "passive income": "Planning passive income...",
    "retirement income": "Projecting retirement income...",
    "income projection": "Calculating income projections...",
    "income": "Calculating income projections...",
    
    # ===== VALUATION & ANALYSIS =====
    "overvalued": "Evaluating valuation...",
    "undervalued": "Evaluating valuation...",
    "fair value": "Calculating fair value...",
    "valuation": "Analyzing valuation...",
    "p/e ratio": "Checking valuation metrics...",
    "price target": "Analyzing price targets...",
    "intrinsic value": "Calculating intrinsic value...",
    
    # ===== RESEARCH & DUE DILIGENCE =====
    "research": "Conducting research...",
    "due diligence": "Performing due diligence...",
    "dd on": "Performing due diligence...",
    "deep dive": "Conducting deep analysis...",
    "analyze": "Analyzing data...",
    "analysis": "Running analysis...",
    
    # ===== PERFORMANCE & RETURNS =====
    "performance": "Analyzing performance...",
    "return": "Calculating returns...",
    "total return": "Calculating total returns...",
    "dividend return": "Calculating dividend returns...",
    "outperform": "Comparing performance...",
    "underperform": "Comparing performance...",
    "track record": "Reviewing track record...",
    
    # ===== SECTORS & INDUSTRIES =====
    "sector rotation": "Analyzing sector rotation...",
    "energy": "Scanning energy sector...",
    "utility": "Scanning utilities...",
    "utilities": "Scanning utilities...",
    "healthcare": "Scanning healthcare sector...",
    "technology": "Scanning tech sector...",
    "tech": "Scanning tech sector...",
    "financial": "Reviewing financials...",
    "consumer": "Scanning consumer sector...",
    "sector": "Scanning sectors...",
    "industry": "Reviewing industries...",
    
    # ===== INTERNATIONAL & GEOGRAPHY =====
    "canadian": "Scanning Canadian markets...",
    "european": "Scanning European markets...",
    "international": "Scanning global markets...",
    "foreign": "Scanning international stocks...",
    "global": "Scanning global markets...",
    "overseas": "Scanning international markets...",
    
    # ===== GROWTH VS INCOME =====
    "growth stock": "Analyzing growth stocks...",
    "growth": "Analyzing growth potential...",
    "dividend growth": "Analyzing dividend growth...",
    "growth rate": "Calculating growth rates...",
    "income stock": "Finding income stocks...",
    
    # ===== SPECIFIC METRICS =====
    "payout ratio": "Evaluating payout ratios...",
    "payout": "Evaluating payout ratios...",
    "yield": "Checking yields...",
    "distribution": "Checking distributions...",
    "dividend": "Calculating dividends...",
    "drip": "Analyzing dividend reinvestment...",
    "earnings": "Checking earnings...",
    "revenue": "Analyzing revenue...",
    "debt": "Analyzing debt levels...",
    "free cash flow": "Checking cash flows...",
    "cash flow": "Checking cash flows...",
    
    # ===== MARKET CONDITIONS =====
    "bear market": "Analyzing market conditions...",
    "bull market": "Analyzing market conditions...",
    "recession": "Assessing recession impact...",
    "inflation": "Analyzing inflation effects...",
    "interest rate": "Checking rate environment...",
    "fed": "Analyzing Fed policy...",
    "market": "Analyzing markets...",
    
    # ===== ASSET TYPES =====
    "reit": "Analyzing REITs...",
    "mlp": "Analyzing MLPs...",
    "etf": "Reviewing ETFs...",
    "mutual fund": "Reviewing mutual funds...",
    "bond": "Analyzing bonds...",
    "stock": "Analyzing stocks...",
    "equity": "Analyzing equities...",
    
    # ===== DATA OPERATIONS =====
    "historical": "Searching historical data...",
    "history": "Searching historical data...",
    "trending": "Finding trending stocks...",
    "popular": "Finding popular picks...",
    "aggregate": "Aggregating sources...",
    "data": "Enriching with AI...",
    
    # ===== LISTS & CATEGORIES =====
    "list": "Building dividend lists...",
    "category": "Finding categories...",
    "top": "Finding top performers...",
    "best": "Finding best options...",
    "worst": "Identifying weak performers...",
    "highest": "Finding highest yielders...",
    "lowest": "Finding lowest volatility...",
    
    # ===== TAX CONSIDERATIONS =====
    "tax": "Analyzing tax implications...",
    "qualified dividend": "Checking dividend qualifications...",
    "non-qualified": "Checking tax treatment...",
    "roth": "Analyzing tax strategies...",
    "ira": "Analyzing retirement accounts...",
    "taxable": "Analyzing tax impact...",
    
    # ===== QUICK ACTIONS =====
    "show": "Retrieving data...",
    "get": "Fetching information...",
    "what": "Processing query...",
    "how": "Analyzing question...",
    "when": "Checking dates...",
    "why": "Investigating reasoning...",
    "explain": "Preparing explanation...",
    
    # ===== DEFAULT FALLBACK =====
    "default": "Harvey is thinking..."
}


def detect_status_message(query: str) -> str:
    """
    Detect appropriate status message based on query content.
    
    Args:
        query: User's query text
        
    Returns:
        Appropriate status message string
    """
    if not query:
        return STATUS_MAPPINGS["default"]
    
    query_lower = query.lower()
    
    # First check for ticker patterns ($TICKER or #TICKER)
    ticker_pattern = r'[\$#]([A-Z]{1,5})'
    ticker_match = re.search(ticker_pattern, query, re.IGNORECASE)
    if ticker_match:
        ticker = ticker_match.group(1).upper()
        logger.info(f"Status detector: Found ticker {ticker}")
        
        # Context-specific ticker messages
        if "distribution" in query_lower or "distributions" in query_lower:
            return f"Checking {ticker} distributions..."
        elif "fundamental" in query_lower or "fundamentals" in query_lower:
            return f"Pulling {ticker} fundamentals..."
        elif "ex-dividend" in query_lower or "ex dividend" in query_lower:
            return "Finding ex-dividend dates..."
        elif "safety" in query_lower or "cut" in query_lower or "suspend" in query_lower:
            return "Evaluating dividend safety..."
        else:
            # Default ticker message
            return f"Pulling {ticker} fundamentals..."
    
    # Sort keywords by length (longest first) to match most specific phrases
    # This ensures "dividend aristocrat" matches before "dividend"
    sorted_keywords = sorted(
        [(k, v) for k, v in STATUS_MAPPINGS.items() if k != "default"],
        key=lambda x: len(x[0]),
        reverse=True
    )
    
    for keyword, status_msg in sorted_keywords:
        if keyword in query_lower:
            logger.info(f"Status detector: Matched keyword '{keyword}' → '{status_msg}'")
            return status_msg
    
    # Default fallback
    logger.info("Status detector: Using default status message")
    return STATUS_MAPPINGS["default"]


def get_status_sse_chunk(status_message: str, request_id: str = "status-msg") -> bytes:
    """
    Format status message as SSE chunk.
    
    Args:
        status_message: Status message text
        request_id: Request ID for SSE chunk
        
    Returns:
        SSE-formatted bytes ready to stream
    """
    import orjson
    
    sse_data = {
        "id": request_id,
        "object": "chat.completion.chunk",
        "choices": [{
            "delta": {
                "content": f"*{status_message}*\n\n"
            }
        }]
    }
    
    sse_chunk = f'data: {orjson.dumps(sse_data).decode()}\n\n'
    return sse_chunk.encode('utf-8')


# For backward compatibility
def get_contextual_status(query: str) -> str:
    """Legacy function name - calls detect_status_message"""
    return detect_status_message(query)
