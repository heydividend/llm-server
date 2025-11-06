"""
Growth Rate Predictor Model

Uses RandomForest regression to predict annual dividend growth rates.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from typing import Dict, Any
import logging

from . import BaseModel, ModelRegistry

logger = logging.getLogger(__name__)


@ModelRegistry.register
class GrowthRatePredictor(BaseModel):
    """
    RandomForest regression model for dividend growth rate prediction.
    
    Predicts annual dividend growth rate based on:
    - Historical growth patterns
    - Payment consistency
    - Payout ratios
    - Sector and industry trends
    """
    
    def __init__(self, n_estimators: int = 100, random_state: int = 42):
        """
        Initialize growth rate predictor.
        
        Args:
            n_estimators: Number of trees in the forest
            random_state: Random seed for reproducibility
        """
        super().__init__("growth_rate_predictor")
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=8,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=random_state,
            n_jobs=-1
        )
        self.random_state = random_state
    
    def train(self, X: pd.DataFrame, y: pd.Series = None) -> Dict[str, Any]:
        """
        Train the growth rate predictor.
        
        If y is not provided, uses dividend_growth_yoy from features.
        
        Args:
            X: Feature DataFrame
            y: Optional target growth rates (if None, uses dividend_growth_yoy)
            
        Returns:
            Dictionary of training metrics
        """
        logger.info(f"Training {self.model_name} with {len(X)} samples...")
        
        if y is None:
            if 'dividend_growth_yoy' not in X.columns:
                raise ValueError("dividend_growth_yoy column required when y is not provided")
            y = X['dividend_growth_yoy']
        
        feature_cols = [col for col in X.columns if col not in ['Ticker', 'dividend_growth_yoy']]
        X_train_data = X[feature_cols]
        self.feature_names = feature_cols
        
        X_train, X_test, y_train, y_test = train_test_split(
            X_train_data, y, test_size=0.2, random_state=self.random_state
        )
        
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        y_pred_train = self.model.predict(X_train)
        y_pred_test = self.model.predict(X_test)
        
        train_r2 = r2_score(y_train, y_pred_train)
        test_r2 = r2_score(y_test, y_pred_test)
        train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
        test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
        train_mae = mean_absolute_error(y_train, y_pred_train)
        test_mae = mean_absolute_error(y_test, y_pred_test)
        
        cv_scores = cross_val_score(
            self.model, X_train_data, y, cv=5, scoring='r2', n_jobs=-1
        )
        
        self.training_metrics = {
            'train_r2': train_r2,
            'test_r2': test_r2,
            'train_rmse': train_rmse,
            'test_rmse': test_rmse,
            'train_mae': train_mae,
            'test_mae': test_mae,
            'cv_mean_r2': cv_scores.mean(),
            'cv_std_r2': cv_scores.std(),
            'n_samples': len(X),
            'n_features': len(feature_cols)
        }
        
        logger.info(f"Training complete: R² = {test_r2:.4f}, RMSE = {test_rmse:.4f}")
        return self.training_metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict dividend growth rates.
        
        Args:
            X: Feature DataFrame
            
        Returns:
            Array of predicted growth rates
        """
        if not self.is_trained:
            raise ValueError("Model is not trained yet")
        
        X_data = X[self.feature_names]
        predictions = self.model.predict(X_data)
        
        return np.clip(predictions, -1.0, 2.0)
