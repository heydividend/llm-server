"""
Payout Ratio Predictor Model

Uses XGBoost regression to predict payout ratios with sustainability analysis.
"""

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from typing import Dict, Any
import logging

from . import BaseModel, ModelRegistry

logger = logging.getLogger(__name__)


@ModelRegistry.register
class PayoutRatioPredictor(BaseModel):
    """
    XGBoost regression model for payout ratio prediction with sustainability threshold.
    
    Predicts payout ratios and flags sustainability concerns.
    Sustainable payout ratios typically range from 30-70% for stocks.
    
    Features:
    - Current payout ratio
    - Dividend growth rate
    - Payment consistency
    - Yield metrics
    - Security type (ETF vs Stock)
    """
    
    SUSTAINABILITY_THRESHOLD_LOW = 30.0
    SUSTAINABILITY_THRESHOLD_HIGH = 70.0
    
    def __init__(self, random_state: int = 42):
        """
        Initialize payout ratio predictor.
        
        Args:
            random_state: Random seed for reproducibility
        """
        super().__init__("payout_ratio_predictor")
        self.model = xgb.XGBRegressor(
            n_estimators=150,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=random_state,
            n_jobs=-1,
            objective='reg:squarederror'
        )
        self.random_state = random_state
    
    def train(self, X: pd.DataFrame, y: pd.Series = None) -> Dict[str, Any]:
        """
        Train the payout ratio predictor.
        
        If y is not provided, uses payout_ratio from features.
        
        Args:
            X: Feature DataFrame
            y: Optional target payout ratios (if None, uses payout_ratio)
            
        Returns:
            Dictionary of training metrics
        """
        logger.info(f"Training {self.model_name} with {len(X)} samples...")
        
        if y is None:
            if 'payout_ratio' not in X.columns:
                raise ValueError("payout_ratio column required when y is not provided")
            y = X['payout_ratio']
        
        feature_cols = [col for col in X.columns if col not in ['Ticker', 'payout_ratio']]
        X_train_data = X[feature_cols]
        self.feature_names = feature_cols
        
        X_train, X_test, y_train, y_test = train_test_split(
            X_train_data, y, test_size=0.2, random_state=self.random_state
        )
        
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=False
        )
        self.is_trained = True
        
        y_pred_train = self.model.predict(X_train)
        y_pred_test = self.model.predict(X_test)
        
        train_r2 = r2_score(y_train, y_pred_train)
        test_r2 = r2_score(y_test, y_pred_test)
        train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
        test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
        train_mae = mean_absolute_error(y_train, y_pred_train)
        test_mae = mean_absolute_error(y_test, y_pred_test)
        
        sustainability_train = self._compute_sustainability(y_pred_train)
        sustainability_test = self._compute_sustainability(y_pred_test)
        
        self.training_metrics = {
            'train_r2': train_r2,
            'test_r2': test_r2,
            'train_rmse': train_rmse,
            'test_rmse': test_rmse,
            'train_mae': train_mae,
            'test_mae': test_mae,
            'sustainability_threshold_low': self.SUSTAINABILITY_THRESHOLD_LOW,
            'sustainability_threshold_high': self.SUSTAINABILITY_THRESHOLD_HIGH,
            'train_sustainable_pct': (sustainability_train == 'sustainable').sum() / len(sustainability_train) * 100,
            'test_sustainable_pct': (sustainability_test == 'sustainable').sum() / len(sustainability_test) * 100,
            'n_samples': len(X),
            'n_features': len(feature_cols)
        }
        
        logger.info(f"Training complete: R² = {test_r2:.4f}, RMSE = {test_rmse:.4f}")
        logger.info(f"Sustainability: {self.training_metrics['test_sustainable_pct']:.1f}% sustainable")
        return self.training_metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict payout ratios.
        
        Args:
            X: Feature DataFrame
            
        Returns:
            Array of predicted payout ratios
        """
        if not self.is_trained:
            raise ValueError("Model is not trained yet")
        
        X_data = X[self.feature_names]
        predictions = self.model.predict(X_data)
        
        return np.clip(predictions, 0, 200)
    
    def _compute_sustainability(self, payout_ratios: np.ndarray) -> np.ndarray:
        """
        Compute sustainability classification for payout ratios.
        
        Args:
            payout_ratios: Array of payout ratios
            
        Returns:
            Array of sustainability labels
        """
        sustainability = np.full(len(payout_ratios), 'unsustainable', dtype=object)
        
        sustainable_mask = (payout_ratios >= self.SUSTAINABILITY_THRESHOLD_LOW) & \
                          (payout_ratios <= self.SUSTAINABILITY_THRESHOLD_HIGH)
        sustainability[sustainable_mask] = 'sustainable'
        
        low_mask = payout_ratios < self.SUSTAINABILITY_THRESHOLD_LOW
        sustainability[low_mask] = 'low_payout'
        
        high_mask = payout_ratios > self.SUSTAINABILITY_THRESHOLD_HIGH
        sustainability[high_mask] = 'high_risk'
        
        return sustainability
    
    def predict_with_sustainability(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Predict payout ratios with sustainability classification.
        
        Args:
            X: Feature DataFrame
            
        Returns:
            DataFrame with predictions and sustainability labels
        """
        predictions = self.predict(X)
        sustainability = self._compute_sustainability(predictions)
        
        return pd.DataFrame({
            'payout_ratio': predictions,
            'sustainability': sustainability
        })
