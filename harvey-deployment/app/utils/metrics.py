import datetime as dt
from typing import List, Iterable, Dict, Any, Optional

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