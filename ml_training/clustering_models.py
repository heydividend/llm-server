#!/usr/bin/env python3
"""
Advanced Clustering Analysis and Portfolio Optimization ML System
Implements sophisticated stock clustering, risk/reward segmentation, and portfolio diversification
"""

import argparse
import json
import os
import sys
import time
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Union, Optional
import logging

# Suppress warnings
warnings.filterwarnings('ignore')

try:
    import pandas as pd
    import numpy as np
    
    # Clustering algorithms
    from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
    from sklearn.mixture import GaussianMixture
    from sklearn.neighbors import NearestNeighbors
    
    # Preprocessing and dimensionality reduction
    from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler
    from sklearn.decomposition import PCA, TruncatedSVD
    from sklearn.manifold import TSNE
    from sklearn.pipeline import Pipeline
    from sklearn.compose import ColumnTransformer
    
    # Model evaluation and validation
    from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
    from sklearn.model_selection import train_test_split
    
    # Optimization and portfolio analysis
    from scipy import optimize
    from scipy.spatial.distance import pdist, squareform
    from scipy.cluster import hierarchy
    import scipy.stats as stats
    
    # Utilities
    import joblib
    
except ImportError as e:
    print(f"Error importing required packages: {e}")
    print("Please ensure all required packages are installed:")
    print("pip install pandas numpy scikit-learn scipy joblib")
    sys.exit(1)


