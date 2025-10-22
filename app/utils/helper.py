import os, re, json, time, math, datetime as dt
from typing import Dict, Any, List, Iterable, Optional, Tuple
from urllib.parse import quote_plus, urlparse, urljoin
from urllib.robotparser import RobotFileParser
from collections import defaultdict
import contextvars  # NEW: per-request LLM selection

import httpx        # NEW: for Ollama calls
import orjson
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError, OperationalError

# Enhanced web search dependencies
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from readability import Document
import trafilatura
from bs4 import BeautifulSoup
import newspaper
from difflib import SequenceMatcher

import logging, uuid
from starlette.datastructures import UploadFile as StarletteUploadFile
import mimetypes


from app.config.settings import (
    SQL_ONLY, DANGEROUS, SEMICOLON, ALLOWED_TB, OFFICIAL_DOMAINS, LOW_PRIORITY_DOMAINS,
    SCHEMA_DOC, CREATE_VIEWS_SQL, PLANNER_SYSTEM_DEFAULT, ANSWER_SYSTEM_DEFAULT,
    SCHEMA_CAPABLE_KEYWORDS, NEWS_KEYWORDS, NODE_ANALYZE_URL, GREETING_WORDS,
    FINANCE_KEYWORDS, SMALLTALK_KEYWORDS, NEWS_KEYWORDS, SCHEMA_CAPABLE_KEYWORDS,
    TICKER_CANDIDATE, _STOPWORDS, NODE_ANALYZE_URL
)

import contextvars
import requests as _req

ACTIVE_LLM    = contextvars.ContextVar("ACTIVE_LLM", default="chatgpt")
LLAMA_MODEL   = contextvars.ContextVar("LLAMA_MODEL", default=os.getenv("OLLAMA_MODEL", "llama3.1:8b"))
OLLAMA_BASE   = (os.getenv("OLLAMA_BASE") or "http://localhost:11434").rstrip("/")
OLLAMA_CHAT   = f"{OLLAMA_BASE}/api/chat"     # use chat endpoint (POST)
OLLAMA_TAGS   = f"{OLLAMA_BASE}/api/tags"     # list installed models
OLLAMA_VERSION= f"{OLLAMA_BASE}/api/version"  # sanity check

def set_active_llm(provider: str, model: str | None = None):
    prov = (provider or "").strip().lower()
    if prov == "llama":
        ACTIVE_LLM.set("llama")
        if model:
            LLAMA_MODEL.set(model)
    else:
        ACTIVE_LLM.set("chatgpt")

def get_active_llm():
    return ACTIVE_LLM.get(), LLAMA_MODEL.get()


def _ollama_messages_from_openai(messages: list[dict]) -> list[dict]:
    """
    Map OpenAI-style messages to Ollama chat format.
    """
    out = []
    for m in messages:
        role = (m.get("role") or "").strip()
        content = m.get("content") or ""
        if not role or not content:
            continue
        out.append({"role": role, "content": content})
    return out


def _ollama_list_tags() -> list[str]:
    try:
        r = _req.get(OLLAMA_TAGS, timeout=10)
        r.raise_for_status()
        data = r.json() or {}
        models = data.get("models") or []
        return [m.get("name") for m in models if isinstance(m, dict) and m.get("name")]
    except Exception:
        return []


def _explain_ollama_404(model: str) -> str:
    tags = _ollama_list_tags()
    if tags:
        return (f"Ollama returned 404 for model '{model}'. Installed models are:\n"
                + "\n".join([f" - {t}" for t in tags])
                + "\nSet OLLAMA_MODEL to one of the above, or pull the desired tag:\n"
                + f"  ollama pull {model}\n")
    return (f"Ollama returned 404 for model '{model}'. No matching tag found. "
            f"Check that the model is pulled:\n  ollama pull {model}\n"
            f"Or set OLLAMA_MODEL to an installed tag.\n")


def _ollama_chat_stream_sync(messages: list[dict], model: str) -> iter:
    """
    Streaming chat with Ollama (/api/chat). Synchronous, no asyncio.
    """
    payload = {
        "model": model,
        "messages": _ollama_messages_from_openai(messages),
        "stream": True,
    }
    with _req.post(OLLAMA_CHAT, json=payload, stream=True, timeout=300) as r:
        if r.status_code == 404:
            # read body for error detail, then raise a friendly message
            try:
                body = r.json()
                detail = body.get("error") or body
            except Exception:
                detail = r.text
            raise RuntimeError(_explain_ollama_404(model) + f"\nDetails: {detail}")
        r.raise_for_status()
        for line in r.iter_lines(decode_unicode=True):
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            # Ollama /api/chat streams lines like {"message":{"role":"assistant","content":"..."}, "done":false}
            msg = (obj or {}).get("message") or {}
            chunk = msg.get("content") or ""
            if chunk:
                yield chunk


