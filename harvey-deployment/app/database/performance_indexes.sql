-- Performance Indexes for Harvey Database
-- 
-- These indexes optimize common query patterns:
-- - Ticker lookups
-- - Date-based filtering
-- - Price queries
--
-- SQL Server Note: SQL Server doesn't have "IF NOT EXISTS" for CREATE INDEX
-- We use conditional logic to check if index exists before creating

-- Index 1: Fast ticker lookups in vDividends
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_vDividends_Ticker' AND object_id = OBJECT_ID('dbo.vDividends'))
BEGIN
    CREATE NONCLUSTERED INDEX idx_vDividends_Ticker
    ON dbo.vDividends(Ticker)
    INCLUDE (Payment_Date, Ex_Dividend_Date, Amount, Frequency, Currency);
    PRINT 'Created index: idx_vDividends_Ticker';
END
ELSE
BEGIN
    PRINT 'Index already exists: idx_vDividends_Ticker';
END
GO

-- Index 2: Recent dividend queries (payment date descending)
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_vDividends_PaymentDate' AND object_id = OBJECT_ID('dbo.vDividends'))
BEGIN
    CREATE NONCLUSTERED INDEX idx_vDividends_PaymentDate
    ON dbo.vDividends(Payment_Date DESC)
    INCLUDE (Ticker, Amount, Frequency, Ex_Dividend_Date);
    PRINT 'Created index: idx_vDividends_PaymentDate';
END
ELSE
BEGIN
    PRINT 'Index already exists: idx_vDividends_PaymentDate';
END
GO

-- Index 3: Ex-dividend date filtering
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_vDividends_ExDividendDate' AND object_id = OBJECT_ID('dbo.vDividends'))
BEGIN
    CREATE NONCLUSTERED INDEX idx_vDividends_ExDividendDate
    ON dbo.vDividends(Ex_Dividend_Date DESC)
    INCLUDE (Ticker, Payment_Date, Amount, Frequency);
    PRINT 'Created index: idx_vDividends_ExDividendDate';
END
ELSE
BEGIN
    PRINT 'Index already exists: idx_vDividends_ExDividendDate';
END
GO

-- Index 4: Composite index for sorted ticker queries with dates
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_vDividends_Ticker_PaymentDate' AND object_id = OBJECT_ID('dbo.vDividends'))
BEGIN
    CREATE NONCLUSTERED INDEX idx_vDividends_Ticker_PaymentDate
    ON dbo.vDividends(Ticker, Payment_Date DESC)
    INCLUDE (Amount, Frequency, Ex_Dividend_Date, Currency);
    PRINT 'Created index: idx_vDividends_Ticker_PaymentDate';
END
ELSE
BEGIN
    PRINT 'Index already exists: idx_vDividends_Ticker_PaymentDate';
END
GO

-- Index 5: Latest price queries (ticker + timestamp)
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_vPrices_Ticker_Timestamp' AND object_id = OBJECT_ID('dbo.vPrices'))
BEGIN
    CREATE NONCLUSTERED INDEX idx_vPrices_Ticker_Timestamp
    ON dbo.vPrices(Ticker, Trade_Timestamp_UTC DESC)
    INCLUDE (Last_Price, Bid_Price, Ask_Price, High_Price, Low_Price, Volume);
    PRINT 'Created index: idx_vPrices_Ticker_Timestamp';
END
ELSE
BEGIN
    PRINT 'Index already exists: idx_vPrices_Ticker_Timestamp';
END
GO

-- Index 6: Ticker lookups in vPrices
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_vPrices_Ticker' AND object_id = OBJECT_ID('dbo.vPrices'))
BEGIN
    CREATE NONCLUSTERED INDEX idx_vPrices_Ticker
    ON dbo.vPrices(Ticker)
    INCLUDE (Trade_Timestamp_UTC, Last_Price, Volume);
    PRINT 'Created index: idx_vPrices_Ticker';
END
ELSE
BEGIN
    PRINT 'Index already exists: idx_vPrices_Ticker';
END
GO

PRINT 'Performance indexes created successfully!';
GO
