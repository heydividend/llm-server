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

-- ============================================================================
-- CONTINUOUS LEARNING PIPELINE TABLES (Phase 3: Gemini-Enhanced Learning)
-- ============================================================================

-- Feedback Labels Table (Gemini-analyzed categorization)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'feedback_labels')
    CREATE TABLE dbo.feedback_labels (
        label_id VARCHAR(100) PRIMARY KEY,
        feedback_id VARCHAR(50) NOT NULL,
        
        -- Gemini analysis results
        category VARCHAR(50) NOT NULL, -- 'accuracy', 'helpfulness', 'tone', 'completeness', 'relevance'
        sentiment_reason NVARCHAR(MAX), -- Why Gemini thinks feedback was positive/negative
        improvement_suggestions NVARCHAR(MAX), -- Specific suggestions for improvement
        
        -- Pattern identification
        response_strengths NVARCHAR(MAX), -- JSON array: ['clear_explanation', 'data_driven']
        response_weaknesses NVARCHAR(MAX), -- JSON array: ['too_technical', 'missing_context']
        
        -- Topic classification
        primary_topic VARCHAR(100), -- 'dividend_analysis', 'portfolio_advice', 'tax_planning'
        subtopics NVARCHAR(MAX), -- JSON array: ['yield_calculation', 'payout_ratio']
        
        -- Quality assessment
        training_worthiness DECIMAL(3,2), -- 0.0-1.0 score of how good for training
        pii_detected BIT DEFAULT 0, -- Privacy flag
        toxic_content BIT DEFAULT 0, -- Governance flag
        
        -- Analysis metadata
        analyzed_by VARCHAR(50) DEFAULT 'gemini-2.0-flash-exp',
        analysis_tokens INT,
        analysis_latency_ms INT,
        created_at DATETIME2 DEFAULT GETDATE(),
        
        FOREIGN KEY (feedback_id) REFERENCES dbo.conversation_feedback(feedback_id) ON DELETE CASCADE
    );

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_feedback_labels_feedback') AND EXISTS (SELECT * FROM sys.tables WHERE name = 'feedback_labels')
    CREATE INDEX idx_feedback_labels_feedback ON dbo.feedback_labels(feedback_id);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_feedback_labels_category') AND EXISTS (SELECT * FROM sys.tables WHERE name = 'feedback_labels')
    CREATE INDEX idx_feedback_labels_category ON dbo.feedback_labels(category, training_worthiness DESC);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_feedback_labels_quality') AND EXISTS (SELECT * FROM sys.tables WHERE name = 'feedback_labels')
    CREATE INDEX idx_feedback_labels_quality ON dbo.feedback_labels(training_worthiness DESC, pii_detected, toxic_content);

-- Fine-Tuning Samples Table (RLHF training pairs)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'fine_tuning_samples')
    CREATE TABLE dbo.fine_tuning_samples (
        sample_id VARCHAR(100) PRIMARY KEY,
        
        -- Training pair type
        sample_type VARCHAR(50) NOT NULL, -- 'preference_pair', 'demonstration', 'rejection'
        
        -- Chosen response (positive feedback)
        chosen_feedback_id VARCHAR(50),
        chosen_prompt NVARCHAR(MAX) NOT NULL,
        chosen_response NVARCHAR(MAX) NOT NULL,
        chosen_rating DECIMAL(3,2), -- Quality score
        
        -- Rejected response (negative feedback, if pair)
        rejected_feedback_id VARCHAR(50),
        rejected_prompt NVARCHAR(MAX),
        rejected_response NVARCHAR(MAX),
        rejected_rating DECIMAL(3,2),
        
        -- Context and metadata
        query_type VARCHAR(100),
        category VARCHAR(50), -- From feedback_labels
        
        -- Quality and governance
        quality_score DECIMAL(3,2) NOT NULL, -- Overall sample quality
        pii_filtered BIT DEFAULT 0, -- PII removed?
        toxicity_filtered BIT DEFAULT 0, -- Toxic content removed?
        ready_for_training BIT DEFAULT 0, -- Passed all checks?
        
        -- Usage tracking
        used_in_training BIT DEFAULT 0,
        training_batch_id VARCHAR(100),
        training_date DATETIME2,
        
        -- OpenAI fine-tuning format
        openai_format NVARCHAR(MAX), -- JSONL format for fine-tuning
        
        created_at DATETIME2 DEFAULT GETDATE(),
        
        FOREIGN KEY (chosen_feedback_id) REFERENCES dbo.conversation_feedback(feedback_id) ON DELETE CASCADE
    );

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_fine_tuning_type') AND EXISTS (SELECT * FROM sys.tables WHERE name = 'fine_tuning_samples')
    CREATE INDEX idx_fine_tuning_type ON dbo.fine_tuning_samples(sample_type, ready_for_training);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_fine_tuning_ready') AND EXISTS (SELECT * FROM sys.tables WHERE name = 'fine_tuning_samples')
    CREATE INDEX idx_fine_tuning_ready ON dbo.fine_tuning_samples(ready_for_training, used_in_training, quality_score DESC);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_fine_tuning_category') AND EXISTS (SELECT * FROM sys.tables WHERE name = 'fine_tuning_samples')
    CREATE INDEX idx_fine_tuning_category ON dbo.fine_tuning_samples(category, query_type);

