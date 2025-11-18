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
            y = X['dividend_growth_yoy'].copy()
        else:
            y = y.copy()
        
        logger.info("=== Data Distribution (BEFORE outlier removal) ===")
        logger.info(f"  Min: {y.min():.4f}")
        logger.info(f"  Max: {y.max():.4f}")
        logger.info(f"  Median: {y.median():.4f}")
        logger.info(f"  Mean: {y.mean():.4f}")
        logger.info(f"  Std: {y.std():.4f}")
        logger.info(f"  25th percentile: {y.quantile(0.25):.4f}")
        logger.info(f"  75th percentile: {y.quantile(0.75):.4f}")
        
        original_count = len(y)
        
        q1 = y.quantile(0.25)
        q3 = y.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        logger.info(f"IQR-based outlier bounds: [{lower_bound:.4f}, {upper_bound:.4f}]")
        
        reasonable_lower = -0.5
        reasonable_upper = 2.0
        
        final_lower = max(lower_bound, reasonable_lower)
        final_upper = min(upper_bound, reasonable_upper)
        
        if final_lower >= final_upper:
            logger.warning(f"Invalid bounds after intersection: [{final_lower:.4f}, {final_upper:.4f}]")
            logger.warning("Falling back to clipping-only approach (no outlier removal)")
            y_clipped = np.clip(y, reasonable_lower, reasonable_upper)
            num_clipped = (y != y_clipped).sum()
            logger.warning(f"Clipped {num_clipped} extreme values ({num_clipped/original_count*100:.1f}% of data)")
            logger.info(f"  Values clipped to [{reasonable_lower:.4f}, {reasonable_upper:.4f}]")
            X_filtered = X.copy()
            y_filtered = y_clipped
            num_outliers_removed = 0
        else:
            logger.info(f"Final outlier removal bounds: [{final_lower:.4f}, {final_upper:.4f}]")
            
            outlier_mask = (y >= final_lower) & (y <= final_upper)
            num_outliers_removed = (~outlier_mask).sum()
            
            if num_outliers_removed > 0:
                if outlier_mask.sum() < 100:
                    logger.warning(f"Outlier removal would leave only {outlier_mask.sum()} samples")
                    logger.warning("Falling back to clipping instead of removing outliers")
                    y_clipped = np.clip(y, final_lower, final_upper)
                    num_clipped = (y != y_clipped).sum()
                    logger.warning(f"Clipped {num_clipped} extreme values instead ({num_clipped/original_count*100:.1f}% of data)")
                    X_filtered = X.copy()
                    y_filtered = y_clipped
                    num_outliers_removed = 0
                else:
                    logger.warning(f"Removing {num_outliers_removed} outliers ({num_outliers_removed/original_count*100:.1f}% of data)")
                    logger.info(f"  Outliers below {final_lower:.4f}: {(y < final_lower).sum()}")
                    logger.info(f"  Outliers above {final_upper:.4f}: {(y > final_upper).sum()}")
                    
                    X_filtered = X[outlier_mask].copy()
                    y_filtered = y[outlier_mask].copy()
            else:
                logger.info("No outliers detected within reasonable bounds")
                X_filtered = X.copy()
                y_filtered = y.copy()
        
        logger.info("=== Data Distribution (AFTER outlier removal) ===")
        logger.info(f"  Samples: {len(y_filtered)} (removed {num_outliers_removed})")
        logger.info(f"  Min: {y_filtered.min():.4f}")
        logger.info(f"  Max: {y_filtered.max():.4f}")
        logger.info(f"  Median: {y_filtered.median():.4f}")
        logger.info(f"  Mean: {y_filtered.mean():.4f}")
        logger.info(f"  Std: {y_filtered.std():.4f}")
        
        feature_cols = [col for col in X_filtered.columns if col not in ['Ticker', 'dividend_growth_yoy']]
        X_train_data = X_filtered[feature_cols]
        self.feature_names = feature_cols
        
        X_train, X_test, y_train, y_test = train_test_split(
            X_train_data, y_filtered, test_size=0.2, random_state=self.random_state
        )
        
        logger.info(f"Training on {len(X_train)} samples, testing on {len(X_test)} samples")
        
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
            self.model, X_train_data, y_filtered, cv=5, scoring='r2', n_jobs=-1
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
            'n_samples': len(X_filtered),
            'n_features': len(feature_cols),
            'outliers_removed': num_outliers_removed,
            'outlier_percentage': num_outliers_removed/original_count*100 if original_count > 0 else 0
        }
        
        if test_r2 < 0:
            logger.warning("=" * 60)
            logger.warning(f"WARNING: Negative R² score ({test_r2:.4f})!")
            logger.warning("Model is performing worse than predicting the mean.")
            logger.warning("This suggests:")
            logger.warning("  1. Features may not be predictive of growth rate")
            logger.warning("  2. More data or better features may be needed")
            logger.warning("  3. Target variable may have too much noise")
            logger.warning("=" * 60)
        
        logger.info(f"Training complete: R² = {test_r2:.4f}, RMSE = {test_rmse:.4f}, MAE = {test_mae:.4f}")
        logger.info(f"Cross-validation R²: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
        
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
