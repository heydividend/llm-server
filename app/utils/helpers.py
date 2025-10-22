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