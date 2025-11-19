"""
Gemini ML Model Evaluator Service
Cross-validates ML predictions using Gemini 2.5 Pro, generates natural language
explanations, detects anomalies, and provides confidence scores.

Phase 4 of Gemini-Enhanced Harvey Intelligence System
"""

import logging
import json
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum

from app.services.gemini_client import get_gemini_client
from app.core.database import get_db_connection

logger = logging.getLogger("gemini_ml_evaluator")


class ValidationResult(str, Enum):
    """Gemini's validation assessment of ML predictions."""
    AGREE = "agree"
    DISAGREE = "disagree"
    UNCERTAIN = "uncertain"
    PARTIALLY_AGREE = "partially_agree"


class ModelType(str, Enum):
    """Supported ML model types for evaluation."""
    DIVIDEND_SCORER = "dividend_scorer"
    YIELD_PREDICTOR = "yield_predictor"
    GROWTH_PREDICTOR = "growth_predictor"
    PAYOUT_PREDICTOR = "payout_predictor"
    CUT_RISK_ANALYZER = "cut_risk_analyzer"
    ANOMALY_DETECTOR = "anomaly_detector"
    STOCK_CLUSTERER = "stock_clusterer"


class GeminiMLEvaluator:
    """
    Cross-validates ML predictions using Gemini 2.5 Pro.
    
    Features:
    - Natural language explanations for ML predictions
    - Validation of prediction reasonableness
    - Anomaly detection (outlier predictions)
    - Confidence scoring (0.0-1.0)
    - Cross-model consistency checking
    - Database audit trail
    """
    
    def __init__(self, max_evaluations_per_day: int = 1000):
        """
        Initialize Gemini ML Evaluator.
        
        Args:
            max_evaluations_per_day: Cost control limit (default: 1000/day)
        """
        self.gemini = get_gemini_client()
        self.max_evaluations_per_day = max_evaluations_per_day
        self.evaluation_count_today = 0
        
        logger.info("Gemini ML Evaluator initialized")
        logger.info(f"  - Daily evaluation limit: {max_evaluations_per_day}")
    
    def _get_evaluation_prompt(
        self,
        model_type: ModelType,
        ticker: str,
        prediction_value: float,
        model_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate Gemini prompt for evaluating ML prediction.
        
        Args:
            model_type: Type of ML model
            ticker: Stock ticker symbol
            prediction_value: Model's prediction
            model_metadata: Additional model output (confidence, features, etc.)
        
        Returns:
            Formatted prompt for Gemini
        """
        metadata_str = ""
        if model_metadata:
            metadata_str = f"\n\nAdditional Model Data:\n{json.dumps(model_metadata, indent=2)}"
        
        prompts = {
            ModelType.DIVIDEND_SCORER: f"""
You are a financial analyst evaluating a machine learning model's dividend quality assessment.

**Task**: Validate and explain why stock {ticker} received a dividend quality score of {prediction_value:.2f} (0-100 scale).

**Analysis Required**:
1. Is this score reasonable based on {ticker}'s fundamentals (payout ratio, yield, dividend history)?
2. What factors would justify this score?
3. What are potential red flags or concerns?
4. Does this align with industry standards for dividend quality scoring?

**Output Format**:
- Validation: [AGREE/DISAGREE/UNCERTAIN/PARTIALLY_AGREE]
- Confidence: [0.0-1.0]
- Explanation: [2-3 sentences explaining your assessment]
- Key Factors: [List 2-3 key factors that support or contradict this score]
- Anomaly Risk: [HIGH/MEDIUM/LOW - likelihood this is an outlier prediction]
{metadata_str}
""",
            
            ModelType.YIELD_PREDICTOR: f"""
You are a financial analyst evaluating a machine learning model's dividend yield forecast.

**Task**: Validate the predicted 12-month dividend yield of {prediction_value:.2f}% for {ticker}.

**Analysis Required**:
1. Is this yield prediction realistic given {ticker}'s current yield and growth trajectory?
2. What market conditions would support this forecast?
3. Are there risks that could make this prediction inaccurate?
4. How does this compare to sector averages?

**Output Format**:
- Validation: [AGREE/DISAGREE/UNCERTAIN/PARTIALLY_AGREE]
- Confidence: [0.0-1.0]
- Explanation: [2-3 sentences explaining your assessment]
- Key Factors: [List 2-3 key factors that support or contradict this prediction]
- Anomaly Risk: [HIGH/MEDIUM/LOW - likelihood this is an outlier prediction]
{metadata_str}
""",
            
            ModelType.GROWTH_PREDICTOR: f"""
You are a financial analyst evaluating a machine learning model's dividend growth forecast.

**Task**: Validate the predicted dividend growth rate of {prediction_value:.2f}% for {ticker}.

**Analysis Required**:
1. Is this growth rate sustainable given {ticker}'s earnings growth and payout ratio?
2. What fundamental factors support or contradict this growth forecast?
3. How does this compare to {ticker}'s historical dividend growth?
4. Are there risks to this growth projection?

**Output Format**:
- Validation: [AGREE/DISAGREE/UNCERTAIN/PARTIALLY_AGREE]
- Confidence: [0.0-1.0]
- Explanation: [2-3 sentences explaining your assessment]
- Key Factors: [List 2-3 key factors that support or contradict this prediction]
- Anomaly Risk: [HIGH/MEDIUM/LOW - likelihood this is an outlier prediction]
{metadata_str}
""",
            
            ModelType.PAYOUT_PREDICTOR: f"""
You are a financial analyst evaluating a machine learning model's payout ratio forecast.

**Task**: Validate the predicted payout ratio of {prediction_value:.2f}% for {ticker}.

**Analysis Required**:
1. Is this payout ratio sustainable given {ticker}'s earnings and cash flow?
2. What are the risks if the payout ratio reaches this level?
3. How does this compare to industry benchmarks for {ticker}'s sector?
4. Are there fundamental factors that would support or contradict this forecast?

**Output Format**:
- Validation: [AGREE/DISAGREE/UNCERTAIN/PARTIALLY_AGREE]
- Confidence: [0.0-1.0]
- Explanation: [2-3 sentences explaining your assessment]
- Key Factors: [List 2-3 key factors that support or contradict this prediction]
- Anomaly Risk: [HIGH/MEDIUM/LOW - likelihood this is an outlier prediction]
{metadata_str}
""",
            
            ModelType.CUT_RISK_ANALYZER: f"""
You are a financial analyst evaluating a machine learning model's dividend cut risk assessment.

**Task**: Validate the dividend cut risk score of {prediction_value:.2f} (0-100, higher = more risk) for {ticker}.

**Analysis Required**:
1. Is this risk assessment accurate given {ticker}'s financial health and dividend coverage?
2. What specific factors contribute to this risk level?
3. Are there early warning signs that support or contradict this assessment?
4. How urgent is the risk, if any?

**Output Format**:
- Validation: [AGREE/DISAGREE/UNCERTAIN/PARTIALLY_AGREE]
- Confidence: [0.0-1.0]
- Explanation: [2-3 sentences explaining your assessment]
- Key Factors: [List 2-3 key factors that support or contradict this risk score]
- Anomaly Risk: [HIGH/MEDIUM/LOW - likelihood this is an outlier prediction]
{metadata_str}
""",
            
            ModelType.ANOMALY_DETECTOR: f"""
You are a financial analyst evaluating a machine learning model's anomaly detection output.

**Task**: Validate the anomaly score of {prediction_value:.2f} (0-100, higher = more anomalous) for {ticker}.

**Analysis Required**:
1. Is this stock truly anomalous compared to peers?
2. What unusual patterns or characteristics would justify this score?
3. Is the anomaly positive (opportunity) or negative (warning)?
4. Should investors investigate this further?

**Output Format**:
- Validation: [AGREE/DISAGREE/UNCERTAIN/PARTIALLY_AGREE]
- Confidence: [0.0-1.0]
- Explanation: [2-3 sentences explaining your assessment]
- Key Factors: [List 2-3 key factors that support or contradict this anomaly score]
- Anomaly Risk: [HIGH/MEDIUM/LOW - likelihood this prediction itself is an outlier]
{metadata_str}
""",
            
            ModelType.STOCK_CLUSTERER: f"""
You are a financial analyst evaluating a machine learning model's stock clustering result.

**Task**: Validate that {ticker} belongs to cluster {prediction_value:.0f} based on dividend characteristics.

**Analysis Required**:
1. Does this clustering make sense given {ticker}'s dividend profile?
2. What characteristics likely drove this cluster assignment?
3. Would you group {ticker} with similar stocks in this cluster?
4. Are there better cluster assignments?

**Output Format**:
- Validation: [AGREE/DISAGREE/UNCERTAIN/PARTIALLY_AGREE]
- Confidence: [0.0-1.0]
- Explanation: [2-3 sentences explaining your assessment]
- Key Factors: [List 2-3 key factors that support or contradict this clustering]
- Anomaly Risk: [HIGH/MEDIUM/LOW - likelihood this is an incorrect cluster assignment]
{metadata_str}
"""
        }
        
        return prompts.get(model_type, f"Evaluate prediction {prediction_value} for {ticker}")
    
    def _parse_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Gemini's structured response into evaluation metrics.
        
        Args:
            response_text: Gemini's response text
        
        Returns:
            Parsed evaluation data
        """
        lines = response_text.strip().split('\n')
        parsed = {
            'validation': ValidationResult.UNCERTAIN,
            'confidence_score': 0.5,
            'explanation': '',
            'key_factors': [],
            'anomaly_risk': 'MEDIUM'
        }
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('**'):
                continue
            
            # Parse validation
            if line.startswith('- Validation:') or line.startswith('Validation:'):
                val = line.split(':', 1)[1].strip().strip('[]').upper()
                if 'AGREE' in val and 'DISAGREE' not in val and 'PARTIALLY' not in val:
                    parsed['validation'] = ValidationResult.AGREE
                elif 'DISAGREE' in val:
                    parsed['validation'] = ValidationResult.DISAGREE
                elif 'PARTIALLY' in val:
                    parsed['validation'] = ValidationResult.PARTIALLY_AGREE
                else:
                    parsed['validation'] = ValidationResult.UNCERTAIN
            
            # Parse confidence
            elif line.startswith('- Confidence:') or line.startswith('Confidence:'):
                try:
                    conf_str = line.split(':', 1)[1].strip().strip('[]')
                    parsed['confidence_score'] = float(conf_str)
                except (ValueError, IndexError):
                    parsed['confidence_score'] = 0.5
            
            # Parse explanation
            elif line.startswith('- Explanation:') or line.startswith('Explanation:'):
                parsed['explanation'] = line.split(':', 1)[1].strip().strip('[]')
                current_section = 'explanation'
            
            # Parse key factors
            elif line.startswith('- Key Factors:') or line.startswith('Key Factors:'):
                current_section = 'key_factors'
            
            # Parse anomaly risk
            elif line.startswith('- Anomaly Risk:') or line.startswith('Anomaly Risk:'):
                risk = line.split(':', 1)[1].strip().strip('[]').upper()
                if 'HIGH' in risk:
                    parsed['anomaly_risk'] = 'HIGH'
                elif 'LOW' in risk:
                    parsed['anomaly_risk'] = 'LOW'
                else:
                    parsed['anomaly_risk'] = 'MEDIUM'
                current_section = None
            
            # Continue multi-line sections
            elif current_section == 'explanation' and not line.startswith('-'):
                parsed['explanation'] += ' ' + line
            
            elif current_section == 'key_factors' and line.startswith('-'):
                factor = line.lstrip('-').strip()
                if factor:
                    parsed['key_factors'].append(factor)
        
        # Clean up explanation
        parsed['explanation'] = parsed['explanation'].strip()
        
        return parsed
    
    def evaluate_prediction(
        self,
        model_type: ModelType,
        ticker: str,
        prediction_value: float,
        model_metadata: Optional[Dict[str, Any]] = None,
        save_to_db: bool = True
    ) -> Dict[str, Any]:
        """
        Evaluate a single ML prediction using Gemini.
        
        Args:
            model_type: Type of ML model
            ticker: Stock ticker symbol
            prediction_value: Model's prediction
            model_metadata: Additional model output
            save_to_db: Store evaluation in database (default: True)
        
        Returns:
            Evaluation result with explanation, validation, confidence
        """
        # Check daily limit
        if self.evaluation_count_today >= self.max_evaluations_per_day:
            logger.warning(f"Daily evaluation limit reached ({self.max_evaluations_per_day})")
            return {
                'success': False,
                'error': 'Daily evaluation limit reached',
                'limit': self.max_evaluations_per_day
            }
        
        try:
            logger.info(f"Evaluating {model_type.value} prediction for {ticker}: {prediction_value}")
            
            # Generate prompt
            prompt = self._get_evaluation_prompt(model_type, ticker, prediction_value, model_metadata)
            
            # Get Gemini evaluation
            gemini_response = self.gemini.generate_text(
                prompt=prompt,
                temperature=0.3,  # Lower temperature for more deterministic analysis
                max_tokens=1024,
                use_cache=True
            )
            
            # Parse response
            parsed = self._parse_gemini_response(gemini_response['text'])
            
            # Build result
            result = {
                'success': True,
                'ticker': ticker,
                'model_type': model_type.value,
                'prediction_value': prediction_value,
                'validation': parsed['validation'].value,
                'confidence_score': parsed['confidence_score'],
                'explanation': parsed['explanation'],
                'key_factors': parsed['key_factors'],
                'anomaly_detected': parsed['anomaly_risk'] == 'HIGH',
                'anomaly_risk': parsed['anomaly_risk'],
                'gemini_usage': gemini_response.get('usage', {}),
                'evaluation_timestamp': datetime.utcnow().isoformat()
            }
            
            # Increment counter
            self.evaluation_count_today += 1
            
            # Save to database
            if save_to_db:
                self._save_evaluation_to_db(result, model_metadata)
            
            logger.info(f"Evaluation complete: {parsed['validation'].value} (confidence: {parsed['confidence_score']:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Evaluation failed for {ticker}: {e}")
            return {
                'success': False,
                'ticker': ticker,
                'model_type': model_type.value,
                'error': str(e)
            }
    
    def evaluate_batch(
        self,
        predictions: List[Dict[str, Any]],
        batch_size: int = 5,
        delay_between_batches: float = 1.0
    ) -> List[Dict[str, Any]]:
        """
        Evaluate multiple ML predictions in batches.
        
        Args:
            predictions: List of predictions to evaluate
                Each dict should have: model_type, ticker, prediction_value, metadata (optional)
            batch_size: Predictions per batch (default: 5)
            delay_between_batches: Delay in seconds (default: 1.0)
        
        Returns:
            List of evaluation results
        """
        import time
        
        results = []
        total_batches = (len(predictions) + batch_size - 1) // batch_size
        
        logger.info(f"Batch evaluating {len(predictions)} predictions in {total_batches} batches")
        
        for i in range(0, len(predictions), batch_size):
            batch = predictions[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} predictions)")
            
            for pred in batch:
                try:
                    model_type = ModelType(pred['model_type'])
                    result = self.evaluate_prediction(
                        model_type=model_type,
                        ticker=pred['ticker'],
                        prediction_value=pred['prediction_value'],
                        model_metadata=pred.get('metadata'),
                        save_to_db=pred.get('save_to_db', True)
                    )
                    results.append(result)
                except Exception as e:
                    logger.error(f"Batch evaluation failed for {pred.get('ticker')}: {e}")
                    results.append({
                        'success': False,
                        'ticker': pred.get('ticker'),
                        'model_type': pred.get('model_type'),
                        'error': str(e)
                    })
            
            # Delay between batches
            if i + batch_size < len(predictions):
                time.sleep(delay_between_batches)
        
        logger.info(f"Batch evaluation complete: {len(results)} results")
        return results
    
    def compare_models(
        self,
        ticker: str,
        predictions: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Compare predictions across multiple models for consistency.
        
        Args:
            ticker: Stock ticker symbol
            predictions: Dict of {model_type: prediction_value}
        
        Returns:
            Cross-model consistency analysis
        """
        logger.info(f"Comparing {len(predictions)} model predictions for {ticker}")
        
        evaluations = []
        for model_type_str, pred_value in predictions.items():
            try:
                model_type = ModelType(model_type_str)
                eval_result = self.evaluate_prediction(
                    model_type=model_type,
                    ticker=ticker,
                    prediction_value=pred_value,
                    save_to_db=False  # Don't save individual evaluations
                )
                evaluations.append(eval_result)
            except Exception as e:
                logger.error(f"Model comparison failed for {model_type_str}: {e}")
        
        # Analyze consistency
        validations = [e.get('validation') for e in evaluations if e.get('success')]
        confidence_scores = [e.get('confidence_score', 0) for e in evaluations if e.get('success')]
        anomalies = [e for e in evaluations if e.get('anomaly_detected')]
        
        agree_count = sum(1 for v in validations if v == ValidationResult.AGREE.value)
        disagree_count = sum(1 for v in validations if v == ValidationResult.DISAGREE.value)
        
        return {
            'ticker': ticker,
            'models_evaluated': len(evaluations),
            'successful_evaluations': len(validations),
            'agreement_rate': agree_count / len(validations) if validations else 0.0,
            'avg_confidence': sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0,
            'anomalies_detected': len(anomalies),
            'consistency_score': agree_count / len(validations) if validations else 0.0,
            'evaluations': evaluations,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _save_evaluation_to_db(self, evaluation: Dict[str, Any], model_metadata: Optional[Dict[str, Any]] = None):
        """
        Save evaluation result to ml_evaluation_audit table.
        
        Args:
            evaluation: Evaluation result
            model_metadata: Additional model metadata
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            audit_id = str(uuid.uuid4())
            
            # Prepare metadata JSON
            metadata = {
                'key_factors': evaluation.get('key_factors', []),
                'anomaly_risk': evaluation.get('anomaly_risk'),
                'gemini_usage': evaluation.get('gemini_usage', {}),
                'model_metadata': model_metadata or {}
            }
            
            cursor.execute("""
                INSERT INTO dbo.ml_evaluation_audit (
                    audit_id, ticker, model_name, prediction_value,
                    gemini_validation, explanation, confidence_score,
                    anomaly_detected, metadata, evaluation_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
            """, (
                audit_id,
                evaluation['ticker'],
                evaluation['model_type'],
                evaluation['prediction_value'],
                evaluation['validation'],
                evaluation['explanation'],
                evaluation['confidence_score'],
                evaluation.get('anomaly_detected', False),
                json.dumps(metadata)
            ))
            
            conn.commit()
            logger.debug(f"Evaluation saved to database: {audit_id}")
            
        except Exception as e:
            logger.error(f"Failed to save evaluation to database: {e}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    
    def get_evaluation_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get evaluation statistics for the past N days.
        
        Args:
            days: Number of days to analyze (default: 7)
        
        Returns:
            Statistics on evaluations, validation rates, confidence scores
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    model_name,
                    COUNT(*) as total_evaluations,
                    SUM(CASE WHEN gemini_validation = 'agree' THEN 1 ELSE 0 END) as agree_count,
                    SUM(CASE WHEN gemini_validation = 'disagree' THEN 1 ELSE 0 END) as disagree_count,
                    SUM(CASE WHEN anomaly_detected = 1 THEN 1 ELSE 0 END) as anomaly_count,
                    AVG(confidence_score) as avg_confidence,
                    MIN(confidence_score) as min_confidence,
                    MAX(confidence_score) as max_confidence
                FROM dbo.ml_evaluation_audit
                WHERE evaluation_timestamp >= DATEADD(day, -?, GETDATE())
                GROUP BY model_name
            """, (days,))
            
            rows = cursor.fetchall()
            
            stats = {
                'period_days': days,
                'models': [],
                'total_evaluations': 0,
                'overall_agreement_rate': 0.0,
                'overall_avg_confidence': 0.0,
                'total_anomalies': 0
            }
            
            total_agree = 0
            total_evals = 0
            total_confidence = 0.0
            
            for row in rows:
                model_stat = {
                    'model_name': row[0],
                    'total_evaluations': row[1],
                    'agree_count': row[2],
                    'disagree_count': row[3],
                    'anomaly_count': row[4],
                    'avg_confidence': float(row[5]) if row[5] else 0.0,
                    'min_confidence': float(row[6]) if row[6] else 0.0,
                    'max_confidence': float(row[7]) if row[7] else 0.0,
                    'agreement_rate': row[2] / row[1] if row[1] > 0 else 0.0
                }
                stats['models'].append(model_stat)
                
                total_agree += row[2]
                total_evals += row[1]
                total_confidence += float(row[5] or 0.0) * row[1]
                stats['total_anomalies'] += row[4]
            
            stats['total_evaluations'] = total_evals
            stats['overall_agreement_rate'] = total_agree / total_evals if total_evals > 0 else 0.0
            stats['overall_avg_confidence'] = total_confidence / total_evals if total_evals > 0 else 0.0
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get evaluation statistics: {e}")
            return {'error': str(e)}
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()


# Global instance
_evaluator: Optional[GeminiMLEvaluator] = None


def get_ml_evaluator() -> GeminiMLEvaluator:
    """Get or create global ML evaluator instance."""
    global _evaluator
    if _evaluator is None:
        _evaluator = GeminiMLEvaluator()
    return _evaluator
