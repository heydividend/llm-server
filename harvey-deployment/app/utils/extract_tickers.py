"""
FastAPI Ticker Extractor Endpoint

Usage:
    uvicorn ticker_api:app --reload

Endpoints:
    POST /extract-tickers
        Body: {
            "query": "compare apple and amazon",
            "debug": false  // optional
        }
        Returns: {
            "original_query": "compare apple and amazon",
            "updated_query": "compare #AAPL and #AMZN",
            "detected_tickers": ["AAPL", "AMZN"],
            "elapsed_ms": 12.345,
            "success": true
        }
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
import csv
import os
import re
import time
from difflib import get_close_matches

# Attempt to use rapidfuzz for better fuzzy matching; fallback to difflib
try:
    from rapidfuzz import process, fuzz  # type: ignore
    _HAS_RAPIDFUZZ = True
except Exception:
    _HAS_RAPIDFUZZ = False

# Initialize FastAPI app
app = FastAPI(
    title="Ticker Extractor API",
    description="Extract stock tickers from natural language queries",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stopwords (remove common words that are not helpful)
STOPWORDS = {
    "the", "a", "an", "of", "and", "or", "latest", "dividend", "stock",
    "stocks", "price", "value", "values", "show", "tell", "about", "what",
    "is", "are", "i", "me", "please", "can", "you", "give", "get", "find",
    "more", "how", "who", "has", "paid"
}

# Common company suffixes to handle intelligently
COMPANY_SUFFIXES = {
    "inc", "corp", "corporation", "company", "co", "ltd", "limited",
    "plc", "llc", "holdings", "group", "technologies", "systems", "services"
}

# Words that should NEVER trigger matches on their own
FORBIDDEN_SOLO_WORDS = COMPANY_SUFFIXES | {"compare", "corporation", "inc", "company"}

RE_WORD = re.compile(r"\b[\w\.\-&']+\b", re.UNICODE)  # tokenization

# Global cache for tickers data
_TICKERS_CACHE = None
_CACHE_PATH = None


class TickerRequest(BaseModel):
    query: str = Field(..., description="Natural language query to extract tickers from")
    debug: Optional[bool] = Field(False, description="Enable debug output")
    csv_path: Optional[str] = Field(None, description="Custom path to tickers.csv")


class TickerResponse(BaseModel):
    original_query: str
    updated_query: str
    detected_tickers: List[str]
    elapsed_ms: float
    success: bool
    error: Optional[str] = None
    debug_info: Optional[dict] = None


def locate_default_tickers_csv():
    """Locate the default tickers.csv in the project root."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.normpath(os.path.join(script_dir, "..", "tickers.csv"))
    
    # Also check current directory
    if not os.path.exists(candidate):
        candidate = os.path.join(os.getcwd(), "tickers.csv")
    
    return candidate


def normalize_company_name(name):
    """
    Normalize company name by removing suffixes and extra words.
    Returns both the full normalized name and key words.
    """
    if not name:
        return "", []
    
    # Convert to lowercase and split
    words = name.lower().replace(",", "").split()
    
    # Remove common suffixes from the end
    filtered_words = []
    for w in words:
        w_clean = w.strip(".")
        if w_clean not in COMPANY_SUFFIXES:
            filtered_words.append(w_clean)
    
    # Return normalized full name and key words
    normalized = " ".join(filtered_words)
    return normalized, filtered_words


