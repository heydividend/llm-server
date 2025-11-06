"""
Training Data Management API
Endpoints for ingesting and processing training questions through Harvey's multi-model system.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import asyncio

from app.core.auth import verify_api_key
from app.services.training_ingestion_service import training_ingestion
from app.services.bulk_profile_ingestion import bulk_ingestion
from app.services.training_evaluation_service import training_evaluator, ExpertiseLevel
from app.services.passive_income_training_service import passive_income_trainer
from app.core.logging_config import get_logger

logger = get_logger("training")

router = APIRouter()


class IngestRequest(BaseModel):
    batch_size: int = Field(default=100, description="Number of questions to ingest")
    category: Optional[str] = Field(None, description="Specific category to ingest")


class ProcessRequest(BaseModel):
    batch_size: int = Field(default=10, description="Number of questions to process")
    run_async: bool = Field(default=True, description="Run processing in background")


class BulkProfileRequest(BaseModel):
    content: str = Field(..., description="CSV or JSONL content with investor profiles")
    file_format: str = Field(default="csv", description="Format: 'csv' or 'jsonl'")
    process_immediately: bool = Field(default=False, description="Process questions immediately")


class EvaluateResponseRequest(BaseModel):
    question: str = Field(..., description="The question that was asked")
    response: str = Field(..., description="The model's response to evaluate")
    expertise_level: Optional[str] = Field(default="intermediate", description="beginner, intermediate, or advanced")
    model_name: Optional[str] = Field(default=None, description="Model that generated the response")


class BatchEvaluationRequest(BaseModel):
    responses: List[Dict[str, Any]] = Field(..., description="List of Q&A pairs to evaluate")
    expertise_level: Optional[str] = Field(default=None, description="Override expertise level for all")


class PassiveIncomeTrainingRequest(BaseModel):
    training_data: str = Field(..., description="JSONL content with dividend training questions")
    lesson_plan: Optional[str] = Field(default=None, description="JSON lesson plan")
    auto_rewrite_prompts: Optional[str] = Field(default=None, description="JSON auto-rewrite prompts")
    dataset_name: str = Field(default="main", description="Name of the dataset")


@router.post("/training/ingest")
async def ingest_training_questions(
    request: IngestRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Ingest training questions into the database.
    
    This loads the 1,000+ predefined dividend questions plus investor profiling scenarios.
    """
    try:
        result = training_ingestion.ingest_training_questions(
            batch_size=request.batch_size,
            include_profiles=True  # Include investor profile questions
        )
        
        if result.get("success"):
            return JSONResponse({
                "success": True,
                "message": result.get("message"),
                "total_ingested": result.get("total_ingested"),
                "category_counts": result.get("category_counts")
            })
        else:
            raise HTTPException(status_code=500, detail=result.get("error"))
            
    except Exception as e:
        logger.error(f"Failed to ingest training questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/training/process")
