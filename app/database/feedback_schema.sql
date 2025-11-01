-- Conversation Feedback & Learning System Schema
-- Azure SQL Server Compatible

-- Table 1: Store user feedback on Harvey's responses
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'conversation_feedback')
BEGIN
    CREATE TABLE conversation_feedback (
    feedback_id VARCHAR(50) PRIMARY KEY,
    request_id VARCHAR(50) NOT NULL,
    response_id VARCHAR(50) NOT NULL,
    session_id VARCHAR(50),
    conversation_id VARCHAR(50),
    
    -- Feedback data
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    sentiment VARCHAR(20) CHECK (sentiment IN ('positive', 'negative', 'neutral')),
    feedback_type VARCHAR(50), -- 'thumbs_up', 'thumbs_down', 'rating', 'comment'
    user_comment TEXT,
    
    -- Issue tags (what was wrong/right)
    tags TEXT, -- Comma-separated: 'accurate,helpful,fast' or 'confusing,incomplete'
    
    -- Context (what was the conversation about)
    user_query TEXT NOT NULL,
    harvey_response TEXT,
    response_metadata TEXT, -- JSON string: tickers, ML predictions used, etc.
    
    -- Query classification
    query_type VARCHAR(100), -- 'dividend_history', 'portfolio_analysis', 'ml_prediction', etc.
    action_taken VARCHAR(100), -- 'sql_query', 'web_search', 'ml_prediction', 'passive_income_plan'
    
    -- User context
    user_ip VARCHAR(50),
    user_agent TEXT,
    session_duration_sec INTEGER,
    
    -- Timestamps
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE()
    );
END
GO

-- Table 2: Track successful response patterns
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'successful_response_patterns')
BEGIN
    CREATE TABLE successful_response_patterns (
    pattern_id VARCHAR(50) PRIMARY KEY,
    query_type VARCHAR(100) NOT NULL,
    action_type VARCHAR(100), -- 'sql_query', 'web_search', 'ml_prediction', etc.
    
    -- Performance metrics
    avg_rating DECIMAL(3,2),
    positive_feedback_count INTEGER DEFAULT 0,
    negative_feedback_count INTEGER DEFAULT 0,
    total_responses INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2), -- Percentage of positive feedback
    
    -- Pattern characteristics (JSON string)
    key_features TEXT, -- '{"includes_ml_predictions":true,"table_format":true,"uses_charts":false}'
    
    -- Examples
    example_queries TEXT, -- Comma-separated or JSON array as string
    example_responses TEXT,
    
    -- Metadata
    first_seen DATETIME DEFAULT GETDATE(),
    last_updated DATETIME DEFAULT GETDATE(),
    last_positive_feedback DATETIME
    );
END
GO

-- Table 3: User preference learning (for personalization)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'user_preferences')
BEGIN
    CREATE TABLE user_preferences (
    user_id VARCHAR(50) PRIMARY KEY,
    session_id VARCHAR(50),
    
    -- Response preferences (learned from feedback)
    preferred_response_length VARCHAR(20), -- 'concise', 'detailed', 'comprehensive'
    preferred_features TEXT, -- Comma-separated: 'ml_predictions,charts,tax_tips,sector_analysis'
    
    -- Portfolio preferences
    portfolio_style VARCHAR(50), -- 'dividend_growth', 'high_yield', 'balanced', 'value'
    risk_tolerance VARCHAR(20), -- 'conservative', 'moderate', 'aggressive'
    
    -- Interaction patterns
    avg_session_duration_sec INTEGER,
    total_queries INTEGER DEFAULT 0,
    positive_feedback_count INTEGER DEFAULT 0,
    negative_feedback_count INTEGER DEFAULT 0,
    
    -- Communication style
    communication_style VARCHAR(20), -- 'professional', 'casual', 'technical'
    prefers_charts BIT DEFAULT 0,
    prefers_ml_predictions BIT DEFAULT 1,
    
    -- Metadata
    first_seen DATETIME DEFAULT GETDATE(),
    last_seen DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE()
    );
END
GO

-- Table 4: Training data for GPT-4o fine-tuning
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'gpt_training_data')
BEGIN
    CREATE TABLE gpt_training_data (
    training_id VARCHAR(50) PRIMARY KEY,
    feedback_id VARCHAR(50) REFERENCES conversation_feedback(feedback_id),
    
    -- Training pair
    user_message TEXT NOT NULL,
    assistant_message TEXT NOT NULL,
    
    -- Quality score
    quality_score DECIMAL(3,2), -- Derived from rating, 0.0 to 1.0
    is_high_quality BIT DEFAULT 0, -- rating >= 4
    
    -- Training metadata
    used_in_training BIT DEFAULT 0,
    training_batch_id VARCHAR(50),
    model_version VARCHAR(50), -- e.g., 'harvey-v1', 'harvey-v2'
    
    -- Context
    query_type VARCHAR(100),
    includes_ml_predictions BIT DEFAULT 0,
    includes_sql_results BIT DEFAULT 0,
    includes_web_search BIT DEFAULT 0,
    
    -- Timestamps
    created_at DATETIME DEFAULT GETDATE(),
    exported_at DATETIME
    );
END
GO

-- Indexes for performance
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_feedback_response_id')
    CREATE INDEX idx_feedback_response_id ON conversation_feedback(response_id);
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_feedback_session_id')
    CREATE INDEX idx_feedback_session_id ON conversation_feedback(session_id);
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_feedback_rating')
    CREATE INDEX idx_feedback_rating ON conversation_feedback(rating);
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_feedback_sentiment')
    CREATE INDEX idx_feedback_sentiment ON conversation_feedback(sentiment);
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_feedback_query_type')
    CREATE INDEX idx_feedback_query_type ON conversation_feedback(query_type);
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_feedback_created_at')
    CREATE INDEX idx_feedback_created_at ON conversation_feedback(created_at);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_patterns_query_type')
    CREATE INDEX idx_patterns_query_type ON successful_response_patterns(query_type);
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_patterns_success_rate')
    CREATE INDEX idx_patterns_success_rate ON successful_response_patterns(success_rate);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_training_quality')
    CREATE INDEX idx_training_quality ON gpt_training_data(is_high_quality);
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_training_used')
    CREATE INDEX idx_training_used ON gpt_training_data(used_in_training);
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_training_batch')
    CREATE INDEX idx_training_batch ON gpt_training_data(training_batch_id);
GO

-- Views for analytics
IF EXISTS (SELECT * FROM sys.views WHERE name = 'v_feedback_summary')
    DROP VIEW v_feedback_summary;
GO

CREATE VIEW v_feedback_summary AS
SELECT 
    query_type,
    action_taken,
    COUNT(*) as total_feedback,
    AVG(rating) as avg_rating,
    SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) as positive_count,
    SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) as negative_count,
    ROUND(100.0 * SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
FROM conversation_feedback
WHERE rating IS NOT NULL
GROUP BY query_type, action_taken;
GO

IF EXISTS (SELECT * FROM sys.views WHERE name = 'v_high_quality_training_data')
    DROP VIEW v_high_quality_training_data;
GO

CREATE VIEW v_high_quality_training_data AS
SELECT 
    t.training_id,
    t.user_message,
    t.assistant_message,
    t.quality_score,
    f.rating,
    f.query_type,
    t.created_at
FROM gpt_training_data t
JOIN conversation_feedback f ON t.feedback_id = f.feedback_id
WHERE t.is_high_quality = 1
  AND t.used_in_training = 0;
GO
