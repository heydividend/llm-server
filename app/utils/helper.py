"""
Cleaned up helper.py - Contains only core request handling functions.

REMOVED DUPLICATES (see commit history for details):
- Database engine setup (lines 169-268) → use app/core/database.py
- LLM client initialization (lines 45-156, 199-223) → use app/core/llm_providers.py
- Web search functions (lines 271-536) → use app/web_search/
- SQL utilities (lines 538-563) → use app/core/database.py
- Helper functions (lines 565-669) → use app/utils/helpers.py
- Metrics computation (lines 669+) → use app/utils/metrics.py
- Duplicate context vars and Ollama functions → use app/core/llm_providers.py

KEPT FUNCTIONS (required by ai_controller.py):
- is_upload_like: Check if object is file upload
- extract_text_via_node: Extract text from uploaded files via Node service
- _maybe_flatten_vision_json: Flatten vision API JSON responses
- handle_request: Main request processing pipeline
- handle_web_request: Web search request handler
"""

import os
import re
import json
import time
import datetime as dt
import logging
import mimetypes
import requests
from typing import Dict, Any, List, Iterable

import orjson
import pandas as pd
from dotenv import load_dotenv

from app.config.settings import (
    PLANNER_SYSTEM_DEFAULT,
    ANSWER_SYSTEM_DEFAULT,
    NODE_ANALYZE_URL,
)

from app.core.database import (
    engine,
    exec_sql_stream,
    sanitize_sql,
)

from app.core.llm_providers import (
    set_active_llm,
    get_active_llm,
    oai_plan,
    oai_stream,
)

from app.web_search.enhanced_search import (
    perform_enhanced_web_search,
)

from app.utils.helpers import (
    is_greeting_only,
    extract_ticker_list,
    has_finance_intent,
    should_route_to_web,
    user_wants_cap,
    parse_last_n_years,
    openai_sse_wrap,
    write_runlog,
)

from app.utils.metrics import compute_dividend_metrics
from app.services.passive_income_planner import PassiveIncomePlanService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("ai_controller")

BASE = "/home/azureuser/llm/server"
ENV = os.path.join(BASE, ".env") if os.path.isdir(BASE) else ".env"
load_dotenv(ENV)

AUTO_WEB_FALLBACK = os.getenv("AUTO_WEB_FALLBACK", "true").lower() in ("1", "true", "yes")
FAST_WEB_MAX_PAGES = int(os.getenv("FAST_WEB_MAX_PAGES", "5"))


def handle_web_request(question: str, as_stream: bool = True, max_pages: int = 8, fast: bool = False):
    """Handle web search requests with streaming or non-streaming responses."""
    req_id = f"chatcmpl-web-{int(time.time()*1000)}"
    if as_stream:
        def gen():
            yield from perform_enhanced_web_search(question, max_pages=max_pages, fast=fast)
        return openai_sse_wrap(gen(), req_id)
    else:
        return perform_enhanced_web_search(question, max_pages=max_pages, fast=fast)


def _maybe_flatten_vision_json(s: str) -> str:
    """
    Flatten vision API JSON responses into plain text.
    Handles Azure Document Intelligence and similar vision API responses.
    """
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
                        if t:
                            lines.append(t)
                elif "words" in pg and pg["words"]:
                    words = [w.get("text", "") for w in pg["words"] if isinstance(w, dict)]
                    if any(words):
                        lines.append(" ".join([w for w in words if w]))
                lines.append("")
        flat = "\n".join(lines).strip()
        return flat or s
    except Exception:
        return s