def _ollama_chat_once_sync(messages: list[dict], model: str) -> str:
    """
    Single chat response with Ollama (/api/chat, stream=False).
    """
    payload = {
        "model": model,
        "messages": _ollama_messages_from_openai(messages),
        "stream": False,
    }
    r = _req.post(OLLAMA_CHAT, json=payload, timeout=300)
    if r.status_code == 404:
        try:
            body = r.json()
            detail = body.get("error") or body
        except Exception:
            detail = r.text
        raise RuntimeError(_explain_ollama_404(model) + f"\nDetails: {detail}")
    r.raise_for_status()
    data = r.json() or {}
    # Non-stream response has: {"message":{"role":"assistant","content":"..."}, ...}
    msg = (data or {}).get("message") or {}
    return msg.get("content") or ""

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("ai_controller")

# ---------- ENV ----------
BASE = "/home/azureuser/llm/server"
ENV  = os.path.join(BASE, ".env") if os.path.isdir(BASE) else ".env"
load_dotenv(ENV)

HOST = os.getenv("SQLSERVER_HOST")
PORT = os.getenv("SQLSERVER_PORT", "1433")
DB   = os.getenv("SQLSERVER_DB")
USER = os.getenv("SQLSERVER_USER")
PWD  = os.getenv("SQLSERVER_PASSWORD")
DRV  = os.getenv("ODBC_DRIVER", "ODBC Driver 18 for SQL Server")
LOGIN_TIMEOUT = os.getenv("SQLSERVER_LOGIN_TIMEOUT", "10")
CONN_TIMEOUT  = os.getenv("SQLSERVER_CONN_TIMEOUT", "20")


# Enhanced web search credentials
GOOGLE_CSE_KEY = os.getenv("GOOGLE_CSE_KEY", "").strip()
GOOGLE_CSE_CX  = os.getenv("GOOGLE_CSE_CX", "").strip()
BING_API_KEY   = "6806eeb1a92747c4acb3cd0d93c804c7"

# Auto web fallback configuration
AUTO_WEB_FALLBACK = os.getenv("AUTO_WEB_FALLBACK", "true").lower() in ("1","true","yes")
FAST_WEB_MAX_PAGES = int(os.getenv("FAST_WEB_MAX_PAGES", "5"))

params = {
    "driver": DRV,
    "Encrypt": "yes",
    "TrustServerCertificate": "no",
    "LoginTimeout": LOGIN_TIMEOUT,
    "Connection Timeout": CONN_TIMEOUT,
}
param_str = "&".join([f"{k}={quote_plus(v)}" for k, v in params.items()])
ENGINE_URL = f"mssql+pyodbc://{quote_plus(USER)}:{quote_plus(PWD)}@{HOST}:{PORT}/{quote_plus(DB)}?{param_str}"

# === OpenAI/Azure clients (existing) ===
USE_AZURE = os.getenv("AZURE_OPENAI", "false").lower() in ("1","true","yes")
if USE_AZURE:
    from openai import AzureOpenAI
    OAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    OAI_API_KEY    = os.getenv("AZURE_OPENAI_API_KEY")
    OAI_ENDPOINT   = os.getenv("AZURE_OPENAI_ENDPOINT")
    OAI_API_VER    = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
    oai_client = AzureOpenAI(api_key=OAI_API_KEY, azure_endpoint=OAI_ENDPOINT, api_version=OAI_API_VER)
    CHAT_MODEL = OAI_DEPLOYMENT
else:
    from openai import OpenAI
    OAI_API_KEY = os.getenv("OPENAI_API_KEY")
    oai_client = OpenAI(api_key=OAI_API_KEY)
    CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o")

# === NEW: Per-request LLM selection via ContextVar ===
import requests as _req  # use sync requests for Ollama streaming

ACTIVE_LLM = contextvars.ContextVar("ACTIVE_LLM", default="chatgpt")
LLAMA_MODEL = contextvars.ContextVar("LLAMA_MODEL", default=os.getenv("OLLAMA_MODEL", "llama3.1:8b"))

# Use a base URL and build endpoints to avoid 404s from double "/api"
OLLAMA_BASE = os.getenv("OLLAMA_BASE", "http://localhost:11434").rstrip("/")
OLLAMA_GENERATE = f"{OLLAMA_BASE}/api/generate"   # sync streaming endpoint



def _format_chat_prompt(messages: List[Dict[str, str]]) -> str:
    parts = []
    for m in messages:
        role = (m.get("role") or "").strip().upper()
        content = m.get("content") or ""
        if role and content:
            parts.append(f"{role}: {content}")
    return "\n".join(parts)



