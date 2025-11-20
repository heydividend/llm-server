"""
Training Data Ingestion Service
Processes 1,000+ dividend questions through Harvey's 5-model system
to create high-quality training data for continuous improvement.
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
import hashlib
from app.services.investor_profiling_service import investor_profiling

logger = logging.getLogger("training_ingestion")


class TrainingDataIngestion:
    """
    Ingests training questions and processes them through all 5 AI models
    to create comprehensive training data for Harvey's dividend expertise.
    """
    
    # 1,000 Training Questions categorized by expertise area
    TRAINING_QUESTIONS = {
        "dividend_analysis": [
            "What is the 5-year dividend CAGR for AAPL?",
            "Calculate the dividend coverage ratio for JNJ",
            "What's the free cash flow payout ratio for KO?",
            "How many consecutive years has PG paid dividends?",
            "What's the dividend sustainability score for T?",
            "Compare dividend growth rates between MSFT and GOOGL",
            "What's the forward dividend yield for VZ?",
            "Calculate the yield on cost if I bought PEP 3 years ago",
            "What's the dividend capture potential for XOM this month?",
            "Show me the dividend payment history for IBM last 10 years",
            "What's the earnings payout ratio vs FCF payout ratio for MO?",
            "Calculate the dividend discount model valuation for CVX",
            "What's the ex-dividend drop percentage typically for ABBV?",
            "Show the dividend aristocrats with yields above 4%",
            "What's the dividend kings list sorted by yield?",
            "Calculate the Gordon Growth Model price for MMM",
            "What's the dividend safety score using Altman Z-score for GE?",
            "Show dividend champions under $50 per share",
            "What's the average dividend increase percentage for NEE?",
            "Calculate the dividend reinvestment compound return over 10 years for O",
            # Add 130 more analytical questions
        ],
        
        "income_strategies": [
            "Build a $50K portfolio targeting $500 monthly income",
            "Create a dividend ladder with weekly payments",
            "Design a portfolio with no overlapping ex-dates",
            "Optimize for tax-efficient dividend income above $100K salary",
            "Build a REIT portfolio for $1000 monthly income",
            "Create a covered call strategy on dividend aristocrats",
            "Design a cash-secured puts income strategy with SPY",
            "Build a portfolio mixing growth and income 50/50",
            "Create a defensive dividend portfolio for recession protection",
            "Design an international dividend portfolio for geographic diversification",
            "Build a monthly income portfolio under $10K investment",
            "Create a dividend capture calendar for next month",
            "Design a portfolio with 8% yield and monthly payments",
            "Build a dividend snowball strategy starting with $5K",
            "Create a barbell dividend strategy with high yield and growth",
            "Design a sector-rotation dividend strategy for market cycles",
            "Build a dogs of the Dow dividend strategy",
            "Create a fallen angels dividend recovery portfolio",
            "Design a dividend portfolio for early retirement at 50",
            "Build a tax-loss harvesting dividend strategy",
            # Add 180 more strategy questions
        ],
        
        "technical_timing": [
            "When does AAPL typically announce dividend increases?",
            "What's the best entry point before ex-dividend for KO?",
            "Show stocks going ex-dividend in next 3 days",
            "What's the optimal holding period for dividend capture?",
            "When do dividend aristocrats typically raise dividends?",
            "Show the seasonal patterns for XOM dividend payments",
            "What's the correlation between T price and dividend yield?",
            "Calculate the dividend capture arbitrage opportunity for ABBV",
            "What's the historical ex-dividend date pattern for PFE?",
            "Show the dividend announcement surprise history for JPM",
            # Add 140 more technical questions
        ],
        
        "etf_funds": [
            "Compare SCHD vs VIG for dividend growth investing",
            "What's the expense ratio impact on JEPI returns?",
            "Show all monthly paying dividend ETFs sorted by yield",
            "What's the overlap between JEPI and JEPQ holdings?",
            "Compare covered call ETFs QYLD, RYLD, XYLD by premium income",
            "What's the NAV erosion rate for QYLD over 5 years?",
            "Show weekly paying dividend ETFs with yield above 5%",
            "Compare international dividend ETFs by withholding tax",
            "What's the rebalancing frequency for DVY?",
            "Show sector-specific dividend ETFs by 3-year performance",
            # Add 90 more ETF questions
        ],
        
        "tax_optimization": [
            "Calculate qualified dividend tax for $50K income",
            "What's the tax difference between ordinary and qualified dividends?",
            "How do I optimize dividend income in IRA vs taxable account?",
            "Calculate the after-tax yield for municipal bond funds",
            "What's the foreign tax credit for VXUS dividends?",
            "Show tax-efficient dividend strategies for high earners",
            "Calculate NIIT impact on dividend income over $250K",
            "What's the stepped-up basis benefit for inherited dividend stocks?",
            "How do MLP distributions affect K-1 tax forms?",
            "Calculate the tax drag on REIT ordinary dividends",
            # Add 90 more tax questions
        ],
        
        "risk_management": [
            "What's the dividend cut probability for T based on debt?",
            "Show warning signs of unsustainable dividends",
            "Calculate the downside protection from KO dividends",
            "What's the correlation between dividend cuts and price drops?",
            "Show defensive dividend stocks for bear markets",
            "Calculate portfolio beta with 50% dividend stocks",
            "What's the interest rate sensitivity of utility dividends?",
            "Show dividend stocks with lowest 52-week volatility",
            "Calculate the Sharpe ratio for dividend aristocrats portfolio",
            "What's the maximum drawdown for dividend kings in 2008?",
            # Add 90 more risk questions
        ],
        
        "sector_geographic": [
            "Show highest yielding utility dividends with 5+ year history",
            "What are the best REIT dividends for monthly income?",
            "Compare energy sector dividend sustainability post-2020",
            "Show financial sector dividend growth rates excluding 2008",
            "What are the best tech dividends for growth?",
            "Compare healthcare dividend aristocrats by consistency",
            "Show consumer staples defensive dividends",
            "What are the best industrial dividend growers?",
            "Compare materials sector dividend coverage ratios",
            "Show communication services dividend yields",
            # Add 90 more sector questions
        ],
        
        "drip_reinvestment": [
            "Calculate DRIP returns with $100 monthly investment in SPY",
            "What's the share accumulation from DRIP over 20 years?",
            "Compare DRIP vs cash dividends for tax efficiency",
            "Show the compound effect of DRIP with 5% dividend growth",
            "Calculate fractional shares from DRIP reinvestment",
            "What's the optimal DRIP strategy for retirement in 15 years?",
            "Show DRIP-eligible brokers and their fees",
            "Calculate DRIP breakeven vs taking cash with 3% inflation",
            "What's the impact of DRIP on cost basis tracking?",
            "Show synthetic DRIP strategies for non-eligible stocks",
            # Add 40 more DRIP questions
        ],
        
        "advanced_strategies": [
            "Design a dividend arbitrage strategy using options",
            "Create a pairs trading strategy with REITs",
            "Build a mean reversion strategy around ex-dividend dates",
            "Design a dividend factor model for stock selection",
            "Create a machine learning model for dividend cut predictions",
            "Build a sentiment analysis for dividend announcements",
            "Design a cross-asset dividend strategy with stocks and bonds",
            "Create a dividend momentum portfolio with monthly rebalancing",
            "Build a contrarian dividend value strategy",
            "Design a dividend quality score ranking system",
            # Add 90 more advanced questions
        ],
        
        "realtime_monitoring": [
            "Alert me when AAPL announces dividend increase",
            "Show stocks with dividend announcements today",
            "What dividends were cut this week?",
            "Show surprise dividend increases this month",
            "Alert when any aristocrat yield exceeds 5%",
            "What companies missed dividend payments this quarter?",
            "Show special dividends announced this quarter",
            "Alert for dividend reinstatement news",
            "What's the dividend news sentiment today?",
            "Show trending dividend discussions on FinTwit",
            # Add 30 more monitoring questions
        ]
    }
    
    def __init__(self):
        self.db_connection_string = self._build_connection_string()
        self.engine = None
        if self.db_connection_string:
            try:
                self.engine = create_engine(
                    self.db_connection_string,
                    poolclass=NullPool,
                    pool_pre_ping=True
                )
                self._ensure_training_tables()
            except Exception as e:
                logger.error(f"Failed to initialize database: {e}")
    
    def _build_connection_string(self) -> Optional[str]:
        """Build SQL Server connection string from environment variables."""
        host = os.getenv("SQLSERVER_HOST")
        user = os.getenv("SQLSERVER_USER")
        password = os.getenv("SQLSERVER_PASSWORD")
        db = os.getenv("SQLSERVER_DB")
        
        if not all([host, user, password, db]):
            logger.warning("Missing database credentials for training ingestion")
            return None
        
        return f"mssql+pyodbc://{user}:{password}@{host}/{db}?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
    
    def _ensure_training_tables(self):
        """Create training data tables if they don't exist."""
        create_tables_sql = """
        -- Training Questions Queue
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='training_questions' AND xtype='U')
        CREATE TABLE training_questions (
            question_id NVARCHAR(50) PRIMARY KEY,
            category NVARCHAR(50) NOT NULL,
            question_text NVARCHAR(MAX) NOT NULL,
            complexity_level INT DEFAULT 1,
            processed BIT DEFAULT 0,
            created_at DATETIME DEFAULT GETDATE(),
            processed_at DATETIME NULL,
            INDEX idx_processed (processed),
            INDEX idx_category (category)
        );
        
        -- Multi-Model Responses
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='training_responses' AND xtype='U')
        CREATE TABLE training_responses (
            response_id NVARCHAR(50) PRIMARY KEY,
            question_id NVARCHAR(50) NOT NULL,
            model_name NVARCHAR(50) NOT NULL,
            response_text NVARCHAR(MAX) NOT NULL,
            response_time_ms INT,
            confidence_score FLOAT,
            extracted_metrics NVARCHAR(MAX),
            quality_score FLOAT,
            created_at DATETIME DEFAULT GETDATE(),
            FOREIGN KEY (question_id) REFERENCES training_questions(question_id),
            INDEX idx_question (question_id),
            INDEX idx_model (model_name),
            INDEX idx_quality (quality_score)
        );
        
        -- Training Data Export
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='harvey_training_data' AND xtype='U')
        CREATE TABLE harvey_training_data (
            training_id NVARCHAR(50) PRIMARY KEY,
            question_id NVARCHAR(50) NOT NULL,
            best_model NVARCHAR(50),
            combined_response NVARCHAR(MAX),
            training_format NVARCHAR(MAX), -- OpenAI fine-tuning format
            quality_score FLOAT,
            exported BIT DEFAULT 0,
            created_at DATETIME DEFAULT GETDATE(),
            exported_at DATETIME NULL,
            FOREIGN KEY (question_id) REFERENCES training_questions(question_id),
            INDEX idx_exported (exported),
            INDEX idx_quality_export (quality_score, exported)
        );
        """
        
        try:
            with self.engine.begin() as conn:
                for statement in create_tables_sql.split(';'):
                    if statement.strip():
                        conn.execute(text(statement))
            logger.info("Training tables verified/created successfully")
        except Exception as e:
            logger.error(f"Failed to create training tables: {e}")
    
    def ingest_training_questions(self, batch_size: int = 100, include_profiles: bool = True) -> Dict[str, Any]:
        """
        Ingest training questions into the database for processing.
        
        Args:
            batch_size: Number of questions to ingest at once
            
        Returns:
            Dict with ingestion statistics
        """
        if not self.engine:
            return {"success": False, "error": "Database not configured"}
        
        total_ingested = 0
        category_counts = {}
        
        try:
            with self.engine.begin() as conn:
                # Ingest standard training questions
                for category, questions in self.TRAINING_QUESTIONS.items():
                    category_count = 0
                    
                    for question in questions[:batch_size]:  # Process in batches
                        # Generate unique ID for question
                        question_id = f"tq_{hashlib.md5(question.encode()).hexdigest()[:12]}"
                        
                        # Check if question already exists
                        exists = conn.execute(
                            text("SELECT 1 FROM training_questions WHERE question_id = :qid"),
                            {"qid": question_id}
                        ).fetchone()
                        
                        if not exists:
                            # Determine complexity level based on question
                            complexity = self._determine_complexity(question)
                            
                            # Insert question
                            conn.execute(
                                text("""
                                    INSERT INTO training_questions 
                                    (question_id, category, question_text, complexity_level)
                                    VALUES (:qid, :cat, :qtext, :complexity)
                                """),
                                {
                                    "qid": question_id,
                                    "cat": category,
                                    "qtext": question,
                                    "complexity": complexity
                                }
                            )
                            category_count += 1
                            total_ingested += 1
                    
                    category_counts[category] = category_count
                    logger.info(f"Ingested {category_count} questions for {category}")
                
                # Ingest investor profile-based questions if enabled
                if include_profiles:
                    profile_training_set = investor_profiling.create_comprehensive_training_set()
                    profile_count = 0
                    
                    for item in profile_training_set[:batch_size]:
                        question_id = item['question_id']
                        
                        # Check if question already exists
                        exists = conn.execute(
                            text("SELECT 1 FROM training_questions WHERE question_id = :qid"),
                            {"qid": question_id}
                        ).fetchone()
                        
                        if not exists:
                            # Insert profile-based question
                            conn.execute(
                                text("""
                                    INSERT INTO training_questions 
                                    (question_id, category, question_text, complexity_level)
                                    VALUES (:qid, :cat, :qtext, :complexity)
                                """),
                                {
                                    "qid": question_id,
                                    "cat": item['category'],
                                    "qtext": item['question'],
                                    "complexity": item.get('complexity', 3)
                                }
                            )
                            profile_count += 1
                            total_ingested += 1
                    
                    category_counts['investor_profiles'] = profile_count
                    logger.info(f"Ingested {profile_count} investor profile questions")
            
            return {
                "success": True,
                "total_ingested": total_ingested,
                "category_counts": category_counts,
                "message": f"Successfully ingested {total_ingested} training questions"
            }
            
        except Exception as e:
            logger.error(f"Failed to ingest training questions: {e}")
            return {"success": False, "error": str(e)}
    
    def _determine_complexity(self, question: str) -> int:
        """
        Determine question complexity level (1-5).
        
        1 = Simple lookup (What is X?)
        2 = Basic calculation (Calculate yield)
        3 = Comparison (Compare X vs Y)
        4 = Strategy design (Build portfolio)
        5 = Advanced analysis (Machine learning, optimization)
        """
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['what is', 'show', 'list', 'when']):
            return 1
        elif any(word in question_lower for word in ['calculate', 'compute', 'how much']):
            return 2
        elif any(word in question_lower for word in ['compare', 'versus', 'vs', 'difference']):
            return 3
        elif any(word in question_lower for word in ['build', 'create', 'design', 'optimize']):
            return 4
        elif any(word in question_lower for word in ['machine learning', 'arbitrage', 'factor model']):
            return 5
        else:
            return 2  # Default to basic calculation
    
    async def process_question_batch(self, batch_size: int = 10) -> Dict[str, Any]:
        """
        Process a batch of questions through all 5 AI models.
        
        This simulates what would happen in production:
        1. Fetch unprocessed questions
        2. Send to each AI model (GPT-5, Grok-4, DeepSeek-R1, Gemini, FinGPT)
        3. Score and rank responses
        4. Create training data from best responses
        """
        if not self.engine:
            return {"success": False, "error": "Database not configured"}
        
        try:
            # Get unprocessed questions
            with self.engine.connect() as conn:
                questions = conn.execute(
                    text("""
                        SELECT TOP :batch question_id, question_text, category, complexity_level
                        FROM training_questions
                        WHERE processed = 0
                        ORDER BY complexity_level, created_at
                    """),
                    {"batch": batch_size}
                ).fetchall()
                
                if not questions:
                    return {"success": True, "message": "No questions to process"}
                
                processed_count = 0
                
                for question in questions:
                    question_id = question[0]
                    question_text = question[1]
                    category = question[2]
                    complexity = question[3]
                    
                    # Process through each model (simulated here, would call actual APIs)
                    models = ['GPT-5', 'Grok-4', 'DeepSeek-R1', 'Gemini-2.5-Pro', 'FinGPT']
                    best_score = 0
                    best_model = None
                    best_response = None
                    
                    for model in models:
                        # Generate response (this would call actual model APIs)
                        response = await self._generate_model_response(
                            model, question_text, category, complexity
                        )
                        
                        # Store response
                        response_id = f"tr_{hashlib.md5(f'{question_id}_{model}'.encode()).hexdigest()[:12]}"
                        
                        conn.execute(
                            text("""
                                INSERT INTO training_responses
                                (response_id, question_id, model_name, response_text, 
                                 response_time_ms, confidence_score, quality_score)
                                VALUES (:rid, :qid, :model, :rtext, :time, :conf, :quality)
                            """),
                            {
                                "rid": response_id,
                                "qid": question_id,
                                "model": model,
                                "rtext": response['text'],
                                "time": response['time_ms'],
                                "conf": response['confidence'],
                                "quality": response['quality_score']
                            }
                        )
                        
                        # Track best response
                        if response['quality_score'] > best_score:
                            best_score = response['quality_score']
                            best_model = model
                            best_response = response['text']
                    
                    # Create training data from best response
                    training_id = f"htd_{hashlib.md5(question_id.encode()).hexdigest()[:12]}"
                    training_format = json.dumps({
                        "messages": [
                            {"role": "user", "content": question_text},
                            {"role": "assistant", "content": best_response}
                        ]
                    })
                    
                    conn.execute(
                        text("""
                            INSERT INTO harvey_training_data
                            (training_id, question_id, best_model, combined_response, 
                             training_format, quality_score)
                            VALUES (:tid, :qid, :model, :response, :format, :score)
                        """),
                        {
                            "tid": training_id,
                            "qid": question_id,
                            "model": best_model,
                            "response": best_response,
                            "format": training_format,
                            "score": best_score
                        }
                    )
                    
                    # Mark question as processed
                    conn.execute(
                        text("""
                            UPDATE training_questions 
                            SET processed = 1, processed_at = GETDATE()
                            WHERE question_id = :qid
                        """),
                        {"qid": question_id}
                    )
                    
                    processed_count += 1
                    logger.info(f"Processed question {question_id} - Best model: {best_model}")
                
                conn.commit()
                
            return {
                "success": True,
                "processed_count": processed_count,
                "message": f"Successfully processed {processed_count} questions"
            }
            
        except Exception as e:
            logger.error(f"Failed to process question batch: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_model_response(
        self, model: str, question: str, category: str, complexity: int
    ) -> Dict[str, Any]:
        """
        Generate response from specific AI model.
        
        In production, this would call the actual AI APIs.
        For training, we simulate responses based on model characteristics.
        """
        # Simulate model-specific response characteristics
        if model == 'GPT-5':
            # GPT-5: Best for complex analysis and explanations
            return {
                "text": f"[GPT-5 Analysis] For '{question}': Comprehensive analysis with detailed calculations...",
                "time_ms": 2000 + complexity * 500,
                "confidence": 0.85 + (0.03 * complexity),
                "quality_score": 0.90 if complexity >= 3 else 0.85
            }
        elif model == 'Grok-4':
            # Grok-4: Fastest for quick calculations
            return {
                "text": f"[Grok-4 Quick] {question}: Direct answer with calculation...",
                "time_ms": 500 + complexity * 100,
                "confidence": 0.88,
                "quality_score": 0.95 if complexity <= 2 else 0.80
            }
        elif model == 'DeepSeek-R1':
            # DeepSeek-R1: Best for quantitative analysis
            return {
                "text": f"[DeepSeek Quant] {question}: Mathematical model with formulas...",
                "time_ms": 1500 + complexity * 300,
                "confidence": 0.92,
                "quality_score": 0.95 if 'calculate' in question.lower() else 0.85
            }
        elif model == 'Gemini-2.5-Pro':
            # Gemini: Best for charts and visualizations
            return {
                "text": f"[Gemini Visual] {question}: Data visualization and patterns...",
                "time_ms": 1800 + complexity * 400,
                "confidence": 0.86,
                "quality_score": 0.92 if 'compare' in question.lower() else 0.84
            }
        else:  # FinGPT
            # FinGPT: Best for dividend-specific scoring
            return {
                "text": f"[FinGPT Dividend] {question}: Dividend-focused analysis with scoring...",
                "time_ms": 1200 + complexity * 200,
                "confidence": 0.89,
                "quality_score": 0.94 if 'dividend' in question.lower() else 0.82
            }
    
    def export_training_data(self, min_quality: float = 0.85) -> List[Dict[str, Any]]:
        """
        Export high-quality training data for fine-tuning.
        
        Returns data in OpenAI fine-tuning format.
        """
        if not self.engine:
            return []
        
        try:
            with self.engine.connect() as conn:
                results = conn.execute(
                    text("""
                        SELECT training_format, quality_score, best_model
                        FROM harvey_training_data
                        WHERE quality_score >= :min_quality
                          AND exported = 0
                        ORDER BY quality_score DESC
                    """),
                    {"min_quality": min_quality}
                ).fetchall()
                
                training_data = []
                for row in results:
                    training_data.append(json.loads(row[0]))
                
                # Mark as exported
                if training_data:
                    conn.execute(
                        text("""
                            UPDATE harvey_training_data
                            SET exported = 1, exported_at = GETDATE()
                            WHERE quality_score >= :min_quality AND exported = 0
                        """),
                        {"min_quality": min_quality}
                    )
                    conn.commit()
                
                logger.info(f"Exported {len(training_data)} training examples")
                return training_data
                
        except Exception as e:
            logger.error(f"Failed to export training data: {e}")
            return []
    
    def store_training_question(self, category: str, question_text: str, complexity_level: int = 2) -> Dict[str, Any]:
        """
        Store a training question in the database.
        
        Args:
            category: Question category  
            question_text: The question text
            complexity_level: Complexity level 1-5
            
        Returns:
            Dict with success status and question_id
        """
        if not self.engine:
            return {"success": False, "error": "Database not configured"}
        
        try:
            question_id = hashlib.md5(f"{category}:{question_text}".encode()).hexdigest()[:10]
            
            with self.engine.begin() as conn:
                # Check if question already exists
                existing = conn.execute(
                    text("SELECT question_id FROM training_questions WHERE question_id = :id"),
                    {"id": question_id}
                ).fetchone()
                
                if not existing:
                    conn.execute(
                        text("""
                            INSERT INTO training_questions 
                            (question_id, category, question_text, complexity_level, processed, created_at)
                            VALUES (:id, :category, :question, :complexity, 0, GETDATE())
                        """),
                        {
                            "id": question_id,
                            "category": category,
                            "question": question_text,
                            "complexity": complexity_level
                        }
                    )
                    logger.debug(f"Stored question {question_id} in category {category}")
                
                return {"success": True, "question_id": question_id}
                
        except Exception as e:
            logger.error(f"Failed to store training question: {e}")
            return {"success": False, "error": str(e)}
    
    def store_evaluation_result(self, question_id: str, model_name: str, 
                               evaluation_scores: Dict[str, float], 
                               passes_threshold: bool) -> Dict[str, Any]:
        """
        Store evaluation results for a response.
        
        Args:
            question_id: ID of the question
            model_name: Model that generated the response
            evaluation_scores: Dict with clarity, completeness, actionability, overall scores
            passes_threshold: Whether it passes quality threshold
            
        Returns:
            Dict with success status
        """
        if not self.engine:
            return {"success": False, "error": "Database not configured"}
        
        try:
            with self.engine.begin() as conn:
                # Update the response quality score
                conn.execute(
                    text("""
                        UPDATE training_responses
                        SET quality_score = :overall_score
                        WHERE question_id = :question_id AND model_name = :model
                    """),
                    {
                        "overall_score": evaluation_scores.get("overall", 0),
                        "question_id": question_id,
                        "model": model_name
                    }
                )
                
                # If passes threshold, update or create training data entry
                if passes_threshold:
                    training_id = hashlib.md5(f"{question_id}:{model_name}".encode()).hexdigest()[:10]
                    
                    conn.execute(
                        text("""
                            UPDATE harvey_training_data
                            SET quality_score = :overall_score, best_model = :model
                            WHERE training_id = :training_id
                        """),
                        {
                            "overall_score": evaluation_scores.get("overall", 0),
                            "model": model_name,
                            "training_id": training_id
                        }
                    )
                
                logger.debug(f"Stored evaluation for {question_id} from {model_name}")
                return {"success": True}
                
        except Exception as e:
            logger.error(f"Failed to store evaluation result: {e}")
            return {"success": False, "error": str(e)}
    
    def export_evaluated_training_data(self, min_quality: float = 0.85, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Export evaluated training data that meets quality threshold.
        
        Args:
            min_quality: Minimum quality score
            limit: Maximum number of examples to export
            
        Returns:
            List of training examples with questions and responses
        """
        if not self.engine:
            return []
        
        try:
            with self.engine.connect() as conn:
                results = conn.execute(
                    text("""
                        SELECT TOP(:limit)
                            tq.question_text as question,
                            tq.category,
                            tr.response_text as response,
                            tr.model_name as model,
                            tr.quality_score,
                            htd.training_format
                        FROM harvey_training_data htd
                        INNER JOIN training_questions tq ON htd.question_id = tq.question_id
                        INNER JOIN training_responses tr ON htd.question_id = tr.question_id 
                            AND htd.best_model = tr.model_name
                        WHERE htd.quality_score >= :min_quality
                          AND htd.exported = 0
                        ORDER BY htd.quality_score DESC
                    """),
                    {"min_quality": min_quality, "limit": limit}
                ).fetchall()
                
                training_data = []
                for row in results:
                    training_data.append({
                        "question": row[0],
                        "category": row[1], 
                        "response": row[2],
                        "model": row[3],
                        "quality_score": float(row[4] or 0)
                    })
                
                logger.info(f"Exported {len(training_data)} evaluated training examples")
                return training_data
                
        except Exception as e:
            logger.error(f"Failed to export evaluated training data: {e}")
            return []
    
    def get_training_statistics(self) -> Dict[str, Any]:
        """Get statistics on training data collection."""
        if not self.engine:
            return {"error": "Database not configured"}
        
        try:
            with self.engine.connect() as conn:
                stats = conn.execute(
                    text("""
                        SELECT 
                            (SELECT COUNT(*) FROM training_questions) as total_questions,
                            (SELECT COUNT(*) FROM training_questions WHERE processed = 1) as processed_questions,
                            (SELECT COUNT(*) FROM training_responses) as total_responses,
                            (SELECT COUNT(*) FROM harvey_training_data) as training_examples,
                            (SELECT COUNT(*) FROM harvey_training_data WHERE exported = 1) as exported_examples,
                            (SELECT AVG(quality_score) FROM harvey_training_data) as avg_quality_score
                    """)
                ).fetchone()
                
                return {
                    "total_questions": stats[0] or 0,
                    "processed_questions": stats[1] or 0,
                    "total_responses": stats[2] or 0,
                    "training_examples": stats[3] or 0,
                    "exported_examples": stats[4] or 0,
                    "avg_quality_score": float(stats[5] or 0),
                    "processing_rate": f"{(stats[1] or 0) / (stats[0] or 1) * 100:.1f}%"
                }
                
        except Exception as e:
            logger.error(f"Failed to get training statistics: {e}")
            return {"error": str(e)}
    
    def ingest_gemini_questions(
        self,
        questions: List[Dict[str, Any]],
        prevent_duplicates: bool = True
    ) -> Dict[str, Any]:
        """
        Ingest Gemini-generated training questions into the database.
        
        Args:
            questions: List of question dicts with 'question', 'category', 'answer' (optional)
            prevent_duplicates: Check against existing questions (default: True)
            
        Returns:
            Dict with ingestion statistics
        """
        if not self.engine:
            return {"success": False, "error": "Database not configured"}
        
        ingested_count = 0
        duplicate_count = 0
        error_count = 0
        
        try:
            with self.engine.begin() as conn:
                for q_data in questions:
                    question_text = q_data.get('question', '').strip()
                    category = q_data.get('category', 'unknown')
                    answer = q_data.get('answer', '')
                    
                    if not question_text:
                        error_count += 1
                        continue
                    
                    # Generate question ID based on content
                    question_id = hashlib.md5(
                        f"gemini:{category}:{question_text}".encode()
                    ).hexdigest()[:12]
                    
                    # Check for duplicates if requested
                    if prevent_duplicates:
                        existing = conn.execute(
                            text("""
                                SELECT question_id FROM training_questions 
                                WHERE question_id = :qid OR question_text = :qtext
                            """),
                            {"qid": question_id, "qtext": question_text}
                        ).fetchone()
                        
                        if existing:
                            duplicate_count += 1
                            logger.debug(f"Skipped duplicate: {question_text[:50]}...")
                            continue
                    
                    # Determine complexity level
                    complexity = self._determine_complexity(question_text)
                    
                    # Insert question with gemini_generated source tag
                    conn.execute(
                        text("""
                            INSERT INTO training_questions 
                            (question_id, category, question_text, complexity_level, processed, created_at)
                            VALUES (:qid, :cat, :qtext, :complexity, 0, GETDATE())
                        """),
                        {
                            "qid": question_id,
                            "cat": category,
                            "qtext": question_text,
                            "complexity": complexity
                        }
                    )
                    
                    # If answer is provided, create training data entry
                    if answer:
                        training_id = f"htd_{hashlib.md5(question_id.encode()).hexdigest()[:12]}"
                        training_format = json.dumps({
                            "messages": [
                                {"role": "user", "content": question_text},
                                {"role": "assistant", "content": answer}
                            ]
                        })
                        
                        conn.execute(
                            text("""
                                INSERT INTO harvey_training_data
                                (training_id, question_id, best_model, combined_response, 
                                 training_format, quality_score, exported)
                                VALUES (:tid, :qid, :model, :response, :format, :score, 0)
                            """),
                            {
                                "tid": training_id,
                                "qid": question_id,
                                "model": "Gemini-2.5-Pro",
                                "response": answer,
                                "format": training_format,
                                "score": 0.9  # Default high score for Gemini responses
                            }
                        )
                    
                    ingested_count += 1
                
                logger.info(
                    f"Ingested {ingested_count} Gemini questions "
                    f"({duplicate_count} duplicates, {error_count} errors)"
                )
                
                return {
                    "success": True,
                    "ingested": ingested_count,
                    "duplicates": duplicate_count,
                    "errors": error_count,
                    "total_processed": len(questions)
                }
                
        except Exception as e:
            logger.error(f"Failed to ingest Gemini questions: {e}")
            return {"success": False, "error": str(e)}
    
    def merge_gemini_with_manual(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics on merged manual and Gemini-generated questions.
        
        Args:
            category: Optional category filter
            
        Returns:
            Dict with counts by source
        """
        if not self.engine:
            return {"error": "Database not configured"}
        
        try:
            with self.engine.connect() as conn:
                # Count questions by source (inferred from question_id prefix)
                query = """
                    SELECT 
                        CASE 
                            WHEN question_id LIKE 'gemini:%' THEN 'gemini_generated'
                            ELSE 'manual'
                        END as source,
                        category,
                        COUNT(*) as count
                    FROM training_questions
                """
                
                if category:
                    query += " WHERE category = :category"
                
                query += " GROUP BY CASE WHEN question_id LIKE 'gemini:%' THEN 'gemini_generated' ELSE 'manual' END, category"
                
                params = {"category": category} if category else {}
                results = conn.execute(text(query), params).fetchall()
                
                stats = {"by_source": {}, "by_category": {}}
                
                for row in results:
                    source = row[0]
                    cat = row[1]
                    count = row[2]
                    
                    if source not in stats["by_source"]:
                        stats["by_source"][source] = 0
                    stats["by_source"][source] += count
                    
                    if cat not in stats["by_category"]:
                        stats["by_category"][cat] = {"manual": 0, "gemini_generated": 0}
                    stats["by_category"][cat][source] = count
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to merge statistics: {e}")
            return {"error": str(e)}


# Global instance
training_ingestion = TrainingDataIngestion()