def load_tickers(csv_path):
    """
    Load tickers from CSV file.
    Returns: tickers dict, name_to_ticker dict, companies list, keyword_index dict
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"tickers CSV not found: {csv_path}")
    
    tickers = {}  # ticker -> company name (original)
    name_to_ticker = {}  # normalized company name -> ticker
    companies = []  # list of company names (original)
    keyword_index = {}  # individual keywords -> list of tickers
    
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        # detect header (common: 'ticker','name')
        first = next(reader, None)
        if first is None:
            return tickers, name_to_ticker, companies, keyword_index
        
        # If header row looks like header:
        header_row = [c.strip().lower() for c in first]
        if "ticker" in header_row and ("name" in header_row or "company" in header_row):
            # Use DictReader for the rest
            fh.seek(0)
            dr = csv.DictReader(fh)
            for row in dr:
                t = row.get("ticker") or row.get("symbol") or row.get("Ticker") or ""
                n = row.get("name") or row.get("company") or row.get("Name") or ""
                if t and n:
                    t = t.strip().upper()
                    n = n.strip()
                    tickers[t] = n
                    
                    # Store normalized versions
                    normalized, keywords = normalize_company_name(n)
                    name_to_ticker[n.lower()] = t
                    name_to_ticker[normalized] = t
                    companies.append(n)
                    
                    # Index by keywords
                    for kw in keywords:
                        if kw not in keyword_index:
                            keyword_index[kw] = []
                        keyword_index[kw].append(t)
        else:
            # assume each row is "TICKER,Company Name"
            # first row is already a data row
            fh.seek(0)
            for row in reader:
                if not row:
                    continue
                t = row[0].strip().upper()
                n = row[1].strip() if len(row) > 1 else row[0].strip()
                if t:
                    tickers[t] = n
                    
                    # Store normalized versions
                    normalized, keywords = normalize_company_name(n)
                    name_to_ticker[n.lower()] = t
                    name_to_ticker[normalized] = t
                    companies.append(n)
                    
                    # Index by keywords
                    for kw in keywords:
                        if kw not in keyword_index:
                            keyword_index[kw] = []
                        keyword_index[kw].append(t)
    
    return tickers, name_to_ticker, companies, keyword_index


def get_tickers_data(csv_path=None, force_reload=False):
    """Get tickers data from cache or load from CSV."""
    global _TICKERS_CACHE, _CACHE_PATH
    
    if csv_path is None:
        csv_path = locate_default_tickers_csv()
    
    # Return cached data if available and path matches
    if not force_reload and _TICKERS_CACHE is not None and _CACHE_PATH == csv_path:
        return _TICKERS_CACHE
    
    # Load and cache
    tickers_data = load_tickers(csv_path)
    _TICKERS_CACHE = tickers_data
    _CACHE_PATH = csv_path
    
    return tickers_data


def clean_query(query):
    """Clean query by removing stopwords."""
    if not query:
        return ""
    parts = RE_WORD.findall(query.lower())
    filtered = [p for p in parts if p not in STOPWORDS]
    return " ".join(filtered)


def extract_tickers_from_query(query, tickers, name_to_ticker, companies, keyword_index, use_fuzzy=True, debug=False):
    """
    Extract tickers from natural language query.
    Returns list of (ticker, confidence, match_text, start, end) tuples and elapsed time in ms.
    """
    start = time.perf_counter()
    results = {}  # ticker -> (confidence, match_text, start, end)
    original = query or ""
    query_stripped = clean_query(original)
    
    debug_info = {}
    
    # Detect if query likely contains multiple tickers
    multi_ticker_indicators = ["vs", "versus", "and", "or", "compare", ","]
    is_multi_query = any(indicator in original.lower() for indicator in multi_ticker_indicators)
    
    if debug:
        debug_info["original"] = original
        debug_info["cleaned"] = query_stripped
        debug_info["is_multi_query"] = is_multi_query
    
    # 1) $TICKER style (e.g., $AAPL)
    for m in re.finditer(r"\$([A-Za-z0-9\.\-]{1,8})", original):
        t = m.group(1).upper()
        if t in tickers:
            match_info = (0.99, m.group(0), m.start(), m.end())
            if t not in results or results[t][0] < 0.99:
                results[t] = match_info
    
    # 2) Direct token matches (case-insensitive) - but avoid single suffix words
    for m in RE_WORD.finditer(original):
        tk = m.group(0)
        tk_up = tk.upper()
        tk_low = tk.lower()
        
        # Skip if it's a forbidden solo word
        if tk_low in FORBIDDEN_SOLO_WORDS:
            continue
            
        if tk_up in tickers:
            match_info = (0.98, tk, m.start(), m.end())
            if tk_up not in results or results[tk_up][0] < 0.98:
                results[tk_up] = match_info
    
    # 3) Exact company-name substring matches (multi-word only for suffixes)
    qlow = original.lower()
    for name_lower, t in name_to_ticker.items():
        # Skip single-word suffix matches
        name_words = name_lower.split()
        if len(name_words) == 1 and name_words[0] in FORBIDDEN_SOLO_WORDS:
            continue
        
        # Find all occurrences of this company name
        pattern = re.escape(name_lower)
        for m in re.finditer(r'\b' + pattern + r'\b', qlow):
            match_ratio = len(name_lower) / max(len(query_stripped), 1)
            confidence = min(0.97, 0.80 + match_ratio * 0.17)
            match_info = (confidence, original[m.start():m.end()], m.start(), m.end())
            if t not in results or results[t][0] < confidence:
                results[t] = match_info
    
    # 4) Keyword-based matching
    query_normalized, query_keywords = normalize_company_name(query_stripped)
    meaningful_keywords = [kw for kw in query_keywords if len(kw) >= 3 and kw not in FORBIDDEN_SOLO_WORDS]
    
    for kw in meaningful_keywords:
        if kw in keyword_index:
            candidate_tickers = keyword_index[kw]
            for t in candidate_tickers:
                company_name = tickers[t]
                _, company_keywords = normalize_company_name(company_name)
                
                matching_kw = set(meaningful_keywords) & set(company_keywords)
                
                # Require at least 2 matching keywords OR 1 highly distinctive keyword
                if len(matching_kw) >= 2 or (len(matching_kw) == 1 and len(company_keywords) == 1):
                    match_score = len(matching_kw) / len(company_keywords)
                    if len(query_stripped) < 5:
                        confidence = 0.65 + match_score * 0.25
                    else:
                        confidence = 0.70 + match_score * 0.20
                    
                    # Find the keyword position in original query
                    kw_pattern = re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE)
                    m = kw_pattern.search(original)
                    if m:
                        match_info = (confidence, m.group(0), m.start(), m.end())
                        if t not in results or results[t][0] < confidence:
                            results[t] = match_info
    
    # 5) Fuzzy matching
    if use_fuzzy and qlow and len(query_stripped) >= 3:
        if is_multi_query:
            separator_pattern = r'\s+(?:vs|versus|and|or|compare)\s+|,\s*'
            raw_parts = re.split(f'({separator_pattern})', original)
            
            query_parts = []
            current_pos = 0
            for part in raw_parts:
                if not part or re.match(separator_pattern, part):
                    current_pos += len(part) if part else 0
                    continue
                    
                cleaned = clean_query(part)
                if cleaned and len(cleaned) >= 3:
                    words = cleaned.lower().split()
                    if not (len(words) == 1 and words[0] in FORBIDDEN_SOLO_WORDS):
                        part_stripped = part.strip()
                        pos = original.find(part_stripped, current_pos)
                        if pos >= 0:
                            query_parts.append((cleaned, part_stripped, pos, pos + len(part_stripped)))
                
                current_pos += len(part)
        else:
            words = query_stripped.lower().split()
            if not (len(words) == 1 and words[0] in FORBIDDEN_SOLO_WORDS):
                query_parts = [(query_stripped, original, 0, len(original))]
            else:
                query_parts = []
        
        for query_part, original_part, part_start, part_end in query_parts:
            if len(query_part) < 3:
                continue
                
            search_targets = []
            ticker_map = {}
            
            for t, company_name in tickers.items():
                normalized, _ = normalize_company_name(company_name)
                search_targets.append(company_name)
                search_targets.append(normalized)
                search_targets.append(t)
                ticker_map[company_name.lower()] = t
                ticker_map[normalized] = t
                ticker_map[t.upper()] = t
            
            if _HAS_RAPIDFUZZ:
                matches = process.extract(query_part, search_targets, scorer=fuzz.WRatio, limit=10)
                if debug:
                    debug_info[f"rapidfuzz_matches_{query_part}"] = matches
                for match_text, score, _ in matches:
                    min_score = 75 if len(query_part) < 5 else 65
                    if score >= min_score:
                        t = ticker_map.get(match_text.upper()) or ticker_map.get(match_text.lower()) or ticker_map.get(match_text)
                        if t:
                            confidence = min(0.95, score / 100.0)
                            match_info = (confidence, original_part, part_start, part_end)
                            
                            if t not in results or results[t][0] < confidence:
                                results[t] = match_info
            else:
                normalized_companies = [normalize_company_name(c)[0] for c in companies]
                close = get_close_matches(query_part, normalized_companies, n=5, cutoff=0.65)
                if debug:
                    debug_info[f"difflib_matches_{query_part}"] = close
                for normalized_match in close:
                    t = name_to_ticker.get(normalized_match)
                    if t:
                        match_info = (0.85, original_part, part_start, part_end)
                        
                        if t not in results or results[t][0] < 0.85:
                            results[t] = match_info
    
    # 6) Final filtering
    if len(query_stripped) < 4:
        min_confidence = 0.85
    elif is_multi_query:
        min_confidence = 0.70
    else:
        min_confidence = 0.75
    
    final = {t: info for t, info in results.items() if t in tickers and info[0] >= min_confidence}
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    
    if debug:
        debug_info["elapsed_ms"] = elapsed_ms
        debug_info["raw_results"] = {k: (v[0], v[1]) for k, v in results.items()}
        debug_info["final_results"] = {k: (v[0], v[1]) for k, v in final.items()}
    
    # Sort by position in query (then by confidence)
    sorted_list = sorted(final.items(), key=lambda x: (x[1][2], -x[1][0]))
    return sorted_list, elapsed_ms, debug_info if debug else None


def replace_tickers_in_query(query, ticker_matches, tickers):
    """
    Replace company names/tickers in query with hashtag format.
    Returns the updated query string ready for AI model consumption.
    """
    if not ticker_matches:
        return query
    
    # Sort by position (descending) to replace from end to start
    sorted_matches = sorted(ticker_matches, key=lambda x: -x[1][2])
    
    result = query
    for ticker, (confidence, match_text, start, end) in sorted_matches:
        # Replace the matched text with #TICKER
        result = result[:start] + f"#{ticker}" + result[end:]
    
    return result


@app.post("/extract-tickers", response_model=TickerResponse)
async def extract_tickers(request: TickerRequest):
    """
    Extract tickers from a natural language query and return updated query.
    
    Example request:
    ```json
    {
        "query": "compare apple and amazon",
        "debug": false
    }
    ```
    """
    try:
        # Get tickers data (from cache or load)
        csv_path = request.csv_path or locate_default_tickers_csv()
        tickers, name_to_ticker, companies, keyword_index = get_tickers_data(csv_path)
        
        # Extract tickers
        ticker_matches, elapsed_ms, debug_info = extract_tickers_from_query(
            request.query, 
            tickers, 
            name_to_ticker, 
            companies, 
            keyword_index, 
            debug=request.debug
        )
        
        # Replace tickers in query
        updated_query = replace_tickers_in_query(request.query, ticker_matches, tickers)
        detected_tickers = [t for t, _ in ticker_matches]
        
        return TickerResponse(
            original_query=request.query,
            updated_query=updated_query,
            detected_tickers=detected_tickers,
            elapsed_ms=round(elapsed_ms, 3),
            success=True,
            debug_info=debug_info if request.debug else None
        )
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        return TickerResponse(
            original_query=request.query,
            updated_query=request.query,
            detected_tickers=[],
            elapsed_ms=0.0,
            success=False,
            error=str(e)
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "has_rapidfuzz": _HAS_RAPIDFUZZ,
        "cache_loaded": _TICKERS_CACHE is not None
    }


@app.post("/reload-tickers")
async def reload_tickers(csv_path: Optional[str] = None):
    """Reload tickers CSV (useful for updates without restart)."""
    try:
        path = csv_path or locate_default_tickers_csv()
        tickers, name_to_ticker, companies, keyword_index = get_tickers_data(path, force_reload=True)
        return {
            "success": True,
            "message": f"Loaded {len(tickers)} tickers from {path}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def extract_tickers_function(query: str, csv_path: str = None, debug: bool = False) -> dict:
    """
    Standalone function to extract tickers from a query.
    
    Args:
        query: Natural language query string
        csv_path: Optional path to tickers CSV (uses default if None)
        debug: Enable debug output
    
    Returns:
        dict: {
            "original_query": str,
            "updated_query": str,
            "detected_tickers": List[str],
            "elapsed_ms": float,
            "success": bool,
            "error": Optional[str],
            "debug_info": Optional[dict]
        }
    
    Example:
        >>> result = extract_tickers_function("compare apple and amazon")
        >>> print(result["updated_query"])
        "compare #AAPL and #AMZN"
    """
    print("Extracting tickers from query: -------<>---<>-<>----<>-<>---<>---------", query)
    
    # return {
    #         "original_query": query,
    #         "updated_query": query,
    #         "detected_tickers": [],
    #         "elapsed_ms": 0.0,
    #         "success": True,
    #         "error": None,
    #         "debug_info": debug_info if debug else None
    # }
    
    try:
        # Get tickers data (from cache or load)
        if csv_path is None:
            csv_path = locate_default_tickers_csv()
        
        tickers, name_to_ticker, companies, keyword_index = get_tickers_data(csv_path)
        
        # Extract tickers
        ticker_matches, elapsed_ms, debug_info = extract_tickers_from_query(
            query, 
            tickers, 
            name_to_ticker, 
            companies, 
            keyword_index, 
            debug=debug
        )
        
        # Replace tickers in query
        updated_query = replace_tickers_in_query(query, ticker_matches, tickers)
        detected_tickers = [t for t, _ in ticker_matches]
        print("-------<>---<>-<>111111<>-<>---<>---------", updated_query)
        return {
            "original_query": query,
            "updated_query": updated_query,
            "detected_tickers": detected_tickers,
            "elapsed_ms": round(elapsed_ms, 3),
            "success": True,
            "error": None,
            "debug_info": debug_info if debug else None
        }
        
    except FileNotFoundError as e:
        return {
            "original_query": query,
            "updated_query": query,
            "detected_tickers": [],
            "elapsed_ms": 0.0,
            "success": False,
            "error": f"CSV file not found: {str(e)}",
            "debug_info": None
        }
    except Exception as e:
        return {
            "original_query": query,
            "updated_query": query,
            "detected_tickers": [],
            "elapsed_ms": 0.0,
            "success": False,
            "error": str(e),
            "debug_info": None
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)