def open_engine():
    return create_engine(
        ENGINE_URL,
        fast_executemany=True,
        pool_pre_ping=True,
        pool_size=8,
        max_overflow=8,
    )

def create_robust_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    return session

engine = open_engine()
try:
    with engine.begin() as conn:
        for stmt in [s.strip() for s in CREATE_VIEWS_SQL.split(";") if s.strip()]:
            conn.exec_driver_sql(stmt)
except Exception as e:
    print(f"[warn] ensure_views failed: {e}")

# ---------- Enhanced Web Search Functions (unchanged) ----------
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

def extract_text_multiple_methods(html_content: str, url: str) -> Dict[str, str]:
    results = {}
    try:
        text = trafilatura.extract(html_content, include_links=False, include_images=False)
        if text and len(text) > 200:
            results['trafilatura'] = text
    except Exception:
        pass
    try:
        doc = Document(html_content)
        title = doc.short_title()
        content = doc.summary()
        text = BeautifulSoup(content, 'html.parser').get_text()
        if text and len(text) > 200:
            results['readability'] = {'title': title, 'text': text}
    except Exception:
        pass
    try:
        article = newspaper.Article(url)
        article.set_html(html_content)
        article.parse()
        if article.text and len(article.text) > 200:
            results['newspaper'] = {
                'title': article.title,
                'text': article.text,
                'authors': article.authors,
                'publish_date': article.publish_date
            }
    except Exception:
        pass
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        if text and len(text) > 200:
            results['beautifulsoup'] = text
    except Exception:
        pass
    return results

def calculate_content_quality(text: str, query: str) -> float:
    if not text or len(text) < 100:
        return 0.0
    score = 0.0
    query_lower = query.lower()
    text_lower = text.lower()
    length_score = min(len(text) / 5000, 1.0)
    score += length_score * 20
    query_words = query_lower.split()
    matches = sum(1 for word in query_words if word in text_lower)
    if query_words:
        relevance_score = matches / len(query_words)
        score += relevance_score * 50
    structure_indicators = ['\n\n', '. ', ', ', ':', ';']
    structure_score = sum(min(text.count(ind) / 10, 1) for ind in structure_indicators)
    score += structure_score * 5
    sentences = text.split('.')
    if len(sentences) > 1:
        unique_sentences = len(set(sentences))
        repetition_penalty = (len(sentences) - unique_sentences) / len(sentences)
        score -= repetition_penalty * 20
    return max(0.0, min(100.0, score))

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
        r = requests.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=15)
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
        r = requests.get("https://api.bing.microsoft.com/v7.0/search", headers=headers, params=params, timeout=15)
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

def fetch_and_extract_content(url: str, session: requests.Session, timeout: int = 25) -> Optional[Dict[str, Any]]:
    try:
        response = session.get(url, timeout=timeout, allow_redirects=True)
        if response.status_code != 200:
            return None
        content_type = response.headers.get('content-type', '').lower()
        if 'html' not in content_type and 'text' not in content_type:
            return None
        html_content = response.text
        extraction_results = extract_text_multiple_methods(html_content, url)
        if not extraction_results:
            return None
        best_text, best_title = "", ""
        for method, result in extraction_results.items():
            if isinstance(result, str):
                text, title = result, ""
            else:
                text, title = result.get('text', ''), result.get('title', '')
            if text and len(text) > 200 and len(text) > len(best_text):
                best_text, best_title = text, title
        if not best_text:
            return None
        best_text = ' '.join(best_text.split())[:12000]
        return {"url": url, "title": best_title or "Untitled", "text": best_text,
                "length": len(best_text), "extraction_methods": list(extraction_results.keys())}
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return None

def web_fetch_enhanced(results: List[Dict[str, Any]], max_pages: int = 8, fast: bool = False) -> List[Dict[str, Any]]:
    session = create_robust_session()
    docs = []
    sorted_results = sorted(results[:max_pages], key=lambda x: -x.get("priority", 0))
    for result in sorted_results:
        url = result.get("url", "")
        if not url:
            continue
        content = fetch_and_extract_content(url, session, timeout=12 if fast else 25)
        if content:
            query = result.get("original_query", "")
            quality_score = calculate_content_quality(content["text"], query)
            content.update({
                "original_title": result.get("title", ""),
                "snippet": result.get("snippet", ""),
                "priority": result.get("priority", 0),
                "quality_score": quality_score,
                "source_type": result.get("source_type", "unknown")
            })
            docs.append(content)
        if len(docs) >= max_pages:
            break
    session.close()
    docs.sort(key=lambda x: (-x.get("quality_score", 0), -x.get("priority", 0)))
    return docs

