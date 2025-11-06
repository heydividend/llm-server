"""
Database schema for new AskHeyDividend features:
- Conversational Memory
- Proactive Insights
- Natural Language Alerts
- Tax Optimization AI
- Income Ladder Builder
"""

CREATE_FEATURES_TABLES_SQL = """
-- User Sessions Table (Session-based user identification)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'user_sessions')
    CREATE TABLE dbo.user_sessions (
        session_id VARCHAR(100) PRIMARY KEY,
        created_at DATETIME2 DEFAULT GETDATE(),
        last_active DATETIME2 DEFAULT GETDATE(),
        user_data NVARCHAR(MAX) -- JSON: {email, name, preferences}
    );

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_last_active') AND EXISTS (SELECT * FROM sys.tables WHERE name = 'user_sessions')
    CREATE INDEX idx_last_active ON dbo.user_sessions(last_active);

-- Conversations Table (Chat threads)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'conversations')
    CREATE TABLE dbo.conversations (
        conversation_id VARCHAR(100) PRIMARY KEY,
        session_id VARCHAR(100) NOT NULL,
        title NVARCHAR(500),
        created_at DATETIME2 DEFAULT GETDATE(),
        updated_at DATETIME2 DEFAULT GETDATE(),
        total_tokens INT DEFAULT 0,
        message_count INT DEFAULT 0,
        metadata NVARCHAR(MAX), -- JSON: {topics, tickers_mentioned, etc}
        FOREIGN KEY (session_id) REFERENCES dbo.user_sessions(session_id) ON DELETE CASCADE
    );

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_session_updated') AND EXISTS (SELECT * FROM sys.tables WHERE name = 'conversations')
    CREATE INDEX idx_session_updated ON dbo.conversations(session_id, updated_at DESC);

-- Conversation Messages Table (Individual messages)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'conversation_messages')
    CREATE TABLE dbo.conversation_messages (
        message_id VARCHAR(100) PRIMARY KEY,
        conversation_id VARCHAR(100) NOT NULL,
        role VARCHAR(20) NOT NULL, -- 'user' or 'assistant'
        content NVARCHAR(MAX) NOT NULL,
        tokens INT DEFAULT 0,
        created_at DATETIME2 DEFAULT GETDATE(),
        metadata NVARCHAR(MAX), -- JSON: {query_type, tickers, ml_predictions, etc}
        FOREIGN KEY (conversation_id) REFERENCES dbo.conversations(conversation_id) ON DELETE CASCADE
    );

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_conversation_created') AND EXISTS (SELECT * FROM sys.tables WHERE name = 'conversation_messages')
    CREATE INDEX idx_conversation_created ON dbo.conversation_messages(conversation_id, created_at);

-- User Portfolios Table (Holdings with tax lots)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'user_portfolios')
    CREATE TABLE dbo.user_portfolios (
        portfolio_id VARCHAR(100) PRIMARY KEY,
        session_id VARCHAR(100) NOT NULL,
        ticker VARCHAR(20) NOT NULL,
        shares DECIMAL(18, 6) NOT NULL,
        cost_basis DECIMAL(18, 4), -- Average cost per share
        purchase_date DATE,
        current_price DECIMAL(18, 4),
        current_value DECIMAL(18, 4),
        unrealized_gain_loss DECIMAL(18, 4),
        annual_dividend DECIMAL(18, 4),
        created_at DATETIME2 DEFAULT GETDATE(),
        updated_at DATETIME2 DEFAULT GETDATE(),
        FOREIGN KEY (session_id) REFERENCES dbo.user_sessions(session_id) ON DELETE CASCADE
    );

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_session_ticker') AND EXISTS (SELECT * FROM sys.tables WHERE name = 'user_portfolios')
    CREATE INDEX idx_session_ticker ON dbo.user_portfolios(session_id, ticker);

-- Alert Rules Table (Natural language alerts)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'alert_rules')
    CREATE TABLE dbo.alert_rules (
        alert_id VARCHAR(100) PRIMARY KEY,
        session_id VARCHAR(100) NOT NULL,
        rule_name NVARCHAR(500) NOT NULL,
        natural_language NVARCHAR(MAX) NOT NULL, -- Original user request
        condition_type VARCHAR(50) NOT NULL, -- 'price_target', 'dividend_cut', 'yield_change', etc
        ticker VARCHAR(20),
        trigger_condition NVARCHAR(MAX) NOT NULL, -- JSON: {operator, value, threshold}
        is_active BIT DEFAULT 1,
        notification_method VARCHAR(50) DEFAULT 'in_app', -- 'in_app', 'email', 'both'
        created_at DATETIME2 DEFAULT GETDATE(),
        last_checked DATETIME2,
        FOREIGN KEY (session_id) REFERENCES dbo.user_sessions(session_id) ON DELETE CASCADE
    );

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_session_active') AND EXISTS (SELECT * FROM sys.tables WHERE name = 'alert_rules')
    CREATE INDEX idx_session_active ON dbo.alert_rules(session_id, is_active);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_ticker_active') AND EXISTS (SELECT * FROM sys.tables WHERE name = 'alert_rules')
    CREATE INDEX idx_ticker_active ON dbo.alert_rules(ticker, is_active);

-- Alert Events Table (Triggered alerts history)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'alert_events')
    CREATE TABLE dbo.alert_events (
        event_id VARCHAR(100) PRIMARY KEY,
        alert_id VARCHAR(100) NOT NULL,
        triggered_at DATETIME2 DEFAULT GETDATE(),
        condition_met NVARCHAR(MAX) NOT NULL, -- JSON: Description of what triggered
        ticker VARCHAR(20),
        current_value DECIMAL(18, 4),
        notification_sent BIT DEFAULT 0,
        notification_delivered_at DATETIME2,
        read_status BIT DEFAULT 0,
        FOREIGN KEY (alert_id) REFERENCES dbo.alert_rules(alert_id) ON DELETE CASCADE
    );

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_alert_triggered') AND EXISTS (SELECT * FROM sys.tables WHERE name = 'alert_events')
    CREATE INDEX idx_alert_triggered ON dbo.alert_events(alert_id, triggered_at DESC);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_unread') AND EXISTS (SELECT * FROM sys.tables WHERE name = 'alert_events')
    CREATE INDEX idx_unread ON dbo.alert_events(read_status, triggered_at DESC);

-- Tax Scenarios Table (Tax optimization data)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'tax_scenarios')
    CREATE TABLE dbo.tax_scenarios (
        scenario_id VARCHAR(100) PRIMARY KEY,
        session_id VARCHAR(100) NOT NULL,
        scenario_type VARCHAR(50) NOT NULL, -- 'qualified_dividends', 'tax_loss_harvest', 'gain_harvest'
        ticker VARCHAR(20),
        analysis_data NVARCHAR(MAX) NOT NULL, -- JSON: Full tax analysis
        recommendations NVARCHAR(MAX), -- JSON: AI recommendations
        potential_savings DECIMAL(18, 4),
        tax_year INT,
        created_at DATETIME2 DEFAULT GETDATE(),
        FOREIGN KEY (session_id) REFERENCES dbo.user_sessions(session_id) ON DELETE CASCADE
    );

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_session_year') AND EXISTS (SELECT * FROM sys.tables WHERE name = 'tax_scenarios')
    CREATE INDEX idx_session_year ON dbo.tax_scenarios(session_id, tax_year DESC);

-- Income Ladders Table (Monthly income planning)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'income_ladders')
    CREATE TABLE dbo.income_ladders (
        ladder_id VARCHAR(100) PRIMARY KEY,
        session_id VARCHAR(100) NOT NULL,
        target_monthly_income DECIMAL(18, 4) NOT NULL,
        total_capital_needed DECIMAL(18, 4),
        ladder_strategy NVARCHAR(MAX) NOT NULL, -- JSON: Monthly ticker allocations
        created_at DATETIME2 DEFAULT GETDATE(),
        updated_at DATETIME2 DEFAULT GETDATE(),
        is_active BIT DEFAULT 1,
        FOREIGN KEY (session_id) REFERENCES dbo.user_sessions(session_id) ON DELETE CASCADE
    );

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_session_active_income_ladders') AND EXISTS (SELECT * FROM sys.tables WHERE name = 'income_ladders')
    CREATE INDEX idx_session_active_income_ladders ON dbo.income_ladders(session_id, is_active);

-- Proactive Insights Table (Daily digest queue)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'proactive_insights')
    CREATE TABLE dbo.proactive_insights (
        insight_id VARCHAR(100) PRIMARY KEY,
        session_id VARCHAR(100) NOT NULL,
        insight_type VARCHAR(50) NOT NULL, -- 'daily_digest', 'portfolio_update', 'market_alert'
        title NVARCHAR(500) NOT NULL,
        content NVARCHAR(MAX) NOT NULL,
        priority INT DEFAULT 5, -- 1-10, 10 = highest
        created_at DATETIME2 DEFAULT GETDATE(),
        delivered_at DATETIME2,
        read_status BIT DEFAULT 0,
        metadata NVARCHAR(MAX), -- JSON: {tickers, changes, etc}
        FOREIGN KEY (session_id) REFERENCES dbo.user_sessions(session_id) ON DELETE CASCADE
    );

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_session_unread') AND EXISTS (SELECT * FROM sys.tables WHERE name = 'proactive_insights')
    CREATE INDEX idx_session_unread ON dbo.proactive_insights(session_id, read_status, priority DESC);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_delivered') AND EXISTS (SELECT * FROM sys.tables WHERE name = 'proactive_insights')
    CREATE INDEX idx_delivered ON dbo.proactive_insights(delivered_at);
"""