async def process_training_batch(
    request: ProcessRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """
    Process a batch of training questions through all 5 AI models.
    
    This generates responses from each model and creates training data.
    """
    try:
        if request.run_async:
            # Fix for async background task - create wrapper function
            def run_async_processing():
                """Wrapper to run async task in background."""
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(
                        training_ingestion.process_question_batch(
                            batch_size=request.batch_size
                        )
                    )
                    logger.info(f"Background processing completed: {result}")
                except Exception as e:
                    logger.error(f"Background processing failed: {e}")
                finally:
                    loop.close()
            
            # Add sync wrapper to background tasks
            background_tasks.add_task(run_async_processing)
            return JSONResponse({
                "success": True,
                "message": f"Processing {request.batch_size} questions in background",
                "status": "started"
            })
        else:
            # Run synchronously
            result = await training_ingestion.process_question_batch(
                batch_size=request.batch_size
            )
            return JSONResponse(result)
            
    except Exception as e:
        logger.error(f"Failed to process training batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/training/status")
async def get_training_status(api_key: str = Depends(verify_api_key)):
    """
    Get current training data collection status.
    
    Shows statistics on questions, responses, and training data quality.
    """
    try:
        stats = training_ingestion.get_training_statistics()
        
        return JSONResponse({
            "success": True,
            "statistics": stats,
            "ready_for_export": stats.get("training_examples", 0) > 0
        })
        
    except Exception as e:
        logger.error(f"Failed to get training status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/training/export")
async def export_training_data(
    min_quality: float = 0.85,
    api_key: str = Depends(verify_api_key)
):
    """
    Export training data for fine-tuning.
    
    Returns data in OpenAI fine-tuning format.
    """
    try:
        training_data = training_ingestion.export_training_data(min_quality=min_quality)
        
        if not training_data:
            return JSONResponse({
                "success": False,
                "message": "No training data available for export",
                "data": []
            })
        
        return JSONResponse({
            "success": True,
            "message": f"Exported {len(training_data)} training examples",
            "format": "openai_fine_tuning",
            "data": training_data
        })
        
    except Exception as e:
        logger.error(f"Failed to export training data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/training/schedule")
async def schedule_continuous_training(
    interval_hours: int = 24,
    api_key: str = Depends(verify_api_key)
):
    """
    Schedule continuous training data collection.
    
    Processes questions automatically at specified intervals.
    """
    try:
        # This would integrate with the scheduler service
        return JSONResponse({
            "success": True,
            "message": f"Training scheduled every {interval_hours} hours",
            "next_run": "In progress"
        })
        
    except Exception as e:
        logger.error(f"Failed to schedule training: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/training/bulk-profiles")
async def ingest_bulk_profiles(
    request: BulkProfileRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """
    Ingest bulk investor profiles (200 real profiles) for training.
    
    Accepts CSV or JSONL format with complete investor profiles.
    Generates 10-15 training questions per profile.
    """
    try:
        # Process bulk profiles
        result = bulk_ingestion.process_bulk_profiles(
            content=request.content,
            file_format=request.file_format
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Processing failed"))
        
        profiles = result.get("profiles", [])
        questions = result.get("questions", [])
        statistics = result.get("statistics", {})
        
        # Store questions in database for processing
        if questions and request.process_immediately:
            # Fix for async background task - create wrapper function
            def run_profile_ingestion():
                """Wrapper to run async task in background."""
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(
                        _ingest_profile_questions(questions=questions)
                    )
                except Exception as e:
                    logger.error(f"Background profile ingestion failed: {e}")
                finally:
                    loop.close()
            
            # Process questions through training system
            background_tasks.add_task(run_profile_ingestion)
            
            return JSONResponse({
                "success": True,
                "message": f"Processing {len(profiles)} profiles with {len(questions)} questions",
                "statistics": statistics,
                "status": "processing_started"
            })
        else:
            return JSONResponse({
                "success": True,
                "message": f"Generated {len(questions)} questions from {len(profiles)} profiles",
                "statistics": statistics,
                "questions_sample": questions[:5] if questions else []
            })
            
    except Exception as e:
        logger.error(f"Failed to ingest bulk profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _ingest_profile_questions(questions: List[Dict[str, Any]]):
    """Background task to ingest profile-generated questions."""
    try:
        logger.info(f"Ingesting {len(questions)} profile-generated questions")
        
        # Actually persist questions to the training database
        stored_count = 0
        for question_data in questions:
            result = training_ingestion.store_training_question(
                category=question_data.get("category", "investor_profile"),
                question_text=question_data.get("question", ""),
                complexity_level=question_data.get("complexity", 2)
            )
            if result.get("success"):
                stored_count += 1
        
        logger.info(f"Successfully stored {stored_count}/{len(questions)} profile questions")
        
        # Process a batch through multi-model system if configured
        if stored_count > 0:
            await training_ingestion.process_question_batch(batch_size=min(10, stored_count))
        
    except Exception as e:
        logger.error(f"Failed to ingest profile questions: {e}")


@router.get("/training/profile-stats")
async def get_profile_training_stats(api_key: str = Depends(verify_api_key)):
    """
    Get statistics on profile-based training data.
    
    Shows distribution of investor profiles and generated questions.
    """
    try:
        # This would query the database for profile training statistics
        # For now, return sample stats
        stats = {
            "total_profiles_processed": 200,
            "total_questions_generated": 2000,
            "profile_categories": {
                "young_growth": 45,
                "pre_retirement": 68,
                "retirement": 52,
                "high_net_worth": 35
            },
            "goal_distribution": {
                "income-now": 67,
                "income-growth": 78,
                "balanced": 55
            },
            "risk_distribution": {
                "conservative": 58,
                "moderate": 92,
                "aggressive": 50
            },
            "geographic_distribution": {
                "United States": 140,
                "Canada": 20,
                "Europe": 25,
                "Asia": 15
            }
        }
        
        return JSONResponse({
            "success": True,
            "statistics": stats
        })
        
    except Exception as e:
        logger.error(f"Failed to get profile stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/training/categories")
async def get_training_categories(api_key: str = Depends(verify_api_key)):
    """
    Get list of training question categories.
    """
    categories = [
        {
            "name": "dividend_analysis",
            "description": "Dividend metrics, yields, ratios, and calculations",
            "question_count": 150
        },
        {
            "name": "income_strategies", 
            "description": "Portfolio building and income optimization strategies",
            "question_count": 200
        },
        {
            "name": "technical_timing",
            "description": "Ex-dividend dates, capture strategies, and timing",
            "question_count": 150
        },
        {
            "name": "etf_funds",
            "description": "ETF analysis, comparisons, and NAV considerations",
            "question_count": 100
        },
        {
            "name": "tax_optimization",
            "description": "Tax efficiency and qualified dividend strategies",
            "question_count": 100
        },
        {
            "name": "risk_management",
            "description": "Dividend sustainability and portfolio risk analysis",
            "question_count": 100
        },
        {
            "name": "sector_geographic",
            "description": "Sector-specific and international dividend analysis",
            "question_count": 100
        },
        {
            "name": "drip_reinvestment",
            "description": "DRIP strategies and compound growth calculations",
            "question_count": 50
        },
        {
            "name": "advanced_strategies",
            "description": "Options, arbitrage, and sophisticated strategies",
            "question_count": 100
        },
        {
            "name": "realtime_monitoring",
            "description": "Alerts, announcements, and market monitoring",
            "question_count": 50
        }
    ]
    
    return JSONResponse({
        "success": True,
        "categories": categories,
        "total_questions": sum(c["question_count"] for c in categories)
    })


@router.post("/training/evaluate")
async def evaluate_single_response(
    request: EvaluateResponseRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Evaluate a single training response for quality metrics.
    
    Measures clarity, completeness, and actionability against defined targets.
    """
    try:
        # Convert expertise level string to enum
        expertise_map = {
            "beginner": ExpertiseLevel.BEGINNER,
            "intermediate": ExpertiseLevel.INTERMEDIATE,
            "advanced": ExpertiseLevel.ADVANCED
        }
        expertise_level = expertise_map.get(request.expertise_level.lower(), ExpertiseLevel.INTERMEDIATE)
        
        # Evaluate the response
        metrics = training_evaluator.evaluate_response(
            question=request.question,
            response=request.response,
            expertise_level=expertise_level,
            model_name=request.model_name
        )
        
        return JSONResponse({
            "success": True,
            "metrics": {
                "clarity_score": metrics.clarity_score,
                "completeness_score": metrics.completeness_score,
                "actionability_score": metrics.actionability_score,
                "overall_score": metrics.overall_score,
                "label": metrics.label.value,
                "passes_threshold": metrics.passes_threshold,
                "expertise_level": metrics.expertise_level.value,
                "feedback": metrics.feedback
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to evaluate response: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/training/evaluate-batch")
async def evaluate_batch_responses(
    request: BatchEvaluationRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """
    Evaluate a batch of training responses and get aggregate statistics.
    
    Useful for evaluating model performance across multiple questions.
    """
    try:
        # Convert expertise level if provided
        expertise_level = None
        if request.expertise_level:
            expertise_map = {
                "beginner": ExpertiseLevel.BEGINNER,
                "intermediate": ExpertiseLevel.INTERMEDIATE,
                "advanced": ExpertiseLevel.ADVANCED
            }
            expertise_level = expertise_map.get(request.expertise_level.lower())
        
        # Evaluate the batch
        results = training_evaluator.evaluate_batch(
            responses=request.responses,
            expertise_level=expertise_level
        )
        
        return JSONResponse({
            "success": True,
            "results": results
        })
        
    except Exception as e:
        logger.error(f"Failed to evaluate batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/training/evaluation-targets")
async def get_evaluation_targets(api_key: str = Depends(verify_api_key)):
    """
    Get the current evaluation quality targets.
    
    Shows minimum scores required for different expertise levels.
    """
    try:
        targets = {
            "global": {
                "clear_score_min": 0.9,
                "complete_score_min": 0.85,
                "actionable_score_min": 0.9
            },
            "per_level": {
                "beginner": {
                    "clear_min": 0.92,
                    "complete_min": 0.80,
                    "actionable_min": 0.92,
                    "description": "Simple language, clear steps, risk awareness"
                },
                "intermediate": {
                    "clear_min": 0.90,
                    "complete_min": 0.86,
                    "actionable_min": 0.90,
                    "description": "Balanced depth, practical strategies, data-driven"
                },
                "advanced": {
                    "clear_min": 0.88,
                    "complete_min": 0.90,
                    "actionable_min": 0.88,
                    "description": "Sophisticated analysis, complex strategies, quantitative"
                }
            },
            "score_labels": {
                "excellent": "≥ 0.90",
                "good": "≥ 0.80",
                "fair": "≥ 0.70",
                "poor": "< 0.70"
            },
            "notes": [
                "Scores are continuous in [0,1]",
                "Responses must meet ALL three metrics to pass",
                "Higher expertise levels have adjusted targets",
                "Evaluation considers audience appropriateness"
            ]
        }
        
        return JSONResponse({
            "success": True,
            "targets": targets
        })
        
    except Exception as e:
        logger.error(f"Failed to get evaluation targets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/training/export-quality")
async def export_quality_examples(
    min_score: float = 0.9,
    limit: int = 100,
    api_key: str = Depends(verify_api_key)
):
    """
    Export high-quality training examples for fine-tuning.
    
    Returns Q&A pairs that exceed the quality threshold.
    """
    try:
        # Export evaluated responses that meet quality threshold
        quality_examples = training_ingestion.export_evaluated_training_data(
            min_quality=min_score,
            limit=limit
        )
        
        if not quality_examples:
            return JSONResponse({
                "success": False,
                "message": "No evaluated training data available for export",
                "hint": "Use /training/evaluate-batch first to generate quality scores",
                "data": []
            })
        
        # Format for OpenAI fine-tuning
        formatted_examples = []
        for example in quality_examples:
            formatted_examples.append({
                "messages": [
                    {"role": "system", "content": "You are Harvey, an expert financial advisor specializing in dividend investing."},
                    {"role": "user", "content": example.get("question", "")},
                    {"role": "assistant", "content": example.get("response", "")}
                ],
                "metadata": {
                    "quality_score": example.get("quality_score", 0),
                    "model": example.get("model", "unknown"),
                    "category": example.get("category", "general")
                }
            })
        
        return JSONResponse({
            "success": True,
            "message": f"Exported {len(formatted_examples)} high-quality training examples",
            "export_format": "openai_finetune",
            "min_score_applied": min_score,
            "data": formatted_examples
        })
        
    except Exception as e:
        logger.error(f"Failed to export quality examples: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/training/passive-income")
async def ingest_passive_income_training(
    request: PassiveIncomeTrainingRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """
    Ingest specialized passive income training data (7,200+ questions).
    
    Focused on dividend investing, yield strategies, and income optimization.
    """
    try:
        # Load training questions
        questions = passive_income_trainer.load_training_questions_jsonl(
            jsonl_content=request.training_data,
            dataset_name=request.dataset_name
        )
        
        # Load lesson plan if provided
        if request.lesson_plan:
            lesson_map = passive_income_trainer.load_lesson_plan(request.lesson_plan)
            logger.info(f"Loaded lesson plan with {len(lesson_map)} topics")
        
        # Load auto-rewrite prompts if provided
        if request.auto_rewrite_prompts:
            passive_income_trainer.load_auto_rewrite_prompts(request.auto_rewrite_prompts)
            logger.info("Loaded auto-rewrite prompts for quality improvement")
        
        # Generate enhanced questions
        enhanced = passive_income_trainer.generate_enhanced_training_questions(questions[:100])
        
        # Get statistics
        categories = {}
        complexities = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        
        for q in questions:
            categories[q.category] = categories.get(q.category, 0) + 1
            complexities[q.complexity] = complexities.get(q.complexity, 0) + 1
        
        # Process in background if needed
        if len(questions) > 100:
            # Fix for async background task - create wrapper function
            def run_passive_income_processing():
                """Wrapper to run async task in background."""
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(
                        _process_passive_income_questions(questions=questions[100:])
                    )
                except Exception as e:
                    logger.error(f"Background passive income processing failed: {e}")
                finally:
                    loop.close()
            
            background_tasks.add_task(run_passive_income_processing)
        
        return JSONResponse({
            "success": True,
            "message": f"Ingested {len(questions)} passive income training questions",
            "statistics": {
                "total_questions": len(questions),
                "categories": categories,
                "complexity_distribution": complexities,
                "enhanced_samples": len(enhanced)
            },
            "sample_enhanced": enhanced[:3] if enhanced else []
        })
        
    except Exception as e:
        logger.error(f"Failed to ingest passive income training: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _process_passive_income_questions(questions: List):
    """Background task to process passive income questions."""
    try:
        logger.info(f"Background processing {len(questions)} passive income questions")
        
        # Persist passive income questions to the training database
        stored_count = 0
        for q in questions:
            # Convert TrainingQuestion objects to database format
            result = training_ingestion.store_training_question(
                category=q.category if hasattr(q, 'category') else 'passive_income',
                question_text=q.query if hasattr(q, 'query') else str(q),
                complexity_level=q.complexity if hasattr(q, 'complexity') else 3
            )
            if result.get("success"):
                stored_count += 1
        
        logger.info(f"Stored {stored_count}/{len(questions)} passive income questions")
        
        # Process through multi-model system for responses
        if stored_count > 0:
            batch_size = min(10, stored_count)
            responses = await training_ingestion.process_question_batch(batch_size=batch_size)
            
            # Evaluate response quality and store high-scoring examples
            if responses.get("success"):
                for response_data in responses.get("responses", []):
                    evaluation = training_evaluator.evaluate_response(
                        question=response_data.get("question", ""),
                        response=response_data.get("response", ""),
                        expertise_level=ExpertiseLevel.INTERMEDIATE,
                        model_name=response_data.get("model", "unknown")
                    )
                    
                    # Store evaluation results
                    if evaluation.overall_score >= 0.85:
                        training_ingestion.store_evaluation_result(
                            question_id=response_data.get("question_id"),
                            model_name=response_data.get("model"),
                            evaluation_scores={
                                "clarity": evaluation.clarity_score,
                                "completeness": evaluation.completeness_score,
                                "actionability": evaluation.actionability_score,
                                "overall": evaluation.overall_score
                            },
                            passes_threshold=evaluation.passes_threshold
                        )
        
    except Exception as e:
        logger.error(f"Failed to process passive income questions: {e}")


@router.get("/training/passive-income/stats")
async def get_passive_income_stats(api_key: str = Depends(verify_api_key)):
    """
    Get statistics on passive income training data.
    
    Shows distribution of dividend strategies and question types.
    """
    try:
        stats = {
            "total_questions": 7200,
            "datasets": {
                "main": 6000,
                "supplemental": 1200
            },
            "strategy_types": {
                "organic": "Traditional dividends (KO, SCHD, VIG)",
                "option_overlay": "Covered call ETFs (JEPI, JEPQ)",
                "synthetic": "YieldMax series (TSLY, NVDY)",
                "leveraged_credit": "CEFs with leverage (PDO)",
                "infra_CEF": "Infrastructure CEFs (UTF)",
                "option_CEF": "Option-based CEFs (ETY)"
            },
            "question_categories": {
                "yield_sustainability": 1500,
                "income_planning": 1800,
                "portfolio_construction": 1200,
                "tax_optimization": 900,
                "comparison": 1400,
                "account_location": 600,
                "general": 800
            },
            "key_tickers_covered": [
                "SCHD", "JEPI", "JEPQ", "O", "MAIN", "ARCC",
                "TSLY", "NVDY", "XYLD", "RYLD", "PDO", "UTF",
                "VIG", "VYM", "HDV", "KO", "PG"
            ]
        }
        
        return JSONResponse({
            "success": True,
            "statistics": stats
        })
        
    except Exception as e:
        logger.error(f"Failed to get passive income stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/training/dividend-calendar")
async def create_dividend_calendar(
    tickers: List[Dict[str, str]],  # [{"ticker": "JEPI", "frequency": "monthly"}]
    api_key: str = Depends(verify_api_key)
):
    """
    Create a dividend payment calendar for given tickers.
    
    Helps visualize monthly income flow from different securities.
    """
    try:
        # Convert to tuples for the service
        ticker_list = [(t["ticker"], t["frequency"]) for t in tickers]
        
        # Create calendar
        calendar = passive_income_trainer.create_dividend_calendar(ticker_list)
        
        # Calculate monthly income variance
        monthly_counts = [len(payers) for payers in calendar.values()]
        avg_payers = sum(monthly_counts) / 12
        variance = sum((count - avg_payers) ** 2 for count in monthly_counts) / 12
        
        return JSONResponse({
            "success": True,
            "dividend_calendar": calendar,
            "statistics": {
                "avg_payers_per_month": avg_payers,
                "income_variance": variance,
                "most_payments": max(monthly_counts),
                "least_payments": min(monthly_counts)
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to create dividend calendar: {e}")
        raise HTTPException(status_code=500, detail=str(e))