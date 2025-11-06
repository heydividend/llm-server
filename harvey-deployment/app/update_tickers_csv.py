#!/usr/bin/env python3
import os
import sys
import re
import json
from typing import List, Tuple, Optional, Dict

import pandas as pd
import pyodbc
from dotenv import load_dotenv

# -----------------------------
# .env loading (exactly as given)
# -----------------------------
BASE = os.getcwd()
ENV  = os.path.join(BASE, ".env") if os.path.isdir(BASE) else ".env"
load_dotenv(ENV)

HOST = os.getenv("SQLSERVER_HOST")
PORT = os.getenv("SQLSERVER_PORT", "1433")
DB   = os.getenv("SQLSERVER_DB")
USER = os.getenv("SQLSERVER_USER")
PWD  = os.getenv("SQLSERVER_PASSWORD")
DRV  = os.getenv("ODBC_DRIVER", "ODBC Driver 18 for SQL Server")

# Provided by you
CREATE_VIEWS_SQL = """
CREATE OR ALTER VIEW dbo.vTickers AS
SELECT
  Ticker_ID,
  Fund_Ticker AS Ticker,
  Ticker_Symbol_Name,
  Exchange,
  Exchange_Full_Name,
  Company_Name,
  Website,
  Sector,
  Industry,
  Country,
  'ETF' AS Security_Type,
  Reference_Asset,
  Benchmark_Index,
  Description,
  Inception_Date,
  Gross_Expense_Ratio,
  ThirtyDay_SEC_Yield,
  Created_At,
  Updated_At,
  Distribution_Frequency
FROM dbo.Ingest_Tickers_ETF_Data
UNION ALL
SELECT
  Ticker_ID,
  Ticker AS Ticker,
  Ticker_Symbol_Name,
  Exchange,
  Exchange_Full_Name,
  Company_Name,
  Website,
  Sector,
  Industry,
  Country,
  'Stock' AS Security_Type,
  Reference_Asset,
  Benchmark_Index,
  Description,
  Inception_Date,
  Gross_Expense_Ratio,
  ThirtyDay_SEC_Yield,
  Created_At,
  Updated_At,
  Distribution_Frequency
FROM dbo.Ingest_Tickers_Stock_Data;

CREATE OR ALTER VIEW dbo.vDividends AS
SELECT
  Dividend_ID,
  Ticker_Symbol AS Ticker,
  Dividend_Amount,
  ISNULL(AdjDividend_Amount, Dividend_Amount) AS AdjDividend_Amount,
  Dividend_Type,
  Currency,
  Distribution_Frequency,
  Declaration_Date,
  Ex_Dividend_Date,
  Record_Date,
  Payment_Date,
  Created_At,
  Updated_At,
  'Stock' AS Security_Type
FROM dbo.Ingest_Dividends_Stock_Data
UNION ALL
SELECT
  Dividend_ID,
  Ticker_Symbol AS Ticker,
  Dividend_Amount,
  Dividend_Amount AS AdjDividend_Amount,
  NULL AS Dividend_Type,
  NULL AS Currency,
  NULL AS Distribution_Frequency,
  Declaration_Date,
  Ex_Dividend_Date,
  Record_Date,
  Payment_Date,
  Created_At,
  Updated_At,
  'ETF' AS Security_Type
FROM dbo.Ingest_Dividends_ETF_Data;
"""

# -----------------------------
# Connection helpers
# -----------------------------
def get_conn() -> pyodbc.Connection:
    if not all([HOST, PORT, DB, USER, PWD, DRV]):
        missing = [k for k, v in {
            "SQLSERVER_HOST": HOST,
            "SQLSERVER_PORT": PORT,
            "SQLSERVER_DB": DB,
            "SQLSERVER_USER": USER,
            "SQLSERVER_PASSWORD": PWD,
            "ODBC_DRIVER": DRV
        }.items() if not v]
        raise RuntimeError(f"Missing required .env keys: {', '.join(missing)}")

    # f-string with triple braces -> DRIVER={ODBC Driver ...}
    conn_str = (
        f"DRIVER={{{DRV}}};"
        f"SERVER={HOST},{PORT};"
        f"DATABASE={DB};"
        f"UID={USER};"
        f"PWD={PWD};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
        "Connection Timeout=30;"
    )
    return pyodbc.connect(conn_str)

