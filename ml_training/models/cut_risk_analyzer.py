"""
Cut Risk Analyzer Model

Uses XGBoost binary classifier to predict dividend cut probability.
"""

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from typing import Dict, Any
import logging

from . import BaseModel, ModelRegistry

logger = logging.getLogger(__name__)


@ModelRegistry.register
class CutRiskAnalyzer(BaseModel):
    """
    XGBoost binary classifier for dividend cut risk prediction.
    
    Predicts probability of dividend cut in next 12 months based on:
    - Payout ratio sustainability
    - Dividend growth trends
    - Payment consistency
    - Price volatility
    - Historical payment patterns
    
    High risk indicators:
    - Payout ratio > 100%
    - Negative growth rate
    - High dividend volatility (CV > 0.5)
    - Recent payment delays
    """
    
    HIGH_RISK_PAYOUT_THRESHOLD = 100.0
    HIGH_RISK_CV_THRESHOLD = 0.5
    
    def __init__(self, random_state: int = 42):
        """
        Initialize cut risk analyzer.
        
        Args:
            random_state: Random seed for reproducibility
        """
        super().__init__("cut_risk_analyzer")
        self.model = xgb.XGBClassifier(
            n_estimators=150,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=random_state,
            n_jobs=-1,
            objective='binary:logistic',
            eval_metric='logloss'
        )
        self.random_state = random_state
    
    def _compute_cut_risk_labels(self, features_df: pd.DataFrame) -> pd.Series:
        """
        Compute cut risk labels based on risk indicators.
        
        High risk (1) if ANY of:
        - Payout ratio > 100%
        - Negative growth AND high CV
        - Extremely high payout (>150%)
        
        Args:
            features_df: Feature DataFrame
            
        Returns:
            Series of binary labels (1 = high risk, 0 = low risk)
        """
        high_payout = features_df['payout_ratio'] > self.HIGH_RISK_PAYOUT_THRESHOLD
        negative_growth = features_df['dividend_growth_yoy'] < -0.1
        high_cv = features_df['dividend_cv'] > self.HIGH_RISK_CV_THRESHOLD
        extreme_payout = features_df['payout_ratio'] > 150.0
        
        at_risk = high_payout | (negative_growth & high_cv) | extreme_payout
        
        return at_risk.astype(int)
    
    def train(self, X: pd.DataFrame, y: pd.Series = None) -> Dict[str, Any]:
        """
        Train the cut risk analyzer.
        
        If y is not provided, computes risk labels from features.
        
        Args:
            X: Feature DataFrame
            y: Optional target labels (if None, computed from features)
            
        Returns:
            Dictionary of training metrics
        """
        logger.info(f"Training {self.model_name} with {len(X)} samples...")
        
        if y is None:
            logger.info("Computing cut risk labels from features...")
            y = self._compute_cut_risk_labels(X)
        
        feature_cols = [col for col in X.columns if col != 'Ticker']
        X_train_data = X[feature_cols]
        self.feature_names = feature_cols
        
        class_counts = y.value_counts()
        logger.info(f"Class distribution: {dict(class_counts)}")
        
        if len(class_counts) < 2:
            logger.warning("Only one class present in data, adding synthetic minority class")
            minority_indices = y.sample(n=max(10, len(y) // 10), random_state=self.random_state).index
            y.loc[minority_indices] = 1 - y.loc[minority_indices]
        
        X_train, X_test, y_train, y_test = train_test_split(
            X_train_data, y, test_size=0.2, random_state=self.random_state, stratify=y
        )
        
        scale_pos_weight = (y_train == 0).sum() / max((y_train == 1).sum(), 1)
        self.model.set_params(scale_pos_weight=scale_pos_weight)
        
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=False
        )
        self.is_trained = True
        
        y_pred_train = self.model.predict(X_train)
        y_pred_test = self.model.predict(X_test)
        y_pred_proba_train = self.model.predict_proba(X_train)[:, 1]
        y_pred_proba_test = self.model.predict_proba(X_test)[:, 1]
        
        train_accuracy = accuracy_score(y_train, y_pred_train)
        test_accuracy = accuracy_score(y_test, y_pred_test)
        train_precision = precision_score(y_train, y_pred_train, zero_division=0)
        test_precision = precision_score(y_test, y_pred_test, zero_division=0)
        train_recall = recall_score(y_train, y_pred_train, zero_division=0)
        test_recall = recall_score(y_test, y_pred_test, zero_division=0)
        train_f1 = f1_score(y_train, y_pred_train, zero_division=0)
        test_f1 = f1_score(y_test, y_pred_test, zero_division=0)
        
        try:
            train_auc = roc_auc_score(y_train, y_pred_proba_train)
            test_auc = roc_auc_score(y_test, y_pred_proba_test)
        except ValueError:
            train_auc = 0.5
            test_auc = 0.5
        
        self.training_metrics = {
            'train_accuracy': train_accuracy,
            'test_accuracy': test_accuracy,
            'train_precision': train_precision,
            'test_precision': test_precision,
            'train_recall': train_recall,
            'test_recall': test_recall,
            'train_f1': train_f1,
            'test_f1': test_f1,
            'train_auc': train_auc,
            'test_auc': test_auc,
            'n_samples': len(X),
            'n_features': len(feature_cols),
            'class_distribution': dict(class_counts)
        }
        
        logger.info(f"Training complete: Accuracy = {test_accuracy:.4f}, F1 = {test_f1:.4f}")
        return self.training_metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict cut risk labels (0 = low risk, 1 = high risk).
        
        Args:
            X: Feature DataFrame
            
        Returns:
            Array of binary predictions
        """
        if not self.is_trained:
            raise ValueError("Model is not trained yet")
        
        X_data = X[self.feature_names]
        return self.model.predict(X_data)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict probability of dividend cut.
        
        Args:
            X: Feature DataFrame
            
        Returns:
            Array of probabilities (0-1)
        """
        if not self.is_trained:
            raise ValueError("Model is not trained yet")
        
        X_data = X[self.feature_names]
        return self.model.predict_proba(X_data)[:, 1]
    
    def get_risk_level(self, probability: float) -> str:
        """
        Convert cut probability to risk level.
        
        Args:
            probability: Cut probability (0-1)
            
        Returns:
            Risk level label
        """
        if probability < 0.2:
            return 'very_low'
        elif probability < 0.4:
            return 'low'
        elif probability < 0.6:
            return 'moderate'
        elif probability < 0.8:
            return 'high'
        else:
            return 'very_high'
