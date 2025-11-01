"""
Yield Predictor Model

Uses XGBoost regression to predict future dividend yields at multiple time horizons.
Supports 3, 6, 12, and 24 month predictions.
"""

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from typing import Dict, Any, Literal
import logging

from . import BaseModel, ModelRegistry

logger = logging.getLogger(__name__)


@ModelRegistry.register
class YieldPredictor(BaseModel):
    """
    XGBoost regression model for dividend yield prediction.
    
    Predicts future yields at multiple time horizons:
    - 3 months
    - 6 months
    - 12 months
    - 24 months
    
    Features:
    - Current yield metrics
    - Historical growth rates
    - Payment consistency
    - Price volatility
    - Payout ratios
    """
    
    def __init__(self, 
                 horizon: Literal['3_months', '6_months', '12_months', '24_months'] = '12_months',
                 random_state: int = 42):
        """
        Initialize yield predictor.
        
        Args:
            horizon: Prediction time horizon
            random_state: Random seed for reproducibility
        """
        super().__init__(f"yield_predictor_{horizon}")
        self.horizon = horizon
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
    
    def _compute_future_yield(self, features_df: pd.DataFrame) -> pd.Series:
        """
        Compute expected future yield based on growth trends.
        
        Args:
            features_df: Feature DataFrame
            
        Returns:
            Series of predicted future yields
        """
        current_yield = features_df['dividend_yield_12m']
        growth_rate = features_df['dividend_growth_yoy']
        
        horizon_multipliers = {
            '3_months': 0.25,
            '6_months': 0.5,
            '12_months': 1.0,
            '24_months': 2.0
        }
        
        multiplier = horizon_multipliers.get(self.horizon, 1.0)
        
        future_yield = current_yield * (1 + growth_rate * multiplier)
        
        return future_yield.clip(0, 50)
    
    def train(self, X: pd.DataFrame, y: pd.Series = None) -> Dict[str, Any]:
        """
        Train the yield predictor.
        
        If y is not provided, computes future yields from features.
        
        Args:
            X: Feature DataFrame
            y: Optional target future yields (if None, computed from features)
            
        Returns:
            Dictionary of training metrics
        """
        logger.info(f"Training {self.model_name} with {len(X)} samples...")
        
        if y is None:
            logger.info(f"Computing {self.horizon} yield predictions from features...")
            y = self._compute_future_yield(X)
        
        feature_cols = [col for col in X.columns if col != 'Ticker']
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
        
        self.training_metrics = {
            'horizon': self.horizon,
            'train_r2': train_r2,
            'test_r2': test_r2,
            'train_rmse': train_rmse,
            'test_rmse': test_rmse,
            'train_mae': train_mae,
            'test_mae': test_mae,
            'n_samples': len(X),
            'n_features': len(feature_cols)
        }
        
        logger.info(f"Training complete: R² = {test_r2:.4f}, RMSE = {test_rmse:.4f}")
        return self.training_metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict future dividend yields.
        
        Args:
            X: Feature DataFrame
            
        Returns:
            Array of predicted yields
        """
        if not self.is_trained:
            raise ValueError("Model is not trained yet")
        
        X_data = X[self.feature_names]
        predictions = self.model.predict(X_data)
        
        return np.clip(predictions, 0, 50)
