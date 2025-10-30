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
    format_ml_yield_forecast, format_ml_anomaly, format_ml_comprehensive, has_finance_intent,
    format_ml_payout_rating_single, format_ml_cut_risk_single, format_ml_yield_forecast_single,
    format_ml_anomaly_single, format_ml_comprehensive_single
)
from app.utils.metrics import compute_dividend_metrics
from app.utils.markdown_formatter import ProfessionalMarkdownFormatter
from app.utils.conversational_prompts import (
    detect_share_ownership, get_follow_up_prompts, format_ttm_message,
    is_dividend_query, should_show_conversational_prompts
)
from app.utils.ttm_calculator import (
    calculate_ttm_distributions, format_ttm_result, format_ttm_summary
)
from app.utils import dividend_analytics
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
    Handle ML prediction requests with progressive streaming.
    
    Args:
        question: User's question
        parsed_tickers: List of ticker symbols extracted from question
        query_type: Type of ML query (payout_rating, cut_risk, yield_forecast, anomaly, comprehensive)
    
    Returns:
        Generator yielding formatted ML response progressively (header -> per-ticker results -> footer)
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
                yield "## Dividend Payout Rating\n\n"
                response = ml_client.get_payout_rating(parsed_tickers)
                data = response.get("data", [])
                
                if not data:
                    yield "No payout rating data available.\n"
                else:
                    for item in data:
                        yield format_ml_payout_rating_single(item)
            
            elif query_type == "cut_risk":
                yield "## Dividend Cut Risk Analysis\n\n"
                response = ml_client.get_cut_risk(parsed_tickers, include_earnings=True)
                data = response.get("data", [])
                
                if not data:
                    yield "No cut risk data available.\n"
                else:
                    for item in data:
                        yield format_ml_cut_risk_single(item)
            
            elif query_type == "yield_forecast":
                yield "## Dividend Growth Forecast\n\n"
                response = ml_client.get_yield_forecast(parsed_tickers)
                data = response.get("data", [])
                
                if not data:
                    yield "No yield forecast data available.\n"
                else:
                    for item in data:
                        yield format_ml_yield_forecast_single(item)
            
            elif query_type == "anomaly":
                yield "## Dividend Anomaly Detection\n\n"
                response = ml_client.check_anomalies(parsed_tickers)
                data = response.get("data", [])
                
                if not data:
                    yield "No anomaly data available.\n"
                else:
                    for item in data:
                        yield format_ml_anomaly_single(item)
            
            elif query_type == "comprehensive":
                yield "## Comprehensive ML Score\n\n"
                response = ml_client.get_comprehensive_score(parsed_tickers)
                data = response.get("data", [])
                
                if not data:
                    yield "No comprehensive score data available.\n"
                else:
                    for item in data:
                        yield format_ml_comprehensive_single(item)
            
            else:
                yield "## Dividend Payout Rating\n\n"
                response = ml_client.get_payout_rating(parsed_tickers)
                data = response.get("data", [])
                
                if not data:
                    yield "No payout rating data available.\n"
                else:
                    for item in data:
                        yield format_ml_payout_rating_single(item)
            
            yield "\n---\n*ML predictions powered by HeyDividend's Internal ML API*"
            
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
        # Detect if this is a dividend query by checking column names
        columns_lower = [col.lower() for col in columns]
        dividend_fields = ['dividend_amount', 'yield', 'payout_ratio', 'ex_date', 'pay_date', 
                          'exdate', 'paydate', 'ex_dividend_date', 'payment_date', 
                          'declaration_date', 'declarationdate', 'distribution_amount']
        is_dividend_query = any(field in columns_lower for field in dividend_fields)
        
        # Buffer all rows first
        cnt = 0
        for r in rows_iter:
            cnt += 1
            rows_buffer.append(r)
        run["rows_streamed"] = cnt
        
        # a) Format and display data table
        yield "\n# DATA\n\n"
        
        if is_dividend_query and cnt > 0:
            # Use professional markdown formatting for dividend queries
            try:
                formatter = ProfessionalMarkdownFormatter()
                
                # Convert rows to list of dictionaries for the formatter
                dividend_data = []
                for row in rows_buffer:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        row_dict[col] = row[i]
                    dividend_data.append(row_dict)
                
                # Format the professional dividend table
                formatted_table = formatter.format_dividend_table(dividend_data)
                yield formatted_table + "\n\n"
                yield f"(total rows: {cnt})\n"
            except Exception as e:
                logger.error(f"Error formatting dividend table with professional formatter: {e}")
                # Fallback to ASCII table on error
                yield "│ " + " │ ".join(columns) + " │\n"
                yield "─" * min(180, 4 * len(columns) + 8) + "\n"
                for r in rows_buffer:
                    cells = ["(null)" if (v is None or (isinstance(v, float) and pd.isna(v))) else str(v) for v in r]
                    yield "│ " + " │ ".join(cells) + " │\n"
                yield f"(total rows: {cnt})\n"
        else:
            # Use current streaming format for non-dividend queries
            yield "│ " + " │ ".join(columns) + " │\n"
            yield "─" * min(180, 4 * len(columns) + 8) + "\n"
            for r in rows_buffer:
                cells = ["(null)" if (v is None or (isinstance(v, float) and pd.isna(v))) else str(v) for v in r]
                yield "│ " + " │ ".join(cells) + " │\n"
            yield f"(total rows streamed: {cnt})\n"

        # b0) Share ownership detection and TTM calculation (before zero-row check)
        ownership_info = detect_share_ownership(question)
        if ownership_info and cnt > 0 and is_dividend_query:
            try:
                ticker = ownership_info['ticker']
                shares = ownership_info['shares']
                
                # Convert rows_buffer to list of dicts for TTM calculator
                distributions = []
                for row in rows_buffer:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        row_dict[col] = row[i]
                    distributions.append(row_dict)
                
                ttm_result = calculate_ttm_distributions(shares, ticker, distributions)
                ttm_message = format_ttm_result(ttm_result)
                yield "\n\n" + ttm_message + "\n\n"
            except Exception as e:
                logger.warning(f"Error calculating TTM for {ticker}: {e}")

        # b1) 4-Tier Dividend Analytics (after data table, before ANSWER)
        if is_dividend_query and cnt > 0:
            try:
                # Convert rows_buffer to list of dicts for analytics
                distributions = []
                for row in rows_buffer:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        row_dict[col] = row[i]
                    distributions.append(row_dict)
                
                yield "\n## 📊 Analytics Summary\n\n"
                
                # 1. Descriptive Analytics
                try:
                    desc_analytics = dividend_analytics.analyze_payment_history(distributions)
                    if desc_analytics and desc_analytics.get('total_payments', 0) > 0:
                        yield "### Descriptive Analytics\n"
                        yield f"- **Total Payments**: {desc_analytics['total_payments']}\n"
                        yield f"- **Frequency**: {desc_analytics['frequency']}\n"
                        yield f"- **Average Amount**: ${desc_analytics['avg_amount']:.4f}\n"
                        yield f"- **Consistency Score**: {desc_analytics['consistency_score']}/100\n"
                        yield f"- **Pattern**: {desc_analytics['pattern']}\n\n"
                except Exception as e:
                    logger.warning(f"Error in descriptive analytics: {e}")
                
                # 2. Diagnostic Analytics (distribution consistency)
                try:
                    diagnostic = dividend_analytics.analyze_distribution_consistency(distributions)
                    if diagnostic and diagnostic.get('regularity_score') is not None:
                        yield "### Diagnostic Analytics\n"
                        yield f"- **Regularity Score**: {diagnostic['regularity_score']}/100\n"
                        if diagnostic.get('outliers', 0) > 0:
                            yield f"- **Outliers Detected**: {diagnostic['outliers']} payment(s)\n"
                        if diagnostic.get('missed_payments', 0) > 0:
                            yield f"- **Potential Missed Payments**: {diagnostic['missed_payments']}\n"
                        yield f"- **Variance**: {diagnostic.get('variance', 'N/A')}\n\n"
                except Exception as e:
                    logger.warning(f"Error in diagnostic analytics: {e}")
                
                # 3. Predictive Analytics (if we have ticker info)
                if parsed_tickers and len(parsed_tickers) > 0:
                    try:
                        ticker = parsed_tickers[0]
                        next_dist = dividend_analytics.predict_next_distribution(ticker, distributions)
                        if next_dist and next_dist.get('predicted_date'):
                            yield "### Predictive Analytics\n"
                            yield f"- **Predicted Next Distribution**: ${next_dist.get('predicted_amount', 0):.4f}\n"
                            yield f"- **Estimated Date**: {next_dist['predicted_date']}\n"
                            if next_dist.get('confidence'):
                                yield f"- **Confidence**: {next_dist['confidence']}\n"
                            yield "\n"
                    except Exception as e:
                        logger.warning(f"Error in predictive analytics: {e}")
                
                # 4. Prescriptive Analytics (recommendations)
                if parsed_tickers and len(parsed_tickers) > 0:
                    try:
                        ticker = parsed_tickers[0]
                        # Build analytics data for recommendations by extracting values
                        analytics_data = {
                            'consistency_score': desc_analytics.get('consistency_score', 50) if 'desc_analytics' in locals() else 50,
                            'cut_risk_score': 0.3,  # Default moderate risk - would need ML API for actual value
                            'current_yield': 0.0,  # Would need price data to calculate
                            'growth_rate': 0.0  # Would need historical comparison
                        }
                        recommendations = dividend_analytics.recommend_action(ticker, analytics_data)
                        if recommendations and recommendations.get('recommendation'):
                            yield "### Prescriptive Recommendations\n"
                            yield f"- **Action**: {recommendations['recommendation']}\n"
                            yield f"- **Rationale**: {recommendations.get('rationale', 'Based on historical analysis')}\n"
                            if recommendations.get('confidence_score'):
                                yield f"- **Confidence Score**: {recommendations['confidence_score']}/100\n"
                            yield "\n"
                    except Exception as e:
                        logger.warning(f"Error in prescriptive analytics: {e}")
                
            except Exception as e:
                logger.error(f"Error in 4-tier analytics: {e}")

        # b2) zero-row safeguard → web fallback
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
        
        answer_content = ""
        for tok in oai_stream(msgs):
            answer_content += tok
            yield tok
        
        # Add conversational follow-up prompts for dividend queries
        if is_dividend_query and should_show_conversational_prompts(question, cnt > 0):
            try:
                follow_ups = get_follow_up_prompts(parsed_tickers, num_prompts=3)
                if follow_ups:
                    yield "\n\n---\n\n### 💡 What would you like to explore next?\n\n"
                    for i, prompt in enumerate(follow_ups, 1):
                        yield f"{i}. {prompt}\n"
                    yield "\n"
            except Exception as e:
                logger.warning(f"Error generating follow-up prompts: {e}")
        
        # Add legacy action prompts for backward compatibility
        if is_dividend_query:
            try:
                action_prompt = ProfessionalMarkdownFormatter.add_action_prompt("", parsed_tickers)
                yield action_prompt
            except Exception as e:
                logger.warning(f"Error adding action prompt: {e}")
        
        run["answer_ms"] = int((time.time() - ans_t0) * 1000)
        write_runlog(run, logfile)

    req_id = f"chatcmpl-{int(time.time() * 1000)}"
    return openai_sse_wrap(composed(), req_id)