def generate_enhanced_summary(question: str, sources: List[Dict[str, Any]]) -> Iterable[str]:
    if not sources:
        yield "I couldn't retrieve any reliable content from web sources."
        return
    source_contexts, source_map = [], []
    for i, source in enumerate(sources, 1):
        title = source.get("title", "Untitled")
        url = source.get("url", "")
        text = source.get("text", "")[:2000]
        priority = source.get("priority", 0)
        quality = source.get("quality_score", 0)
        quality_indicator = ""
        if priority >= 100:
            quality_indicator = " [OFFICIAL]"
        elif priority >= 80:
            quality_indicator = " [AUTHORITATIVE]"
        elif quality >= 70:
            quality_indicator = " [HIGH QUALITY]"
        source_map.append(f"[{i}] {title}{quality_indicator} — {url}")
        source_contexts.append(f"SOURCE [{i}]{quality_indicator}\nTITLE: {title}\nURL: {url}\nCONTENT:\n{text}\n")
    system_prompt = """You are an expert researcher and analyst. Provide accurate, well-sourced answers based on the provided sources.
Guidelines:
- Prioritize OFFICIAL and AUTHORITATIVE sources
- Use [n] citations for factual claims
- Be specific with numbers and dates
- If sources conflict, note it and cite both
- Clear structure; concise but thorough"""
    user_prompt = f"""QUESTION: {question}

{chr(10).join(source_contexts)}

Provide a comprehensive answer with inline [n] citations."""
    messages = [{"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}]
    for chunk in oai_stream(messages, temperature=0.2, max_tokens=2000):
        yield chunk
    yield "\n\n## Sources\n"
    for src in source_map:
        yield f"- {src}\n"

def perform_enhanced_web_search(query: str, max_pages: int = 8, fast: bool = False) -> Iterable[str]:
    all_results = []
    google_results = web_search_google_cse_enhanced(query, num=10)
    for r in google_results:
        r["original_query"] = query
    all_results.extend(google_results)
    if len(google_results) < 8:
        bing_results = web_search_bing_enhanced(query, count=8)
        for r in bing_results:
            r["original_query"] = query
        existing_urls = {r["url"] for r in all_results}
        all_results.extend([r for r in bing_results if r["url"] not in existing_urls])
    if not all_results:
        yield "I couldn't retrieve any search results. Please check the search service configuration."
        return
    docs = web_fetch_enhanced(all_results, max_pages=max_pages, fast=fast)
    if not docs:
        yield "I found search results but couldn't access the full content. Here's what I found from the snippets:\n\n"
        for i, result in enumerate(all_results[:max_pages], 1):
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            url = result.get("url", "")
            indicator = " [OFFICIAL]" if result.get("priority", 0) >= 100 else ""
            yield f"[{i}] **{title}**{indicator}\n{snippet}\nSource: {url}\n\n"
        return
    for chunk in generate_enhanced_summary(query, docs):
        yield chunk

# ---------- SQL utils (unchanged) ----------
def normalize_sql_server(sql: str) -> str:
    s = sql
    s = re.sub(r"(?i)\b(current_date|now\(\))\b", "CAST(GETDATE() AS DATE)", s)
    s = re.sub(r"(?i)\bgetdate\(\)\b", "GETDATE()", s)
    s = re.sub(r"(?i)CAST\(GETDATE\(\) AS DATE\)\s*-\s*INTERVAL\s*'(\d+)'\s*YEAR",
               r"DATEADD(year, -\1, CAST(GETDATE() AS DATE))", s)
    s = re.sub(r"(?i)\bINTERVAL\s+(\d+)\s+YEAR\b",
               r"DATEADD(year, -\1, CAST(GETDATE() AS DATE))", s)
    m = re.search(r"(?i)\blimit\s+(\d+)\b", s)
    if m and not re.search(r"(?i)\bselect\s+top\s+\d+", s):
        n = m.group(1)
        s = re.sub(r"(?i)^\s*select\s+", f"SELECT TOP {n} ", s, count=1)
        s = re.sub(r"(?i)\s+limit\s+\d+\s*$", "", s)
    return s

def sanitize_sql(sql: str) -> str:
    sql = normalize_sql_server(sql)
    if not SQL_ONLY.match(sql or ""):
        raise ValueError("Planner did not return a single SELECT (or WITH-CTE ending in SELECT).")
    if DANGEROUS.search(sql):
        raise ValueError("Unsafe SQL detected.")
    if SEMICOLON.search(sql):
        raise ValueError("Semicolons are not allowed.")
    if not ALLOWED_TB.search(sql):
        raise ValueError("SQL must reference dbo.vTickers or dbo.vDividends.")
    return sql.strip()

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

# ---------- DB execution (streaming) ----------
def exec_sql_stream(engine, sql: str, fetch_size: int = 10000):
    set_cmds = "SET NOCOUNT ON; SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;"
    q = f"{set_cmds}\n{sql}"
    conn = engine.connect().execution_options(stream_results=True, yield_per=fetch_size)
    result = conn.exec_driver_sql(q)
    columns = list(result.keys())
    def row_iter():
        nonlocal result, conn
        try:
            for row in result:
                yield tuple(row)
        finally:
            result.close(); conn.close()
    return columns, row_iter()

# ---------- Metrics ----------
def safe_float(x):
    try:
        return float(x) if x is not None and str(x).strip() != "" else None
    except Exception:
        return None

def parse_date(x):
    try:
        if x in (None, "", "(null)"): return None
        return dt.date.fromisoformat(str(x)[:10])
    except Exception:
        return None

def compute_dividend_metrics(columns: List[str], rows: Iterable[tuple], last_n_years: Optional[int]):
    idx = {c.lower(): i for i, c in enumerate(columns)}
    have = lambda name: name.lower() in idx
    metrics = {"rows": 0, "tickers": {}, "date_min": None, "date_max": None, "filtered_years": last_n_years or 0}
    today = dt.date.today()
    cutoff = dt.date(today.year - last_n_years, today.month, today.day) if last_n_years else None
    for r in rows:
        metrics["rows"] += 1
        ticker = r[idx["ticker"]] if have("Ticker") else None
        pay_dt = parse_date(r[idx["payment_date"]]) if have("Payment_Date") else None
        adj_amt = None
        if have("AdjDividend_Amount"): adj_amt = safe_float(r[idx["adjdividend_amount"]])
        if adj_amt is None and have("Dividend_Amount"): adj_amt = safe_float(r[idx["dividend_amount"]])
        if cutoff and pay_dt and pay_dt < cutoff: continue
        if pay_dt:
            metrics["date_min"] = pay_dt if (metrics["date_min"] is None or pay_dt < metrics["date_min"]) else metrics["date_min"]
            metrics["date_max"] = pay_dt if (metrics["date_max"] is None or pay_dt > metrics["date_max"]) else metrics["date_max"]
        if ticker:
            t = metrics["tickers"].setdefault(ticker, {"total":0.0,"count":0,"latest_date":None,"latest_amt":None})
            if adj_amt is not None:
                t["total"] += adj_amt; t["count"] += 1
            if pay_dt and (t["latest_date"] is None or pay_dt > t["latest_date"]):
                t["latest_date"] = pay_dt; t["latest_amt"]  = adj_amt
    metrics["ranking"] = sorted(metrics["tickers"].items(), key=lambda kv: (-kv[1]["total"], kv[0]))
    return metrics

# ---------- LLM backends ----------
def _format_chat_prompt(messages: List[Dict[str, str]]) -> str:
    parts = []
    for m in messages:
        role = (m.get("role") or "").strip().upper()
        content = m.get("content") or ""
        if role and content:
            parts.append(f"{role}: {content}")
    return "\n".join(parts)

async def _ollama_chat_stream(messages: List[Dict[str, str]], model: str) -> Iterable[str]:
    prompt = _format_chat_prompt(messages)
    payload = {"model": model, "prompt": prompt, "stream": True}
    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", OLLAMA_URL, json=payload) as r:
            async for line in r.aiter_lines():
                if not line:
                    continue
                try:
                    j = json.loads(line)
                    content = j.get("response", "")
                    if content:
                        yield content
                except Exception:
                    # Some Ollama builds send non-JSON keepalives; ignore
                    continue

async def _ollama_chat_once(messages: List[Dict[str, str]], model: str) -> str:
    prompt = _format_chat_prompt(messages)
    payload = {"model": model, "prompt": prompt, "stream": False}
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(OLLAMA_URL, json=payload)
        r.raise_for_status()
        data = r.json() or {}
        return data.get("response", "") or ""

# ---------- OpenAI helpers (NOW: dynamic) ----------
def oai_stream(messages: list[dict], temperature=0.2, max_tokens=2000):
    """
    Streams from the active provider:
      - llama  -> Ollama /api/chat (sync)
      - chatgpt-> OpenAI/Azure (existing)
    """
    provider, llama_model = get_active_llm()
    if provider == "llama":
        for chunk in _ollama_chat_stream_sync(messages, llama_model):
            yield chunk
        return

    # OpenAI/Azure path (unchanged)
    stream = oai_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=temperature,
        stream=True,
        max_tokens=max_tokens
    )
    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta and delta.content is not None:
            yield delta.content

def oai_plan(question: str, planner_system: str):
    """
    Planner step that returns JSON. Uses active provider.
    Llama path uses Ollama /api/chat (non-stream) and then json.loads fallback.
    """
    provider, llama_model = get_active_llm()
    if provider == "llama":
        msgs = [
            {"role": "system", "content": planner_system},
            {"role": "user",   "content": question},
        ]
        try:
            result_text = _ollama_chat_once_sync(msgs, llama_model)
        except Exception as e:
            logger.error(f"[planner] Llama failed: {e}")
            # degrade to simple chat path
            return {"action": "chat", "final_answer": f"I couldn't plan with llama ({e})."}
        try:
            return json.loads(result_text)
        except Exception:
            # If the model didn't return JSON, treat as direct chat
            return {"action": "chat", "final_answer": result_text}

    # OpenAI/Azure path (unchanged)
    resp = oai_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{"role":"system","content": planner_system},
                  {"role":"user","content": question}],
        temperature=0.1,
        max_tokens=2000,
    )
    txt = resp.choices[0].message.content.strip()
    try:
        return json.loads(txt)
    except Exception:
        if any(w in question.lower() for w in ["hi","hello","salam","hey"]):
            return {"action":"chat", "final_answer":"Hi! How can I help you today?"}
        return {"action":"chat", "final_answer":"I'm here. Ask about tickers or dividends and I'll pull the data."}