# -----------------------------
# DB discovery & extraction
# -----------------------------
def view_exists(cursor, view_schema: str, view_name: str) -> bool:
    cursor.execute("""
        SELECT 1
        FROM INFORMATION_SCHEMA.VIEWS
        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?;
    """, (view_schema, view_name))
    return cursor.fetchone() is not None

def try_create_views(cursor) -> None:
    # Split on GO-like separators not required; pyodbc can run the whole batch if no GO is present.
    cursor.execute(CREATE_VIEWS_SQL)

def fetch_from_vtickers(cursor) -> pd.DataFrame:
    # Only pull the columns we need
    cursor.execute("SELECT Ticker, Company_Name FROM dbo.vTickers;")
    rows = cursor.fetchall()
    return pd.DataFrame.from_records(rows, columns=["ticker", "name"])

def list_candidate_tables(cursor) -> List[Tuple[str, str]]:
    """
    Return (schema, table) where table name contains 'ticker' or 'symbol' (case-insensitive)
    """
    cursor.execute("""
        SELECT TABLE_SCHEMA, TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE='BASE TABLE'
          AND (LOWER(TABLE_NAME) LIKE '%ticker%' OR LOWER(TABLE_NAME) LIKE '%symbol%')
        ORDER BY TABLE_SCHEMA, TABLE_NAME;
    """)
    return [(r[0], r[1]) for r in cursor.fetchall()]

def table_columns(cursor, schema: str, table: str) -> List[str]:
    cursor.execute("""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION;
    """, (schema, table))
    return [r[0] for r in cursor.fetchall()]

def pick_columns(cols: List[str]) -> Optional[Tuple[str, str]]:
    """
    Choose (ticker_col, name_col) from a column list.
    We only accept tables having a 'ticker-like' column, and a reasonable 'name-like' column.
    """
    lc = [c.lower() for c in cols]
    # Preferred orders
    ticker_pref = ["fund_ticker", "ticker", "ticker_symbol", "symbol", "ticker_symbol_name"]
    name_pref   = ["company_name", "security_name", "name", "ticker_symbol_name"]

    ticker_col = next((cols[lc.index(c)] for c in ticker_pref if c in lc), None)
    # name can fall back to ticker_symbol_name if that's the only descriptive field
    name_col   = next((cols[lc.index(c)] for c in name_pref   if c in lc), None)

    if ticker_col is None:
        return None
    # If name is missing, we still allow it (we'll leave name blank and keep existing)
    if name_col is None:
        name_col = ticker_col  # placeholder; we'll null it later in SELECT
    return ticker_col, name_col

def fetch_union_from_candidate_tables(cursor) -> pd.DataFrame:
    candidates = list_candidate_tables(cursor)
    selects: List[str] = []
    mappings: List[Tuple[str, str, str]] = []  # (schema.table, ticker_col, name_col)

    for schema, table in candidates:
        cols = table_columns(cursor, schema, table)
        picked = pick_columns(cols)
        if not picked:
            continue
        ticker_col, name_col = picked
        fq = f"[{schema}].[{table}]"
        if ticker_col == name_col:
            # name missing; return NULL for name
            selects.append(
                f"SELECT DISTINCT LTRIM(RTRIM(CAST([{ticker_col}] AS NVARCHAR(255)))) AS ticker, NULL AS name FROM {fq}"
            )
        else:
            selects.append(
                f"SELECT DISTINCT "
                f"LTRIM(RTRIM(CAST([{ticker_col}] AS NVARCHAR(255)))) AS ticker, "
                f"LTRIM(RTRIM(CAST([{name_col}]   AS NVARCHAR(512)))) AS name "
                f"FROM {fq}"
            )
        mappings.append((fq, ticker_col, name_col))

    if not selects:
        return pd.DataFrame(columns=["ticker", "name"])

    sql = " \nUNION\n ".join(selects)
    # Filter out empties
    sql = f"SELECT ticker, name FROM (\n{sql}\n) S WHERE ticker IS NOT NULL AND ticker <> '';"
    cursor.execute(sql)
    rows = cursor.fetchall()
    df = pd.DataFrame.from_records(rows, columns=["ticker", "name"])
    return df

