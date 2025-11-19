-- ============================================================================
-- GEMINI INTELLIGENCE SYSTEM DATABASE SCHEMA
-- ============================================================================
-- This file creates 4 standalone tables for Gemini features:
--   1. feedback_labels - Gemini-analyzed feedback categorization
--   2. fine_tuning_samples - RLHF training pairs
--   3. learning_metrics - Improvement tracking over time
--   4. ml_evaluation_audit - ML model validation
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
        created_at DATETIME2 DEFAULT GETDATE()
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
        
        created_at DATETIME2 DEFAULT GETDATE()
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
        evaluation_timestamp DATETIME2 DEFAULT GETDATE()
    );

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_ml_eval_ticker_model') AND EXISTS (SELECT * FROM sys.tables WHERE name = 'ml_evaluation_audit')
    CREATE INDEX idx_ml_eval_ticker_model ON dbo.ml_evaluation_audit(ticker, model_name);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_ml_eval_model_timestamp') AND EXISTS (SELECT * FROM sys.tables WHERE name = 'ml_evaluation_audit')
    CREATE INDEX idx_ml_eval_model_timestamp ON dbo.ml_evaluation_audit(model_name, evaluation_timestamp DESC);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_ml_eval_validation') AND EXISTS (SELECT * FROM sys.tables WHERE name = 'ml_evaluation_audit')
    CREATE INDEX idx_ml_eval_validation ON dbo.ml_evaluation_audit(gemini_validation, confidence_score DESC);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_ml_eval_anomaly') AND EXISTS (SELECT * FROM sys.tables WHERE name = 'ml_evaluation_audit')
    CREATE INDEX idx_ml_eval_anomaly ON dbo.ml_evaluation_audit(anomaly_detected, evaluation_timestamp DESC);

-- Success message
PRINT '✅ Gemini Intelligence System tables created successfully!'
PRINT 'Created tables:'
PRINT '  - feedback_labels'
PRINT '  - fine_tuning_samples'
PRINT '  - learning_metrics'
PRINT '  - ml_evaluation_audit'
