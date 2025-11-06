"""
Anomaly Detector Model

Uses Isolation Forest to detect unusual dividend payment patterns, cuts, or suspensions.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from typing import Dict, Any
import logging

from . import BaseModel, ModelRegistry

logger = logging.getLogger(__name__)


@ModelRegistry.register
class AnomalyDetector(BaseModel):
    """
    Isolation Forest model for anomaly detection in dividend payments.
    
    Detects unusual patterns such as:
    - Sudden dividend cuts or suspensions
    - Irregular payment schedules
    - Unusual yield spikes
    - Erratic payout ratios
    - Payment timing anomalies
    
    Features:
    - Dividend consistency (CV)
    - Payment frequency regularity
    - Yield volatility
    - Payout ratio extremes
    - Growth rate anomalies
    """
    
    def __init__(self, contamination: float = 0.1, random_state: int = 42):
        """
        Initialize anomaly detector.
        
        Args:
            contamination: Expected proportion of anomalies (0.1 = 10%)
            random_state: Random seed for reproducibility
        """
        super().__init__("anomaly_detector")
        self.model = IsolationForest(
            n_estimators=100,
            max_samples='auto',
            contamination=contamination,
            random_state=random_state,
            n_jobs=-1
        )
        self.random_state = random_state
        self.contamination = contamination
    
    def train(self, X: pd.DataFrame, y: pd.Series = None) -> Dict[str, Any]:
        """
        Train the anomaly detector.
        
        Note: Isolation Forest is unsupervised, so y is not used.
        
        Args:
            X: Feature DataFrame
            y: Not used (unsupervised learning)
            
        Returns:
            Dictionary of training metrics
        """
        logger.info(f"Training {self.model_name} with {len(X)} samples...")
        
        feature_cols = [col for col in X.columns if col != 'Ticker']
        X_train_data = X[feature_cols]
        self.feature_names = feature_cols
        
        X_train, X_test = train_test_split(
            X_train_data, test_size=0.2, random_state=self.random_state
        )
        
        self.model.fit(X_train)
        self.is_trained = True
        
        train_predictions = self.model.predict(X_train)
        test_predictions = self.model.predict(X_test)
        
        train_scores = self.model.score_samples(X_train)
        test_scores = self.model.score_samples(X_test)
        
        train_anomaly_count = (train_predictions == -1).sum()
        test_anomaly_count = (test_predictions == -1).sum()
        train_anomaly_pct = train_anomaly_count / len(train_predictions) * 100
        test_anomaly_pct = test_anomaly_count / len(test_predictions) * 100
        
        self.training_metrics = {
            'contamination': self.contamination,
            'train_anomaly_count': int(train_anomaly_count),
            'test_anomaly_count': int(test_anomaly_count),
            'train_anomaly_pct': train_anomaly_pct,
            'test_anomaly_pct': test_anomaly_pct,
            'train_score_mean': train_scores.mean(),
            'train_score_std': train_scores.std(),
            'test_score_mean': test_scores.mean(),
            'test_score_std': test_scores.std(),
            'n_samples': len(X),
            'n_features': len(feature_cols)
        }
        
        logger.info(f"Training complete: {test_anomaly_pct:.1f}% anomalies detected")
        return self.training_metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict anomaly labels (-1 = anomaly, 1 = normal).
        
        Args:
            X: Feature DataFrame
            
        Returns:
            Array of predictions (-1 or 1)
        """
        if not self.is_trained:
            raise ValueError("Model is not trained yet")
        
        X_data = X[self.feature_names]
        return self.model.predict(X_data)
    
    def predict_score(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict anomaly scores (lower = more anomalous).
        
        Args:
            X: Feature DataFrame
            
        Returns:
            Array of anomaly scores
        """
        if not self.is_trained:
            raise ValueError("Model is not trained yet")
        
        X_data = X[self.feature_names]
        return self.model.score_samples(X_data)
    
    def get_anomalies(self, X: pd.DataFrame, include_scores: bool = True) -> pd.DataFrame:
        """
        Get anomaly predictions with optional scores.
        
        Args:
            X: Feature DataFrame with Ticker column
            include_scores: Whether to include anomaly scores
            
        Returns:
            DataFrame with anomaly predictions
        """
        predictions = self.predict(X)
        
        result = pd.DataFrame({
            'Ticker': X['Ticker'] if 'Ticker' in X.columns else range(len(X)),
            'is_anomaly': predictions == -1
        })
        
        if include_scores:
            scores = self.predict_score(X)
            result['anomaly_score'] = scores
            result['anomaly_severity'] = self._compute_severity(scores)
        
        return result
    
    def _compute_severity(self, scores: np.ndarray) -> np.ndarray:
        """
        Compute anomaly severity from scores.
        
        Args:
            scores: Anomaly scores (lower = more anomalous)
            
        Returns:
            Array of severity labels
        """
        severity = np.full(len(scores), 'normal', dtype=object)
        
        score_threshold_high = np.percentile(scores, 10)
        score_threshold_med = np.percentile(scores, 25)
        
        severity[scores < score_threshold_high] = 'critical'
        severity[(scores >= score_threshold_high) & (scores < score_threshold_med)] = 'moderate'
        
        return severity
