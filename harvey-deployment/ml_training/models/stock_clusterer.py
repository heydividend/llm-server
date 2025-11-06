"""
Stock Clusterer Model

Uses KMeans clustering to group similar dividend-paying stocks for discovery.
"""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, davies_bouldin_score
from typing import Dict, Any, List
import logging

from . import BaseModel, ModelRegistry

logger = logging.getLogger(__name__)


@ModelRegistry.register
class StockClusterer(BaseModel):
    """
    KMeans clustering model for grouping similar dividend stocks.
    
    Creates 8 clusters based on:
    - Dividend yield characteristics
    - Growth patterns
    - Payout ratios
    - Payment consistency
    - Price volatility
    - Security type (ETF vs Stock)
    
    Enables "stocks like X" discovery and portfolio diversification.
    """
    
    N_CLUSTERS = 8
    
    def __init__(self, n_clusters: int = 8, random_state: int = 42):
        """
        Initialize stock clusterer.
        
        Args:
            n_clusters: Number of clusters to create
            random_state: Random seed for reproducibility
        """
        super().__init__("stock_clusterer")
        self.n_clusters = n_clusters
        self.model = KMeans(
            n_clusters=n_clusters,
            random_state=random_state,
            n_init=10,
            max_iter=300
        )
        self.scaler = StandardScaler()
        self.random_state = random_state
        self.cluster_profiles = {}
    
    def train(self, X: pd.DataFrame, y: pd.Series = None) -> Dict[str, Any]:
        """
        Train the stock clusterer.
        
        Note: KMeans is unsupervised, so y is not used.
        
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
        
        X_scaled = self.scaler.fit_transform(X_train_data)
        
        self.model.fit(X_scaled)
        self.is_trained = True
        
        labels = self.model.labels_
        
        silhouette = silhouette_score(X_scaled, labels)
        davies_bouldin = davies_bouldin_score(X_scaled, labels)
        
        cluster_sizes = pd.Series(labels).value_counts().sort_index()
        
        self._compute_cluster_profiles(X, labels)
        
        self.training_metrics = {
            'n_clusters': self.n_clusters,
            'silhouette_score': silhouette,
            'davies_bouldin_score': davies_bouldin,
            'cluster_sizes': dict(cluster_sizes),
            'n_samples': len(X),
            'n_features': len(feature_cols)
        }
        
        logger.info(f"Training complete: Silhouette = {silhouette:.4f}")
        logger.info(f"Cluster sizes: {dict(cluster_sizes)}")
        return self.training_metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict cluster assignments.
        
        Args:
            X: Feature DataFrame
            
        Returns:
            Array of cluster labels (0 to n_clusters-1)
        """
        if not self.is_trained:
            raise ValueError("Model is not trained yet")
        
        X_data = X[self.feature_names]
        X_scaled = self.scaler.transform(X_data)
        return self.model.predict(X_scaled)
    
    def _compute_cluster_profiles(self, X: pd.DataFrame, labels: np.ndarray):
        """
        Compute characteristic profiles for each cluster.
        
        Args:
            X: Feature DataFrame
            labels: Cluster labels
        """
        X_with_labels = X.copy()
        X_with_labels['cluster'] = labels
        
        for cluster_id in range(self.n_clusters):
            cluster_data = X_with_labels[X_with_labels['cluster'] == cluster_id]
            
            if len(cluster_data) == 0:
                continue
            
            profile = {
                'size': len(cluster_data),
                'avg_yield': cluster_data.get('dividend_yield_12m', pd.Series([0])).mean(),
                'avg_growth': cluster_data.get('dividend_growth_yoy', pd.Series([0])).mean(),
                'avg_payout': cluster_data.get('payout_ratio', pd.Series([0])).mean(),
                'avg_cv': cluster_data.get('dividend_cv', pd.Series([0])).mean(),
                'avg_volatility': cluster_data.get('price_volatility', pd.Series([0])).mean()
            }
            
            self.cluster_profiles[cluster_id] = profile
    
    def get_cluster_profile(self, cluster_id: int) -> Dict[str, Any]:
        """
        Get profile for a specific cluster.
        
        Args:
            cluster_id: Cluster ID (0 to n_clusters-1)
            
        Returns:
            Dictionary with cluster characteristics
        """
        if cluster_id not in self.cluster_profiles:
            raise ValueError(f"Cluster {cluster_id} not found")
        
        return self.cluster_profiles[cluster_id]
    
    def find_similar_stocks(self, 
                          X: pd.DataFrame, 
                          ticker: str, 
                          n_similar: int = 5) -> List[str]:
        """
        Find stocks similar to a given ticker.
        
        Args:
            X: Feature DataFrame with Ticker column
            ticker: Ticker symbol to find similar stocks for
            n_similar: Number of similar stocks to return
            
        Returns:
            List of similar ticker symbols
        """
        if 'Ticker' not in X.columns:
            raise ValueError("X must contain a 'Ticker' column")
        
        if ticker not in X['Ticker'].values:
            raise ValueError(f"Ticker {ticker} not found in data")
        
        clusters = self.predict(X)
        X_with_clusters = X.copy()
        X_with_clusters['cluster'] = clusters
        
        target_cluster = X_with_clusters[X_with_clusters['Ticker'] == ticker]['cluster'].iloc[0]
        
        same_cluster = X_with_clusters[
            (X_with_clusters['cluster'] == target_cluster) & 
            (X_with_clusters['Ticker'] != ticker)
        ]
        
        if len(same_cluster) == 0:
            return []
        
        target_features = X[X['Ticker'] == ticker][self.feature_names].iloc[0]
        
        distances = same_cluster[self.feature_names].apply(
            lambda row: np.sqrt(((row - target_features) ** 2).sum()),
            axis=1
        )
        
        similar_indices = distances.nsmallest(n_similar).index
        similar_tickers = same_cluster.loc[similar_indices, 'Ticker'].tolist()
        
        return similar_tickers
    
    def get_cluster_summary(self) -> pd.DataFrame:
        """
        Get summary statistics for all clusters.
        
        Returns:
            DataFrame with cluster profiles
        """
        if not self.cluster_profiles:
            return pd.DataFrame()
        
        return pd.DataFrame(self.cluster_profiles).T
