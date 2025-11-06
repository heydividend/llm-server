"""
Dividend Quality Scorer Model

Uses RandomForest regression to score dividend quality on a 0-100 scale.
Considers dividend consistency, growth, payout ratios, and payment history.
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
class DividendQualityScorer(BaseModel):
    """
    RandomForest regression model for dividend quality scoring (0-100 scale).
    
    Features:
    - Dividend consistency (coefficient of variation)
    - Payment history (days, count)
    - Growth rate (YoY)
    - Yield metrics (3m, 6m, 12m)
    - Price volatility
    - Payout ratio
    
    Target:
    - Composite quality score (0-100) based on multiple factors
    """
    
    def __init__(self, n_estimators: int = 100, random_state: int = 42):
        """
        Initialize dividend quality scorer.
        
        Args:
            n_estimators: Number of trees in the forest
            random_state: Random seed for reproducibility
        """
        super().__init__("dividend_quality_scorer")
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=random_state,
            n_jobs=-1
        )
        self.random_state = random_state
    
    def _compute_quality_score(self, features_df: pd.DataFrame) -> pd.Series:
        """
        Compute composite quality score from features.
        
        Score components (0-100 scale):
        - Consistency (30%): Low dividend_cv = high score
        - Growth (25%): Positive dividend_growth_yoy = high score
        - History (20%): Long payment_history_days = high score
        - Yield (15%): Reasonable dividend_yield_12m (3-8% optimal)
        - Payout (10%): Sustainable payout_ratio (30-70% optimal)
        
        Args:
            features_df: Feature DataFrame
            
        Returns:
            Series of quality scores (0-100)
        """
        score = pd.Series(0.0, index=features_df.index)
        
        consistency_score = 100 * (1 - np.clip(features_df['dividend_cv'], 0, 1))
        score += 0.30 * consistency_score
        
        growth_score = np.clip(features_df['dividend_growth_yoy'] * 100 + 50, 0, 100)
        score += 0.25 * growth_score
        
        history_score = np.clip(features_df['payment_history_days'] / 365 * 10, 0, 100)
        score += 0.20 * history_score
        
        yield_optimal = np.abs(features_df['dividend_yield_12m'] - 5.5)
        yield_score = 100 * (1 - np.clip(yield_optimal / 10, 0, 1))
        score += 0.15 * yield_score
        
        payout_optimal = np.abs(features_df['payout_ratio'] - 50)
        payout_score = 100 * (1 - np.clip(payout_optimal / 70, 0, 1))
        score += 0.10 * payout_score
        
        return score.clip(0, 100)
    
    def train(self, X: pd.DataFrame, y: pd.Series = None) -> Dict[str, Any]:
        """
        Train the dividend quality scorer.
        
        If y is not provided, computes quality scores from features.
        
        Args:
            X: Feature DataFrame
            y: Optional target quality scores (if None, computed from features)
            
        Returns:
            Dictionary of training metrics
        """
        logger.info(f"Training {self.model_name} with {len(X)} samples...")
        
        if y is None:
            logger.info("Computing quality scores from features...")
            y = self._compute_quality_score(X)
        
        feature_cols = [col for col in X.columns if col != 'Ticker']
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
        Predict dividend quality scores.
        
        Args:
            X: Feature DataFrame
            
        Returns:
            Array of quality scores (0-100)
        """
        if not self.is_trained:
            raise ValueError("Model is not trained yet")
        
        X_data = X[self.feature_names]
        predictions = self.model.predict(X_data)
        
        return np.clip(predictions, 0, 100)
    
    def get_grade(self, score: float) -> str:
        """
        Convert quality score to letter grade.
        
        Args:
            score: Quality score (0-100)
            
        Returns:
            Letter grade (A+ to F)
        """
        if score >= 95:
            return 'A+'
        elif score >= 90:
            return 'A'
        elif score >= 85:
            return 'A-'
        elif score >= 80:
            return 'B+'
        elif score >= 75:
            return 'B'
        elif score >= 70:
            return 'B-'
        elif score >= 65:
            return 'C+'
        elif score >= 60:
            return 'C'
        elif score >= 55:
            return 'C-'
        elif score >= 50:
            return 'D'
        else:
            return 'F'
