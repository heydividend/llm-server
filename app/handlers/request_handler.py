import time, datetime as dt
from typing import Dict, Any, List, Iterable
import logging
import re
import pandas as pd
from sqlalchemy.exc import OperationalError
from app.core.llm_providers import oai_plan, oai_stream, set_active_llm, get_active_llm
from app.core.database import engine, sanitize_sql, exec_sql_stream
from app.web_search.enhanced_search import perform_enhanced_web_search
from app.utils.helpers import (
    user_wants_cap, parse_last_n_years, extract_ticker_list, 
    should_route_to_web, is_greeting_only, openai_sse_wrap, write_runlog,
    is_ml_query, detect_ml_query_type, format_ml_payout_rating, format_ml_cut_risk,
    format_ml_yield_forecast, format_ml_anomaly, format_ml_comprehensive, has_finance_intent
)
from app.utils.metrics import compute_dividend_metrics
from app.config.settings import (
    PLANNER_SYSTEM_DEFAULT, ANSWER_SYSTEM_DEFAULT, 
    AUTO_WEB_FALLBACK, FAST_WEB_MAX_PAGES
)

logger = logging.getLogger("ai_controller")

def handle_web_request(question: str, as_stream: bool = True, max_pages: int = 8, fast: bool = False):
    req_id = f"chatcmpl-web-{int(time.time()*1000)}"
    if as_stream:
        def gen():
            yield from perform_enhanced_web_search(question, max_pages=max_pages, fast=fast)
        return openai_sse_wrap(gen(), req_id)
    else:
        return perform_enhanced_web_search(question, max_pages=max_pages, fast=fast)


def handle_ml_request(question: str, parsed_tickers: List[str], query_type: str = "payout_rating"):
    """
    Handle ML prediction requests.
    
    Args:
        question: User's question
        parsed_tickers: List of ticker symbols extracted from question
        query_type: Type of ML query (payout_rating, cut_risk, yield_forecast, anomaly, comprehensive)
    
    Returns:
        Generator yielding formatted ML response
    """
    from app.services.ml_api_client import get_ml_client
    
    req_id = f"chatcmpl-ml-{int(time.time()*1000)}"
    
    def gen():
        try:
            if not parsed_tickers:
                yield "Please specify one or more ticker symbols for ML analysis. For example: 'What's the payout rating for AAPL?'"
                return
            
            logger.info(f"ML request: type={query_type}, tickers={parsed_tickers}")
            
            ml_client = get_ml_client()
            
            if query_type == "payout_rating":
                response = ml_client.get_payout_rating(parsed_tickers)
                formatted = format_ml_payout_rating(response.get("data", []))
            
            elif query_type == "cut_risk":
                response = ml_client.get_cut_risk(parsed_tickers, include_earnings=True)
                formatted = format_ml_cut_risk(response.get("data", []))
            
            elif query_type == "yield_forecast":
                response = ml_client.get_yield_forecast(parsed_tickers)
                formatted = format_ml_yield_forecast(response.get("data", []))
            
            elif query_type == "anomaly":
                response = ml_client.check_anomalies(parsed_tickers)
                formatted = format_ml_anomaly(response.get("data", []))
            
            elif query_type == "comprehensive":
                response = ml_client.get_comprehensive_score(parsed_tickers)
                formatted = format_ml_comprehensive(response.get("data", []))
            
            else:
                response = ml_client.get_payout_rating(parsed_tickers)
                formatted = format_ml_payout_rating(response.get("data", []))
            
            yield formatted
            
            yield "\n\n---\n*ML predictions powered by HeyDividend's Internal ML API*"
            
        except Exception as e:
            logger.error(f"ML API error: {e}")
            
            yield f"I encountered an error while fetching ML predictions: {str(e)}\n\n"
            yield "Let me provide a general analysis instead:\n\n"
            
            msgs = [
                {"role": "system", "content": "You are a friendly dividend investing assistant. Provide helpful analysis based on general knowledge."},
                {"role": "user", "content": question}
            ]
            
            for tok in oai_stream(msgs):
                yield tok
    
    return openai_sse_wrap(gen(), req_id)

def handle_request(question: str, user_system_all: str, overrides: Dict[str, str], debug=False, logfile="runlogger.jsonl"):
    """
    Core request pipeline with dynamic LLM selection.
    """
    # Switch provider/model per-request
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

    # ML query detection (before planner)
    if is_ml_query(question):
        ml_query_type = detect_ml_query_type(question)
        logger.info(f"Detected ML query: type={ml_query_type}, tickers={parsed_tickers}")
        return handle_ml_request(question, parsed_tickers, ml_query_type)

    # Early auto web switch (FAST)
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

    # CHAT PATH
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

    # SQL PATH
    sql_raw = (plan.get("sql") or "").strip()
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
        for tok in oai_stream(msgs):
            yield tok
        run["answer_ms"] = int((time.time() - ans_t0) * 1000)
        write_runlog(run, logfile)

    req_id = f"chatcmpl-{int(time.time() * 1000)}"
    return openai_sse_wrap(composed(), req_id)