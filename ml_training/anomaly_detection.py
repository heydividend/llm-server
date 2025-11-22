#!/usr/bin/env python3
"""
Advanced Ensemble Anomaly Detection Model for Dividend Analytics
Implements multiple algorithms for comprehensive anomaly detection in dividend data
"""

import argparse
import json
import os
import sys
import time
import warnings
from datetime import datetime
from typing import Dict, List, Tuple, Any, Union

# Suppress warnings
warnings.filterwarnings('ignore')

try:
    import pandas as pd
    import numpy as np
    from sklearn.ensemble import IsolationForest
    from sklearn.svm import OneClassSVM
    from sklearn.neighbors import LocalOutlierFactor
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.model_selection import train_test_split, GridSearchCV
    from sklearn.metrics import classification_report, confusion_matrix, precision_score, recall_score
    import joblib
    from scipy import stats
except ImportError as e:
    print(f"Error importing required packages: {e}")
    print("Please ensure all required packages are installed:")
    print("pip install pandas numpy scikit-learn joblib scipy")
    sys.exit(1)


class DividendAnomalyDetector:
    """
    Advanced ensemble anomaly detection model for dividend data
    Uses multiple algorithms: Isolation Forest, One-Class SVM, and Local Outlier Factor
    """
    
    def __init__(self, contamination: float = 0.08, random_state: int = 42):
        """
        Initialize the ensemble anomaly detector
        
        Args:
            contamination: Expected proportion of anomalies in the data (~5-10% for dividend cuts)
            random_state: Random seed for reproducibility
        """
        self.contamination = float(contamination)
        self.random_state = random_state
        
        # Ensemble models
        self.isolation_forest = None
        self.one_class_svm = None
        self.lof_detector = None
        
        # Model weights (optimized for real-time performance)
        # Isolation Forest is primary for speed, SVM reduced for large datasets
        self.model_weights = {'isolation_forest': 0.6, 'one_class_svm': 0.25, 'lof': 0.15}
        
        # Performance optimization settings
        self.fast_mode = False  # Use only Isolation Forest for real-time
        self.svm_threshold = 1000  # Skip SVM for datasets larger than this
        
        # Data preprocessing
        self.scaler = None
        self.label_encoders = {}
        self.feature_columns = []
        self.categorical_columns = []
        self.numerical_columns = []
        
        # Feature importance (for interpretability)
        self.feature_importance = {}
        
        # Anomaly type classifiers
        self.anomaly_thresholds = {
            'amount_change': 0.25,  # 25% change threshold
            'timing_deviation': 14,  # 14 days deviation
            'yield_spike': 2.0,      # 2x yield increase
            'suspension_risk': 0.7   # High risk threshold
        }
        
    def prepare_data(self, data: List[Dict]) -> pd.DataFrame:
        """
        Prepare and clean data for model training/prediction
        
        Args:
            data: Raw dividend data
            
        Returns:
            Cleaned DataFrame ready for ML
        """
        print(f"📊 Preparing {len(data)} records for processing...")
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Handle missing values
        df = df.fillna({
            'dividend_amount': 0,
            'market_cap': 0,
            'sector': 'Unknown',
            'industry': 'Unknown',
            'frequency': 'Unknown',
            'dividend_type': 'Regular'
        })
        
        # Define feature columns
        self.numerical_columns = [
            'dividend_amount', 'dividend_amount_log', 'market_cap', 'market_cap_log',
            'yield_estimate', 'dividend_growth', 'days_since_last', 'rolling_avg_4q',
            'rolling_std_4q', 'rolling_growth_volatility', 'consistency_score',
            'trend_direction', 'quarter', 'month', 'day_of_year', 'days_to_payment',
            'days_to_record', 'dividend_history_count'
        ]
        
        self.categorical_columns = [
            'sector', 'industry', 'frequency', 'dividend_type', 'size_category'
        ]
        
        # Select available columns
        available_numerical = [col for col in self.numerical_columns if col in df.columns]
        available_categorical = [col for col in self.categorical_columns if col in df.columns]
        
        self.feature_columns = available_numerical + available_categorical
        
        print(f"Using {len(available_numerical)} numerical and {len(available_categorical)} categorical features")
        
        # Ensure we return a proper DataFrame
        selected_columns = self.feature_columns + ['symbol', 'ex_dividend_date']
        selected_columns = [col for col in selected_columns if col in df.columns]
        result_df = df[selected_columns].copy()
        return result_df
    
    def encode_categorical_features(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """
        Encode categorical features using LabelEncoder
        
        Args:
            df: DataFrame with categorical features
            fit: Whether to fit encoders (True for training, False for prediction)
            
        Returns:
            DataFrame with encoded categorical features
        """
        df_encoded = df.copy()
        
        for col in self.categorical_columns:
            if col in df.columns:
                if fit:
                    if col not in self.label_encoders:
                        self.label_encoders[col] = LabelEncoder()
                    df_encoded[col] = self.label_encoders[col].fit_transform(df[col].astype(str))
                else:
                    if col in self.label_encoders:
                        # Handle unseen categories
                        seen_categories = set(self.label_encoders[col].classes_)
                        df_encoded[col] = df[col].astype(str).apply(
                            lambda x: self.label_encoders[col].transform([x])[0] 
                            if x in seen_categories else -1
                        )
        
        return df_encoded
    
    def scale_features(self, df: pd.DataFrame, fit: bool = True) -> np.ndarray:
        """
        Scale numerical features using StandardScaler
        
        Args:
            df: DataFrame with features
            fit: Whether to fit scaler (True for training, False for prediction)
            
        Returns:
            Scaled feature matrix
        """
        feature_df = df[self.feature_columns].copy()
        
        # Encode categorical features
        feature_df = self.encode_categorical_features(feature_df, fit=fit)
        
        if fit:
            self.scaler = StandardScaler()
            scaled_features = self.scaler.fit_transform(feature_df)
        else:
            if self.scaler is None:
                raise ValueError("Scaler not fitted. Cannot transform data.")
            scaled_features = self.scaler.transform(feature_df)
        
        return scaled_features
    
    def train_ensemble(self, data: List[Dict], **kwargs) -> Dict[str, Any]:
        """
        Train the ensemble anomaly detection model
        
        Args:
            data: Training data
            **kwargs: Additional training parameters
            
        Returns:
            Training results and metrics
        """
        print("🏋️ Starting ensemble model training...")
        
        # Prepare data
        df = self.prepare_data(data)
        
        if len(df) < 50:  # Increased minimum for ensemble training
            raise ValueError("Insufficient data for ensemble training. Need at least 50 records.")
        
        # Scale features
        X = self.scale_features(df, fit=True)
        
        print(f"Training ensemble on {X.shape[0]} samples with {X.shape[1]} features")
        
        # Train Isolation Forest
        print("Training Isolation Forest...")
        self.isolation_forest = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state,
            n_estimators=150,
            max_samples='auto',
            n_jobs=-1
        )
        self.isolation_forest.fit(X)
        
        # Train One-Class SVM (with performance optimization)
        print("Training One-Class SVM...")
        if len(X) > self.svm_threshold:
            print(f"⚡ Large dataset ({len(X)} samples) detected - using optimized SVM settings")
            # Use linear kernel for large datasets (faster than RBF)
            self.one_class_svm = OneClassSVM(
                nu=self.contamination,
                gamma='scale',
                kernel='linear'  # Linear is much faster than RBF for large datasets
            )
        else:
            # Use RBF for smaller datasets (better accuracy)
            self.one_class_svm = OneClassSVM(
                nu=self.contamination,
                gamma='scale',
                kernel='rbf'
            )
        self.one_class_svm.fit(X)
        
        # Train Local Outlier Factor (for novelty detection)
        print("Training Local Outlier Factor...")
        self.lof_detector = LocalOutlierFactor(
            n_neighbors=min(20, max(5, len(X) // 10)),
            contamination=self.contamination,
            novelty=True
        )
        self.lof_detector.fit(X)
        
        # Get ensemble predictions for training data
        if_predictions = self.isolation_forest.predict(X)
        svm_predictions = self.one_class_svm.predict(X)
        lof_predictions = self.lof_detector.predict(X)
        
        # Calculate ensemble scores
        if_scores = self.isolation_forest.decision_function(X)
        svm_scores = self.one_class_svm.decision_function(X)
        lof_scores = self.lof_detector.decision_function(X)
        
        # Normalize scores to [0, 1] range
        if_scores_norm = self._normalize_scores(if_scores)
        svm_scores_norm = self._normalize_scores(svm_scores)
        lof_scores_norm = self._normalize_scores(lof_scores)
        
        # Calculate ensemble predictions
        ensemble_scores = (
            self.model_weights['isolation_forest'] * if_scores_norm +
            self.model_weights['one_class_svm'] * svm_scores_norm +
            self.model_weights['lof'] * lof_scores_norm
        )
        
        # Calculate feature importance (using Isolation Forest)
        self._calculate_feature_importance(X)
        
        # Calculate metrics
        if_anomalies = np.sum(if_predictions == -1)
        svm_anomalies = np.sum(svm_predictions == -1)
        lof_anomalies = np.sum(lof_predictions == -1)
        
        # Ensemble threshold (adaptive based on contamination)
        ensemble_threshold = np.percentile(ensemble_scores, (1 - self.contamination) * 100)
        ensemble_predictions = (ensemble_scores > ensemble_threshold).astype(int)
        ensemble_anomalies = np.sum(ensemble_predictions)
        
        results = {
            'training_samples': len(df),
            'features_used': len(self.feature_columns),
            'model_performance': {
                'isolation_forest': {
                    'anomalies_detected': int(if_anomalies),
                    'anomaly_rate': float(if_anomalies / len(df)),
                    'weight': self.model_weights['isolation_forest']
                },
                'one_class_svm': {
                    'anomalies_detected': int(svm_anomalies),
                    'anomaly_rate': float(svm_anomalies / len(df)),
                    'weight': self.model_weights['one_class_svm']
                },
                'local_outlier_factor': {
                    'anomalies_detected': int(lof_anomalies),
                    'anomaly_rate': float(lof_anomalies / len(df)),
                    'weight': self.model_weights['lof']
                },
                'ensemble': {
                    'anomalies_detected': int(ensemble_anomalies),
                    'anomaly_rate': float(ensemble_anomalies / len(df)),
                    'threshold': float(ensemble_threshold)
                }
            },
            'contamination_param': self.contamination,
            'feature_importance': self.feature_importance,
            'feature_columns': self.feature_columns,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"✅ Ensemble training completed. Detected {ensemble_anomalies} anomalies ({ensemble_anomalies/len(df):.2%} rate)")
        
        return results
    
    def predict_anomaly(self, data: List[Dict]) -> Dict[str, Any]:
        """
        Predict anomalies using ensemble approach with detailed analysis
        
        Args:
            data: Data to analyze for anomalies
            
        Returns:
            Comprehensive prediction results with anomaly scores, types, and explanations
        """
        if self.isolation_forest is None:
            raise ValueError("Models not trained. Call train_ensemble() first.")
        
        print(f"🔍 Predicting anomalies for {len(data)} records...")
        
        # Prepare data
        df = self.prepare_data(data)
        
        # Scale features
        X = self.scale_features(df, fit=False)
        
        # Get predictions from each model
        if_predictions = self.isolation_forest.predict(X)
        svm_predictions = self.one_class_svm.predict(X)
        lof_predictions = self.lof_detector.predict(X)
        
        # Get scores from each model
        if_scores = self.isolation_forest.decision_function(X)
        svm_scores = self.one_class_svm.decision_function(X)
        lof_scores = self.lof_detector.decision_function(X)
        
        # Normalize scores
        if_scores_norm = self._normalize_scores(if_scores)
        svm_scores_norm = self._normalize_scores(svm_scores)
        lof_scores_norm = self._normalize_scores(lof_scores)
        
        # Calculate ensemble scores
        ensemble_scores = (
            self.model_weights['isolation_forest'] * if_scores_norm +
            self.model_weights['one_class_svm'] * svm_scores_norm +
            self.model_weights['lof'] * lof_scores_norm
        )
        
        # Create detailed results
        results_list = []
        for i, (idx, row) in enumerate(df.iterrows()):
            result = {
                'symbol': row['symbol'],
                'ex_dividend_date': row['ex_dividend_date'],
                'anomaly_score': float(ensemble_scores[i]),
                'confidence': self._calculate_confidence(if_scores_norm[i], svm_scores_norm[i], lof_scores_norm[i]),
                'risk_level': self._categorize_risk(ensemble_scores[i]),
                'anomaly_type': self._classify_anomaly_type(row, ensemble_scores[i]),
                'model_scores': {
                    'isolation_forest': float(if_scores_norm[i]),
                    'one_class_svm': float(svm_scores_norm[i]),
                    'local_outlier_factor': float(lof_scores_norm[i])
                },
                'feature_contributions': self._explain_anomaly(row, i),
                'is_anomaly': bool(ensemble_scores[i] > 0.5)
            }
            results_list.append(result)
        
        # Sort by anomaly score (highest first)
        results_list.sort(key=lambda x: x['anomaly_score'], reverse=True)
        
        # Calculate summary statistics
        high_risk_count = sum(1 for r in results_list if r['risk_level'] == 'Critical')
        medium_risk_count = sum(1 for r in results_list if r['risk_level'] in ['High', 'Medium'])
        anomalies_count = sum(1 for r in results_list if r['is_anomaly'])
        
        results = {
            'predictions': results_list,
            'summary': {
                'total_records': len(df),
                'anomalies_detected': anomalies_count,
                'high_risk_alerts': high_risk_count,
                'medium_risk_alerts': medium_risk_count,
                'anomaly_rate': float(anomalies_count / len(df)),
                'score_statistics': {
                    'mean': float(np.mean(ensemble_scores)),
                    'std': float(np.std(ensemble_scores)),
                    'min': float(np.min(ensemble_scores)),
                    'max': float(np.max(ensemble_scores)),
                    'percentiles': {
                        '90th': float(np.percentile(ensemble_scores, 90)),
                        '95th': float(np.percentile(ensemble_scores, 95)),
                        '99th': float(np.percentile(ensemble_scores, 99))
                    }
                }
            },
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"✅ Prediction completed. Found {anomalies_count} anomalies, {high_risk_count} critical alerts")
        
        return results
    
    def predict_anomaly_fast(self, data: List[Dict]) -> Dict[str, Any]:
        """
        Fast anomaly prediction using only Isolation Forest for real-time scenarios
        
        Args:
            data: Data to analyze for anomalies
            
        Returns:
            Fast prediction results with anomaly scores
        """
        if self.isolation_forest is None:
            raise ValueError("Models not trained. Call train_ensemble() first.")
        
        print(f"⚡ Fast anomaly prediction for {len(data)} records (Isolation Forest only)...")
        start_time = time.time()
        
        # Prepare data
        df = self.prepare_data(data)
        
        # Scale features
        X = self.scale_features(df, fit=False)
        
        # Get predictions only from Isolation Forest (fastest)
        if_predictions = self.isolation_forest.predict(X)
        if_scores = self.isolation_forest.decision_function(X)
        if_scores_norm = self._normalize_scores(if_scores)
        
        # Create fast results (simplified structure)
        results_list = []
        for i, (idx, row) in enumerate(df.iterrows()):
            result = {
                'symbol': row['symbol'],
                'ex_dividend_date': row['ex_dividend_date'],
                'anomaly_score': float(if_scores_norm[i]),
                'risk_level': self._categorize_risk(if_scores_norm[i]),
                'is_anomaly': bool(if_predictions[i] == -1),
                'confidence_score': min(0.95, 0.7 + abs(if_scores_norm[i] - 0.5))  # Simplified confidence
            }
            results_list.append(result)
        
        # Sort by anomaly score (highest first)
        results_list.sort(key=lambda x: x['anomaly_score'], reverse=True)
        
        processing_time = time.time() - start_time
        anomalies_count = sum(1 for r in results_list if r['is_anomaly'])
        
        print(f"⚡ Fast prediction completed in {processing_time:.3f}s ({len(data)/processing_time:.1f} records/sec)")
        
        return {
            'predictions': results_list,
            'summary': {
                'total_analyzed': len(data),
                'anomalies_detected': anomalies_count,
                'anomaly_rate': anomalies_count / len(data),
                'processing_time_seconds': processing_time,
                'records_per_second': len(data) / processing_time if processing_time > 0 else 0,
                'mode': 'fast_isolation_forest_only'
            },
            'metadata': {
                'model_used': 'isolation_forest_only',
                'timestamp': datetime.now().isoformat(),
                'performance_optimized': True
            }
        }
    
    def _normalize_scores(self, scores: np.ndarray) -> np.ndarray:
        """
        Normalize anomaly scores to [0, 1] range
        """
        min_score = np.min(scores)
        max_score = np.max(scores)
        if max_score == min_score:
            return np.ones_like(scores) * 0.5
        return (scores - min_score) / (max_score - min_score)
    
    def _calculate_confidence(self, if_score: float, svm_score: float, lof_score: float) -> float:
        """
        Calculate confidence based on agreement between models
        """
        scores = [if_score, svm_score, lof_score]
        mean_score = np.mean(scores)
        std_score = np.std(scores)
        
        # Higher confidence when models agree (low std) and score is extreme
        confidence = (1 - std_score) * (2 * abs(mean_score - 0.5))
        return float(np.clip(confidence, 0, 1))
    
    def _categorize_risk(self, score: float) -> str:
        """
        Categorize risk level based on anomaly score
        """
        if score >= 0.8:
            return 'Critical'
        elif score >= 0.65:
            return 'High'
        elif score >= 0.5:
            return 'Medium'
        else:
            return 'Low'
    
    def _classify_anomaly_type(self, row: pd.Series, score: float) -> List[str]:
        """
        Classify the type of anomaly based on features
        """
        anomaly_types = []
        
        # Check for unusual amount changes
        if abs(row.get('dividend_growth', 0)) > self.anomaly_thresholds['amount_change']:
            anomaly_types.append('unusual_amount_change')
        
        # Check for timing anomalies
        if abs(row.get('days_since_last', 90) - 90) > self.anomaly_thresholds['timing_deviation']:
            anomaly_types.append('timing_anomaly')
        
        # Check for yield spikes
        if row.get('yield_estimate', 0) > self.anomaly_thresholds['yield_spike']:
            anomaly_types.append('yield_spike')
        
        # Check for financial stress signals
        if score > self.anomaly_thresholds['suspension_risk']:
            anomaly_types.append('financial_stress')
        
        # Check for dividend cuts (significant negative growth)
        if row.get('dividend_growth', 0) < -0.1:  # 10% cut
            anomaly_types.append('dividend_cut')
        
        return anomaly_types if anomaly_types else ['general_anomaly']
    
    def _calculate_feature_importance(self, X: np.ndarray) -> None:
        """
        Calculate feature importance using Isolation Forest
        """
        if self.isolation_forest is None:
            return
        
        # Simple feature importance based on isolation paths
        feature_scores = []
        for i in range(X.shape[1]):
            # Create corrupted version of feature
            X_corrupted = X.copy()
            np.random.shuffle(X_corrupted[:, i])
            
            # Compare scores
            original_scores = self.isolation_forest.decision_function(X)
            corrupted_scores = self.isolation_forest.decision_function(X_corrupted)
            
            # Feature importance is the difference in mean scores
            importance = abs(np.mean(original_scores) - np.mean(corrupted_scores))
            feature_scores.append(importance)
        
        # Normalize importance scores
        total_importance = sum(feature_scores)
        if total_importance > 0:
            normalized_scores = [score / total_importance for score in feature_scores]
        else:
            normalized_scores = [1.0 / len(feature_scores)] * len(feature_scores)
        
        # Create feature importance dictionary
        self.feature_importance = {
            self.feature_columns[i]: float(normalized_scores[i])
            for i in range(len(self.feature_columns))
        }
    
    def _explain_anomaly(self, row: pd.Series, index: int) -> Dict[str, float]:
        """
        Explain anomaly by showing feature contributions
        """
        contributions = {}
        
        # Get top contributing features based on importance and values
        for feature in self.feature_columns:
            if feature in row.index and feature in self.feature_importance:
                # Normalize feature value and combine with importance
                feature_value = abs(float(row[feature])) if pd.notna(row[feature]) else 0
                importance = self.feature_importance[feature]
                contribution = feature_value * importance
                contributions[feature] = contribution
        
        # Sort by contribution and return top 5
        sorted_contributions = dict(sorted(contributions.items(), key=lambda x: x[1], reverse=True)[:5])
        
        # Normalize contributions to sum to 1
        total_contribution = sum(sorted_contributions.values())
        if total_contribution > 0:
            normalized_contributions = {
                k: v / total_contribution for k, v in sorted_contributions.items()
            }
        else:
            normalized_contributions = sorted_contributions
        
        return normalized_contributions
    
    # Backward compatibility methods
    def train(self, data: List[Dict], **kwargs) -> Dict[str, Any]:
        """Wrapper for ensemble training (backward compatibility)"""
        return self.train_ensemble(data, **kwargs)
    
    def predict(self, data: List[Dict]) -> Dict[str, Any]:
        """Wrapper for ensemble prediction (backward compatibility)"""
        return self.predict_anomaly(data)
    
    def save_model(self, filepath: str) -> None:
        """
        Save trained ensemble models to file
        
        Args:
            filepath: Path to save the models
        """
        if self.isolation_forest is None:
            raise ValueError("No models to save. Train ensemble first.")
        
        model_data = {
            'isolation_forest': self.isolation_forest,
            'one_class_svm': self.one_class_svm,
            'lof_detector': self.lof_detector,
            'model_weights': self.model_weights,
            'scaler': self.scaler,
            'label_encoders': self.label_encoders,
            'feature_columns': self.feature_columns,
            'categorical_columns': self.categorical_columns,
            'numerical_columns': self.numerical_columns,
            'feature_importance': self.feature_importance,
            'anomaly_thresholds': self.anomaly_thresholds,
            'contamination': self.contamination,
            'timestamp': datetime.now().isoformat()
        }
        
        joblib.dump(model_data, filepath)
        print(f"💾 Ensemble models saved to {filepath}")
    
    def load_model(self, filepath: str) -> None:
        """
        Load trained ensemble models from file
        
        Args:
            filepath: Path to load the models from
        """
        model_data = joblib.load(filepath)
        
        self.isolation_forest = model_data['isolation_forest']
        self.one_class_svm = model_data['one_class_svm']
        self.lof_detector = model_data['lof_detector']
        self.model_weights = model_data.get('model_weights', self.model_weights)
        self.scaler = model_data['scaler']
        self.label_encoders = model_data['label_encoders']
        self.feature_columns = model_data['feature_columns']
        self.categorical_columns = model_data['categorical_columns']
        self.numerical_columns = model_data['numerical_columns']
        self.feature_importance = model_data.get('feature_importance', {})
        self.anomaly_thresholds = model_data.get('anomaly_thresholds', self.anomaly_thresholds)
        self.contamination = model_data['contamination']
        
        print(f"📂 Ensemble models loaded from {filepath}")


def main():
    """
    Main function for command-line interface
    """
    parser = argparse.ArgumentParser(description='Dividend Anomaly Detection - Ensemble Model')
    parser.add_argument('--input', required=True, help='Input data file (JSON)')
    parser.add_argument('--mode', choices=['train', 'predict'], required=True, help='Mode: train or predict')
    parser.add_argument('--output', help='Output directory for models/results')
    parser.add_argument('--model', help='Model file path (for prediction mode)')
    parser.add_argument('--params', help='Training parameters file (JSON)')
    parser.add_argument('--contamination', type=float, default=0.08, help='Expected anomaly rate')
    
    args = parser.parse_args()
    
    try:
        # Load input data
        with open(args.input, 'r') as f:
            payload = json.load(f)
        
        # Unwrap metadata envelope
        if isinstance(payload, dict) and 'data' in payload:
            data = payload['data']
            print(f"📦 Loaded export package:")
            print(f"   Export date: {payload.get('metadata', {}).get('export_date', 'unknown')}")
            print(f"   Data records: {len(data)}")
        else:
            # Fallback for legacy format (flat array)
            data = payload if isinstance(payload, list) else []
            print(f"📚 Loaded {len(data)} records (legacy format)")
        
        if not data:
            print("❌ No data found in input file")
            return
        
        # Initialize detector
        detector = DividendAnomalyDetector(contamination=args.contamination)
        
        if args.mode == 'train':
            # Load training parameters if provided
            params = {}
            if args.params and os.path.exists(args.params):
                with open(args.params, 'r') as f:
                    params = json.load(f)
            
            # Train ensemble model
            results = detector.train_ensemble(data, **params)
            
            # Save model
            if args.output:
                os.makedirs(args.output, exist_ok=True)
                model_path = os.path.join(args.output, 'ensemble_anomaly_detection_model.joblib')
                detector.save_model(model_path)
                results['model_path'] = model_path
            
            # Save training results
            output_dir = args.output or os.path.dirname(args.input)
            results_path = os.path.join(output_dir, 'ensemble_training_results.json')
            with open(results_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"📊 Ensemble training results saved to {results_path}")
            
        elif args.mode == 'predict':
            # Load model
            model_path = args.model
            if not model_path:
                model_path = os.path.join(args.output or '.', 'ensemble_anomaly_detection_model.joblib')
            
            if not os.path.exists(model_path):
                print(f"❌ Model file not found: {model_path}")
                return
            
            detector.load_model(model_path)
            
            # Make predictions
            results = detector.predict_anomaly(data)
            
            # Save results
            output_dir = args.output or os.path.dirname(args.input)
            results_path = os.path.join(output_dir, 'anomaly_results.json')
            with open(results_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"🔍 Anomaly prediction results saved to {results_path}")
            
            # Print critical alerts
            critical_alerts = [r for r in results['predictions'] if r['risk_level'] == 'Critical']
            if critical_alerts:
                print(f"\n🚨 {len(critical_alerts)} CRITICAL ALERTS:")
                for alert in critical_alerts[:5]:  # Show top 5
                    print(f"  {alert['symbol']}: Score {alert['anomaly_score']:.3f} - {alert['anomaly_type']}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()