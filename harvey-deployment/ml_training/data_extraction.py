"""
Data Extraction Module for Harvey ML Training Pipeline

Loads data from Azure SQL database views for ML model training.
Uses existing database connection from app/core/database.py.
"""

import os
import sys
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from sqlalchemy import create_engine
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_database_engine():
    """Create database engine from environment variables."""
    HOST = os.getenv("SQLSERVER_HOST", "")
    PORT = os.getenv("SQLSERVER_PORT", "1433")
    DB = os.getenv("SQLSERVER_DB", "")
    USER = os.getenv("SQLSERVER_USER", "")
    PWD = os.getenv("SQLSERVER_PASSWORD", "")
    USE_PYMSSQL = os.getenv("USE_PYMSSQL", "false").lower() == "true"
    
    if USE_PYMSSQL:
        ENGINE_URL = f"mssql+pymssql://{quote_plus(USER)}:{quote_plus(PWD)}@{HOST}:{PORT}/{quote_plus(DB)}"
        logger.info("Using pymssql driver (no ODBC required)")
    else:
        DRV = os.getenv("ODBC_DRIVER", "FreeTDS")
        LOGIN_TIMEOUT = os.getenv("SQLSERVER_LOGIN_TIMEOUT", "10")
        CONN_TIMEOUT = os.getenv("SQLSERVER_CONN_TIMEOUT", "20")
        
        params = {
            "driver": DRV,
            "TDS_Version": "7.3",
            "Encrypt": "yes",
            "TrustServerCertificate": "no",
            "LoginTimeout": LOGIN_TIMEOUT,
            "Connection Timeout": CONN_TIMEOUT,
            "AUTOCOMMIT": "True",
        }
        param_str = "&".join([f"{k}={quote_plus(v)}" for k, v in params.items()])
        ENGINE_URL = f"mssql+pyodbc://{quote_plus(USER)}:{quote_plus(PWD)}@{HOST}:{PORT}/{quote_plus(DB)}?{param_str}"
        logger.info(f"Using pyodbc driver: {DRV}")
    
    return create_engine(
        ENGINE_URL,
        isolation_level="AUTOCOMMIT",
        fast_executemany=True,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_recycle=3600,
        pool_timeout=30,
    )


