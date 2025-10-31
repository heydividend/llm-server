import re, datetime as dt, time, json, orjson
from typing import List, Optional, Dict, Any, Iterable
import logging
from app.config.settings import (
    GREETING_WORDS, SMALLTALK_KEYWORDS, FINANCE_KEYWORDS, 
    NEWS_KEYWORDS, SCHEMA_CAPABLE_KEYWORDS, TICKER_CANDIDATE, _STOPWORDS
)

logger = logging.getLogger("ai_controller")

def user_wants_cap(prompt: str) -> bool:
    q = prompt.lower()
    return any(k in q for k in [" top ", " limit ", " first ", " sample", " preview"])

def parse_last_n_years(prompt: str) -> Optional[int]:
    q = prompt.lower().replace("yrs", "years").replace("yr", "year")
    m = re.search(r"last\s+(\d+)\s+year", q)
    return int(m.group(1)) if m else None

def is_greeting_only(text: str) -> bool:
    t = re.sub(r"[\s\.,!?\-_:;]+", " ", text).strip().lower()
    words = [w for w in t.split() if w]
    return 1 <= len(words) <= 3 and all(w in GREETING_WORDS for w in words)

def is_smalltalk(text: str) -> bool:
    t = text.strip().lower()
    if is_greeting_only(t):
        return True
    return any(kw in t for kw in SMALLTALK_KEYWORDS)

def has_finance_intent(text: str) -> bool:
    lt = text.lower()
    return any(k in lt for k in FINANCE_KEYWORDS)

def is_news_like(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in NEWS_KEYWORDS)

def is_schema_capable(text: str, tickers_present: bool) -> bool:
    t = text.lower()
    if not any(k in t for k in SCHEMA_CAPABLE_KEYWORDS):
        return False
    return tickers_present or any(k in t for k in ("dividend","ex-div","ex date","payment date","record date","history","payout"))

def should_route_to_web(question: str, parsed_tickers: List[str]) -> bool:
    if is_smalltalk(question):
        return False
    tickers_present = bool(parsed_tickers)
    if is_schema_capable(question, tickers_present):
        return False
    if is_news_like(question):
        return True
    if not has_finance_intent(question) and not tickers_present:
        return True
    return False

def _looks_like_ticker(tok: str) -> bool:
    if tok.isupper():
        return True
    if "." in tok or "-" in tok:
        parts = re.split(r"[.\-]", tok)
        return all(p.isupper() for p in parts if p)
    return False

def extract_ticker_list(prompt: str) -> List[str]:
    raw = prompt.replace("/", " ").replace("|", " ").replace("\n", " ")
    cands = TICKER_CANDIDATE.findall(raw)
    tickers: List[str] = []
    seen = set()
    for tok in cands:
        if tok.upper() in _STOPWORDS:
            continue
        if tok.upper() in {"JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"}:
            continue
        core = re.split(r"[.\-]", tok)[0]
        if not (1 <= len(core) <= 5):
            continue
        if not _looks_like_ticker(tok):
            continue
        up = tok.upper()
        if up not in seen:
            seen.add(up); tickers.append(up)
    return tickers

def openai_sse_wrap(text_chunks: Iterable[str], req_id: str):
    yield f'data: {orjson.dumps({"id":req_id,"object":"chat.completion.chunk","choices":[{"delta":{"role":"assistant"}}]}).decode()}\n\n'
    for piece in text_chunks:
        if piece:
            yield f'data: {orjson.dumps({"id":req_id,"object":"chat.completion.chunk","choices":[{"delta":{"content":piece}}]}).decode()}\n\n'
    yield 'data: [DONE]\n\n'