def openai_sse_wrap(text_chunks: Iterable[str], req_id: str):
    yield f'data: {orjson.dumps({"id":req_id,"object":"chat.completion.chunk","choices":[{"delta":{"role":"assistant"}}]}).decode()}\n\n'
    for piece in text_chunks:
        if piece:
            yield f'data: {orjson.dumps({"id":req_id,"object":"chat.completion.chunk","choices":[{"delta":{"content":piece}}]}).decode()}\n\n'
    yield 'data: [DONE]\n\n'

# ---------- Logging ----------
def write_runlog(entry: Dict[str, Any], logfile: str = "runlogger.jsonl"):
    try:
        with open(logfile, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")
    except Exception as e:
        print(f"[warn] failed to write log: {e}")

# ---------- Web Search Helper Functions ----------
def _canonical_url(u: str) -> str:
    try:
        p = urlparse(u)
        return f"{p.scheme}://{p.netloc}{p.path}".rstrip("/")
    except Exception:
        return u

def handle_web_request(question: str, as_stream: bool = True, max_pages: int = 8, fast: bool = False):
    req_id = f"chatcmpl-web-{int(time.time()*1000)}"
    if as_stream:
        def gen():
            yield from perform_enhanced_web_search(question, max_pages=max_pages, fast=fast)
        return openai_sse_wrap(gen(), req_id)
    else:
        return perform_enhanced_web_search(question, max_pages=max_pages, fast=fast)

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

# ---------- Core request pipeline (unchanged logic; now dynamic LLM) ----------
def handle_request(question: str, user_system_all: str, overrides: Dict[str, str], debug=False, logfile="runlogger.jsonl"):
    """
    Core request pipeline. This version adds a per-request provider/model switch so you
    can run everything (planner, chat, SQL fallback, web search composition) on Llama
    via Ollama when the request says so — without breaking ChatGPT defaults.

    Expects (optionally) in `overrides`:
      - llm_provider: "llama" | "chatgpt" (anything else → chatgpt)
      - llama_model : e.g. "llama3.1:8b" (optional; uses env default if empty)
    """
    
    
    from  app.controllers.ai_controller import query_logger

    # --- NEW: switch provider/model per-request (no-op unless provided)
    prov = (overrides.get("llm_provider") or "").strip().lower()
    ltag = (overrides.get("llama_model") or "").strip()
    if prov == "llama":
        set_active_llm("llama", ltag or None)
        logger.info(f"[router] Using Llama via Ollama (model='{ltag or 'default'}').")
    else:
        set_active_llm("chatgpt", None)
        logger.info("[router] Using ChatGPT provider.")

    # Explicit web mode if requested
    use_web = bool(overrides.get("use_web")) or question.strip().lower().startswith("web:")
    if use_web:
        q = question[4:].strip() if question.strip().lower().startswith("web:") else question
        return handle_web_request(q)

    # Assemble effective system prompts
    planner_system = overrides.get("planner_system") or PLANNER_SYSTEM_DEFAULT
    answer_system  = overrides.get("answer_system")  or ANSWER_SYSTEM_DEFAULT
    if user_system_all:
        planner_system = planner_system + "\n\n" + user_system_all
        answer_system  = answer_system  + "\n\n" + user_system_all

    # Prepend OCR/DI/file text if present
    if overrides.get("prepend_user"):
        question = overrides["prepend_user"] + question

    # Ticker extraction + intent hints
    if is_greeting_only(question):
        parsed_tickers: List[str] = []
    else:
        parsed_tickers = extract_ticker_list(question)

    if parsed_tickers and (has_finance_intent(question) or len(parsed_tickers) >= 2):
        question = f"TICKERS_HINT: {','.join(parsed_tickers)}\n" + question

    # Early auto web switch (FAST) — fixed routing rules
    if AUTO_WEB_FALLBACK and not bool(overrides.get("use_web")):
        if should_route_to_web(question, parsed_tickers):
            return handle_web_request(question, as_stream=True, max_pages=FAST_WEB_MAX_PAGES, fast=True)

    start = time.time()
    plan = oai_plan(question, planner_system)   # uses active provider (ChatGPT or Llama)
    plan_ms = int((time.time() - start) * 1000)

    run = {
        "time": dt.datetime.now().isoformat(timespec="seconds"),
        "question": question,
        "action": plan.get("action"),
        "sql": None,
        "plan_ms": plan_ms,
        "sql_ms": None,
        "answer_ms": None,
        "rows_streamed": None,
    }

    # --- CHAT PATH ---
    if plan.get("action") == "chat":
        # Planner thinks it's chat/out-of-schema → optional web fallback
        if AUTO_WEB_FALLBACK and should_route_to_web(question, parsed_tickers):
            return handle_web_request(question, as_stream=True, max_pages=FAST_WEB_MAX_PAGES, fast=True)

        msgs = [{"role": "system", "content": "You are a friendly, concise assistant."}]
        if user_system_all:
            msgs[0]["content"] += "\n\n" + user_system_all
        msgs.append({"role": "user", "content": plan.get("final_answer") or question})

        def gen():
            ans_start = time.time()
            for tok in oai_stream(msgs):          # uses active provider (ChatGPT or Llama)
                yield tok
            run["answer_ms"] = int((time.time() - ans_start) * 1000)
            write_runlog(run, logfile)

        req_id = f"chatcmpl-{int(time.time() * 1000)}"
        return openai_sse_wrap(gen(), req_id)

    # --- SQL PATH ---
    sql_raw = (plan.get("sql") or "").strip()
    
    if sql_raw:
    # Log the raw user query and the SQL generated by the planner
        metadata = {
            "action": plan.get("action"),
            "llm_provider": overrides.get("llm_provider"),
            "use_web": overrides.get("use_web"),
        }
        
        query_logger.log_query(
            rid=run.get("id", "no-id"),
            query=f"User Query:\n{question}\n\nGenerated SQL:\n{sql_raw}",
            metadata=metadata
        )

    
    try:
        sql = sanitize_sql(sql_raw)
        if user_wants_cap(question):
            if not re.search(r"(?i)\bselect\s+top\s+\d+", sql) and not re.search(r"(?i)\boffset\s+\d+\s+rows\s+fetch", sql):
                sql = re.sub(r"(?i)^\s*select\s+", "SELECT TOP 200 ", sql, count=1)
    except Exception as e:
        # Planner/sql sanitize fails → fast web fallback if appropriate
        if AUTO_WEB_FALLBACK and should_route_to_web(question, parsed_tickers):
            return handle_web_request(question, as_stream=True, max_pages=FAST_WEB_MAX_PAGES, fast=True)

        def gen_err():
            yield f"I couldn't form a safe SQL query ({e}). Try adding ticker, date range, or metric."

        run["sql"] = f"[planner_error] {e}\nSQL_RAW={sql_raw}"
        write_runlog(run, logfile)
        req_id = f"chatcmpl-{int(time.time() * 1000)}"
        return openai_sse_wrap(gen_err(), req_id)

    run["sql"] = sql
    if debug:
        print("# [DEBUG] SQL\n", sql)

    # Execute with tiny retry
    sql_open_t0 = time.time()
    try:
        columns, rows_iter = exec_sql_stream(engine, sql)
    except OperationalError:
        time.sleep(0.4)
        columns, rows_iter = exec_sql_stream(engine, sql)
    run["sql_ms"] = int((time.time() - sql_open_t0) * 1000)

    # Streaming composition: rows + final explanation
    last_n_years = parse_last_n_years(question)
    rows_buffer: List[tuple] = []

    def composed():
        # a) stream data table
        yield "\n# DATA\n\n"
        yield "│ " + " │ ".join(columns) + " │\n"
        yield "─" * min(180, 4 * len(columns) + 8) + "\n"
        cnt = 0
        for r in rows_iter:
            cnt += 1
            rows_buffer.append(r)
            cells = ["(null)" if (v is None or (isinstance(v, float) and pd.isna(v))) else str(v) for v in r]
            yield "│ " + " │ ".join(cells) + " │\n"
            if cnt % 5000 == 0:
                yield f"… streamed {cnt} rows …\n"
        run["rows_streamed"] = cnt
        yield f"(total rows streamed: {cnt})\n"

        # b0) zero-row safeguard → web fallback
        if AUTO_WEB_FALLBACK and cnt == 0 and should_route_to_web(question, parsed_tickers):
            yield "\n# ANSWER\n\n"
            for chunk in perform_enhanced_web_search(question, max_pages=FAST_WEB_MAX_PAGES, fast=True):
                yield chunk
            write_runlog(run, logfile)
            return

        # b) compute metrics and stream final explanation
        m = compute_dividend_metrics(columns, rows_buffer, last_n_years=last_n_years)
        sample_txt = ""
        if rows_buffer:
            sample_txt += "HEADERS: " + " | ".join(columns) + "\n"
            for rr in rows_buffer[:20]:
                vals = ["" if (v is None or (isinstance(v, float) and pd.isna(v))) else str(v) for v in rr]
                sample_txt += "ROW: " + " | ".join(vals) + "\n"

        rank_lines = []
        if m.get("ranking"):
            for i, (tk, v) in enumerate(m["ranking"][:10], 1):
                tot = v["total"]
                cnt2 = v["count"]
                latest_dt = v["latest_date"].isoformat() if v["latest_date"] else "n/a"
                latest_amt = v["latest_amt"] if (v["latest_amt"] is not None) else "n/a"
                rank_lines.append(f"{i}. {tk}: total={tot:.6f}, payouts={cnt2}, latest={latest_dt} ({latest_amt})")

        date_span = ""
        if m.get("date_min") or m.get("date_max"):
            date_span = f"date_range={m.get('date_min')}..{m.get('date_max')}"

        derived_txt = (
            f"rows_streamed={run['rows_streamed']}; tickers={len(m.get('tickers', {}))}; "
            + (f"{date_span}; " if date_span else "")
            + f"filtered_last_years={m.get('filtered_years', 0)}"
        )
        if rank_lines:
            derived_txt += "\nRANKING (per-share totals):\n" + "\n".join(rank_lines)

        invest_note = ""
        if re.search(r"\$?\s*[0-9][0-9,\.]*\s*\$?", question.replace(",", "")):
            invest_note = (
                "Note: share prices aren't in the dataset; I ranked by per-share total dividends. "
                "Provide entry prices to compute $ payouts for an investment amount."
            )

        yield "\n# ANSWER\n\n"
        ans_t0 = time.time()
        msgs = [
            {
                "role": "system",
                "content": (overrides.get("answer_system") or ANSWER_SYSTEM_DEFAULT)
                + ("\n\n" + user_system_all if user_system_all else ""),
            },
            {
                "role": "user",
                "content": f"QUESTION:\n{question}\n\nDERIVED METRICS:\n{derived_txt}\n\nSAMPLE ROWS:\n{sample_txt}\n\n{invest_note}",
            },
        ]
        for tok in oai_stream(msgs):  # uses active provider (ChatGPT or Llama)
            yield tok
        run["answer_ms"] = int((time.time() - ans_t0) * 1000)
        write_runlog(run, logfile)

    req_id = f"chatcmpl-{int(time.time() * 1000)}"
    return openai_sse_wrap(composed(), req_id)

# ---------- Upload helpers (unchanged) ----------
def is_upload_like(obj) -> bool:
    return obj is not None and hasattr(obj, "filename") and hasattr(obj, "content_type") and hasattr(obj, "read")

def extract_text_via_node(file_name: str, file_bytes: bytes, content_type: str | None = None, rid: str | None = None) -> str:
    tag = f"[{rid}]" if rid else ""
    try:
        guessed = content_type or mimetypes.guess_type(file_name)[0] or "application/octet-stream"
        files = {"file": (file_name, file_bytes, guessed)}
        t0 = time.time()
        logger.info(f"{tag} Handoff → Node {NODE_ANALYZE_URL} file='{file_name}' ctype='{guessed}' size={len(file_bytes)}")
        r = requests.post(NODE_ANALYZE_URL, files=files, timeout=120)
        elapsed = int((time.time() - t0) * 1000)
        logger.info(f"{tag} Node response status={r.status_code} elapsed={elapsed}ms")
        r.raise_for_status()
        data = r.json() or {}
        txt = (data.get("text") or "").strip()
        logger.info(f"{tag} Extracted text length={len(txt)} chars")
        if not txt:
            logger.warning(f"{tag} Node returned empty text")
        return txt
    except Exception as e:
        logger.exception(f"{tag} analyze upload failed: {e}")
        return ""

def _is_upload(obj) -> bool:
    return obj is not None and hasattr(obj, "filename") and hasattr(obj, "content_type") and hasattr(obj, "read")