-- Learning Metrics Table (Track improvement over time)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'learning_metrics')
    CREATE TABLE dbo.learning_metrics (
        metric_id VARCHAR(100) PRIMARY KEY,
        
        -- Time period
        period_start DATETIME2 NOT NULL,
        period_end DATETIME2 NOT NULL,
        period_type VARCHAR(20) NOT NULL, -- 'daily', 'weekly', 'monthly'
        
        -- Feedback metrics
        total_feedback INT DEFAULT 0,
        positive_feedback INT DEFAULT 0,
        negative_feedback INT DEFAULT 0,
        avg_rating DECIMAL(3,2),
        feedback_velocity DECIMAL(10,2), -- Feedback per day
        
        -- Category breakdown (JSON)
        feedback_by_category NVARCHAR(MAX), -- {'accuracy': 45, 'helpfulness': 32, ...}
        feedback_by_query_type NVARCHAR(MAX), -- {'dividend_analysis': 67, ...}
        
        -- Training data generated
        samples_generated INT DEFAULT 0,
        high_quality_samples INT DEFAULT 0,
        samples_used INT DEFAULT 0,
        
        -- Improvement trends
        avg_quality_score DECIMAL(3,2),
        quality_trend VARCHAR(20), -- 'improving', 'stable', 'declining'
        top_improvement_areas NVARCHAR(MAX), -- JSON array
        top_problem_areas NVARCHAR(MAX), -- JSON array
        
        -- Gemini usage
        gemini_api_calls INT DEFAULT 0,
        gemini_tokens_used INT DEFAULT 0,
        estimated_cost_usd DECIMAL(10,4),
        
        -- Metadata
        analyzed_by VARCHAR(100) DEFAULT 'continuous_learning_service',
        created_at DATETIME2 DEFAULT GETDATE()
    );

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_learning_period') AND EXISTS (SELECT * FROM sys.tables WHERE name = 'learning_metrics')
    CREATE INDEX idx_learning_period ON dbo.learning_metrics(period_type, period_start DESC);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_learning_quality') AND EXISTS (SELECT * FROM sys.tables WHERE name = 'learning_metrics')
    CREATE INDEX idx_learning_quality ON dbo.learning_metrics(quality_trend, avg_quality_score DESC);

-- ============================================================================
-- ML MODEL EVALUATION AUDIT (Phase 4: Gemini ML Model Evaluator)
-- ============================================================================

-- ML Evaluation Audit Table (Gemini validation of ML predictions)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ml_evaluation_audit')
    CREATE TABLE dbo.ml_evaluation_audit (
        audit_id VARCHAR(100) PRIMARY KEY,
        ticker VARCHAR(20) NOT NULL,
        model_name VARCHAR(50) NOT NULL, -- 'dividend_scorer', 'yield_predictor', etc.
        prediction_value DECIMAL(18, 4) NOT NULL,
        
        -- Gemini validation results
        gemini_validation VARCHAR(50) NOT NULL, -- 'agree', 'disagree', 'uncertain', 'partially_agree'
        explanation NVARCHAR(MAX) NOT NULL, -- Natural language explanation
        confidence_score DECIMAL(3, 2) NOT NULL, -- 0.0-1.0
        
        -- Anomaly detection
        anomaly_detected BIT DEFAULT 0,
        anomaly_risk VARCHAR(20), -- 'HIGH', 'MEDIUM', 'LOW'
        
        -- Metadata
        metadata NVARCHAR(MAX), -- JSON: {key_factors, gemini_usage, model_metadata}
        evaluation_timestamp DATETIME2 DEFAULT GETDATE(),
        
        -- Indexes for performance
        INDEX idx_ticker_model (ticker, model_name),
        INDEX idx_model_timestamp (model_name, evaluation_timestamp DESC),
        INDEX idx_validation (gemini_validation, confidence_score DESC),
        INDEX idx_anomaly (anomaly_detected, evaluation_timestamp DESC)
    );

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_ml_eval_ticker_model') AND EXISTS (SELECT * FROM sys.tables WHERE name = 'ml_evaluation_audit')
    CREATE INDEX idx_ml_eval_ticker_model ON dbo.ml_evaluation_audit(ticker, model_name);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_ml_eval_model_timestamp') AND EXISTS (SELECT * FROM sys.tables WHERE name = 'ml_evaluation_audit')
    CREATE INDEX idx_ml_eval_model_timestamp ON dbo.ml_evaluation_audit(model_name, evaluation_timestamp DESC);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_ml_eval_validation') AND EXISTS (SELECT * FROM sys.tables WHERE name = 'ml_evaluation_audit')
    CREATE INDEX idx_ml_eval_validation ON dbo.ml_evaluation_audit(gemini_validation, confidence_score DESC);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_ml_eval_anomaly') AND EXISTS (SELECT * FROM sys.tables WHERE name = 'ml_evaluation_audit')
    CREATE INDEX idx_ml_eval_anomaly ON dbo.ml_evaluation_audit(anomaly_detected, evaluation_timestamp DESC);
"""