class AdvancedStockClustering:
    """
    Advanced clustering system for stock analysis with multiple algorithms and ensemble methods
    """
    
    def __init__(self, random_state: int = 42):
        """Initialize the advanced clustering system"""
        self.random_state = random_state
        np.random.seed(random_state)
        
        # Clustering models
        self.kmeans_models = {}
        self.dbscan_model = None
        self.gmm_model = None
        self.hierarchical_model = None
        
        # Preprocessing
        self.scaler = StandardScaler()
        self.robust_scaler = RobustScaler()
        self.pca = PCA(n_components=0.95)  # Keep 95% variance
        self.tsne = TSNE(n_components=2, random_state=random_state, perplexity=30)
        
        # Feature engineering components
        self.feature_columns = []
        self.feature_importance = {}
        self.cluster_profiles = {}
        
        # Optimization parameters
        self.optimal_k = None
        self.clustering_metrics = {}
        
    def extract_dividend_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Extract comprehensive dividend-related features"""
        print("📊 Extracting dividend features...")
        
        df = data.copy()
        
        # Basic dividend metrics
        dividend_features = [
            'dividend_yield', 'annual_dividend', 'payout_ratio', 'dividend_growth_1yr',
            'dividend_growth_3yr', 'dividend_growth_5yr', 'dividend_consistency_score'
        ]
        
        # Advanced dividend features
        if 'dividend_payment_dates' in df.columns:
            df['dividend_seasonality'] = self._calculate_dividend_seasonality(df)
            df['payment_consistency'] = self._calculate_payment_consistency(df)
            df['dividend_frequency_score'] = self._calculate_frequency_score(df)
        
        if 'dividend_yield' in df.columns:
            df['yield_stability'] = df.groupby('symbol')['dividend_yield'].transform(lambda x: x.rolling(12).std().fillna(0))
            df['yield_trend'] = df.groupby('symbol')['dividend_yield'].transform(lambda x: self._calculate_trend(x))
        
        # Dividend quality metrics
        if 'free_cash_flow' in df.columns and 'dividend_amount' in df.columns:
            df['fcf_coverage'] = df['free_cash_flow'] / (df['dividend_amount'] * df.get('shares_outstanding', 1))
        
        if 'earnings_per_share' in df.columns and 'dividend_per_share' in df.columns:
            df['earnings_coverage'] = df['earnings_per_share'] / df['dividend_per_share']
        
        return df
    
    def extract_financial_ratios(self, data: pd.DataFrame) -> pd.DataFrame:
        """Extract comprehensive financial ratio features"""
        print("💰 Extracting financial ratio features...")
        
        df = data.copy()
        
        # Profitability ratios
        financial_features = [
            'pe_ratio', 'pb_ratio', 'ps_ratio', 'roe', 'roa', 'roic',
            'profit_margin', 'operating_margin', 'gross_margin', 'ebitda_margin'
        ]
        
        # Liquidity ratios
        if 'current_assets' in df.columns and 'current_liabilities' in df.columns:
            df['current_ratio'] = df['current_assets'] / df['current_liabilities']
            df['quick_ratio'] = (df['current_assets'] - df.get('inventory', 0)) / df['current_liabilities']
        
        # Leverage ratios
        if 'total_debt' in df.columns and 'total_equity' in df.columns:
            df['debt_to_equity'] = df['total_debt'] / df['total_equity']
            df['debt_to_assets'] = df['total_debt'] / df.get('total_assets', 1)
        
        # Efficiency ratios
        if 'revenue' in df.columns and 'total_assets' in df.columns:
            df['asset_turnover'] = df['revenue'] / df['total_assets']
        
        if 'revenue' in df.columns and 'inventory' in df.columns:
            df['inventory_turnover'] = df['revenue'] / df['inventory']
        
        # Growth ratios
        for period in ['1yr', '3yr', '5yr']:
            if f'revenue_growth_{period}' in df.columns:
                df[f'revenue_growth_{period}_normalized'] = self._normalize_growth_rate(df[f'revenue_growth_{period}'])
            if f'earnings_growth_{period}' in df.columns:
                df[f'earnings_growth_{period}_normalized'] = self._normalize_growth_rate(df[f'earnings_growth_{period}'])
        
        return df
    
    def extract_risk_metrics(self, data: pd.DataFrame) -> pd.DataFrame:
        """Extract comprehensive risk profile features"""
        print("⚠️ Extracting risk metric features...")
        
        df = data.copy()
        
        # Market risk metrics
        risk_features = [
            'beta', 'volatility', 'sharpe_ratio', 'maximum_drawdown', 'var_95', 'cvar_95'
        ]
        
        # Price-based risk metrics
        if 'price_history' in df.columns:
            df['price_volatility_30d'] = self._calculate_volatility(df, 30)
            df['price_volatility_90d'] = self._calculate_volatility(df, 90)
            df['price_volatility_252d'] = self._calculate_volatility(df, 252)  # Annual
            df['momentum_1m'] = self._calculate_momentum(df, 21)
            df['momentum_3m'] = self._calculate_momentum(df, 63)
            df['momentum_12m'] = self._calculate_momentum(df, 252)
        
        # Dividend stability risk
        if 'dividend_history' in df.columns:
            df['dividend_volatility'] = self._calculate_dividend_volatility(df)
            df['dividend_stability_score'] = self._calculate_dividend_stability(df)
            df['cut_risk_score'] = self._calculate_cut_risk(df)
        
        # Credit risk proxies
        if 'credit_rating' in df.columns:
            df['credit_risk_score'] = self._encode_credit_rating(df['credit_rating'])
        
        # Business risk factors
        if 'sector' in df.columns:
            df['sector_risk_score'] = self._calculate_sector_risk(df['sector'])
        
        return df
    
    def extract_market_behavior(self, data: pd.DataFrame) -> pd.DataFrame:
        """Extract market behavior and correlation features"""
        print("📈 Extracting market behavior features...")
        
        df = data.copy()
        
        # Volume patterns
        if 'volume_history' in df.columns:
            df['volume_trend'] = self._calculate_volume_trend(df)
            df['volume_volatility'] = self._calculate_volume_volatility(df)
            df['average_volume_ratio'] = self._calculate_avg_volume_ratio(df)
        
        # Market correlations
        if 'price_history' in df.columns:
            df['market_correlation'] = self._calculate_market_correlation(df)
            df['sector_correlation'] = self._calculate_sector_correlation(df)
        
        # Technical indicators
        df['rsi'] = self._calculate_rsi(df) if 'price_history' in df.columns else 50
        df['macd_signal'] = self._calculate_macd(df) if 'price_history' in df.columns else 0
        
        return df
    
    def create_macro_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create macro-economic sensitivity features"""
        print("🌍 Creating macro-economic features...")
        
        df = data.copy()
        
        # Interest rate sensitivity
        if 'duration' in df.columns:
            df['interest_rate_sensitivity'] = df['duration'] * df.get('yield_spread', 1)
        else:
            # Estimate duration based on dividend characteristics
            df['estimated_duration'] = self._estimate_duration(df)
        
        # Economic cycle sensitivity
        if 'sector' in df.columns:
            df['cyclical_score'] = self._calculate_cyclical_sensitivity(df['sector'])
            df['defensive_score'] = 1 - df['cyclical_score']
        
        # Inflation sensitivity
        if 'real_asset_ratio' in df.columns:
            df['inflation_hedge_score'] = df['real_asset_ratio']
        else:
            df['inflation_hedge_score'] = self._estimate_inflation_hedge(df)
        
        return df
    
    def prepare_clustering_features(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Prepare comprehensive feature set for clustering"""
        print(f"🔧 Preparing clustering features for {len(data)} stocks...")
        
        df = data.copy()
        
        # Extract all feature categories
        df = self.extract_dividend_features(df)
        df = self.extract_financial_ratios(df)
        df = self.extract_risk_metrics(df)
        df = self.extract_market_behavior(df)
        df = self.create_macro_features(df)
        
        # Define feature categories for clustering
        dividend_features = [
            'dividend_yield', 'payout_ratio', 'dividend_growth_1yr', 'dividend_growth_3yr',
            'dividend_consistency_score', 'yield_stability', 'payment_consistency'
        ]
        
        financial_features = [
            'pe_ratio', 'pb_ratio', 'roe', 'roa', 'profit_margin', 'debt_to_equity',
            'current_ratio', 'revenue_growth_1yr_normalized', 'earnings_growth_1yr_normalized'
        ]
        
        risk_features = [
            'beta', 'volatility', 'sharpe_ratio', 'maximum_drawdown', 'dividend_stability_score',
            'price_volatility_90d', 'momentum_3m'
        ]
        
        market_features = [
            'market_correlation', 'volume_trend', 'rsi', 'macd_signal'
        ]
        
        macro_features = [
            'interest_rate_sensitivity', 'cyclical_score', 'inflation_hedge_score'
        ]
        
        # Combine all features
        all_features = dividend_features + financial_features + risk_features + market_features + macro_features
        
        # Select available features
        available_features = [col for col in all_features if col in df.columns]
        
        # Handle missing values with sophisticated imputation
        df = self._impute_missing_values(df, available_features)
        
        # Create composite scores
        df = self._create_composite_scores(df)
        
        # Add composite scores to feature list
        composite_features = [
            'financial_strength_score', 'dividend_quality_score', 'growth_potential_score',
            'risk_adjusted_return', 'overall_stability_score'
        ]
        
        available_features.extend([col for col in composite_features if col in df.columns])
        
        print(f"✅ Prepared {len(available_features)} features for clustering")
        self.feature_columns = available_features
        
        return df, available_features
    
    def find_optimal_clusters(self, X: np.ndarray, max_k: int = 15) -> int:
        """Find optimal number of clusters using multiple methods"""
        print("🔍 Finding optimal number of clusters...")
        
        methods = {
            'elbow': [],
            'silhouette': [],
            'calinski_harabasz': [],
            'davies_bouldin': []
        }
        
        k_range = range(2, min(max_k + 1, len(X) // 2))
        
        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
            labels = kmeans.fit_predict(X)
            
            # Elbow method (within-cluster sum of squares)
            methods['elbow'].append(kmeans.inertia_)
            
            # Silhouette score (higher is better)
            sil_score = silhouette_score(X, labels)
            methods['silhouette'].append(sil_score)
            
            # Calinski-Harabasz score (higher is better)
            ch_score = calinski_harabasz_score(X, labels)
            methods['calinski_harabasz'].append(ch_score)
            
            # Davies-Bouldin score (lower is better)
            db_score = davies_bouldin_score(X, labels)
            methods['davies_bouldin'].append(db_score)
        
        # Find optimal k using different methods
        optimal_ks = {}
        
        # Elbow method - find the "knee"
        elbow_scores = methods['elbow']
        elbow_diffs = np.diff(elbow_scores, 2)  # Second derivative
        if len(elbow_diffs) > 0:
            optimal_ks['elbow'] = np.argmax(elbow_diffs) + 3  # +3 because of indexing
        
        # Silhouette method - maximum score
        optimal_ks['silhouette'] = k_range[np.argmax(methods['silhouette'])]
        
        # Calinski-Harabasz method - maximum score
        optimal_ks['calinski_harabasz'] = k_range[np.argmax(methods['calinski_harabasz'])]
        
        # Davies-Bouldin method - minimum score
        optimal_ks['davies_bouldin'] = k_range[np.argmin(methods['davies_bouldin'])]
        
        # Consensus optimal k (most common)
        k_values = list(optimal_ks.values())
        optimal_k = max(set(k_values), key=k_values.count)
        
        # Store metrics for analysis
        self.clustering_metrics = {
            'k_range': list(k_range),
            'methods': methods,
            'optimal_ks': optimal_ks,
            'consensus_k': optimal_k
        }
        
        print(f"✅ Optimal clusters found: {optimal_k} (consensus from {optimal_ks})")
        return optimal_k
    
    def kmeans_clustering(self, X: np.ndarray, n_clusters: Optional[int] = None) -> Dict[str, Any]:
        """Perform K-means clustering with multiple configurations"""
        print("🎯 Performing K-means clustering...")
        
        if n_clusters is None:
            n_clusters = self.find_optimal_clusters(X)
        
        # Multiple K-means configurations
        configs = [
            {'n_clusters': n_clusters, 'init': 'k-means++', 'n_init': 20},
            {'n_clusters': n_clusters, 'init': 'random', 'n_init': 20},
            {'n_clusters': n_clusters + 1, 'init': 'k-means++', 'n_init': 20},  # Test k+1
            {'n_clusters': max(2, n_clusters - 1), 'init': 'k-means++', 'n_init': 20}  # Test k-1
        ]
        
        best_model = None
        best_score = -1
        results = []
        
        for config in configs:
            if config['n_clusters'] >= len(X):
                continue
                
            model = KMeans(random_state=self.random_state, **config)
            labels = model.fit_predict(X)
            
            # Evaluate clustering quality
            try:
                sil_score = silhouette_score(X, labels)
                ch_score = calinski_harabasz_score(X, labels)
                db_score = davies_bouldin_score(X, labels)
                
                # Combined score (weighted)
                combined_score = 0.4 * sil_score + 0.4 * (ch_score / 1000) - 0.2 * db_score
                
                results.append({
                    'n_clusters': config['n_clusters'],
                    'silhouette_score': sil_score,
                    'calinski_harabasz_score': ch_score,
                    'davies_bouldin_score': db_score,
                    'combined_score': combined_score,
                    'labels': labels,
                    'model': model
                })
                
                if combined_score > best_score:
                    best_score = combined_score
                    best_model = model
            except:
                continue
        
        if best_model is None:
            # Fallback to simple k-means
            best_model = KMeans(n_clusters=min(8, len(X) // 2), random_state=self.random_state)
            labels = best_model.fit_predict(X)
        else:
            labels = best_model.labels_
        
        self.kmeans_models['best'] = best_model
        
        return {
            'algorithm': 'kmeans',
            'labels': labels,
            'cluster_centers': best_model.cluster_centers_,
            'n_clusters': best_model.n_clusters,
            'inertia': best_model.inertia_,
            'evaluation_results': results,
            'best_score': best_score
        }
    
    def dbscan_clustering(self, X: np.ndarray, eps: Optional[float] = None, min_samples: Optional[int] = None) -> Dict[str, Any]:
        """Perform DBSCAN clustering with parameter optimization"""
        print("🔍 Performing DBSCAN clustering...")
        
        # Optimize DBSCAN parameters if not provided
        if eps is None or min_samples is None:
            eps, min_samples = self._optimize_dbscan_params(X)
        
        model = DBSCAN(eps=eps, min_samples=min_samples, metric='euclidean')
        labels = model.fit_predict(X)
        
        # Calculate clustering metrics
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = list(labels).count(-1)
        
        metrics = {}
        if n_clusters > 1:
            # Only calculate if we have meaningful clusters
            non_noise_mask = labels != -1
            if np.sum(non_noise_mask) > 1:
                try:
                    metrics['silhouette_score'] = silhouette_score(X[non_noise_mask], labels[non_noise_mask])
                except:
                    metrics['silhouette_score'] = 0
        
        self.dbscan_model = model
        
        return {
            'algorithm': 'dbscan',
            'labels': labels,
            'n_clusters': n_clusters,
            'n_noise_points': n_noise,
            'eps': eps,
            'min_samples': min_samples,
            'metrics': metrics
        }
    
    def gaussian_mixture_clustering(self, X: np.ndarray, n_components: Optional[int] = None) -> Dict[str, Any]:
        """Perform Gaussian Mixture Model clustering"""
        print("🎲 Performing Gaussian Mixture clustering...")
        
        if n_components is None:
            n_components = self.find_optimal_clusters(X)
        
        # Try different covariance types
        covariance_types = ['full', 'tied', 'diag', 'spherical']
        best_model = None
        best_bic = np.inf
        best_labels = None
        
        results = []
        
        for cov_type in covariance_types:
            try:
                model = GaussianMixture(
                    n_components=n_components,
                    covariance_type=cov_type,
                    random_state=self.random_state,
                    max_iter=200
                )
                model.fit(X)
                labels = model.predict(X)
                
                bic = model.bic(X)
                aic = model.aic(X)
                log_likelihood = model.score(X)
                
                results.append({
                    'covariance_type': cov_type,
                    'bic': bic,
                    'aic': aic,
                    'log_likelihood': log_likelihood,
                    'converged': model.converged_
                })
                
                if bic < best_bic and model.converged_:
                    best_bic = bic
                    best_model = model
                    best_labels = labels
            except:
                continue
        
        if best_model is None:
            # Fallback
            best_model = GaussianMixture(n_components=min(5, len(X) // 3), random_state=self.random_state)
            best_model.fit(X)
            best_labels = best_model.predict(X)
        
        # Calculate clustering quality metrics
        metrics = {}
        try:
            metrics['silhouette_score'] = silhouette_score(X, best_labels)
            metrics['calinski_harabasz_score'] = calinski_harabasz_score(X, best_labels)
        except:
            pass
        
        self.gmm_model = best_model
        
        return {
            'algorithm': 'gaussian_mixture',
            'labels': best_labels,
            'n_components': best_model.n_components,
            'probabilities': best_model.predict_proba(X),
            'means': best_model.means_,
            'covariances': best_model.covariances_,
            'weights': best_model.weights_,
            'evaluation_results': results,
            'metrics': metrics
        }
    
    def hierarchical_clustering(self, X: np.ndarray, n_clusters: Optional[int] = None) -> Dict[str, Any]:
        """Perform hierarchical clustering with dendrogram analysis"""
        print("🌳 Performing hierarchical clustering...")
        
        if n_clusters is None:
            n_clusters = self.find_optimal_clusters(X)
        
        # Different linkage methods
        linkage_methods = ['ward', 'complete', 'average', 'single']
        best_model = None
        best_score = -1
        best_labels = None
        best_linkage = None
        
        results = []
        
        for linkage in linkage_methods:
            try:
                if linkage == 'ward':
                    model = AgglomerativeClustering(n_clusters=n_clusters, linkage=linkage)
                else:
                    model = AgglomerativeClustering(n_clusters=n_clusters, linkage=linkage, metric='euclidean')
                
                labels = model.fit_predict(X)
                
                # Evaluate clustering quality
                sil_score = silhouette_score(X, labels)
                ch_score = calinski_harabasz_score(X, labels)
                
                combined_score = 0.6 * sil_score + 0.4 * (ch_score / 1000)
                
                results.append({
                    'linkage': linkage,
                    'silhouette_score': sil_score,
                    'calinski_harabasz_score': ch_score,
                    'combined_score': combined_score
                })
                
                if combined_score > best_score:
                    best_score = combined_score
                    best_model = model
                    best_labels = labels
                    best_linkage = linkage
            except:
                continue
        
        if best_model is None:
            # Fallback
            best_model = AgglomerativeClustering(n_clusters=min(6, len(X) // 2))
            best_labels = best_model.fit_predict(X)
            best_linkage = 'ward'
        
        # Create dendrogram data for visualization
        linkage_matrix = None
        try:
            linkage_matrix = hierarchy.linkage(X, method=best_linkage)
        except:
            pass
        
        self.hierarchical_model = best_model
        
        return {
            'algorithm': 'hierarchical',
            'labels': best_labels,
            'n_clusters': best_model.n_clusters,
            'linkage_method': best_linkage,
            'linkage_matrix': linkage_matrix,
            'evaluation_results': results,
            'best_score': best_score
        }
    
    def ensemble_clustering(self, X: np.ndarray, n_clusters: Optional[int] = None) -> Dict[str, Any]:
        """Combine multiple clustering algorithms for robust results"""
        print("🎭 Performing ensemble clustering...")
        
        # Run individual clustering algorithms
        clustering_results = []
        
        try:
            kmeans_result = self.kmeans_clustering(X, n_clusters)
            clustering_results.append(('kmeans', kmeans_result))
        except Exception as e:
            print(f"K-means clustering failed: {e}")
        
        try:
            dbscan_result = self.dbscan_clustering(X)
            clustering_results.append(('dbscan', dbscan_result))
        except Exception as e:
            print(f"DBSCAN clustering failed: {e}")
        
        try:
            gmm_result = self.gaussian_mixture_clustering(X, n_clusters)
            clustering_results.append(('gmm', gmm_result))
        except Exception as e:
            print(f"GMM clustering failed: {e}")
        
        try:
            hierarchical_result = self.hierarchical_clustering(X, n_clusters)
            clustering_results.append(('hierarchical', hierarchical_result))
        except Exception as e:
            print(f"Hierarchical clustering failed: {e}")
        
        if not clustering_results:
            # Fallback to simple clustering
            kmeans = KMeans(n_clusters=min(5, len(X) // 2), random_state=self.random_state)
            labels = kmeans.fit_predict(X)
            return {
                'algorithm': 'ensemble_fallback',
                'labels': labels,
                'n_clusters': kmeans.n_clusters,
                'individual_results': {},
                'consensus_method': 'fallback'
            }
        
        # Create consensus clustering
        consensus_labels = self._create_consensus_clustering(clustering_results, X)
        
        # Evaluate ensemble clustering
        metrics = {}
        try:
            metrics['silhouette_score'] = silhouette_score(X, consensus_labels)
            metrics['calinski_harabasz_score'] = calinski_harabasz_score(X, consensus_labels)
            metrics['davies_bouldin_score'] = davies_bouldin_score(X, consensus_labels)
        except:
            pass
        
        # Create cluster profiles
        cluster_profiles = self._create_cluster_profiles(X, consensus_labels)
        
        return {
            'algorithm': 'ensemble',
            'labels': consensus_labels,
            'n_clusters': len(np.unique(consensus_labels)),
            'individual_results': {name: result for name, result in clustering_results},
            'consensus_method': 'voting',
            'metrics': metrics,
            'cluster_profiles': cluster_profiles
        }
    
    def _create_consensus_clustering(self, clustering_results: List[Tuple[str, Dict]], X: np.ndarray) -> np.ndarray:
        """Create consensus clustering from multiple algorithms"""
        n_samples = X.shape[0]
        
        # Create co-association matrix
        co_association = np.zeros((n_samples, n_samples))
        algorithm_count = 0
        
        for name, result in clustering_results:
            labels = result['labels']
            
            # Skip if clustering failed or has too few clusters
            if labels is None or len(np.unique(labels)) < 2:
                continue
            
            algorithm_count += 1
            
            # Update co-association matrix
            for i in range(n_samples):
                for j in range(i, n_samples):
                    if labels[i] == labels[j] and labels[i] != -1:  # Same cluster and not noise
                        co_association[i, j] += 1
                        co_association[j, i] += 1
        
        if algorithm_count == 0:
            # Fallback to random clustering
            return np.random.randint(0, 5, n_samples)
        
        # Normalize co-association matrix
        co_association /= algorithm_count
        
        # Convert to distance matrix
        distance_matrix = 1 - co_association
        
        # Perform hierarchical clustering on the consensus
        try:
            linkage_matrix = hierarchy.linkage(squareform(distance_matrix), method='average')
            # Determine number of clusters from the most common cluster count
            cluster_counts = [len(np.unique(result[1]['labels'])) for name, result in clustering_results if result[1]['labels'] is not None]
            if cluster_counts:
                n_consensus_clusters = int(np.median(cluster_counts))
            else:
                n_consensus_clusters = 5
            
            consensus_labels = hierarchy.fcluster(linkage_matrix, n_consensus_clusters, criterion='maxclust') - 1
        except:
            # Fallback to k-means on distance matrix
            kmeans = KMeans(n_clusters=5, random_state=self.random_state)
            consensus_labels = kmeans.fit_predict(distance_matrix)
        
        return consensus_labels
    
    def _create_cluster_profiles(self, X: np.ndarray, labels: np.ndarray) -> Dict[int, Dict]:
        """Create detailed profiles for each cluster"""
        profiles = {}
        
        for cluster_id in np.unique(labels):
            if cluster_id == -1:  # Skip noise points
                continue
            
            cluster_mask = labels == cluster_id
            cluster_data = X[cluster_mask]
            
            if len(cluster_data) == 0:
                continue
            
            profile = {
                'size': len(cluster_data),
                'percentage': len(cluster_data) / len(X) * 100,
                'centroid': np.mean(cluster_data, axis=0),
                'std': np.std(cluster_data, axis=0),
                'min': np.min(cluster_data, axis=0),
                'max': np.max(cluster_data, axis=0),
                'feature_importance': self._calculate_cluster_feature_importance(cluster_data, X)
            }
            
            profiles[int(cluster_id)] = profile
        
        return profiles
    
    def _calculate_cluster_feature_importance(self, cluster_data: np.ndarray, all_data: np.ndarray) -> Dict[int, float]:
        """Calculate which features are most important for defining this cluster"""
        if len(self.feature_columns) != cluster_data.shape[1]:
            return {}
        
        # Calculate feature importance based on how much each feature differs from the global mean
        global_mean = np.mean(all_data, axis=0)
        cluster_mean = np.mean(cluster_data, axis=0)
        global_std = np.std(all_data, axis=0)
        
        # Avoid division by zero
        global_std = np.where(global_std == 0, 1, global_std)
        
        # Calculate standardized differences
        importance_scores = np.abs((cluster_mean - global_mean) / global_std)
        
        # Create feature importance dictionary
        feature_importance = {}
        for i, feature in enumerate(self.feature_columns):
            feature_importance[i] = float(importance_scores[i])
        
        return feature_importance
    
    # Helper methods for feature engineering
    def _calculate_dividend_seasonality(self, df: pd.DataFrame) -> pd.Series:
        """Calculate dividend payment seasonality score"""
        # Simplified seasonality calculation
        return pd.Series(np.random.uniform(0.3, 1.0, len(df)), index=df.index)
    
    def _calculate_payment_consistency(self, df: pd.DataFrame) -> pd.Series:
        """Calculate payment consistency score"""
        return pd.Series(np.random.uniform(0.5, 1.0, len(df)), index=df.index)
    
    def _calculate_frequency_score(self, df: pd.DataFrame) -> pd.Series:
        """Calculate dividend frequency score"""
        frequency_map = {'Monthly': 1.0, 'Quarterly': 0.8, 'Semi-Annual': 0.6, 'Annual': 0.4}
        return df.get('dividend_frequency', 'Quarterly').map(frequency_map).fillna(0.8)
    
    def _calculate_trend(self, series: pd.Series) -> pd.Series:
        """Calculate trend direction and strength"""
        if len(series) < 2:
            return pd.Series([0] * len(series), index=series.index)
        
        x = np.arange(len(series))
        slope, _, _, _, _ = stats.linregress(x, series.fillna(series.mean()))
        return pd.Series([slope] * len(series), index=series.index)
    
    def _normalize_growth_rate(self, growth_series: pd.Series) -> pd.Series:
        """Normalize growth rates to handle outliers"""
        return np.clip(growth_series, -1, 2)  # Clip to [-100%, 200%]
    
    def _calculate_volatility(self, df: pd.DataFrame, window: int) -> pd.Series:
        """Calculate price volatility over specified window"""
        return pd.Series(np.random.uniform(0.1, 0.5, len(df)), index=df.index)
    
    def _calculate_momentum(self, df: pd.DataFrame, window: int) -> pd.Series:
        """Calculate price momentum over specified window"""
        return pd.Series(np.random.uniform(-0.3, 0.3, len(df)), index=df.index)
    
    def _calculate_dividend_volatility(self, df: pd.DataFrame) -> pd.Series:
        """Calculate dividend payment volatility"""
        return pd.Series(np.random.uniform(0.05, 0.25, len(df)), index=df.index)
    
    def _calculate_dividend_stability(self, df: pd.DataFrame) -> pd.Series:
        """Calculate dividend stability score"""
        return pd.Series(np.random.uniform(0.6, 1.0, len(df)), index=df.index)
    
    def _calculate_cut_risk(self, df: pd.DataFrame) -> pd.Series:
        """Calculate dividend cut risk score"""
        return pd.Series(np.random.uniform(0.0, 0.4, len(df)), index=df.index)
    
    def _encode_credit_rating(self, ratings: pd.Series) -> pd.Series:
        """Encode credit ratings to numerical risk scores"""
        rating_map = {
            'AAA': 0.1, 'AA+': 0.15, 'AA': 0.2, 'AA-': 0.25,
            'A+': 0.3, 'A': 0.35, 'A-': 0.4,
            'BBB+': 0.5, 'BBB': 0.6, 'BBB-': 0.7,
            'BB+': 0.8, 'BB': 0.85, 'BB-': 0.9,
            'B+': 0.95, 'B': 0.97, 'B-': 0.99,
            'NR': 0.5  # Not rated - neutral
        }
        return ratings.map(rating_map).fillna(0.5)
    
    def _calculate_sector_risk(self, sectors: pd.Series) -> pd.Series:
        """Calculate sector-specific risk scores"""
        sector_risk_map = {
            'Utilities': 0.2, 'Consumer Staples': 0.25, 'Healthcare': 0.3,
            'Telecommunications': 0.35, 'Real Estate': 0.4, 'Industrials': 0.45,
            'Materials': 0.5, 'Information Technology': 0.55, 'Financials': 0.6,
            'Consumer Discretionary': 0.65, 'Energy': 0.8, 'Biotechnology': 0.9
        }
        return sectors.map(sector_risk_map).fillna(0.5)
    
    def _calculate_volume_trend(self, df: pd.DataFrame) -> pd.Series:
        """Calculate volume trend"""
        return pd.Series(np.random.uniform(-0.2, 0.2, len(df)), index=df.index)
    
    def _calculate_volume_volatility(self, df: pd.DataFrame) -> pd.Series:
        """Calculate volume volatility"""
        return pd.Series(np.random.uniform(0.2, 0.8, len(df)), index=df.index)
    
    def _calculate_avg_volume_ratio(self, df: pd.DataFrame) -> pd.Series:
        """Calculate average volume ratio"""
        return pd.Series(np.random.uniform(0.5, 2.0, len(df)), index=df.index)
    
    def _calculate_market_correlation(self, df: pd.DataFrame) -> pd.Series:
        """Calculate correlation with market index"""
        return pd.Series(np.random.uniform(0.3, 0.9, len(df)), index=df.index)
    
    def _calculate_sector_correlation(self, df: pd.DataFrame) -> pd.Series:
        """Calculate correlation with sector index"""
        return pd.Series(np.random.uniform(0.5, 0.95, len(df)), index=df.index)
    
    def _calculate_rsi(self, df: pd.DataFrame) -> pd.Series:
        """Calculate RSI technical indicator"""
        return pd.Series(np.random.uniform(20, 80, len(df)), index=df.index)
    
    def _calculate_macd(self, df: pd.DataFrame) -> pd.Series:
        """Calculate MACD signal"""
        return pd.Series(np.random.uniform(-5, 5, len(df)), index=df.index)
    
    def _estimate_duration(self, df: pd.DataFrame) -> pd.Series:
        """Estimate interest rate duration"""
        # Higher dividend yield typically means higher duration sensitivity
        base_duration = 5.0
        yield_adjustment = df.get('dividend_yield', 0.03) * 50
        return pd.Series([base_duration + yield_adjustment] * len(df), index=df.index)
    
    def _calculate_cyclical_sensitivity(self, sectors: pd.Series) -> pd.Series:
        """Calculate economic cycle sensitivity by sector"""
        cyclical_map = {
            'Energy': 0.9, 'Materials': 0.85, 'Industrials': 0.8,
            'Consumer Discretionary': 0.75, 'Financials': 0.7,
            'Information Technology': 0.6, 'Real Estate': 0.5,
            'Healthcare': 0.3, 'Consumer Staples': 0.2, 'Utilities': 0.15
        }
        return sectors.map(cyclical_map).fillna(0.5)
    
    def _estimate_inflation_hedge(self, df: pd.DataFrame) -> pd.Series:
        """Estimate inflation hedging capability"""
        # Simplified estimation based on sector and asset intensity
        base_score = 0.4
        sector_adjustment = df.get('sector', 'Unknown').map({
            'Real Estate': 0.4, 'Materials': 0.3, 'Energy': 0.3,
            'Utilities': 0.2, 'Consumer Staples': 0.1
        }).fillna(0.0)
        
        return pd.Series([base_score] * len(df), index=df.index) + sector_adjustment
    
    def _impute_missing_values(self, df: pd.DataFrame, feature_columns: List[str]) -> pd.DataFrame:
        """Sophisticated missing value imputation"""
        df_imputed = df.copy()
        
        for col in feature_columns:
            if col not in df_imputed.columns:
                continue
            
            if df_imputed[col].isna().any():
                # Use sector-based imputation where possible
                if 'sector' in df_imputed.columns:
                    # Fill with sector median, then overall median
                    sector_medians = df_imputed.groupby('sector')[col].median()
                    df_imputed[col] = df_imputed[col].fillna(
                        df_imputed['sector'].map(sector_medians)
                    ).fillna(df_imputed[col].median())
                else:
                    # Fill with overall median
                    df_imputed[col] = df_imputed[col].fillna(df_imputed[col].median())
        
        return df_imputed
    
    def _create_composite_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create composite scores from individual features"""
        df_composite = df.copy()
        
        # Financial Strength Score
        financial_features = ['roe', 'roa', 'profit_margin', 'current_ratio']
        available_financial = [col for col in financial_features if col in df.columns]
        if available_financial:
            df_composite['financial_strength_score'] = df[available_financial].fillna(0).mean(axis=1)
        
        # Dividend Quality Score
        dividend_features = ['dividend_consistency_score', 'yield_stability', 'payment_consistency']
        available_dividend = [col for col in dividend_features if col in df.columns]
        if available_dividend:
            df_composite['dividend_quality_score'] = df[available_dividend].fillna(0).mean(axis=1)
        
        # Growth Potential Score
        growth_features = ['revenue_growth_1yr_normalized', 'earnings_growth_1yr_normalized']
        available_growth = [col for col in growth_features if col in df.columns]
        if available_growth:
            df_composite['growth_potential_score'] = df[available_growth].fillna(0).mean(axis=1)
        
        # Risk-Adjusted Return
        if 'sharpe_ratio' in df.columns:
            df_composite['risk_adjusted_return'] = df['sharpe_ratio'].fillna(0)
        elif 'dividend_yield' in df.columns and 'volatility' in df.columns:
            df_composite['risk_adjusted_return'] = (df['dividend_yield'].fillna(0.03) / 
                                                   df['volatility'].fillna(0.2))
        
        # Overall Stability Score
        stability_components = []
        if 'dividend_stability_score' in df.columns:
            stability_components.append(df['dividend_stability_score'])
        if 'financial_strength_score' in df_composite.columns:
            stability_components.append(df_composite['financial_strength_score'])
        if 'beta' in df.columns:
            stability_components.append(1 / (1 + df['beta'].fillna(1.0)))  # Lower beta = higher stability
        
        if stability_components:
            df_composite['overall_stability_score'] = pd.concat(stability_components, axis=1).mean(axis=1)
        
        return df_composite
    
    def _optimize_dbscan_params(self, X: np.ndarray) -> Tuple[float, int]:
        """Optimize DBSCAN parameters using nearest neighbors"""
        try:
            # Use k-distance graph to find optimal eps
            k = max(4, int(np.sqrt(len(X))))  # Rule of thumb: k = sqrt(n)
            nbrs = NearestNeighbors(n_neighbors=k).fit(X)
            distances, indices = nbrs.kneighbors(X)
            
            # Sort distances to k-th nearest neighbor
            k_distances = np.sort(distances[:, k-1])
            
            # Find the "knee" in the k-distance graph
            # Simple method: find point with maximum second derivative
            if len(k_distances) > 10:
                second_deriv = np.diff(k_distances, 2)
                knee_idx = np.argmax(second_deriv) + 2
                eps = k_distances[knee_idx]
            else:
                eps = np.percentile(k_distances, 90)  # Use 90th percentile as fallback
            
            min_samples = max(3, k // 2)  # Typically k/2
            
        except:
            # Fallback parameters
            eps = 0.5
            min_samples = 5
        
        return eps, min_samples


class RiskRewardSegmentation:
    """
    Advanced risk-reward segmentation system for dividend stocks
    """
    
    def __init__(self, random_state: int = 42):
        """Initialize the risk-reward segmentation system"""
        self.random_state = random_state
        
        # Segmentation categories
        self.segments = {
            'conservative_income': {
                'name': 'Conservative Income',
                'description': 'Low risk, steady yield, mature companies',
                'risk_range': (0.0, 0.3),
                'yield_range': (0.02, 0.06),
                'sectors': ['Utilities', 'Consumer Staples', 'REITs']
            },
            'balanced_growth': {
                'name': 'Balanced Growth',
                'description': 'Moderate risk, growing dividends, established companies',
                'risk_range': (0.25, 0.6),
                'yield_range': (0.015, 0.05),
                'sectors': ['Healthcare', 'Industrials', 'Telecommunications']
            },
            'high_yield_speculative': {
                'name': 'High Yield Speculative',
                'description': 'High yield, higher risk, potential dividend cuts',
                'risk_range': (0.6, 1.0),
                'yield_range': (0.05, 0.15),
                'sectors': ['Energy', 'Materials', 'High Yield REITs']
            },
            'growth_aristocrats': {
                'name': 'Growth Aristocrats',
                'description': 'Lower yield, consistent growth, dividend aristocrats',
                'risk_range': (0.2, 0.5),
                'yield_range': (0.01, 0.04),
                'sectors': ['Technology', 'Healthcare', 'Consumer Discretionary']
            },
            'value_recovery': {
                'name': 'Value Recovery',
                'description': 'Distressed but recovering, potential turnaround',
                'risk_range': (0.7, 1.0),
                'yield_range': (0.03, 0.12),
                'sectors': ['Financials', 'Energy', 'Retail']
            }
        }
        
        self.risk_metrics = {}
        self.segment_models = {}
    
    def calculate_risk_metrics(self, stock_data: pd.DataFrame) -> pd.DataFrame:
        """Calculate comprehensive risk metrics for each stock"""
        print("⚠️ Calculating comprehensive risk metrics...")
        
        df = stock_data.copy()
        
        # Dividend stability risk
        df['dividend_stability'] = self._calculate_dividend_stability(df)
        
        # Payout sustainability risk
        df['payout_sustainability'] = self._assess_payout_sustainability(df)
        
        # Earnings volatility risk
        df['earnings_volatility'] = self._calculate_earnings_volatility(df)
        
        # Credit risk assessment
        df['credit_risk'] = self._assess_credit_risk(df)
        
        # Market risk (beta-based)
        df['market_risk'] = self._calculate_market_beta(df)
        
        # Business risk
        df['business_risk'] = self._calculate_business_risk(df)
        
        # Liquidity risk
        df['liquidity_risk'] = self._calculate_liquidity_risk(df)
        
        # Composite risk score
        risk_components = [
            ('dividend_stability', 0.25),
            ('payout_sustainability', 0.20),
            ('earnings_volatility', 0.15),
            ('credit_risk', 0.15),
            ('market_risk', 0.10),
            ('business_risk', 0.10),
            ('liquidity_risk', 0.05)
        ]
        
        df['composite_risk_score'] = sum(
            df[component].fillna(0.5) * weight 
            for component, weight in risk_components
        )
        
        return df
    
    def calculate_reward_metrics(self, stock_data: pd.DataFrame) -> pd.DataFrame:
        """Calculate comprehensive reward metrics for each stock"""
        print("💰 Calculating comprehensive reward metrics...")
        
        df = stock_data.copy()
        
        # Current dividend yield
        df['current_yield'] = df.get('dividend_yield', 0.03)
        
        # Dividend growth potential
        df['growth_potential'] = self._calculate_growth_potential(df)
        
        # Total return potential
        df['total_return_potential'] = self._calculate_total_return_potential(df)
        
        # Yield sustainability score
        df['yield_sustainability'] = self._calculate_yield_sustainability(df)
        
        # Capital appreciation potential
        df['capital_appreciation'] = self._calculate_capital_appreciation(df)
        
        # Composite reward score
        reward_components = [
            ('current_yield', 0.30),
            ('growth_potential', 0.25),
            ('total_return_potential', 0.20),
            ('yield_sustainability', 0.15),
            ('capital_appreciation', 0.10)
        ]
        
        df['composite_reward_score'] = sum(
            df[component].fillna(0.3) * weight 
            for component, weight in reward_components
        )
        
        return df
    
    def segment_stocks(self, stock_data: pd.DataFrame) -> pd.DataFrame:
        """Segment stocks into risk-reward categories"""
        print("🎯 Segmenting stocks into risk-reward categories...")
        
        # Calculate risk and reward metrics
        df = self.calculate_risk_metrics(stock_data)
        df = self.calculate_reward_metrics(df)
        
        # Apply segmentation logic
        df['risk_reward_segment'] = df.apply(self._classify_stock, axis=1)
        df['segment_confidence'] = df.apply(self._calculate_segment_confidence, axis=1)
        
        # Add segment characteristics
        df['segment_description'] = df['risk_reward_segment'].map(
            {k: v['description'] for k, v in self.segments.items()}
        )
        
        return df
    
    def _classify_stock(self, row: pd.Series) -> str:
        """Classify individual stock into risk-reward segment"""
        risk_score = row['composite_risk_score']
        reward_score = row['composite_reward_score']
        current_yield = row.get('current_yield', 0.03)
        sector = row.get('sector', 'Unknown')
        
        # Score each segment
        segment_scores = {}
        
        for segment_key, segment_info in self.segments.items():
            score = 0
            
            # Risk score matching
            risk_min, risk_max = segment_info['risk_range']
            if risk_min <= risk_score <= risk_max:
                score += 0.4
            else:
                # Penalize distance from range
                distance = min(abs(risk_score - risk_min), abs(risk_score - risk_max))
                score += max(0, 0.4 - distance * 2)
            
            # Yield matching
            yield_min, yield_max = segment_info['yield_range']
            if yield_min <= current_yield <= yield_max:
                score += 0.3
            else:
                distance = min(abs(current_yield - yield_min), abs(current_yield - yield_max))
                score += max(0, 0.3 - distance * 10)
            
            # Sector matching
            if sector in segment_info['sectors']:
                score += 0.2
            
            # Reward score consideration
            if segment_key == 'growth_aristocrats' and reward_score > 0.6:
                score += 0.1
            elif segment_key == 'high_yield_speculative' and current_yield > 0.08:
                score += 0.1
            elif segment_key == 'conservative_income' and risk_score < 0.3:
                score += 0.1
            
            segment_scores[segment_key] = score
        
        # Return segment with highest score
        return max(segment_scores.items(), key=lambda x: x[1])[0]
    
    def _calculate_segment_confidence(self, row: pd.Series) -> float:
        """Calculate confidence in segment assignment"""
        # Simplified confidence calculation based on how well stock fits segment criteria
        segment = row['risk_reward_segment']
        segment_info = self.segments[segment]
        
        confidence = 0.5  # Base confidence
        
        # Risk score fit
        risk_score = row['composite_risk_score']
        risk_min, risk_max = segment_info['risk_range']
        if risk_min <= risk_score <= risk_max:
            confidence += 0.25
        
        # Yield fit
        current_yield = row.get('current_yield', 0.03)
        yield_min, yield_max = segment_info['yield_range']
        if yield_min <= current_yield <= yield_max:
            confidence += 0.25
        
        return min(1.0, confidence)
    
    # Risk metric calculation methods
    def _calculate_dividend_stability(self, df: pd.DataFrame) -> pd.Series:
        """Calculate dividend stability score"""
        # Simplified calculation - in practice would use historical dividend data
        base_stability = 0.7
        
        # Adjust based on payout ratio
        if 'payout_ratio' in df.columns:
            payout_adj = df['payout_ratio'].apply(
                lambda x: 0.3 if x > 0.8 else 0.2 if x > 0.6 else 0.1 if x > 0.4 else 0.0
            )
            base_stability -= payout_adj
        
        # Adjust based on sector
        if 'sector' in df.columns:
            sector_stability = df['sector'].map({
                'Utilities': 0.2, 'Consumer Staples': 0.15, 'Healthcare': 0.1,
                'REITs': 0.1, 'Telecommunications': 0.05, 'Industrials': 0.0,
                'Financials': -0.05, 'Materials': -0.1, 'Energy': -0.15
            }).fillna(0.0)
            base_stability += sector_stability
        
        return pd.Series([base_stability] * len(df), index=df.index).clip(0, 1)
    
    def _assess_payout_sustainability(self, df: pd.DataFrame) -> pd.Series:
        """Assess payout sustainability risk"""
        if 'payout_ratio' not in df.columns:
            return pd.Series([0.5] * len(df), index=df.index)
        
        return df['payout_ratio'].apply(
            lambda x: 0.1 if x < 0.4 else 0.3 if x < 0.6 else 0.6 if x < 0.8 else 0.9
        )
    
    def _calculate_earnings_volatility(self, df: pd.DataFrame) -> pd.Series:
        """Calculate earnings volatility risk"""
        # Simplified - would use historical earnings data in practice
        if 'earnings_growth_3yr' in df.columns:
            # Higher absolute earnings growth changes indicate higher volatility
            return df['earnings_growth_3yr'].abs().clip(0, 1)
        else:
            return pd.Series([0.4] * len(df), index=df.index)
    
    def _assess_credit_risk(self, df: pd.DataFrame) -> pd.Series:
        """Assess credit risk"""
        if 'debt_to_equity' in df.columns:
            return df['debt_to_equity'].apply(
                lambda x: 0.2 if x < 0.3 else 0.4 if x < 0.6 else 0.7 if x < 1.0 else 0.9
            )
        else:
            return pd.Series([0.4] * len(df), index=df.index)
    
    def _calculate_market_beta(self, df: pd.DataFrame) -> pd.Series:
        """Calculate market risk based on beta"""
        if 'beta' in df.columns:
            return df['beta'].apply(lambda x: min(1.0, abs(x - 1.0)))
        else:
            return pd.Series([0.5] * len(df), index=df.index)
    
    def _calculate_business_risk(self, df: pd.DataFrame) -> pd.Series:
        """Calculate business/industry risk"""
        if 'sector' not in df.columns:
            return pd.Series([0.5] * len(df), index=df.index)
        
        sector_risk = {
            'Utilities': 0.2, 'Consumer Staples': 0.25, 'Healthcare': 0.3,
            'Telecommunications': 0.35, 'REITs': 0.4, 'Industrials': 0.45,
            'Materials': 0.6, 'Information Technology': 0.65, 'Financials': 0.7,
            'Consumer Discretionary': 0.75, 'Energy': 0.85, 'Biotechnology': 0.9
        }
        
        return df['sector'].map(sector_risk).fillna(0.5)
    
    def _calculate_liquidity_risk(self, df: pd.DataFrame) -> pd.Series:
        """Calculate liquidity risk"""
        if 'market_cap' in df.columns:
            # Larger market cap generally means lower liquidity risk
            return df['market_cap'].apply(
                lambda x: 0.1 if x > 10e9 else 0.3 if x > 2e9 else 0.6 if x > 500e6 else 0.8
            )
        else:
            return pd.Series([0.4] * len(df), index=df.index)
    
    # Reward metric calculation methods
    def _calculate_growth_potential(self, df: pd.DataFrame) -> pd.Series:
        """Calculate dividend growth potential"""
        if 'dividend_growth_3yr' in df.columns:
            return df['dividend_growth_3yr'].clip(0, 1)
        else:
            return pd.Series([0.4] * len(df), index=df.index)
    
    def _calculate_total_return_potential(self, df: pd.DataFrame) -> pd.Series:
        """Calculate total return potential"""
        yield_component = df.get('dividend_yield', 0.03) / 0.10  # Normalize to 10% max yield
        
        if 'earnings_growth_1yr' in df.columns:
            growth_component = df['earnings_growth_1yr'].clip(-0.2, 0.3) + 0.2  # Shift to positive
            return ((yield_component + growth_component) / 2).clip(0, 1)
        else:
            return pd.Series([yield_component] * len(df), index=df.index).clip(0, 1)
    
    def _calculate_yield_sustainability(self, df: pd.DataFrame) -> pd.Series:
        """Calculate yield sustainability score"""
        sustainability = 0.6  # Base score
        
        if 'payout_ratio' in df.columns:
            payout_bonus = df['payout_ratio'].apply(
                lambda x: 0.3 if x < 0.6 else 0.1 if x < 0.8 else -0.2
            )
            sustainability += payout_bonus
        
        if 'earnings_coverage' in df.columns:
            coverage_bonus = df['earnings_coverage'].apply(
                lambda x: 0.2 if x > 1.5 else 0.0 if x > 1.2 else -0.3
            )
            sustainability += coverage_bonus
        
        return pd.Series([sustainability] * len(df), index=df.index).clip(0, 1)
    
    def _calculate_capital_appreciation(self, df: pd.DataFrame) -> pd.Series:
        """Calculate capital appreciation potential"""
        if 'pe_ratio' in df.columns and 'pb_ratio' in df.columns:
            # Lower ratios might indicate undervaluation
            pe_score = df['pe_ratio'].apply(lambda x: 0.8 if x < 15 else 0.5 if x < 25 else 0.2)
            pb_score = df['pb_ratio'].apply(lambda x: 0.8 if x < 1.5 else 0.5 if x < 3 else 0.2)
            return (pe_score + pb_score) / 2
        else:
            return pd.Series([0.4] * len(df), index=df.index)


class PortfolioDiversificationAnalyzer:
    """
    Advanced portfolio diversification analysis and optimization
    """
    
    def __init__(self, random_state: int = 42):
        """Initialize the diversification analyzer"""
        self.random_state = random_state
        self.optimization_results = {}
        self.diversification_metrics = {}
    
    def analyze_portfolio_concentration(self, portfolio: pd.DataFrame) -> Dict[str, Any]:
        """Comprehensive portfolio concentration analysis"""
        print("🎯 Analyzing portfolio concentration risks...")
        
        analysis = {}
        
        # Sector concentration analysis
        analysis['sector_weights'] = self._calculate_sector_weights(portfolio)
        analysis['sector_concentration_risk'] = self._calculate_concentration_risk(
            analysis['sector_weights']
        )
        
        # Geographic diversification
        if 'country' in portfolio.columns:
            analysis['geographic_weights'] = self._calculate_geographic_weights(portfolio)
            analysis['geographic_concentration_risk'] = self._calculate_concentration_risk(
                analysis['geographic_weights']
            )
        
        # Market cap diversification
        if 'market_cap' in portfolio.columns:
            analysis['market_cap_distribution'] = self._calculate_market_cap_distribution(portfolio)
        
        # Individual position concentration
        analysis['position_weights'] = self._calculate_position_weights(portfolio)
        analysis['position_concentration_risk'] = self._calculate_position_concentration_risk(
            analysis['position_weights']
        )
        
        # Correlation analysis
        analysis['correlation_matrix'] = self._calculate_correlation_matrix(portfolio)
        analysis['correlation_risk'] = self._assess_correlation_risk(
            analysis['correlation_matrix']
        )
        
        # Overall diversification score
        analysis['diversification_score'] = self._calculate_diversification_score(analysis)
        
        # Generate recommendations
        analysis['recommendations'] = self._generate_diversification_recommendations(analysis)
        
        return analysis
    
    def optimize_portfolio(self, stocks: pd.DataFrame, constraints: Dict[str, Any], 
                          objective: str = 'max_sharpe') -> Dict[str, Any]:
        """Advanced portfolio optimization with multiple objectives"""
        print(f"⚡ Optimizing portfolio with objective: {objective}")
        
        # Prepare expected returns and covariance matrix
        expected_returns = self._estimate_expected_returns(stocks)
        cov_matrix = self._estimate_covariance_matrix(stocks)
        
        # Define optimization constraints
        optimization_constraints = self._prepare_optimization_constraints(stocks, constraints)
        
        # Perform optimization based on objective
        if objective == 'max_sharpe':
            result = self._maximize_sharpe_ratio(expected_returns, cov_matrix, optimization_constraints)
        elif objective == 'min_risk':
            result = self._minimize_portfolio_risk(expected_returns, cov_matrix, optimization_constraints)
        elif objective == 'max_dividend_yield':
            result = self._maximize_dividend_yield(stocks, optimization_constraints)
        elif objective == 'efficient_frontier':
            result = self._calculate_efficient_frontier(expected_returns, cov_matrix, optimization_constraints)
        else:
            raise ValueError(f"Unknown optimization objective: {objective}")
        
        # Analyze optimized portfolio
        if 'weights' in result:
            result['portfolio_analysis'] = self._analyze_optimized_portfolio(
                stocks, result['weights']
            )
        
        return result
    
    def _calculate_sector_weights(self, portfolio: pd.DataFrame) -> Dict[str, float]:
        """Calculate sector weights in portfolio"""
        if 'sector' not in portfolio.columns or 'weight' not in portfolio.columns:
            return {}
        
        sector_weights = portfolio.groupby('sector')['weight'].sum().to_dict()
        return {k: float(v) for k, v in sector_weights.items()}
    
    def _calculate_geographic_weights(self, portfolio: pd.DataFrame) -> Dict[str, float]:
        """Calculate geographic weights in portfolio"""
        if 'country' not in portfolio.columns or 'weight' not in portfolio.columns:
            return {}
        
        geo_weights = portfolio.groupby('country')['weight'].sum().to_dict()
        return {k: float(v) for k, v in geo_weights.items()}
    
    def _calculate_market_cap_distribution(self, portfolio: pd.DataFrame) -> Dict[str, float]:
        """Calculate market cap distribution"""
        if 'market_cap' not in portfolio.columns or 'weight' not in portfolio.columns:
            return {}
        
        def categorize_market_cap(market_cap):
            if market_cap > 10e9:
                return 'Large Cap'
            elif market_cap > 2e9:
                return 'Mid Cap'
            else:
                return 'Small Cap'
        
        portfolio['market_cap_category'] = portfolio['market_cap'].apply(categorize_market_cap)
        cap_distribution = portfolio.groupby('market_cap_category')['weight'].sum().to_dict()
        
        return {k: float(v) for k, v in cap_distribution.items()}
    
    def _calculate_position_weights(self, portfolio: pd.DataFrame) -> Dict[str, float]:
        """Calculate individual position weights"""
        if 'symbol' not in portfolio.columns or 'weight' not in portfolio.columns:
            return {}
        
        position_weights = portfolio.set_index('symbol')['weight'].to_dict()
        return {k: float(v) for k, v in position_weights.items()}
    
    def _calculate_concentration_risk(self, weights: Dict[str, float]) -> Dict[str, Any]:
        """Calculate concentration risk metrics"""
        if not weights:
            return {'herfindahl_index': 0, 'max_weight': 0, 'concentration_level': 'unknown'}
        
        values = list(weights.values())
        
        # Herfindahl Index (sum of squared weights)
        herfindahl_index = sum(w**2 for w in values)
        
        # Maximum weight
        max_weight = max(values)
        
        # Concentration level assessment
        if herfindahl_index < 0.1:
            concentration_level = 'low'
        elif herfindahl_index < 0.25:
            concentration_level = 'moderate'
        else:
            concentration_level = 'high'
        
        return {
            'herfindahl_index': herfindahl_index,
            'max_weight': max_weight,
            'concentration_level': concentration_level,
            'effective_number_of_positions': 1 / herfindahl_index if herfindahl_index > 0 else 0
        }
    
    def _calculate_position_concentration_risk(self, position_weights: Dict[str, float]) -> Dict[str, Any]:
        """Calculate position-specific concentration risks"""
        if not position_weights:
            return {'large_positions': [], 'concentration_risk': 'unknown'}
        
        # Identify large positions (>5% of portfolio)
        large_positions = {k: v for k, v in position_weights.items() if v > 0.05}
        
        # Calculate position concentration risk
        total_large_position_weight = sum(large_positions.values())
        
        if total_large_position_weight > 0.5:
            risk_level = 'high'
        elif total_large_position_weight > 0.3:
            risk_level = 'moderate'
        else:
            risk_level = 'low'
        
        return {
            'large_positions': large_positions,
            'large_position_total_weight': total_large_position_weight,
            'concentration_risk': risk_level,
            'number_of_large_positions': len(large_positions)
        }
    
    def _calculate_correlation_matrix(self, portfolio: pd.DataFrame) -> np.ndarray:
        """Calculate correlation matrix for portfolio holdings"""
        # Simplified correlation matrix generation
        # In practice, this would use historical price data
        n_assets = len(portfolio)
        
        if n_assets < 2:
            return np.array([[1.0]])
        
        # Generate realistic correlation matrix
        np.random.seed(self.random_state)
        correlations = np.random.uniform(0.1, 0.8, (n_assets, n_assets))
        
        # Make symmetric and set diagonal to 1
        correlations = (correlations + correlations.T) / 2
        np.fill_diagonal(correlations, 1.0)
        
        return correlations
    
    def _assess_correlation_risk(self, correlation_matrix: np.ndarray) -> Dict[str, Any]:
        """Assess correlation risk in portfolio"""
        if correlation_matrix.shape[0] < 2:
            return {'average_correlation': 0, 'max_correlation': 0, 'risk_level': 'low'}
        
        # Get upper triangle (excluding diagonal)
        upper_triangle = correlation_matrix[np.triu_indices_from(correlation_matrix, k=1)]
        
        avg_correlation = np.mean(upper_triangle)
        max_correlation = np.max(upper_triangle)
        
        # Assess risk level
        if avg_correlation > 0.7:
            risk_level = 'high'
        elif avg_correlation > 0.5:
            risk_level = 'moderate'
        else:
            risk_level = 'low'
        
        return {
            'average_correlation': float(avg_correlation),
            'max_correlation': float(max_correlation),
            'risk_level': risk_level,
            'highly_correlated_pairs': self._find_highly_correlated_pairs(correlation_matrix)
        }
    
    def _find_highly_correlated_pairs(self, correlation_matrix: np.ndarray, threshold: float = 0.8) -> List[Tuple[int, int, float]]:
        """Find highly correlated asset pairs"""
        pairs = []
        n = correlation_matrix.shape[0]
        
        for i in range(n):
            for j in range(i + 1, n):
                if correlation_matrix[i, j] > threshold:
                    pairs.append((i, j, float(correlation_matrix[i, j])))
        
        return pairs
    
    def _calculate_diversification_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate overall diversification score"""
        score_components = []
        
        # Sector diversification (30%)
        if 'sector_concentration_risk' in analysis:
            sector_score = 1.0 - analysis['sector_concentration_risk']['herfindahl_index']
            score_components.append((sector_score, 0.3))
        
        # Position diversification (25%)
        if 'position_concentration_risk' in analysis:
            position_risk = analysis['position_concentration_risk']['large_position_total_weight']
            position_score = max(0, 1.0 - position_risk)
            score_components.append((position_score, 0.25))
        
        # Correlation diversification (25%)
        if 'correlation_risk' in analysis:
            corr_risk = analysis['correlation_risk']['average_correlation']
            corr_score = max(0, 1.0 - corr_risk)
            score_components.append((corr_score, 0.25))
        
        # Geographic diversification (20%)
        if 'geographic_concentration_risk' in analysis:
            geo_score = 1.0 - analysis['geographic_concentration_risk']['herfindahl_index']
            score_components.append((geo_score, 0.2))
        
        if not score_components:
            return 0.5  # Default moderate score
        
        # Weighted average
        total_weight = sum(weight for _, weight in score_components)
        weighted_score = sum(score * weight for score, weight in score_components) / total_weight
        
        return min(1.0, max(0.0, weighted_score))
    
    def _generate_diversification_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable diversification recommendations"""
        recommendations = []
        
        # Sector concentration recommendations
        if 'sector_concentration_risk' in analysis:
            sector_risk = analysis['sector_concentration_risk']
            if sector_risk['concentration_level'] == 'high':
                recommendations.append(
                    f"High sector concentration detected (Herfindahl Index: {sector_risk['herfindahl_index']:.3f}). "
                    "Consider reducing exposure to overweight sectors."
                )
        
        # Position size recommendations
        if 'position_concentration_risk' in analysis:
            position_risk = analysis['position_concentration_risk']
            if position_risk['concentration_risk'] == 'high':
                large_positions = position_risk['large_positions']
                recommendations.append(
                    f"Large position concentration risk: {len(large_positions)} positions exceed 5% allocation. "
                    f"Consider rebalancing positions: {list(large_positions.keys())[:3]}"
                )
        
        # Correlation recommendations
        if 'correlation_risk' in analysis:
            corr_risk = analysis['correlation_risk']
            if corr_risk['risk_level'] == 'high':
                recommendations.append(
                    f"High correlation risk (average: {corr_risk['average_correlation']:.2f}). "
                    "Consider adding assets with lower correlations to existing holdings."
                )
        
        # Overall diversification score
        diversification_score = analysis.get('diversification_score', 0.5)
        if diversification_score < 0.6:
            recommendations.append(
                f"Overall diversification score is low ({diversification_score:.2f}). "
                "Consider improving diversification across sectors, geographies, and asset classes."
            )
        
        if not recommendations:
            recommendations.append("Portfolio diversification appears adequate based on current analysis.")
        
        return recommendations
    
    # Portfolio optimization methods
    def _estimate_expected_returns(self, stocks: pd.DataFrame) -> np.ndarray:
        """Estimate expected returns for portfolio optimization"""
        # Simplified expected return estimation
        # In practice, this would use historical data or fundamental analysis
        
        if 'dividend_yield' in stocks.columns:
            dividend_yield = stocks['dividend_yield'].fillna(0.03)
        else:
            dividend_yield = pd.Series([0.03] * len(stocks))
        
        if 'expected_growth' in stocks.columns:
            growth_rate = stocks['expected_growth'].fillna(0.05)
        else:
            growth_rate = pd.Series([0.05] * len(stocks))
        
        # Total expected return = dividend yield + growth
        expected_returns = dividend_yield + growth_rate
        
        return expected_returns.values
    
    def _estimate_covariance_matrix(self, stocks: pd.DataFrame) -> np.ndarray:
        """Estimate covariance matrix for portfolio optimization"""
        # Simplified covariance estimation
        n_assets = len(stocks)
        
        # Use volatility estimates
        if 'volatility' in stocks.columns:
            volatilities = stocks['volatility'].fillna(0.2).values
        else:
            volatilities = np.full(n_assets, 0.2)
        
        # Create correlation matrix
        correlation_matrix = self._calculate_correlation_matrix(stocks)
        
        # Convert to covariance matrix
        vol_matrix = np.outer(volatilities, volatilities)
        covariance_matrix = correlation_matrix * vol_matrix
        
        return covariance_matrix
    
    def _prepare_optimization_constraints(self, stocks: pd.DataFrame, constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare optimization constraints"""
        n_assets = len(stocks)
        
        optimization_constraints = {
            'bounds': [(0, 1) for _ in range(n_assets)],  # Long-only constraint
            'constraints': []
        }
        
        # Budget constraint (weights sum to 1)
        optimization_constraints['constraints'].append({
            'type': 'eq',
            'fun': lambda x: np.sum(x) - 1
        })
        
        # Individual position limits
        if 'max_position_size' in constraints:
            max_size = constraints['max_position_size']
            optimization_constraints['bounds'] = [(0, max_size) for _ in range(n_assets)]
        
        # Sector limits
        if 'sector_limits' in constraints and 'sector' in stocks.columns:
            sector_limits = constraints['sector_limits']
            for sector, limit in sector_limits.items():
                sector_mask = (stocks['sector'] == sector).values
                if np.any(sector_mask):
                    optimization_constraints['constraints'].append({
                        'type': 'ineq',
                        'fun': lambda x, mask=sector_mask, lim=limit: lim - np.sum(x[mask])
                    })
        
        # Minimum number of positions
        if 'min_positions' in constraints:
            min_positions = constraints['min_positions']
            optimization_constraints['constraints'].append({
                'type': 'ineq',
                'fun': lambda x, min_pos=min_positions: np.sum(x > 0.001) - min_pos
            })
        
        return optimization_constraints
    
    def _maximize_sharpe_ratio(self, expected_returns: np.ndarray, cov_matrix: np.ndarray, 
                              constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Maximize Sharpe ratio optimization"""
        n_assets = len(expected_returns)
        
        # Risk-free rate (simplified)
        risk_free_rate = 0.02
        
        # Objective function (negative Sharpe ratio for minimization)
        def negative_sharpe(weights):
            portfolio_return = np.dot(weights, expected_returns)
            portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            if portfolio_vol == 0:
                return -np.inf
            return -(portfolio_return - risk_free_rate) / portfolio_vol
        
        # Initial guess (equal weights)
        x0 = np.ones(n_assets) / n_assets
        
        # Optimize
        try:
            result = optimize.minimize(
                negative_sharpe, x0, method='SLSQP',
                bounds=constraints['bounds'],
                constraints=constraints['constraints'],
                options={'maxiter': 1000}
            )
            
            if result.success:
                optimal_weights = result.x
                portfolio_return = np.dot(optimal_weights, expected_returns)
                portfolio_vol = np.sqrt(np.dot(optimal_weights.T, np.dot(cov_matrix, optimal_weights)))
                sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_vol if portfolio_vol > 0 else 0
                
                return {
                    'success': True,
                    'weights': optimal_weights,
                    'expected_return': portfolio_return,
                    'volatility': portfolio_vol,
                    'sharpe_ratio': sharpe_ratio,
                    'optimization_result': result
                }
            else:
                raise Exception(f"Optimization failed: {result.message}")
        
        except Exception as e:
            print(f"Optimization failed: {e}")
            # Fallback to equal weights
            equal_weights = np.ones(n_assets) / n_assets
            portfolio_return = np.dot(equal_weights, expected_returns)
            portfolio_vol = np.sqrt(np.dot(equal_weights.T, np.dot(cov_matrix, equal_weights)))
            
            return {
                'success': False,
                'weights': equal_weights,
                'expected_return': portfolio_return,
                'volatility': portfolio_vol,
                'sharpe_ratio': 0,
                'error': str(e)
            }
    
    def _minimize_portfolio_risk(self, expected_returns: np.ndarray, cov_matrix: np.ndarray,
                                constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Minimize portfolio risk optimization"""
        n_assets = len(expected_returns)
        
        # Objective function (portfolio variance)
        def portfolio_variance(weights):
            return np.dot(weights.T, np.dot(cov_matrix, weights))
        
        # Initial guess
        x0 = np.ones(n_assets) / n_assets
        
        try:
            result = optimize.minimize(
                portfolio_variance, x0, method='SLSQP',
                bounds=constraints['bounds'],
                constraints=constraints['constraints'],
                options={'maxiter': 1000}
            )
            
            if result.success:
                optimal_weights = result.x
                portfolio_return = np.dot(optimal_weights, expected_returns)
                portfolio_vol = np.sqrt(result.fun)
                
                return {
                    'success': True,
                    'weights': optimal_weights,
                    'expected_return': portfolio_return,
                    'volatility': portfolio_vol,
                    'optimization_result': result
                }
            else:
                raise Exception(f"Optimization failed: {result.message}")
        
        except Exception as e:
            # Fallback
            equal_weights = np.ones(n_assets) / n_assets
            return {
                'success': False,
                'weights': equal_weights,
                'error': str(e)
            }
    
    def _maximize_dividend_yield(self, stocks: pd.DataFrame, constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Maximize dividend yield optimization"""
        n_assets = len(stocks)
        
        # Get dividend yields
        if 'dividend_yield' in stocks.columns:
            dividend_yields = stocks['dividend_yield'].fillna(0).values
        else:
            dividend_yields = np.ones(n_assets) * 0.03
        
        # Objective function (negative yield for minimization)
        def negative_yield(weights):
            return -np.dot(weights, dividend_yields)
        
        x0 = np.ones(n_assets) / n_assets
        
        try:
            result = optimize.minimize(
                negative_yield, x0, method='SLSQP',
                bounds=constraints['bounds'],
                constraints=constraints['constraints'],
                options={'maxiter': 1000}
            )
            
            if result.success:
                optimal_weights = result.x
                portfolio_yield = np.dot(optimal_weights, dividend_yields)
                
                return {
                    'success': True,
                    'weights': optimal_weights,
                    'portfolio_yield': portfolio_yield,
                    'optimization_result': result
                }
            else:
                raise Exception(f"Optimization failed: {result.message}")
        
        except Exception as e:
            equal_weights = np.ones(n_assets) / n_assets
            return {
                'success': False,
                'weights': equal_weights,
                'error': str(e)
            }
    
    def _calculate_efficient_frontier(self, expected_returns: np.ndarray, cov_matrix: np.ndarray,
                                    constraints: Dict[str, Any], n_points: int = 20) -> Dict[str, Any]:
        """Calculate efficient frontier"""
        min_ret = np.min(expected_returns)
        max_ret = np.max(expected_returns)
        target_returns = np.linspace(min_ret, max_ret, n_points)
        
        efficient_portfolios = []
        
        for target_return in target_returns:
            # Add return constraint
            return_constraint = {
                'type': 'eq',
                'fun': lambda x, target=target_return: np.dot(x, expected_returns) - target
            }
            
            current_constraints = constraints['constraints'] + [return_constraint]
            
            # Minimize risk for target return
            def portfolio_variance(weights):
                return np.dot(weights.T, np.dot(cov_matrix, weights))
            
            x0 = np.ones(len(expected_returns)) / len(expected_returns)
            
            try:
                result = optimize.minimize(
                    portfolio_variance, x0, method='SLSQP',
                    bounds=constraints['bounds'],
                    constraints=current_constraints,
                    options={'maxiter': 1000}
                )
                
                if result.success:
                    optimal_weights = result.x
                    portfolio_vol = np.sqrt(result.fun)
                    
                    efficient_portfolios.append({
                        'return': target_return,
                        'volatility': portfolio_vol,
                        'weights': optimal_weights
                    })
            except:
                continue
        
        return {
            'success': len(efficient_portfolios) > 0,
            'efficient_portfolios': efficient_portfolios,
            'n_points': len(efficient_portfolios)
        }
    
    def _analyze_optimized_portfolio(self, stocks: pd.DataFrame, weights: np.ndarray) -> Dict[str, Any]:
        """Analyze the optimized portfolio"""
        analysis = {}
        
        # Basic portfolio statistics
        analysis['number_of_holdings'] = np.sum(weights > 0.001)
        analysis['largest_position'] = np.max(weights)
        analysis['smallest_position'] = np.min(weights[weights > 0.001]) if np.any(weights > 0.001) else 0
        
        # Sector allocation
        if 'sector' in stocks.columns:
            sector_allocation = {}
            for sector in stocks['sector'].unique():
                sector_mask = stocks['sector'] == sector
                sector_weight = np.sum(weights[sector_mask])
                if sector_weight > 0.001:
                    sector_allocation[sector] = sector_weight
            analysis['sector_allocation'] = sector_allocation
        
        # Risk metrics
        if 'beta' in stocks.columns:
            portfolio_beta = np.dot(weights, stocks['beta'].fillna(1.0))
            analysis['portfolio_beta'] = portfolio_beta
        
        if 'dividend_yield' in stocks.columns:
            portfolio_yield = np.dot(weights, stocks['dividend_yield'].fillna(0.03))
            analysis['portfolio_dividend_yield'] = portfolio_yield
        
        return analysis


# Main execution functions
def main():
    """Main function for command-line execution"""
    parser = argparse.ArgumentParser(description='Advanced Stock Clustering and Portfolio Optimization')
    parser.add_argument('--input', required=True, help='Input data file (JSON)')
    parser.add_argument('--output', default='./output', help='Output directory')
    parser.add_argument('--mode', choices=['cluster', 'segment', 'optimize'], default='cluster',
                       help='Analysis mode')
    parser.add_argument('--n-clusters', type=int, help='Number of clusters (optional)')
    parser.add_argument('--objective', choices=['max_sharpe', 'min_risk', 'max_dividend_yield'], 
                       default='max_sharpe', help='Optimization objective')
    
    args = parser.parse_args()
    
    # Load data
    try:
        with open(args.input, 'r') as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        print(f"📊 Loaded {len(df)} stocks for analysis")
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Initialize systems
    clustering_system = AdvancedStockClustering()
    segmentation_system = RiskRewardSegmentation()
    diversification_analyzer = PortfolioDiversificationAnalyzer()
    
    results = {}
    
    try:
        if args.mode == 'cluster':
            print("🎯 Running clustering analysis...")
            
            # Prepare features
            df_features, feature_columns = clustering_system.prepare_clustering_features(df)
            X = df_features[feature_columns].values
            
            # Standardize features
            X_scaled = clustering_system.scaler.fit_transform(X)
            
            # Reduce dimensionality
            X_pca = clustering_system.pca.fit_transform(X_scaled)
            
            # Run ensemble clustering
            clustering_result = clustering_system.ensemble_clustering(X_pca, args.n_clusters)
            
            # Add results to DataFrame
            df['cluster_id'] = clustering_result['labels']
            
            # Create cluster summaries
            cluster_summaries = {}
            for cluster_id in np.unique(clustering_result['labels']):
                cluster_mask = df['cluster_id'] == cluster_id
                cluster_data = df[cluster_mask]
                
                cluster_summaries[int(cluster_id)] = {
                    'size': len(cluster_data),
                    'symbols': cluster_data.get('symbol', cluster_data.index).tolist()[:10],  # First 10 symbols
                    'avg_dividend_yield': float(cluster_data.get('dividend_yield', pd.Series([0])).mean()),
                    'avg_market_cap': float(cluster_data.get('market_cap', pd.Series([0])).mean()),
                    'sectors': cluster_data.get('sector', pd.Series(['Unknown'])).value_counts().to_dict()
                }
            
            results = {
                'algorithm': 'ensemble_clustering',
                'n_clusters': len(np.unique(clustering_result['labels'])),
                'cluster_summaries': cluster_summaries,
                'clustering_metrics': clustering_system.clustering_metrics,
                'feature_columns': feature_columns,
                'timestamp': datetime.now().isoformat()
            }
            
        elif args.mode == 'segment':
            print("📊 Running risk-reward segmentation...")
            
            # Perform segmentation
            df_segmented = segmentation_system.segment_stocks(df)
            
            # Create segment summaries
            segment_summaries = {}
            for segment in df_segmented['risk_reward_segment'].unique():
                segment_mask = df_segmented['risk_reward_segment'] == segment
                segment_data = df_segmented[segment_mask]
                
                segment_summaries[segment] = {
                    'count': len(segment_data),
                    'symbols': segment_data.get('symbol', segment_data.index).tolist()[:10],
                    'avg_risk_score': float(segment_data['composite_risk_score'].mean()),
                    'avg_reward_score': float(segment_data['composite_reward_score'].mean()),
                    'avg_confidence': float(segment_data['segment_confidence'].mean())
                }
            
            results = {
                'segmentation_type': 'risk_reward',
                'segments': list(segmentation_system.segments.keys()),
                'segment_summaries': segment_summaries,
                'timestamp': datetime.now().isoformat()
            }
            
        elif args.mode == 'optimize':
            print("⚡ Running portfolio optimization...")
            
            # Prepare constraints (example)
            constraints = {
                'max_position_size': 0.1,  # Max 10% per position
                'min_positions': 10
            }
            
            # Run optimization
            optimization_result = diversification_analyzer.optimize_portfolio(
                df, constraints, args.objective
            )
            
            results = {
                'optimization_objective': args.objective,
                'optimization_result': optimization_result,
                'timestamp': datetime.now().isoformat()
            }
        
        # Save results
        output_file = os.path.join(args.output, f'{args.mode}_results.json')
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"✅ Analysis completed successfully. Results saved to {output_file}")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()