# -----------------------------
# CSV merge logic
# -----------------------------
def normalize(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    # standardize columns
    out.columns = [c.strip().lower() for c in out.columns]
    # trim and normalize tickers (keep case, but trim)
    out["ticker"] = out["ticker"].astype(str).str.strip()
    # keep original case for names; just strip
    if "name" in out.columns:
        out["name"] = out["name"].astype(str).str.strip()
        out.loc[out["name"].isin(["None", "nan", "NaN"]), "name"] = ""
    return out[["ticker", "name"]]

def prefer_non_empty(series: pd.Series) -> str:
    for val in series:
        if isinstance(val, str) and val.strip():
            return val.strip()
    return ""

def merge_existing_with_db(existing: pd.DataFrame, db_df: pd.DataFrame) -> pd.DataFrame:
    ex = normalize(existing) if not existing.empty else pd.DataFrame(columns=["ticker", "name"])
    db = normalize(db_df)    if not db_df.empty    else pd.DataFrame(columns=["ticker", "name"])

    combined = pd.concat([db, ex], ignore_index=True)  # DB first so DB names win
    combined = combined.dropna(subset=["ticker"])
    combined = combined[combined["ticker"] != ""]
    # Deduplicate by ticker, preferring first non-empty name
    merged = (
        combined
        .groupby("ticker", as_index=False)
        .agg(name=("name", prefer_non_empty))
        .sort_values("ticker")
        .reset_index(drop=True)
    )
    return merged

# -----------------------------
# Main flow
# -----------------------------
def main(path_csv: str = "tickers.csv", create_views: bool = False) -> int:
    conn = get_conn()
    try:
        cursor = conn.cursor()

        df_db: pd.DataFrame

        used_view = False
        # Optionally (re)create views if requested
        if create_views:
            try:
                try_create_views(cursor)
                conn.commit()
            except Exception as e:
                print(f"Warning: could not create views (continuing): {e}", file=sys.stderr)

        # Prefer vTickers when present
        if view_exists(cursor, "dbo", "vTickers"):
            try:
                df_db = fetch_from_vtickers(cursor)
                used_view = True
            except Exception as e:
                print(f"Warning: vTickers query failed, falling back to table discovery: {e}", file=sys.stderr)
                df_db = fetch_union_from_candidate_tables(cursor)
        else:
            df_db = fetch_union_from_candidate_tables(cursor)

        # Clean DB results to only ticker + name
        if not df_db.empty:
            df_db = df_db[["ticker", "name"]]
        else:
            df_db = pd.DataFrame(columns=["ticker", "name"])

        # Load existing CSV (if any)
        if os.path.exists(path_csv):
            existing = pd.read_csv(path_csv, dtype=str).fillna("")
        else:
            existing = pd.DataFrame(columns=["ticker", "name"])

        before_count = len(existing) if not existing.empty else 0
        after_df = merge_existing_with_db(existing, df_db)
        after_count = len(after_df)

        # Basic stats
        existing_set = set(existing["ticker"]) if not existing.empty else set()
        new_set = set(after_df["ticker"])
        added = len(new_set - existing_set)
        removed = len(existing_set - new_set)

        # Write back
        after_df.to_csv(path_csv, index=False)

        print(json.dumps({
            "source": "vTickers" if used_view else "discovered_tables",
            "csv_path": os.path.abspath(path_csv),
            "before_count": before_count,
            "after_count": after_count,
            "added": added,
            "removed": removed
        }, indent=2))
        return 0
    finally:
        try:
            conn.close()
        except Exception:
            pass

if __name__ == "__main__":
    # CLI: python update_tickers_csv.py [tickers.csv] [--create-views]
    csv_path = "tickers.csv"
    create_views_flag = False
    if len(sys.argv) >= 2:
        csv_path = sys.argv[1]
    if len(sys.argv) >= 3 and sys.argv[2] == "--create-views":
        create_views_flag = True
    sys.exit(main(csv_path, create_views=create_views_flag))
