-- Migration: Add tables for Investor Education, Video Service, and Dividend Lists features
-- Date: 2024-11-16
-- Description: Creates database schema for new Harvey AI features

-- ============================================
-- User Watchlist Table
-- ============================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'user_watchlist')
BEGIN
    CREATE TABLE user_watchlist (
        id INT IDENTITY(1,1) PRIMARY KEY,
        user_id INT NOT NULL,
        ticker VARCHAR(10) NOT NULL,
        added_date DATETIME NOT NULL DEFAULT GETDATE(),
        notes VARCHAR(500) NULL,
        CONSTRAINT UQ_user_watchlist_user_ticker UNIQUE (user_id, ticker)
    );
    
    CREATE INDEX IX_user_watchlist_user_id ON user_watchlist(user_id);
    CREATE INDEX IX_user_watchlist_ticker ON user_watchlist(ticker);
END
GO

-- ============================================
-- User Portfolio Table
-- ============================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'user_portfolio')
BEGIN
    CREATE TABLE user_portfolio (
        id INT IDENTITY(1,1) PRIMARY KEY,
        user_id INT NOT NULL,
        ticker VARCHAR(10) NOT NULL,
        shares DECIMAL(18, 4) NOT NULL,
        cost_basis DECIMAL(18, 4) NOT NULL,
        purchase_date DATE NOT NULL,
        notes VARCHAR(500) NULL,
        CONSTRAINT UQ_user_portfolio_user_ticker UNIQUE (user_id, ticker)
    );
    
    CREATE INDEX IX_user_portfolio_user_id ON user_portfolio(user_id);
    CREATE INDEX IX_user_portfolio_ticker ON user_portfolio(ticker);
END
GO

-- ============================================
-- Dividend Lists Table (Custom User Lists)
-- ============================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'dividend_lists')
BEGIN
    CREATE TABLE dividend_lists (
        list_id INT IDENTITY(1,1) PRIMARY KEY,
        user_id INT NOT NULL,
        list_name VARCHAR(100) NOT NULL,
        category_id VARCHAR(50) NULL,
        description VARCHAR(500) NULL,
        created_date DATETIME NOT NULL DEFAULT GETDATE(),
        updated_date DATETIME NULL,
        stock_count INT NOT NULL DEFAULT 0,
        is_public BIT NOT NULL DEFAULT 0
    );
    
    CREATE INDEX IX_dividend_lists_user_id ON dividend_lists(user_id);
    CREATE INDEX IX_dividend_lists_category_id ON dividend_lists(category_id);
END
GO

-- ============================================
-- Dividend List Stocks Table
-- ============================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'dividend_list_stocks')
BEGIN
    CREATE TABLE dividend_list_stocks (
        id INT IDENTITY(1,1) PRIMARY KEY,
        list_id INT NOT NULL,
        ticker VARCHAR(10) NOT NULL,
        added_date DATETIME NOT NULL DEFAULT GETDATE(),
        sort_order INT NULL,
        notes VARCHAR(500) NULL,
        CONSTRAINT FK_dividend_list_stocks_list FOREIGN KEY (list_id) 
            REFERENCES dividend_lists(list_id) ON DELETE CASCADE,
        CONSTRAINT UQ_dividend_list_stocks_list_ticker UNIQUE (list_id, ticker)
    );
    
    CREATE INDEX IX_dividend_list_stocks_list_id ON dividend_list_stocks(list_id);
    CREATE INDEX IX_dividend_list_stocks_ticker ON dividend_list_stocks(ticker);
END
GO

-- ============================================
-- User Feedback Table (for Investor Education)
-- ============================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'user_feedback')
BEGIN
    CREATE TABLE user_feedback (
        id INT IDENTITY(1,1) PRIMARY KEY,
        user_id INT NULL,
        session_id VARCHAR(100) NULL,
        query_text VARCHAR(MAX) NOT NULL,
        response_text VARCHAR(MAX) NULL,
        feedback_type VARCHAR(50) NULL, -- 'helpful', 'not_helpful', 'misconception_detected'
        rating INT NULL, -- 1-5 stars
        comments VARCHAR(MAX) NULL,
        created_date DATETIME NOT NULL DEFAULT GETDATE()
    );
    
    CREATE INDEX IX_user_feedback_user_id ON user_feedback(user_id);
    CREATE INDEX IX_user_feedback_feedback_type ON user_feedback(feedback_type);
    CREATE INDEX IX_user_feedback_created_date ON user_feedback(created_date);
END
GO

-- ============================================
-- Video Engagement Tracking
-- ============================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'video_engagement')
BEGIN
    CREATE TABLE video_engagement (
        id INT IDENTITY(1,1) PRIMARY KEY,
        user_id INT NULL,
        video_id VARCHAR(50) NOT NULL,
        query_text VARCHAR(500) NULL,
        clicked BIT NOT NULL DEFAULT 0,
        watched BIT NOT NULL DEFAULT 0,
        helpful BIT NULL,
        created_date DATETIME NOT NULL DEFAULT GETDATE()
    );
    
    CREATE INDEX IX_video_engagement_user_id ON video_engagement(user_id);
    CREATE INDEX IX_video_engagement_video_id ON video_engagement(video_id);
    CREATE INDEX IX_video_engagement_created_date ON video_engagement(created_date);
END
GO

-- ============================================
-- Stock Profiles Table Enhancement
-- Add fields if they don't exist
-- ============================================
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'stock_profiles')
BEGIN
    -- Add consecutive_years column if not exists
    IF NOT EXISTS (SELECT * FROM sys.columns 
                   WHERE object_id = OBJECT_ID('stock_profiles') 
                   AND name = 'consecutive_years')
    BEGIN
        ALTER TABLE stock_profiles 
        ADD consecutive_years INT NULL;
    END
    
    -- Add payment_frequency column if not exists
    IF NOT EXISTS (SELECT * FROM sys.columns 
                   WHERE object_id = OBJECT_ID('stock_profiles') 
                   AND name = 'payment_frequency')
    BEGIN
        ALTER TABLE stock_profiles 
        ADD payment_frequency VARCHAR(20) NULL;
    END
    
    -- Add is_active column if not exists
    IF NOT EXISTS (SELECT * FROM sys.columns 
                   WHERE object_id = OBJECT_ID('stock_profiles') 
                   AND name = 'is_active')
    BEGIN
        ALTER TABLE stock_profiles 
        ADD is_active BIT NOT NULL DEFAULT 1;
    END
END
GO

-- ============================================
-- Insert Sample Data for Testing
-- ============================================

-- Sample watchlist entry
IF NOT EXISTS (SELECT * FROM user_watchlist WHERE user_id = 1)
BEGIN
    INSERT INTO user_watchlist (user_id, ticker, added_date)
    VALUES (1, 'AAPL', GETDATE());
END
GO

PRINT 'Migration 001_add_new_features.sql completed successfully';
GO
