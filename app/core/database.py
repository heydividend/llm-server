import os, re
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from typing import List, Iterable, Tuple, Any
from app.config.settings import (
    SQL_ONLY, DANGEROUS, SEMICOLON, ALLOWED_TB, CREATE_VIEWS_SQL, 
    CREATE_ENHANCED_VIEWS_SQL, CREATE_ENHANCED_VIEWS_FALLBACK_SQL
)
from app.config.portfolio_schema import CREATE_PORTFOLIO_TABLES_SQL

# Database Configuration
HOST = os.getenv("SQLSERVER_HOST")
PORT = os.getenv("SQLSERVER_PORT", "1433")
DB   = os.getenv("SQLSERVER_DB")
USER = os.getenv("SQLSERVER_USER")
PWD  = os.getenv("SQLSERVER_PASSWORD")
DRV  = os.getenv("ODBC_DRIVER", "FreeTDS")
LOGIN_TIMEOUT = os.getenv("SQLSERVER_LOGIN_TIMEOUT", "10")
CONN_TIMEOUT  = os.getenv("SQLSERVER_CONN_TIMEOUT", "20")

params = {
    "driver": DRV,
    "TDS_Version": "7.3",
    "Encrypt": "yes",
    "TrustServerCertificate": "no",
    "LoginTimeout": LOGIN_TIMEOUT,
    "Connection Timeout": CONN_TIMEOUT,
}
param_str = "&".join([f"{k}={quote_plus(v)}" for k, v in params.items()])
ENGINE_URL = f"mssql+pyodbc://{quote_plus(USER)}:{quote_plus(PWD)}@{HOST}:{PORT}/{quote_plus(DB)}?{param_str}"

def open_engine():
    return create_engine(
        ENGINE_URL,
        fast_executemany=True,
        pool_pre_ping=True,
        pool_size=20,
        max_overflow=20,
        pool_recycle=3600,
        pool_timeout=30,
    )

# Initialize engine and create views
engine = open_engine()
try:
    with engine.begin() as conn:
        for stmt in [s.strip() for s in CREATE_VIEWS_SQL.split(";") if s.strip()]:
            conn.exec_driver_sql(stmt)
except Exception as e:
    print(f"[warn] ensure_views failed: {e}")

def ensure_enhanced_views():
    """
    Create enhanced views with graceful degradation.
    
    Strategy:
    1. Try to create production enhanced views (requires HeyDividend production tables)
    2. If that fails, create fallback views that wrap legacy views
    3. Verify each view is selectable after creation
    4. Log clear messages about which views were created
    """
    enhanced_views = [
        'vSecurities', 'vDividendsEnhanced', 'vDividendSchedules', 
        'vDividendSignals', 'vQuotesEnhanced', 'vDividendPredictions'
    ]
    
    # Try production enhanced views first
    try:
        with engine.begin() as conn:
            for stmt in [s.strip() for s in CREATE_ENHANCED_VIEWS_SQL.split(";") if s.strip()]:
                conn.exec_driver_sql(stmt)
        
        # Verify all views are selectable
        verification_failed = []
        with engine.connect() as conn:
            for view_name in enhanced_views:
                try:
                    conn.exec_driver_sql(f"SELECT TOP 1 * FROM dbo.{view_name}")
                except Exception as e:
                    verification_failed.append(view_name)
        
        if verification_failed:
            raise Exception(f"Views not selectable: {', '.join(verification_failed)}")
        
        print("[info] ✓ Enhanced views created successfully (production mode)")
        print(f"[info]   Views: {', '.join(enhanced_views)}")
        print("[info]   Data source: HeyDividend production tables (Canonical_Dividends, distribution_schedules, etc.)")
        return True
        
    except Exception as prod_error:
        print(f"[warn] Production enhanced views failed: {prod_error}")
        print("[info] Attempting fallback to legacy view wrappers...")
        
        # Fall back to legacy view wrappers
        try:
            with engine.begin() as conn:
                for stmt in [s.strip() for s in CREATE_ENHANCED_VIEWS_FALLBACK_SQL.split(";") if s.strip()]:
                    conn.exec_driver_sql(stmt)
            
            # Verify fallback views are selectable
            verification_failed = []
            with engine.connect() as conn:
                for view_name in enhanced_views:
                    try:
                        conn.exec_driver_sql(f"SELECT TOP 1 * FROM dbo.{view_name}")
                    except Exception as e:
                        verification_failed.append(view_name)
            
            if verification_failed:
                print(f"[warn] Some fallback views not selectable: {', '.join(verification_failed)}")
            
            print("[info] ✓ Enhanced views created successfully (legacy fallback mode)")
            print(f"[info]   Views: {', '.join(enhanced_views)}")
            print("[info]   Data source: Legacy views (vTickers, vDividends, vPrices) with synthetic confidence scores")
            print("[info]   Note: vDividendSchedules, vDividendSignals, and vDividendPredictions return no data in fallback mode")
            return True
            
        except Exception as fallback_error:
            print(f"[error] Enhanced views fallback also failed: {fallback_error}")
            print("[warn] AI queries may fail when referencing enhanced views")
            return False

# Create enhanced views with graceful degradation
ensure_enhanced_views()

# Create portfolio tables
try:
    with engine.begin() as conn:
        for stmt in [s.strip() for s in CREATE_PORTFOLIO_TABLES_SQL.split(";") if s.strip()]:
            conn.exec_driver_sql(stmt)
except Exception as e:
    print(f"[warn] ensure_portfolio_tables failed: {e}")

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
        raise ValueError("SQL must reference allowed views: vTickers, vDividends, vPrices, vSecurities, vDividendsEnhanced, vDividendSchedules, vDividendSignals, vQuotesEnhanced, or vDividendPredictions.")
    return sql.strip()

def exec_sql_stream(engine, sql: str, fetch_size: int = 10000):
    """Execute SQL and stream results."""
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