"""
Harvey Intelligence Engine - ML Models

Base model classes and model registry for dividend analysis models.
"""

import os
import joblib
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class BaseModel(ABC):
    """Base class for all Harvey ML models."""
    
    def __init__(self, model_name: str):
        """
        Initialize base model.
        
        Args:
            model_name: Name of the model
        """
        self.model_name = model_name
        self.model = None
        self.is_trained = False
        self.feature_names = []
        self.training_metrics = {}
    
    @abstractmethod
    def train(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """
        Train the model.
        
        Args:
            X: Feature DataFrame
            y: Target Series
            
        Returns:
            Dictionary of training metrics
        """
        pass
    
    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions.
        
        Args:
            X: Feature DataFrame
            
        Returns:
            Array of predictions
        """
        pass
    
    def save(self, save_dir: str) -> str:
        """
        Save trained model to disk.
        
        Args:
            save_dir: Directory to save model
            
        Returns:
            Path to saved model file
        """
        if not self.is_trained:
            raise ValueError(f"Model {self.model_name} is not trained yet")
        
        os.makedirs(save_dir, exist_ok=True)
        model_path = os.path.join(save_dir, f"{self.model_name}.pkl")
        
        model_data = {
            'model': self.model,
            'feature_names': self.feature_names,
            'training_metrics': self.training_metrics,
            'model_name': self.model_name
        }
        
        joblib.dump(model_data, model_path)
        logger.info(f"Model saved to {model_path}")
        return model_path
    
    def load(self, model_path: str):
        """
        Load trained model from disk.
        
        Args:
            model_path: Path to saved model file
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        model_data = joblib.load(model_path)
        
        self.model = model_data['model']
        self.feature_names = model_data['feature_names']
        self.training_metrics = model_data.get('training_metrics', {})
        self.is_trained = True
        
        logger.info(f"Model loaded from {model_path}")
    
    def get_feature_importance(self) -> Optional[pd.DataFrame]:
        """
        Get feature importance if available.
        
        Returns:
            DataFrame with feature importances or None
        """
        if not self.is_trained:
            return None
        
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
            return pd.DataFrame({
                'feature': self.feature_names,
                'importance': importances
            }).sort_values('importance', ascending=False)
        
        return None


class ModelRegistry:
    """Registry for all Harvey ML models."""
    
    _models = {}
    
    @classmethod
    def register(cls, model_class):
        """
        Register a model class.
        
        Args:
            model_class: Model class to register
        """
        cls._models[model_class.__name__] = model_class
        return model_class
    
    @classmethod
    def get_model(cls, model_name: str):
        """
        Get a model class by name.
        
        Args:
            model_name: Name of the model class
            
        Returns:
            Model class
        """
        if model_name not in cls._models:
            raise ValueError(f"Model {model_name} not found in registry")
        return cls._models[model_name]
    
    @classmethod
    def list_models(cls) -> List[str]:
        """
        List all registered model names.
        
        Returns:
            List of model names
        """
        return list(cls._models.keys())


__all__ = ['BaseModel', 'ModelRegistry']
