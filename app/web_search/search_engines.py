import os, requests
from typing import Dict, Any, List
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from app.config.settings import OFFICIAL_DOMAINS, LOW_PRIORITY_DOMAINS

# Search Engine Credentials
GOOGLE_CSE_KEY = os.getenv("GOOGLE_CSE_KEY", "").strip()
GOOGLE_CSE_CX  = os.getenv("GOOGLE_CSE_CX", "").strip()
BING_API_KEY   = os.getenv("BING_API_KEY", "").strip()

# Shared session with connection pooling and retry strategy
_search_session = None

def get_search_session():
    global _search_session
    if _search_session is None:
        _search_session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=20,
            pool_maxsize=20
        )
        _search_session.mount("http://", adapter)
        _search_session.mount("https://", adapter)
    return _search_session

def calculate_domain_priority(url: str) -> int:
    domain = urlparse(url).netloc.lower()
    for official in OFFICIAL_DOMAINS:
        if official in domain:
            return 100
    if any(x in domain for x in ['investor', 'ir.']):
        return 90
    financial_sites = ['bloomberg', 'reuters', 'wsj', 'ft.', 'marketwatch',
                       'cnbc', 'yahoo.com/finance', 'morningstar', 'fool', 'seekingalpha']
    for site in financial_sites:
        if site in domain:
            return 80
    for low_priority in LOW_PRIORITY_DOMAINS:
        if low_priority in domain:
            return 20
    return 50

def web_search_google_cse_enhanced(query: str, num: int = 12) -> List[Dict[str, Any]]:
    if not GOOGLE_CSE_KEY or not GOOGLE_CSE_CX:
        return []
    financial_terms = ['dividend', 'earnings', 'financial', 'investor', 'stock', 'etf']
    if any(term in query.lower() for term in financial_terms):
        enhanced_query = f"{query} (site:sec.gov OR site:investor.* OR site:morningstar.com OR site:bloomberg.com OR site:reuters.com)"
    else:
        enhanced_query = query
    params = {
        "key": GOOGLE_CSE_KEY, "cx": GOOGLE_CSE_CX, "q": enhanced_query,
        "num": min(max(num, 1), 10), "safe": "off",
        "fields": "items(title,link,snippet,displayLink,formattedUrl)"
    }
    try:
        session = get_search_session()
        r = session.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=15)
        if r.status_code != 200:
            return []
        items = (r.json() or {}).get("items", []) or []
        results = []
        for i, it in enumerate(items, 1):
            url = it.get("link", "")
            priority = calculate_domain_priority(url)
            results.append({
                "rank": i, "title": it.get("title", ""), "url": url,
                "snippet": it.get("snippet", ""), "display_link": it.get("displayLink", ""),
                "priority": priority, "source_type": "google_cse"
            })
        results.sort(key=lambda x: (-x["priority"], x["rank"]))
        return results
    except Exception as e:
        print(f"Google CSE search failed: {e}")
        return []

def web_search_bing_enhanced(query: str, count: int = 12) -> List[Dict[str, Any]]:
    if not BING_API_KEY:
        return []
    headers = {"Ocp-Apim-Subscription-Key": BING_API_KEY}
    params = {"q": query, "count": min(max(count, 1), 15), "mkt": "en-US",
              "responseFilter": "Webpages", "textDecorations": False, "textFormat": "Raw"}
    try:
        session = get_search_session()
        r = session.get("https://api.bing.microsoft.com/v7.0/search", headers=headers, params=params, timeout=15)
        if r.status_code != 200:
            return []
        values = (r.json().get("webPages") or {}).get("value", []) or []
        results = []
        for i, v in enumerate(values, 1):
            url = v.get("url", "")
            priority = calculate_domain_priority(url)
            results.append({
                "rank": i, "title": v.get("name", ""), "url": url,
                "snippet": v.get("snippet", ""), "display_link": urlparse(url).netloc,
                "priority": priority, "source_type": "bing"
            })
        results.sort(key=lambda x: (-x["priority"], x["rank"]))
        return results
    except Exception as e:
        print(f"Bing search failed: {e}")
        return []