def write_runlog(entry: Dict[str, Any], logfile: str = "runlogger.jsonl"):
    try:
        with open(logfile, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")
    except Exception as e:
        print(f"[warn] failed to write log: {e}")

def _canonical_url(u: str) -> str:
    from urllib.parse import urlparse
    try:
        p = urlparse(u)
        return f"{p.scheme}://{p.netloc}{p.path}".rstrip("/")
    except Exception:
        return u

def _maybe_flatten_vision_json(s: str) -> str:
    try:
        if not s or s[0] not in "{[":
            return s
        data = json.loads(s)
        ar = (data.get("analyzeResult") or {})
        pages = ar.get("readResults") or ar.get("pages") or []
        if not isinstance(pages, list) or not pages:
            text = ar.get("content")
            return text if isinstance(text, str) and text.strip() else s
        lines: list[str] = []
        for pg in pages:
            if isinstance(pg, dict):
                if "lines" in pg and pg["lines"]:
                    for ln in pg["lines"]:
                        t = (ln or {}).get("text")
                        if t: lines.append(t)
                elif "words" in pg and pg["words"]:
                    words = [w.get("text","") for w in pg["words"] if isinstance(w, dict)]
                    if any(words): lines.append(" ".join([w for w in words if w]))
                lines.append("")
        flat = "\n".join(lines).strip()
        return flat or s
    except Exception:
        return s


ML_QUERY_KEYWORDS = {
    "payout_rating": ["payout rating", "payout score", "dividend rating", "dividend sustainability", "payout quality"],
    "cut_risk": ["cut risk", "dividend cut", "cut probability", "dividend safety", "risk of cut", "at risk", "cutting dividend"],
    "yield_forecast": ["yield forecast", "dividend growth", "growth forecast", "dividend forecast", "future yield", "growth rate"],
    "anomaly": ["anomaly", "unusual pattern", "abnormal dividend", "irregular payment", "dividend issue"],
    "comprehensive": ["ml score", "comprehensive score", "overall score", "dividend score", "ml analysis", "ml rating"]
}


def is_ml_query(text: str) -> bool:
    """Detect if query is requesting ML predictions."""
    t = text.lower()
    for keywords_list in ML_QUERY_KEYWORDS.values():
        if any(kw in t for kw in keywords_list):
            return True
    return False


def detect_ml_query_type(text: str) -> str:
    """
    Determine which ML endpoint to call based on query keywords.
    
    Returns:
        One of: "payout_rating", "cut_risk", "yield_forecast", "anomaly", "comprehensive", or "payout_rating" (default)
    """
    t = text.lower()
    
    for query_type, keywords in ML_QUERY_KEYWORDS.items():
        if any(kw in t for kw in keywords):
            return query_type
    
    return "payout_rating"


def is_batch_ml_query(text: str, tickers: List[str]) -> bool:
    """
    Detect if query requests batch ML scoring for multiple tickers.
    
    Args:
        text: User query text
        tickers: List of parsed ticker symbols
        
    Returns:
        True if batch ML scoring requested for 2+ tickers, False otherwise
    """
    if len(tickers) < 2:
        return False
    
    t = text.lower()
    batch_keywords = [
        "watchlist", "portfolio", "compare", "rank", "score", "rate",
        "best", "worst", "top", "which", "analyze", "evaluate"
    ]
    
    return any(kw in t for kw in batch_keywords)


def is_portfolio_optimization_query(text: str) -> bool:
    """
    Detect if query requests portfolio optimization.
    
    Args:
        text: User query text
        
    Returns:
        True if portfolio optimization requested, False otherwise
    """
    t = text.lower()
    optimization_keywords = [
        "optimize portfolio", "optimize my portfolio", "improve diversification",
        "rebalance", "portfolio optimization", "diversify", "improve portfolio",
        "portfolio allocation", "asset allocation", "portfolio mix",
        "should i buy", "should i sell", "portfolio suggestions",
        "portfolio recommendations"
    ]
    
    return any(kw in t for kw in optimization_keywords)


def is_cluster_dashboard_query(text: str) -> bool:
    """
    Detect if query requests cluster dashboard / market overview.
    
    Args:
        text: User query text
        
    Returns:
        True if cluster dashboard requested, False otherwise
    """
    t = text.lower()
    cluster_keywords = [
        "dividend market overview", "market overview", "what clusters",
        "dividend categories", "dividend clusters", "cluster", "categories",
        "dividend types", "dividend classes", "market segments",
        "dividend landscape", "dividend groups", "types of dividend"
    ]
    
    return any(kw in t for kw in cluster_keywords)


def format_ml_payout_rating(data: List[Dict]) -> str:
    """Format payout rating response as markdown."""
    if not data:
        return "No payout rating data available."
    
    lines = ["## 📊 Dividend Payout Rating\n"]
    
    for item in data:
        symbol = item.get("symbol", "N/A")
        rating = item.get("payout_rating", 0)
        label = item.get("rating_label", "N/A")
        confidence = item.get("confidence", 0)
        percentile = item.get("payout_percentile", 0)
        
        emoji = "🟢" if rating >= 80 else "🟡" if rating >= 60 else "🔴"
        
        lines.append(f"### {emoji} {symbol}")
        lines.append(f"- **Payout Rating:** {rating:.1f}/100 ({label})")
        lines.append(f"- **Percentile:** Top {100-percentile}%")
        lines.append(f"- **Confidence:** {confidence*100:.0f}%")
        
        if "payout_quality_score" in item:
            lines.append(f"- **Quality Score:** {item['payout_quality_score']:.1f}")
        if "nav_protection_score" in item:
            lines.append(f"- **NAV Protection:** {item['nav_protection_score']:.1f}")
        
        lines.append("")
    
    return "\n".join(lines)


def format_ml_cut_risk(data: List[Dict]) -> str:
    """Format cut risk response as markdown."""
    if not data:
        return "No cut risk data available."
    
    lines = ["## ⚠️ Dividend Cut Risk Analysis\n"]
    
    for item in data:
        symbol = item.get("symbol", "N/A")
        risk_score = item.get("cut_risk_score", 0)
        risk_level = item.get("risk_level", "unknown")
        confidence = item.get("confidence", 0)
        risk_factors = item.get("risk_factors", [])
        
        emoji_map = {
            "very_low": "🟢",
            "low": "🟢",
            "moderate": "🟡",
            "high": "🟠",
            "very_high": "🔴"
        }
        emoji = emoji_map.get(risk_level, "⚪")
        
        lines.append(f"### {emoji} {symbol}")
        lines.append(f"- **Cut Risk Score:** {risk_score*100:.1f}% ({risk_level.replace('_', ' ').title()})")
        lines.append(f"- **Confidence:** {confidence*100:.0f}%")
        
        if "payout_ratio" in item:
            lines.append(f"- **Payout Ratio:** {item['payout_ratio']:.1f}%")
        if "earnings_coverage" in item:
            lines.append(f"- **Earnings Coverage:** {item['earnings_coverage']:.2f}x")
        
        if risk_factors:
            lines.append(f"- **Risk Factors:**")
            for factor in risk_factors:
                lines.append(f"  - {factor.replace('_', ' ').title()}")
        
        lines.append("")
    
    return "\n".join(lines)


def format_ml_yield_forecast(data: List[Dict]) -> str:
    """Format yield forecast response as markdown."""
    if not data:
        return "No yield forecast data available."
    
    lines = ["## 📈 Dividend Growth Forecast\n"]
    
    for item in data:
        symbol = item.get("symbol", "N/A")
        growth_rate = item.get("predicted_growth_rate", 0)
        current_yield = item.get("current_yield", 0)
        confidence = item.get("confidence", 0)
        
        emoji = "🚀" if growth_rate >= 10 else "📈" if growth_rate >= 5 else "📊"
        
        lines.append(f"### {emoji} {symbol}")
        lines.append(f"- **Predicted Growth Rate:** {growth_rate:.1f}% annually")
        lines.append(f"- **Current Yield:** {current_yield:.2f}%")
        lines.append(f"- **Confidence:** {confidence*100:.0f}%")
        lines.append("")
    
    return "\n".join(lines)


def format_ml_anomaly(data: List[Dict]) -> str:
    """Format anomaly detection response as markdown."""
    if not data:
        return "No anomaly data available."
    
    lines = ["## 🔍 Dividend Anomaly Detection\n"]
    
    for item in data:
        symbol = item.get("symbol", "N/A")
        has_anomaly = item.get("has_anomaly", False) or item.get("is_anomaly", False)
        anomaly_score = item.get("anomaly_score", 0)
        anomaly_type = item.get("anomaly_type")
        details = item.get("details", "")
        confidence = item.get("confidence", 0)
        
        emoji = "🔴" if has_anomaly else "🟢"
        status = "Anomaly Detected" if has_anomaly else "Normal"
        
        lines.append(f"### {emoji} {symbol} - {status}")
        lines.append(f"- **Anomaly Score:** {anomaly_score*100:.1f}%")
        
        if has_anomaly and anomaly_type:
            lines.append(f"- **Type:** {anomaly_type.replace('_', ' ').title()}")
        
        if details:
            lines.append(f"- **Details:** {details}")
        
        lines.append(f"- **Confidence:** {confidence*100:.0f}%")
        lines.append("")
    
    return "\n".join(lines)


def format_ml_comprehensive(data: List[Dict]) -> str:
    """Format comprehensive ML score response as markdown."""
    if not data:
        return "No comprehensive score data available."
    
    lines = ["## 🎯 Comprehensive ML Score\n"]
    
    for item in data:
        symbol = item.get("symbol", "N/A")
        overall_score = item.get("overall_score", 0)
        recommendation = item.get("recommendation", "hold")
        confidence = item.get("confidence", 0)
        
        emoji_map = {
            "strong_buy": "🟢",
            "buy": "🟡",
            "hold": "⚪",
            "sell": "🔴"
        }
        emoji = emoji_map.get(recommendation, "⚪")
        
        lines.append(f"### {emoji} {symbol}")
        lines.append(f"- **Overall Score:** {overall_score:.1f}/100")
        lines.append(f"- **Recommendation:** {recommendation.replace('_', ' ').title()}")
        lines.append(f"- **Confidence:** {confidence*100:.0f}%")
        
        if "payout_rating" in item:
            lines.append(f"- **Payout Rating:** {item['payout_rating']:.1f}")
        if "cut_risk_score" in item:
            lines.append(f"- **Cut Risk:** {item['cut_risk_score']*100:.1f}%")
        if "growth_forecast" in item:
            lines.append(f"- **Growth Forecast:** {item['growth_forecast']:.1f}%")
        
        lines.append("")
    
    return "\n".join(lines)


def format_ml_payout_rating_single(item: Dict) -> str:
    """Format single payout rating result for streaming."""
    symbol = item.get("symbol", "N/A")
    rating = item.get("payout_rating", 0)
    label = item.get("rating_label", "N/A")
    confidence = item.get("confidence", 0)
    percentile = item.get("payout_percentile", 0)
    
    emoji = "🟢" if rating >= 80 else "🟡" if rating >= 60 else "🔴"
    
    lines = [f"### {emoji} {symbol}"]
    lines.append(f"- **Payout Rating:** {rating:.1f}/100 ({label})")
    lines.append(f"- **Percentile:** Top {100-percentile}%")
    lines.append(f"- **Confidence:** {confidence*100:.0f}%")
    
    if "payout_quality_score" in item:
        lines.append(f"- **Quality Score:** {item['payout_quality_score']:.1f}")
    if "nav_protection_score" in item:
        lines.append(f"- **NAV Protection:** {item['nav_protection_score']:.1f}")
    
    lines.append("")
    return "\n".join(lines)


def format_ml_cut_risk_single(item: Dict) -> str:
    """Format single cut risk result for streaming."""
    symbol = item.get("symbol", "N/A")
    risk_score = item.get("cut_risk_score", 0)
    risk_level = item.get("risk_level", "unknown")
    confidence = item.get("confidence", 0)
    risk_factors = item.get("risk_factors", [])
    
    emoji_map = {
        "very_low": "🟢",
        "low": "🟢",
        "moderate": "🟡",
        "high": "🟠",
        "very_high": "🔴"
    }
    emoji = emoji_map.get(risk_level, "⚪")
    
    lines = [f"### {emoji} {symbol}"]
    lines.append(f"- **Cut Risk Score:** {risk_score*100:.1f}% ({risk_level.replace('_', ' ').title()})")
    lines.append(f"- **Confidence:** {confidence*100:.0f}%")
    
    if "payout_ratio" in item:
        lines.append(f"- **Payout Ratio:** {item['payout_ratio']:.1f}%")
    if "earnings_coverage" in item:
        lines.append(f"- **Earnings Coverage:** {item['earnings_coverage']:.2f}x")
    
    if risk_factors:
        lines.append(f"- **Risk Factors:**")
        for factor in risk_factors:
            lines.append(f"  - {factor.replace('_', ' ').title()}")
    
    lines.append("")
    return "\n".join(lines)


def format_ml_yield_forecast_single(item: Dict) -> str:
    """Format single yield forecast result for streaming."""
    symbol = item.get("symbol", "N/A")
    growth_rate = item.get("predicted_growth_rate", 0)
    current_yield = item.get("current_yield", 0)
    confidence = item.get("confidence", 0)
    
    emoji = "🚀" if growth_rate >= 10 else "📈" if growth_rate >= 5 else "📊"
    
    lines = [f"### {emoji} {symbol}"]
    lines.append(f"- **Predicted Growth Rate:** {growth_rate:.1f}% annually")
    lines.append(f"- **Current Yield:** {current_yield:.2f}%")
    lines.append(f"- **Confidence:** {confidence*100:.0f}%")
    lines.append("")
    return "\n".join(lines)


def format_ml_anomaly_single(item: Dict) -> str:
    """Format single anomaly result for streaming."""
    symbol = item.get("symbol", "N/A")
    has_anomaly = item.get("has_anomaly", False) or item.get("is_anomaly", False)
    anomaly_score = item.get("anomaly_score", 0)
    anomaly_type = item.get("anomaly_type")
    details = item.get("details", "")
    confidence = item.get("confidence", 0)
    
    emoji = "🔴" if has_anomaly else "🟢"
    status = "Anomaly Detected" if has_anomaly else "Normal"
    
    lines = [f"### {emoji} {symbol} - {status}"]
    lines.append(f"- **Anomaly Score:** {anomaly_score*100:.1f}%")
    
    if has_anomaly and anomaly_type:
        lines.append(f"- **Type:** {anomaly_type.replace('_', ' ').title()}")
    
    if details:
        lines.append(f"- **Details:** {details}")
    
    lines.append(f"- **Confidence:** {confidence*100:.0f}%")
    lines.append("")
    return "\n".join(lines)


def format_ml_comprehensive_single(item: Dict) -> str:
    """Format single comprehensive score result for streaming."""
    symbol = item.get("symbol", "N/A")
    overall_score = item.get("overall_score", 0)
    recommendation = item.get("recommendation", "hold")
    confidence = item.get("confidence", 0)
    
    emoji_map = {
        "strong_buy": "🟢",
        "buy": "🟡",
        "hold": "⚪",
        "sell": "🔴"
    }
    emoji = emoji_map.get(recommendation, "⚪")
    
    lines = [f"### {emoji} {symbol}"]
    lines.append(f"- **Overall Score:** {overall_score:.1f}/100")
    lines.append(f"- **Recommendation:** {recommendation.replace('_', ' ').title()}")
    lines.append(f"- **Confidence:** {confidence*100:.0f}%")
    
    if "payout_rating" in item:
        lines.append(f"- **Payout Rating:** {item['payout_rating']:.1f}")
    if "cut_risk_score" in item:
        lines.append(f"- **Cut Risk:** {item['cut_risk_score']*100:.1f}%")
    if "growth_forecast" in item:
        lines.append(f"- **Growth Forecast:** {item['growth_forecast']:.1f}%")
    
    lines.append("")
    return "\n".join(lines)