class DataExtractor:
    """Extracts and prepares data from database views for ML training."""
    
    def __init__(self):
        """Initialize data extractor with database engine."""
        self.engine = create_database_engine()
        logger.info("DataExtractor initialized with standalone database connection")
    
    def load_dividend_history(self, limit: Optional[int] = None) -> pd.DataFrame:
        """
        Load dividend history from vDividends view.
        
        Args:
            limit: Optional limit on number of rows to load
            
        Returns:
            DataFrame with dividend history
        """
        query = """
        SELECT 
            Ticker,
            Dividend_Amount,
            AdjDividend_Amount,
            Dividend_Type,
            Currency,
            Distribution_Frequency,
            Declaration_Date,
            Ex_Dividend_Date,
            Record_Date,
            Payment_Date,
            Security_Type,
            Created_At,
            Updated_At
        FROM dbo.vDividends
        WHERE Ticker IS NOT NULL 
          AND Dividend_Amount IS NOT NULL
          AND Ex_Dividend_Date IS NOT NULL
        ORDER BY Ex_Dividend_Date DESC
        """
        
        if limit:
            query = f"SELECT TOP {limit} " + query.split("SELECT ", 1)[1]
        
        logger.info(f"Loading dividend history{f' (limit: {limit})' if limit else ''}...")
        df = pd.read_sql(query, self.engine)
        logger.info(f"Loaded {len(df)} dividend records")
        return df
    
    def load_price_history(self, limit: Optional[int] = None) -> pd.DataFrame:
        """
        Load price history from vPrices view.
        
        Args:
            limit: Optional limit on number of rows to load
            
        Returns:
            DataFrame with price history
        """
        query = """
        SELECT 
            Ticker,
            Price,
            Volume,
            Bid,
            Ask,
            Change_Percent,
            Trade_Timestamp_UTC,
            Quote_Timestamp_UTC,
            Snapshot_Timestamp,
            Security_Type,
            Created_At
        FROM dbo.vPrices
        WHERE Ticker IS NOT NULL 
          AND Price IS NOT NULL
          AND Price > 0
        ORDER BY COALESCE(Trade_Timestamp_UTC, Snapshot_Timestamp, Created_At) DESC
        """
        
        if limit:
            query = f"SELECT TOP {limit} " + query.split("SELECT ", 1)[1]
        
        logger.info(f"Loading price history{f' (limit: {limit})' if limit else ''}...")
        df = pd.read_sql(query, self.engine)
        logger.info(f"Loaded {len(df)} price records")
        return df
    
    def load_ticker_info(self) -> pd.DataFrame:
        """
        Load ticker/company information from vTickers view.
        
        Returns:
            DataFrame with ticker information
        """
        query = """
        SELECT 
            Ticker,
            Ticker_Symbol_Name,
            Company_Name,
            Exchange,
            Sector,
            Industry,
            Country,
            Security_Type,
            Reference_Asset,
            Benchmark_Index,
            Inception_Date,
            Gross_Expense_Ratio,
            ThirtyDay_SEC_Yield,
            Distribution_Frequency
        FROM dbo.vTickers
        WHERE Ticker IS NOT NULL
        """
        
        logger.info("Loading ticker information...")
        df = pd.read_sql(query, self.engine)
        logger.info(f"Loaded {len(df)} ticker records")
        return df
    
    def get_latest_prices(self) -> pd.DataFrame:
        """
        Get latest price for each ticker.
        
        Returns:
            DataFrame with latest prices per ticker
        """
        query = """
        WITH LatestPrices AS (
            SELECT 
                Ticker,
                Price,
                Volume,
                Change_Percent,
                COALESCE(Trade_Timestamp_UTC, Snapshot_Timestamp, Created_At) AS Price_Date,
                ROW_NUMBER() OVER (PARTITION BY Ticker ORDER BY 
                    COALESCE(Trade_Timestamp_UTC, Snapshot_Timestamp, Created_At) DESC) AS rn
            FROM dbo.vPrices
            WHERE Price IS NOT NULL AND Price > 0
        )
        SELECT 
            Ticker,
            Price,
            Volume,
            Change_Percent,
            Price_Date
        FROM LatestPrices
        WHERE rn = 1
        """
        
        logger.info("Loading latest prices...")
        df = pd.read_sql(query, self.engine)
        logger.info(f"Loaded latest prices for {len(df)} tickers")
        return df
    
    def compute_dividend_features(self, ticker: Optional[str] = None) -> pd.DataFrame:
        """
        Compute dividend-related features for ML training.
        
        Features include:
        - Dividend yield trends (3m, 6m, 12m)
        - Payout consistency (coefficient of variation)
        - Growth rate (YoY)
        - Payment frequency
        - Days since last payment
        - Dividend coverage
        
        Args:
            ticker: Optional ticker to filter by
            
        Returns:
            DataFrame with computed features per ticker
        """
        logger.info(f"Computing dividend features{f' for {ticker}' if ticker else ''}...")
        
        ticker_filter = f"AND d.Ticker = '{ticker}'" if ticker else ""
        
        query = f"""
        WITH DividendMetrics AS (
            SELECT 
                d.Ticker,
                COUNT(DISTINCT d.Ex_Dividend_Date) AS payment_count,
                AVG(d.Dividend_Amount) AS avg_dividend,
                STDEV(d.Dividend_Amount) AS std_dividend,
                MIN(d.Ex_Dividend_Date) AS first_payment_date,
                MAX(d.Ex_Dividend_Date) AS last_payment_date,
                SUM(CASE WHEN d.Ex_Dividend_Date >= DATEADD(month, -3, CAST(GETDATE() AS DATE)) 
                    THEN d.Dividend_Amount ELSE 0 END) AS dividends_3m,
                SUM(CASE WHEN d.Ex_Dividend_Date >= DATEADD(month, -6, CAST(GETDATE() AS DATE)) 
                    THEN d.Dividend_Amount ELSE 0 END) AS dividends_6m,
                SUM(CASE WHEN d.Ex_Dividend_Date >= DATEADD(year, -1, CAST(GETDATE() AS DATE)) 
                    THEN d.Dividend_Amount ELSE 0 END) AS dividends_12m,
                SUM(CASE WHEN d.Ex_Dividend_Date >= DATEADD(year, -2, CAST(GETDATE() AS DATE)) 
                    AND d.Ex_Dividend_Date < DATEADD(year, -1, CAST(GETDATE() AS DATE))
                    THEN d.Dividend_Amount ELSE 0 END) AS dividends_prev_12m
            FROM dbo.vDividends d
            WHERE d.Dividend_Amount IS NOT NULL 
              AND d.Ex_Dividend_Date IS NOT NULL
              {ticker_filter}
            GROUP BY d.Ticker
        ),
        PriceMetrics AS (
            SELECT 
                p.Ticker,
                AVG(p.Price) AS avg_price,
                STDEV(p.Price) AS std_price,
                MIN(p.Price) AS min_price,
                MAX(p.Price) AS max_price
            FROM dbo.vPrices p
            WHERE p.Price IS NOT NULL AND p.Price > 0
              {ticker_filter.replace('d.', 'p.') if ticker_filter else ''}
            GROUP BY p.Ticker
        )
        SELECT 
            dm.Ticker,
            dm.payment_count,
            dm.avg_dividend,
            dm.std_dividend,
            CASE WHEN dm.avg_dividend > 0 
                THEN dm.std_dividend / dm.avg_dividend 
                ELSE 0 END AS dividend_cv,
            dm.dividends_3m,
            dm.dividends_6m,
            dm.dividends_12m,
            dm.dividends_prev_12m,
            CASE WHEN dm.dividends_prev_12m > 0 
                THEN (dm.dividends_12m - dm.dividends_prev_12m) / dm.dividends_prev_12m 
                ELSE 0 END AS dividend_growth_yoy,
            DATEDIFF(day, dm.last_payment_date, CAST(GETDATE() AS DATE)) AS days_since_last_payment,
            DATEDIFF(day, dm.first_payment_date, dm.last_payment_date) AS payment_history_days,
            pm.avg_price,
            pm.std_price,
            CASE WHEN pm.avg_price > 0 
                THEN pm.std_price / pm.avg_price 
                ELSE 0 END AS price_volatility,
            CASE WHEN pm.avg_price > 0 
                THEN (dm.dividends_12m / pm.avg_price) * 100 
                ELSE 0 END AS dividend_yield_12m
        FROM DividendMetrics dm
        LEFT JOIN PriceMetrics pm ON dm.Ticker = pm.Ticker
        WHERE dm.payment_count >= 2
        """
        
        df = pd.read_sql(query, self.engine)
        
        df['dividend_cv'] = df['dividend_cv'].fillna(0)
        df['dividend_growth_yoy'] = df['dividend_growth_yoy'].fillna(0)
        df['price_volatility'] = df['price_volatility'].fillna(0)
        df['dividend_yield_12m'] = df['dividend_yield_12m'].fillna(0)
        
        logger.info(f"Computed features for {len(df)} tickers")
        return df
    
    def prepare_training_data(self, 
                            include_features: List[str] = None,
                            min_history_days: int = 365) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Prepare comprehensive training dataset with features and targets.
        
        Args:
            include_features: List of feature names to include (None = all)
            min_history_days: Minimum payment history in days
            
        Returns:
            Tuple of (features_df, targets_df)
        """
        logger.info("Preparing comprehensive training data...")
        
        dividend_features = self.compute_dividend_features()
        
        dividend_features = dividend_features[
            dividend_features['payment_history_days'] >= min_history_days
        ]
        
        ticker_info = self.load_ticker_info()
        latest_prices = self.get_latest_prices()
        
        training_data = dividend_features.merge(
            ticker_info[['Ticker', 'Sector', 'Industry', 'Security_Type', 'Distribution_Frequency']], 
            on='Ticker', 
            how='left'
        )
        
        training_data = training_data.merge(
            latest_prices[['Ticker', 'Price']], 
            on='Ticker', 
            how='left'
        )
        
        training_data['has_sector'] = training_data['Sector'].notna().astype(int)
        training_data['has_industry'] = training_data['Industry'].notna().astype(int)
        training_data['is_etf'] = (training_data['Security_Type'] == 'ETF').astype(int)
        
        training_data['payout_ratio'] = np.where(
            training_data['Price'] > 0,
            (training_data['dividends_12m'] / training_data['Price']) * 100,
            0
        )
        
        training_data['payout_ratio'] = training_data['payout_ratio'].clip(0, 200)
        
        feature_cols = [
            'payment_count', 'avg_dividend', 'dividend_cv', 'dividends_3m',
            'dividends_6m', 'dividends_12m', 'dividend_growth_yoy',
            'days_since_last_payment', 'payment_history_days', 'price_volatility',
            'dividend_yield_12m', 'payout_ratio', 'has_sector', 'has_industry', 'is_etf'
        ]
        
        if include_features:
            feature_cols = [col for col in feature_cols if col in include_features]
        
        features_df = training_data[['Ticker'] + feature_cols].copy()
        
        targets_df = training_data[['Ticker', 'dividends_12m', 'dividend_growth_yoy', 
                                   'payout_ratio', 'dividend_yield_12m']].copy()
        
        features_df = features_df.fillna(0)
        targets_df = targets_df.fillna(0)
        
        logger.info(f"Prepared training data: {len(features_df)} samples, {len(feature_cols)} features")
        return features_df, targets_df


if __name__ == "__main__":
    extractor = DataExtractor()
    
    print("\n=== Testing Data Extraction ===\n")
    
    print("1. Loading dividend history (sample)...")
    dividends = extractor.load_dividend_history(limit=10)
    print(f"   Loaded {len(dividends)} records")
    print(dividends.head())
    
    print("\n2. Loading price history (sample)...")
    prices = extractor.load_price_history(limit=10)
    print(f"   Loaded {len(prices)} records")
    print(prices.head())
    
    print("\n3. Loading ticker information...")
    tickers = extractor.load_ticker_info()
    print(f"   Loaded {len(tickers)} tickers")
    print(tickers.head())
    
    print("\n4. Computing dividend features...")
    features = extractor.compute_dividend_features()
    print(f"   Computed features for {len(features)} tickers")
    print(features.head())
    
    print("\n5. Preparing training data...")
    features_df, targets_df = extractor.prepare_training_data()
    print(f"   Features shape: {features_df.shape}")
    print(f"   Targets shape: {targets_df.shape}")
    
    print("\n=== Data Extraction Test Complete ===")