def handle_request(question: str, user_system_all: str, overrides: Dict[str, str], debug=False, logfile="runlogger.jsonl"):
    """
    Core request pipeline with per-request LLM provider switching.
    
    Supports both ChatGPT and Llama via Ollama for all operations:
    planner, chat, SQL fallback, and web search composition.
    
    Args:
        question: User's query
        user_system_all: System prompt additions
        overrides: Dict containing:
            - llm_provider: "llama" | "chatgpt" (default: chatgpt)
            - llama_model: e.g. "llama3.1:8b" (optional)
            - planner_system: Custom planner system prompt
            - answer_system: Custom answer system prompt
            - prepend_user: Text to prepend to question
            - use_web: Force web search mode
        debug: Enable debug output
        logfile: Path to runlog file
    
    Returns:
        Generator yielding SSE-formatted response chunks
    """
    from app.controllers.ai_controller import query_logger

    prov = (overrides.get("llm_provider") or "").strip().lower()
    ltag = (overrides.get("llama_model") or "").strip()
    if prov == "llama":
        set_active_llm("llama", ltag or None)
        logger.info(f"[router] Using Llama via Ollama (model='{ltag or 'default'}').")
    else:
        set_active_llm("chatgpt", None)
        logger.info("[router] Using ChatGPT provider.")

    use_web = bool(overrides.get("use_web")) or question.strip().lower().startswith("web:")
    if use_web:
        q = question[4:].strip() if question.strip().lower().startswith("web:") else question
        return handle_web_request(q)

    planner_system = overrides.get("planner_system") or PLANNER_SYSTEM_DEFAULT
    answer_system = overrides.get("answer_system") or ANSWER_SYSTEM_DEFAULT
    if user_system_all:
        planner_system = planner_system + "\n\n" + user_system_all
        answer_system = answer_system + "\n\n" + user_system_all

    if overrides.get("prepend_user"):
        question = overrides["prepend_user"] + question

    if is_greeting_only(question):
        parsed_tickers: List[str] = []
    else:
        parsed_tickers = extract_ticker_list(question)

    if parsed_tickers and (has_finance_intent(question) or len(parsed_tickers) >= 2):
        question = f"TICKERS_HINT: {','.join(parsed_tickers)}\n" + question

    if AUTO_WEB_FALLBACK and not bool(overrides.get("use_web")):
        if should_route_to_web(question, parsed_tickers):
            return handle_web_request(question, as_stream=True, max_pages=FAST_WEB_MAX_PAGES, fast=True)

    start = time.time()
    plan = oai_plan(question, planner_system)
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

    if plan.get("action") == "passive_income_plan":
        def gen_passive_income():
            yield "\n# PASSIVE INCOME PORTFOLIO BUILDER\n\n"
            
            target_income = 100000.0
            years = 5
            risk_tolerance = "moderate"
            
            q_lower = question.lower()
            income_match = re.search(r'\$?\s*(\d+[\d,]*(?:\.\d+)?)\s*k?(?:\s*(?:per|a|annually|yearly|year))?', q_lower)
            if income_match:
                amt_str = income_match.group(1).replace(',', '')
                amt = float(amt_str)
                if 'k' in income_match.group(0).lower():
                    amt *= 1000
                if amt > 100:
                    target_income = amt
            
            year_match = re.search(r'(\d+)\s*(?:year|yr)', q_lower)
            if year_match:
                years = int(year_match.group(1))
                years = max(1, min(years, 30))
            
            if any(word in q_lower for word in ['conservative', 'safe', 'low risk']):
                risk_tolerance = 'conservative'
            elif any(word in q_lower for word in ['aggressive', 'high risk', 'growth']):
                risk_tolerance = 'aggressive'
            
            yield f"Generating passive income plan for **${target_income:,.0f}** annual income over **{years} years** with **{risk_tolerance}** risk tolerance...\n\n"
            
            plan_result = PassiveIncomePlanService.generate_plan(
                target_annual_income=target_income,
                years=years,
                risk_tolerance=risk_tolerance
            )
            
            if not plan_result.get("success"):
                yield f"⚠️ Error generating plan: {plan_result.get('error', 'Unknown error')}\n"
                return
            
            summary = plan_result.get("summary", {})
            assumptions = plan_result.get("assumptions", {})
            allocations = plan_result.get("allocations", [])
            projections = plan_result.get("projections", [])
            diversification = plan_result.get("diversification", {})
            
            yield "## 📊 Plan Summary\n\n"
            yield f"- **Target Annual Income**: ${summary.get('target_annual_income', 0):,.0f}\n"
            yield f"- **Required Capital**: ${summary.get('required_capital', 0):,.0f}\n"
            yield f"- **Average Dividend Yield**: {summary.get('avg_dividend_yield', 0):.2f}%\n"
            yield f"- **Risk Tolerance**: {summary.get('risk_tolerance', 'moderate').title()}\n"
            yield f"- **Investment Horizon**: {summary.get('years', 5)} years\n"
            yield f"- **Number of Holdings**: {summary.get('num_holdings', 0)}\n\n"
            
            yield "## 🎯 Key Assumptions\n\n"
            yield f"- **Expected Dividend Yield**: {assumptions.get('dividend_yield', 'N/A')}\n"
            yield f"- **Annual Dividend Growth**: {assumptions.get('annual_dividend_growth', 'N/A')}\n"
            yield f"- **Risk Profile**: {assumptions.get('risk_profile', 'moderate').title()}\n\n"
            
            if allocations:
                yield "## 💼 Portfolio Allocations\n\n"
                yield "| Ticker | Company | Sector | Shares | Price | Cost | Allocation | Yield |\n"
                yield "|--------|---------|--------|--------|-------|------|------------|-------|\n"
                for alloc in allocations:
                    ticker = alloc.get('ticker', 'N/A')
                    company = (alloc.get('company_name', '')[:20] + '...') if len(alloc.get('company_name', '')) > 20 else alloc.get('company_name', 'N/A')
                    sector = alloc.get('sector', 'Other')
                    shares = alloc.get('shares', 0)
                    price = alloc.get('price', 0)
                    cost = alloc.get('cost', 0)
                    allocation_pct = alloc.get('allocation_pct', 0)
                    div_yield = alloc.get('dividend_yield_pct', 0)
                    yield f"| {ticker} | {company} | {sector} | {shares:.2f} | ${price:.2f} | ${cost:,.0f} | {allocation_pct:.1f}% | {div_yield:.2f}% |\n"
                yield "\n"
            else:
                yield "## ⚠️ Unable to Generate Portfolio\n\n"
                yield "I couldn't find sufficient dividend stock data in the database to create a portfolio plan. This could mean:\n\n"
                yield "1. **Database Empty**: The dividend data tables may not have recent information\n2. **No Suitable Stocks**: No stocks match the criteria (>2% yield, recent dividends)\n3. **Database Connection Issue**: Temporary connectivity problem\n\n"
                yield "**Self-Healing Alternatives:**\n\n"
                yield "- I can search the web for current dividend stock recommendations\n2. I can provide general passive income strategies based on market knowledge\n3. You can ask me about specific dividend stocks you're considering (e.g., 'Tell me about SCHD dividends')\n\n"
                yield "Would you like me to try one of these alternative approaches?\n\n"
            
            if projections:
                yield "## 📈 5-Year Income Projections\n\n"
                yield "| Year | Projected Annual Income |\n"
                yield "|------|-------------------------|\n"
                for proj in projections:
                    year = proj.get('year', 0)
                    income = proj.get('projected_income', 0)
                    yield f"| Year {year} | ${income:,.2f} |\n"
                yield "\n"
            
            if diversification:
                yield "## 🌐 Sector Diversification\n\n"
                yield "| Sector | Allocation |\n"
                yield "|--------|------------|\n"
                for sector, pct in diversification.items():
                    yield f"| {sector} | {pct:.1f}% |\n"
                yield "\n"
            
            yield "## 📊 Visual Charts\n\n"
            
            chart_data = {
                "allocations": allocations,
                "projections": projections,
                "diversification": diversification
            }
            
            yield f'<div id="portfolio-charts" data-charts=\'{json.dumps(chart_data)}\'></div>\n\n'
            
            yield "---\n\n"
            yield "### Next Steps\n\n"
            yield "**Save Portfolio**: Reply with a name to save this as a watchlist or portfolio for tracking.\n\n"
            yield "---\n\n"
            yield "**Investment Disclaimer**: This analysis is based on historical dividend data and conservative growth assumptions (3-5.5% yield, 3% annual growth). Past performance does not guarantee future results. This is for informational purposes only and does not constitute financial advice. Please consult a qualified financial advisor before making any investment decisions. Markets are subject to risks including loss of principal.\n\n"
            yield "**Data Sources**: Historical dividend payments, current market prices, sector classifications from Azure SQL Database. Last updated: Real-time market data.\n"
        
        req_id = f"chatcmpl-{int(time.time() * 1000)}"
        return openai_sse_wrap(gen_passive_income(), req_id)

    if plan.get("action") == "chat":
        if AUTO_WEB_FALLBACK and should_route_to_web(question, parsed_tickers):
            return handle_web_request(question, as_stream=True, max_pages=FAST_WEB_MAX_PAGES, fast=True)

        msgs = [{"role": "system", "content": "You are a friendly, concise assistant."}]
        if user_system_all:
            msgs[0]["content"] += "\n\n" + user_system_all
        msgs.append({"role": "user", "content": plan.get("final_answer") or question})

        def gen():
            ans_start = time.time()
            for tok in oai_stream(msgs):
                yield tok
            run["answer_ms"] = int((time.time() - ans_start) * 1000)
            write_runlog(run, logfile)

        req_id = f"chatcmpl-{int(time.time() * 1000)}"
        return openai_sse_wrap(gen(), req_id)

    sql_raw = (plan.get("sql") or "").strip()

    if sql_raw:
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

    sql_open_t0 = time.time()
    try:
        from sqlalchemy.exc import OperationalError
        columns, rows_iter = exec_sql_stream(engine, sql)
    except OperationalError:
        time.sleep(0.4)
        columns, rows_iter = exec_sql_stream(engine, sql)
    run["sql_ms"] = int((time.time() - sql_open_t0) * 1000)

    last_n_years = parse_last_n_years(question)
    rows_buffer: List[tuple] = []

    def composed():
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

        if AUTO_WEB_FALLBACK and cnt == 0 and should_route_to_web(question, parsed_tickers):
            yield "\n# ANSWER\n\n"
            for chunk in perform_enhanced_web_search(question, max_pages=FAST_WEB_MAX_PAGES, fast=True):
                yield chunk
            write_runlog(run, logfile)
            return

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
        for tok in oai_stream(msgs):
            yield tok
        run["answer_ms"] = int((time.time() - ans_t0) * 1000)
        write_runlog(run, logfile)

    req_id = f"chatcmpl-{int(time.time() * 1000)}"
    return openai_sse_wrap(composed(), req_id)


def is_upload_like(obj) -> bool:
    """Check if an object is a file upload (has filename, content_type, and read method)."""
    return obj is not None and hasattr(obj, "filename") and hasattr(obj, "content_type") and hasattr(obj, "read")


def extract_text_via_node(file_name: str, file_bytes: bytes, content_type: str | None = None, rid: str | None = None) -> str:
    """
    Extract text from uploaded files using Node.js service.
    
    Supports OCR and document intelligence for various file formats
    including PDFs, images, and Office documents.
    
    Args:
        file_name: Original filename
        file_bytes: File content as bytes
        content_type: MIME type (optional, will be guessed if not provided)
        rid: Request ID for logging
    
    Returns:
        Extracted text or empty string on failure
    """
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
