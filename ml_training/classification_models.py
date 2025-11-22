#!/usr/bin/env python3
"""
Comprehensive Dividend Classification Models for Investment Analytics
Implements both Dividend Safety Rating and Growth Stage Classification
"""

import argparse
import json
import os
import sys
import time
import warnings
from datetime import datetime
from typing import Dict, List, Tuple, Any, Union, Optional

# Suppress warnings
warnings.filterwarnings('ignore')

try:
    import pandas as pd
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split, GridSearchCV, TimeSeriesSplit, cross_val_score
    from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
    from sklearn.metrics import (
        classification_report, confusion_matrix, precision_score, 
        recall_score, f1_score, roc_auc_score, accuracy_score
    )
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    import joblib
    try:
        import xgboost as xgb
        XGBOOST_AVAILABLE = True
    except ImportError:
        XGBOOST_AVAILABLE = False
        print("⚠️ XGBoost not available - will use Gradient Boosting instead")
except ImportError as e:
    print(f"Error importing required packages: {e}")
    print("Please ensure all required packages are installed:")
    print("pip install pandas numpy scikit-learn joblib")
    if not XGBOOST_AVAILABLE:
        print("Optional: pip install xgboost (for enhanced performance)")
    sys.exit(1)


class DividendSafetyClassifier:
    """
    Multi-class classifier for dividend safety ratings
    Classifications: Safe, At Risk, Likely Cut
    """
    
    def __init__(self, random_state: int = 42):
        """Initialize the dividend safety classifier"""
        self.random_state = random_state
        
        # Model ensemble
        self.rf_model = None
        self.xgb_model = None
        self.lr_model = None
        self.ensemble_weights = {'rf': 0.4, 'xgb': 0.4, 'lr': 0.2}
        
        # Data preprocessing
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.preprocessor = None
        
        # Feature columns
        self.numerical_features = [
            'dividend_amount', 'market_cap_log', 'payout_ratio', 'earnings_coverage',
            'free_cash_flow_coverage', 'debt_to_equity', 'dividend_consistency_score',
            'sector_relative_yield', 'earnings_volatility', 'revenue_growth_3yr',
            'earnings_growth_3yr', 'dividend_growth_3yr', 'debt_to_assets',
            'current_ratio', 'roe', 'roa', 'profit_margin', 'operating_margin',
            'dividend_yield', 'beta', 'pe_ratio', 'pb_ratio'
        ]
        
        self.categorical_features = [
            'sector', 'industry', 'market_size_category', 'dividend_frequency',
            'credit_rating_category', 'exchange'
        ]
        
        # Safety classification mapping
        self.safety_classes = ['Safe', 'At Risk', 'Likely Cut']
        self.class_descriptions = {
            'Safe': '90%+ confidence dividend will continue',
            'At Risk': 'Moderate risk 40-60% - some warning signs',
            'Likely Cut': 'High risk 70%+ of cut - poor fundamentals'
        }
        
        # Feature importance tracking
        self.feature_importance = {}
        self.training_metrics = {}
        
    def create_safety_labels(self, data: pd.DataFrame) -> pd.Series:
        """
        Create safety labels based on fundamental indicators
        This is used for supervised learning when historical outcomes are known
        """
        print("🏷️ Creating safety labels based on fundamental indicators...")
        
        labels = []
        for _, row in data.iterrows():
            # Safety scoring based on key metrics
            safety_score = 0
            risk_factors = 0
            
            # Payout ratio assessment (40% weight)
            if pd.notna(row.get('payout_ratio')):
                payout = row['payout_ratio']
                if payout < 0.5:  # Conservative payout
                    safety_score += 40
                elif payout < 0.7:  # Moderate payout
                    safety_score += 25
                elif payout < 0.9:  # High payout
                    safety_score += 10
                    risk_factors += 1
                else:  # Unsustainable payout
                    risk_factors += 3
            
            # Earnings coverage (30% weight)
            if pd.notna(row.get('earnings_coverage')):
                coverage = row['earnings_coverage']
                if coverage > 2.0:  # Strong coverage
                    safety_score += 30
                elif coverage > 1.5:  # Adequate coverage
                    safety_score += 20
                elif coverage > 1.0:  # Marginal coverage
                    safety_score += 10
                    risk_factors += 1
                else:  # Insufficient coverage
                    risk_factors += 3
            
            # Debt levels (20% weight)
            if pd.notna(row.get('debt_to_equity')):
                debt_ratio = row['debt_to_equity']
                if debt_ratio < 0.3:  # Low debt
                    safety_score += 20
                elif debt_ratio < 0.6:  # Moderate debt
                    safety_score += 15
                elif debt_ratio < 1.0:  # High debt
                    safety_score += 5
                    risk_factors += 1
                else:  # Very high debt
                    risk_factors += 2
            
            # Dividend consistency (10% weight)
            if pd.notna(row.get('dividend_consistency_score')):
                consistency = row['dividend_consistency_score']
                if consistency > 0.8:  # Very consistent
                    safety_score += 10
                elif consistency > 0.6:  # Moderately consistent
                    safety_score += 7
                elif consistency > 0.4:  # Somewhat consistent
                    safety_score += 3
                else:  # Inconsistent
                    risk_factors += 1
            
            # Final classification based on score and risk factors
            if risk_factors >= 3 or safety_score < 30:
                labels.append('Likely Cut')
            elif risk_factors >= 1 or safety_score < 60:
                labels.append('At Risk')
            else:
                labels.append('Safe')
        
        return pd.Series(labels)
    
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare and engineer features for safety classification"""
        print(f"🔧 Preparing safety classification features for {len(data)} records...")
        
        df = data.copy()
        
        # Fill missing values with appropriate defaults
        df = df.fillna({
            'dividend_amount': 0,
            'market_cap_log': 0,
            'payout_ratio': 0.5,  # Default moderate payout
            'earnings_coverage': 1.0,  # Default minimal coverage
            'free_cash_flow_coverage': 1.0,
            'debt_to_equity': 0.5,  # Default moderate debt
            'dividend_consistency_score': 0.5,
            'sector_relative_yield': 1.0,
            'earnings_volatility': 0.2,
            'revenue_growth_3yr': 0.03,  # Default 3% growth
            'earnings_growth_3yr': 0.03,
            'dividend_growth_3yr': 0.03,
            'debt_to_assets': 0.3,
            'current_ratio': 1.5,
            'roe': 0.12,  # Default 12% ROE
            'roa': 0.06,  # Default 6% ROA
            'profit_margin': 0.1,
            'operating_margin': 0.15,
            'dividend_yield': 0.03,
            'beta': 1.0,
            'pe_ratio': 15,
            'pb_ratio': 2.0,
            'sector': 'Unknown',
            'industry': 'Unknown',
            'market_size_category': 'Mid Cap',
            'dividend_frequency': 'Quarterly',
            'credit_rating_category': 'Investment Grade',
            'exchange': 'Unknown'
        })
        
        # Create derived features for safety assessment
        df['payout_safety_score'] = df['payout_ratio'].apply(
            lambda x: 1.0 if x < 0.5 else 0.7 if x < 0.7 else 0.3 if x < 0.9 else 0.0
        )
        
        df['coverage_safety_score'] = df['earnings_coverage'].apply(
            lambda x: 1.0 if x > 2.0 else 0.7 if x > 1.5 else 0.3 if x > 1.0 else 0.0
        )
        
        df['debt_safety_score'] = df['debt_to_equity'].apply(
            lambda x: 1.0 if x < 0.3 else 0.7 if x < 0.6 else 0.3 if x < 1.0 else 0.0
        )
        
        # Financial strength composite score
        df['financial_strength'] = (
            df['payout_safety_score'] * 0.4 + 
            df['coverage_safety_score'] * 0.3 + 
            df['debt_safety_score'] * 0.2 + 
            df['dividend_consistency_score'] * 0.1
        )
        
        # Risk flags
        df['high_payout_risk'] = (df['payout_ratio'] > 0.8).astype(int)
        df['low_coverage_risk'] = (df['earnings_coverage'] < 1.2).astype(int)
        df['high_debt_risk'] = (df['debt_to_equity'] > 0.8).astype(int)
        df['earnings_decline_risk'] = (df['earnings_growth_3yr'] < 0).astype(int)
        
        # Total risk score
        df['total_risk_score'] = (
            df['high_payout_risk'] + df['low_coverage_risk'] + 
            df['high_debt_risk'] + df['earnings_decline_risk']
        )
        
        return df
    
    def train_safety_classifier(self, data: pd.DataFrame, labels: Optional[pd.Series] = None) -> Dict[str, Any]:
        """
        Train the dividend safety classifier ensemble
        
        Args:
            data: Feature data
            labels: Target labels (if None, will create labels from fundamentals)
            
        Returns:
            Training results and metrics
        """
        print("🏋️ Training Dividend Safety Classifier...")
        
        # Prepare features
        df = self.prepare_features(data)
        
        # Create or use provided labels
        if labels is None:
            y = self.create_safety_labels(df)
        else:
            y = labels
        
        # Encode labels
        y_encoded = self.label_encoder.fit_transform(y)
        
        # Select and prepare features
        available_numerical = [col for col in self.numerical_features if col in df.columns]
        available_categorical = [col for col in self.categorical_features if col in df.columns]
        
        # Add engineered features
        available_numerical.extend([
            'financial_strength', 'total_risk_score', 'payout_safety_score', 
            'coverage_safety_score', 'debt_safety_score'
        ])
        
        # Create preprocessor
        self.preprocessor = ColumnTransformer(
            transformers=[
                ('num', StandardScaler(), available_numerical),
                ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), available_categorical)
            ],
            remainder='drop'
        )
        
        # Prepare final dataset
        X = df[available_numerical + available_categorical]
        
        # Time-aware split for financial data
        split_point = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_point], X.iloc[split_point:]
        y_train, y_test = y_encoded[:split_point], y_encoded[split_point:]
        
        print(f"📊 Training set: {len(X_train)}, Test set: {len(X_test)}")
        print(f"📊 Class distribution: {dict(zip(*np.unique(y_train, return_counts=True)))}")
        
        # Train ensemble models
        results = {}
        
        # 1. Random Forest
        print("🌲 Training Random Forest...")
        rf_pipeline = Pipeline([
            ('preprocessor', self.preprocessor),
            ('classifier', RandomForestClassifier(
                n_estimators=100,
                max_depth=15,
                min_samples_split=10,
                min_samples_leaf=5,
                class_weight='balanced',
                random_state=self.random_state,
                n_jobs=-1
            ))
        ])
        
        rf_pipeline.fit(X_train, y_train)
        self.rf_model = rf_pipeline
        
        # Evaluate Random Forest
        rf_pred = rf_pipeline.predict(X_test)
        rf_prob = rf_pipeline.predict_proba(X_test)
        results['rf'] = {
            'accuracy': accuracy_score(y_test, rf_pred),
            'precision': precision_score(y_test, rf_pred, average='weighted'),
            'recall': recall_score(y_test, rf_pred, average='weighted'),
            'f1': f1_score(y_test, rf_pred, average='weighted')
        }
        
        # 2. XGBoost or Gradient Boosting
        if XGBOOST_AVAILABLE:
            print("🚀 Training XGBoost...")
            xgb_pipeline = Pipeline([
                ('preprocessor', self.preprocessor),
                ('classifier', xgb.XGBClassifier(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=self.random_state,
                    eval_metric='mlogloss'
                ))
            ])
        else:
            print("📈 Training Gradient Boosting...")
            xgb_pipeline = Pipeline([
                ('preprocessor', self.preprocessor),
                ('classifier', GradientBoostingClassifier(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    random_state=self.random_state
                ))
            ])
        
        xgb_pipeline.fit(X_train, y_train)
        self.xgb_model = xgb_pipeline
        
        # Evaluate XGBoost/GBM
        xgb_pred = xgb_pipeline.predict(X_test)
        xgb_prob = xgb_pipeline.predict_proba(X_test)
        results['xgb'] = {
            'accuracy': accuracy_score(y_test, xgb_pred),
            'precision': precision_score(y_test, xgb_pred, average='weighted'),
            'recall': recall_score(y_test, xgb_pred, average='weighted'),
            'f1': f1_score(y_test, xgb_pred, average='weighted')
        }
        
        # 3. Logistic Regression
        print("📊 Training Logistic Regression...")
        lr_pipeline = Pipeline([
            ('preprocessor', self.preprocessor),
            ('classifier', LogisticRegression(
                multi_class='multinomial',
                solver='lbfgs',
                class_weight='balanced',
                random_state=self.random_state,
                max_iter=1000
            ))
        ])
        
        lr_pipeline.fit(X_train, y_train)
        self.lr_model = lr_pipeline
        
        # Evaluate Logistic Regression
        lr_pred = lr_pipeline.predict(X_test)
        lr_prob = lr_pipeline.predict_proba(X_test)
        results['lr'] = {
            'accuracy': accuracy_score(y_test, lr_pred),
            'precision': precision_score(y_test, lr_pred, average='weighted'),
            'recall': recall_score(y_test, lr_pred, average='weighted'),
            'f1': f1_score(y_test, lr_pred, average='weighted')
        }
        
        # Ensemble prediction
        ensemble_prob = (
            rf_prob * self.ensemble_weights['rf'] + 
            xgb_prob * self.ensemble_weights['xgb'] + 
            lr_prob * self.ensemble_weights['lr']
        )
        ensemble_pred = np.argmax(ensemble_prob, axis=1)
        
        results['ensemble'] = {
            'accuracy': accuracy_score(y_test, ensemble_pred),
            'precision': precision_score(y_test, ensemble_pred, average='weighted'),
            'recall': recall_score(y_test, ensemble_pred, average='weighted'),
            'f1': f1_score(y_test, ensemble_pred, average='weighted')
        }
        
        # Store training metrics
        self.training_metrics = {
            'timestamp': datetime.now().isoformat(),
            'training_size': len(X_train),
            'test_size': len(X_test),
            'classes': self.safety_classes,
            'results': results,
            'feature_count': len(available_numerical + available_categorical)
        }
        
        print("✅ Safety classifier training completed!")
        print(f"📊 Ensemble Accuracy: {results['ensemble']['accuracy']:.3f}")
        
        return self.training_metrics
    
    def predict_safety(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Predict dividend safety ratings for given data
        
        Args:
            data: Feature data for prediction
            
        Returns:
            List of safety predictions with confidence and reasoning
        """
        print(f"🔮 Predicting safety ratings for {len(data)} records...")
        
        if not all([self.rf_model, self.xgb_model, self.lr_model]):
            raise ValueError("Models not trained. Please train the classifier first.")
        
        # Prepare features
        df = self.prepare_features(data)
        
        # Get feature columns
        available_numerical = [col for col in self.numerical_features if col in df.columns]
        available_categorical = [col for col in self.categorical_features if col in df.columns]
        available_numerical.extend([
            'financial_strength', 'total_risk_score', 'payout_safety_score', 
            'coverage_safety_score', 'debt_safety_score'
        ])
        
        X = df[available_numerical + available_categorical]
        
        # Get individual model predictions
        rf_prob = self.rf_model.predict_proba(X)
        xgb_prob = self.xgb_model.predict_proba(X)
        lr_prob = self.lr_model.predict_proba(X)
        
        # Ensemble prediction
        ensemble_prob = (
            rf_prob * self.ensemble_weights['rf'] + 
            xgb_prob * self.ensemble_weights['xgb'] + 
            lr_prob * self.ensemble_weights['lr']
        )
        
        ensemble_pred = np.argmax(ensemble_prob, axis=1)
        
        # Prepare results
        results = []
        for i, (pred_idx, probs) in enumerate(zip(ensemble_pred, ensemble_prob)):
            # Get prediction details
            predicted_class = self.label_encoder.inverse_transform([pred_idx])[0]
            confidence = float(probs[pred_idx])
            
            # Generate reasoning based on key features
            reasoning = self._generate_safety_reasoning(df.iloc[i], predicted_class, probs)
            
            # Feature importance for this prediction
            feature_importance = self._get_prediction_features(df.iloc[i])
            
            result = {
                'symbol': df.iloc[i].get('symbol', f'STOCK_{i}'),
                'rating': predicted_class,
                'confidence': confidence,
                'class_probabilities': {
                    class_name: float(prob) 
                    for class_name, prob in zip(self.safety_classes, probs)
                },
                'reasoning': reasoning,
                'features_used': feature_importance,
                'risk_score': float(df.iloc[i]['total_risk_score']),
                'financial_strength': float(df.iloc[i]['financial_strength']),
                'timestamp': datetime.now().isoformat()
            }
            results.append(result)
        
        return results
    
    def _generate_safety_reasoning(self, row: pd.Series, prediction: str, probabilities: np.ndarray) -> List[str]:
        """Generate human-readable reasoning for safety prediction"""
        reasoning = []
        
        # Payout ratio analysis
        payout = row.get('payout_ratio', 0.5)
        if payout < 0.5:
            reasoning.append(f"Conservative payout ratio of {payout:.1%} indicates sustainable dividends")
        elif payout > 0.8:
            reasoning.append(f"High payout ratio of {payout:.1%} raises sustainability concerns")
        
        # Earnings coverage
        coverage = row.get('earnings_coverage', 1.0)
        if coverage > 2.0:
            reasoning.append(f"Strong earnings coverage of {coverage:.1f}x provides dividend security")
        elif coverage < 1.2:
            reasoning.append(f"Low earnings coverage of {coverage:.1f}x indicates potential dividend risk")
        
        # Debt levels
        debt_ratio = row.get('debt_to_equity', 0.5)
        if debt_ratio < 0.3:
            reasoning.append(f"Low debt-to-equity ratio of {debt_ratio:.1f} supports financial stability")
        elif debt_ratio > 0.8:
            reasoning.append(f"High debt-to-equity ratio of {debt_ratio:.1f} increases financial risk")
        
        # Consistency score
        consistency = row.get('dividend_consistency_score', 0.5)
        if consistency > 0.8:
            reasoning.append(f"Excellent dividend consistency score of {consistency:.1%}")
        elif consistency < 0.4:
            reasoning.append(f"Poor dividend consistency score of {consistency:.1%}")
        
        # Growth trends
        earnings_growth = row.get('earnings_growth_3yr', 0.03)
        if earnings_growth < 0:
            reasoning.append(f"Declining earnings growth of {earnings_growth:.1%} over 3 years")
        elif earnings_growth > 0.1:
            reasoning.append(f"Strong earnings growth of {earnings_growth:.1%} over 3 years")
        
        return reasoning
    
    def _get_prediction_features(self, row: pd.Series) -> Dict[str, float]:
        """Get key features used in prediction"""
        feature_dict = {}
        
        key_features = [
            'payout_ratio', 'earnings_coverage', 'debt_to_equity', 
            'dividend_consistency_score', 'financial_strength', 'total_risk_score'
        ]
        
        for feature in key_features:
            if feature in row:
                feature_dict[feature] = float(row[feature])
        
        return feature_dict


class DividendGrowthClassifier:
    """
    Multi-class classifier for dividend growth stages
    Classifications: Growth, Mature, Declining
    """
    
    def __init__(self, random_state: int = 42):
        """Initialize the dividend growth classifier"""
        self.random_state = random_state
        
        # Model ensemble
        self.rf_model = None
        self.xgb_model = None
        self.lr_model = None
        self.ensemble_weights = {'rf': 0.4, 'xgb': 0.4, 'lr': 0.2}
        
        # Data preprocessing
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.preprocessor = None
        
        # Feature columns for growth classification
        self.numerical_features = [
            'dividend_growth_1yr', 'dividend_growth_3yr', 'dividend_growth_5yr',
            'revenue_growth_1yr', 'revenue_growth_3yr', 'revenue_growth_5yr',
            'earnings_growth_1yr', 'earnings_growth_3yr', 'earnings_growth_5yr',
            'company_age', 'market_cap_log', 'dividend_yield', 'payout_ratio',
            'reinvestment_rate', 'capex_to_revenue', 'rd_to_revenue',
            'dividend_growth_volatility', 'earnings_volatility', 'revenue_volatility',
            'market_share_trend', 'industry_growth_rate', 'beta'
        ]
        
        self.categorical_features = [
            'sector', 'industry', 'market_size_category', 'industry_lifecycle_stage',
            'business_model', 'capital_intensity_category', 'geographic_focus'
        ]
        
        # Growth classification mapping
        self.growth_classes = ['Growth', 'Mature', 'Declining']
        self.class_descriptions = {
            'Growth': 'Increasing dividends 5%+ annually - expanding businesses',
            'Mature': 'Stable dividends 0-5% growth - established companies',
            'Declining': 'Flat/decreasing dividends - mature industries'
        }
        
        # Training metrics
        self.training_metrics = {}
    
    def create_growth_labels(self, data: pd.DataFrame) -> pd.Series:
        """
        Create growth stage labels based on dividend and business metrics
        """
        print("🏷️ Creating growth stage labels based on dividend trends...")
        
        labels = []
        for _, row in data.iterrows():
            growth_score = 0
            maturity_indicators = 0
            decline_indicators = 0
            
            # Dividend growth analysis (50% weight)
            div_growth_3yr = row.get('dividend_growth_3yr', 0.03)
            div_growth_5yr = row.get('dividend_growth_5yr', 0.03)
            
            if div_growth_3yr > 0.05 and div_growth_5yr > 0.05:  # Consistent 5%+ growth
                growth_score += 50
            elif div_growth_3yr > 0.02 and div_growth_5yr > 0.0:  # Modest growth
                growth_score += 30
                maturity_indicators += 1
            elif div_growth_3yr < 0.0 or div_growth_5yr < 0.0:  # Declining dividends
                decline_indicators += 3
            else:  # Flat growth
                maturity_indicators += 2
            
            # Business growth analysis (30% weight)
            earnings_growth = row.get('earnings_growth_3yr', 0.03)
            revenue_growth = row.get('revenue_growth_3yr', 0.03)
            
            if earnings_growth > 0.08 and revenue_growth > 0.05:  # Strong business growth
                growth_score += 30
            elif earnings_growth > 0.03 and revenue_growth > 0.02:  # Moderate growth
                growth_score += 15
                maturity_indicators += 1
            elif earnings_growth < 0.0 or revenue_growth < 0.0:  # Declining business
                decline_indicators += 2
            
            # Company maturity analysis (20% weight)
            company_age = row.get('company_age', 10)
            payout_ratio = row.get('payout_ratio', 0.5)
            
            if company_age > 30 and payout_ratio > 0.7:  # Mature company characteristics
                maturity_indicators += 2
            elif company_age < 15 and payout_ratio < 0.5:  # Young, growing company
                growth_score += 20
            
            # Final classification
            if decline_indicators >= 2 or (growth_score < 20 and maturity_indicators >= 2):
                labels.append('Declining')
            elif growth_score >= 60 or (growth_score >= 40 and maturity_indicators == 0):
                labels.append('Growth')
            else:
                labels.append('Mature')
        
        return pd.Series(labels)
    
    def prepare_growth_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare and engineer features for growth classification"""
        print(f"🔧 Preparing growth classification features for {len(data)} records...")
        
        df = data.copy()
        
        # Fill missing values
        df = df.fillna({
            'dividend_growth_1yr': 0.03,
            'dividend_growth_3yr': 0.03,
            'dividend_growth_5yr': 0.03,
            'revenue_growth_1yr': 0.03,
            'revenue_growth_3yr': 0.03,
            'revenue_growth_5yr': 0.03,
            'earnings_growth_1yr': 0.03,
            'earnings_growth_3yr': 0.03,
            'earnings_growth_5yr': 0.03,
            'company_age': 10,
            'market_cap_log': 0,
            'dividend_yield': 0.03,
            'payout_ratio': 0.5,
            'reinvestment_rate': 0.3,
            'capex_to_revenue': 0.05,
            'rd_to_revenue': 0.02,
            'dividend_growth_volatility': 0.1,
            'earnings_volatility': 0.2,
            'revenue_volatility': 0.1,
            'market_share_trend': 0.0,
            'industry_growth_rate': 0.03,
            'beta': 1.0,
            'sector': 'Unknown',
            'industry': 'Unknown',
            'market_size_category': 'Mid Cap',
            'industry_lifecycle_stage': 'Mature',
            'business_model': 'Traditional',
            'capital_intensity_category': 'Medium',
            'geographic_focus': 'Domestic'
        })
        
        # Create composite growth metrics
        df['avg_dividend_growth'] = (
            df['dividend_growth_1yr'] * 0.5 + 
            df['dividend_growth_3yr'] * 0.3 + 
            df['dividend_growth_5yr'] * 0.2
        )
        
        df['avg_business_growth'] = (
            df['earnings_growth_3yr'] * 0.6 + 
            df['revenue_growth_3yr'] * 0.4
        )
        
        df['growth_consistency'] = 1.0 - (
            df['dividend_growth_volatility'] * 0.6 + 
            df['earnings_volatility'] * 0.4
        )
        
        # Maturity indicators
        df['maturity_score'] = (
            (df['company_age'] / 50) * 0.4 + 
            df['payout_ratio'] * 0.3 + 
            (1 - df['reinvestment_rate']) * 0.3
        )
        
        # Growth momentum
        df['growth_momentum'] = (
            df['avg_dividend_growth'] * 0.4 + 
            df['avg_business_growth'] * 0.4 + 
            df['industry_growth_rate'] * 0.2
        )
        
        # Innovation proxy
        df['innovation_score'] = (
            df['rd_to_revenue'] * 0.6 + 
            df['capex_to_revenue'] * 0.4
        )
        
        return df
    
    def train_growth_classifier(self, data: pd.DataFrame, labels: Optional[pd.Series] = None) -> Dict[str, Any]:
        """Train the dividend growth classifier ensemble"""
        print("🏋️ Training Dividend Growth Classifier...")
        
        # Prepare features
        df = self.prepare_growth_features(data)
        
        # Create or use provided labels
        if labels is None:
            y = self.create_growth_labels(df)
        else:
            y = labels
        
        # Encode labels
        y_encoded = self.label_encoder.fit_transform(y)
        
        # Select features
        available_numerical = [col for col in self.numerical_features if col in df.columns]
        available_categorical = [col for col in self.categorical_features if col in df.columns]
        
        # Add engineered features
        available_numerical.extend([
            'avg_dividend_growth', 'avg_business_growth', 'growth_consistency',
            'maturity_score', 'growth_momentum', 'innovation_score'
        ])
        
        # Create preprocessor
        self.preprocessor = ColumnTransformer(
            transformers=[
                ('num', StandardScaler(), available_numerical),
                ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), available_categorical)
            ],
            remainder='drop'
        )
        
        # Prepare dataset
        X = df[available_numerical + available_categorical]
        
        # Time-aware split
        split_point = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_point], X.iloc[split_point:]
        y_train, y_test = y_encoded[:split_point], y_encoded[split_point:]
        
        print(f"📊 Training set: {len(X_train)}, Test set: {len(X_test)}")
        print(f"📊 Class distribution: {dict(zip(*np.unique(y_train, return_counts=True)))}")
        
        # Train ensemble models (same structure as safety classifier)
        results = {}
        
        # Random Forest
        print("🌲 Training Random Forest for Growth Classification...")
        rf_pipeline = Pipeline([
            ('preprocessor', self.preprocessor),
            ('classifier', RandomForestClassifier(
                n_estimators=100,
                max_depth=12,
                min_samples_split=8,
                min_samples_leaf=4,
                class_weight='balanced',
                random_state=self.random_state,
                n_jobs=-1
            ))
        ])
        
        rf_pipeline.fit(X_train, y_train)
        self.rf_model = rf_pipeline
        
        rf_pred = rf_pipeline.predict(X_test)
        results['rf'] = {
            'accuracy': accuracy_score(y_test, rf_pred),
            'precision': precision_score(y_test, rf_pred, average='weighted'),
            'recall': recall_score(y_test, rf_pred, average='weighted'),
            'f1': f1_score(y_test, rf_pred, average='weighted')
        }
        
        # XGBoost/Gradient Boosting
        if XGBOOST_AVAILABLE:
            print("🚀 Training XGBoost for Growth Classification...")
            xgb_pipeline = Pipeline([
                ('preprocessor', self.preprocessor),
                ('classifier', xgb.XGBClassifier(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=self.random_state,
                    eval_metric='mlogloss'
                ))
            ])
        else:
            print("📈 Training Gradient Boosting for Growth Classification...")
            xgb_pipeline = Pipeline([
                ('preprocessor', self.preprocessor),
                ('classifier', GradientBoostingClassifier(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    random_state=self.random_state
                ))
            ])
        
        xgb_pipeline.fit(X_train, y_train)
        self.xgb_model = xgb_pipeline
        
        xgb_pred = xgb_pipeline.predict(X_test)
        results['xgb'] = {
            'accuracy': accuracy_score(y_test, xgb_pred),
            'precision': precision_score(y_test, xgb_pred, average='weighted'),
            'recall': recall_score(y_test, xgb_pred, average='weighted'),
            'f1': f1_score(y_test, xgb_pred, average='weighted')
        }
        
        # Logistic Regression
        print("📊 Training Logistic Regression for Growth Classification...")
        lr_pipeline = Pipeline([
            ('preprocessor', self.preprocessor),
            ('classifier', LogisticRegression(
                multi_class='multinomial',
                solver='lbfgs',
                class_weight='balanced',
                random_state=self.random_state,
                max_iter=1000
            ))
        ])
        
        lr_pipeline.fit(X_train, y_train)
        self.lr_model = lr_pipeline
        
        lr_pred = lr_pipeline.predict(X_test)
        results['lr'] = {
            'accuracy': accuracy_score(y_test, lr_pred),
            'precision': precision_score(y_test, lr_pred, average='weighted'),
            'recall': recall_score(y_test, lr_pred, average='weighted'),
            'f1': f1_score(y_test, lr_pred, average='weighted')
        }
        
        # Ensemble evaluation
        rf_prob = rf_pipeline.predict_proba(X_test)
        xgb_prob = xgb_pipeline.predict_proba(X_test)
        lr_prob = lr_pipeline.predict_proba(X_test)
        
        ensemble_prob = (
            rf_prob * self.ensemble_weights['rf'] + 
            xgb_prob * self.ensemble_weights['xgb'] + 
            lr_prob * self.ensemble_weights['lr']
        )
        ensemble_pred = np.argmax(ensemble_prob, axis=1)
        
        results['ensemble'] = {
            'accuracy': accuracy_score(y_test, ensemble_pred),
            'precision': precision_score(y_test, ensemble_pred, average='weighted'),
            'recall': recall_score(y_test, ensemble_pred, average='weighted'),
            'f1': f1_score(y_test, ensemble_pred, average='weighted')
        }
        
        # Store training metrics
        self.training_metrics = {
            'timestamp': datetime.now().isoformat(),
            'training_size': len(X_train),
            'test_size': len(X_test),
            'classes': self.growth_classes,
            'results': results,
            'feature_count': len(available_numerical + available_categorical)
        }
        
        print("✅ Growth classifier training completed!")
        print(f"📊 Ensemble Accuracy: {results['ensemble']['accuracy']:.3f}")
        
        return self.training_metrics
    
    def predict_growth_stage(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Predict dividend growth stages for given data"""
        print(f"🔮 Predicting growth stages for {len(data)} records...")
        
        if not all([self.rf_model, self.xgb_model, self.lr_model]):
            raise ValueError("Models not trained. Please train the classifier first.")
        
        # Prepare features
        df = self.prepare_growth_features(data)
        
        # Get features
        available_numerical = [col for col in self.numerical_features if col in df.columns]
        available_categorical = [col for col in self.categorical_features if col in df.columns]
        available_numerical.extend([
            'avg_dividend_growth', 'avg_business_growth', 'growth_consistency',
            'maturity_score', 'growth_momentum', 'innovation_score'
        ])
        
        X = df[available_numerical + available_categorical]
        
        # Get predictions
        rf_prob = self.rf_model.predict_proba(X)
        xgb_prob = self.xgb_model.predict_proba(X)
        lr_prob = self.lr_model.predict_proba(X)
        
        # Ensemble prediction
        ensemble_prob = (
            rf_prob * self.ensemble_weights['rf'] + 
            xgb_prob * self.ensemble_weights['xgb'] + 
            lr_prob * self.ensemble_weights['lr']
        )
        ensemble_pred = np.argmax(ensemble_prob, axis=1)
        
        # Prepare results
        results = []
        for i, (pred_idx, probs) in enumerate(zip(ensemble_pred, ensemble_prob)):
            predicted_class = self.label_encoder.inverse_transform([pred_idx])[0]
            confidence = float(probs[pred_idx])
            
            reasoning = self._generate_growth_reasoning(df.iloc[i], predicted_class, probs)
            feature_importance = self._get_growth_features(df.iloc[i])
            
            result = {
                'symbol': df.iloc[i].get('symbol', f'STOCK_{i}'),
                'growth_stage': predicted_class,
                'confidence': confidence,
                'class_probabilities': {
                    class_name: float(prob) 
                    for class_name, prob in zip(self.growth_classes, probs)
                },
                'reasoning': reasoning,
                'features_used': feature_importance,
                'growth_momentum': float(df.iloc[i]['growth_momentum']),
                'maturity_score': float(df.iloc[i]['maturity_score']),
                'timestamp': datetime.now().isoformat()
            }
            results.append(result)
        
        return results
    
    def _generate_growth_reasoning(self, row: pd.Series, prediction: str, probabilities: np.ndarray) -> List[str]:
        """Generate reasoning for growth prediction"""
        reasoning = []
        
        # Dividend growth trends
        div_growth_3yr = row.get('dividend_growth_3yr', 0.03)
        if div_growth_3yr > 0.05:
            reasoning.append(f"Strong dividend growth of {div_growth_3yr:.1%} over 3 years")
        elif div_growth_3yr < 0:
            reasoning.append(f"Declining dividend growth of {div_growth_3yr:.1%} over 3 years")
        
        # Business growth
        earnings_growth = row.get('earnings_growth_3yr', 0.03)
        if earnings_growth > 0.08:
            reasoning.append(f"Robust earnings growth of {earnings_growth:.1%} supports future dividend increases")
        elif earnings_growth < 0:
            reasoning.append(f"Declining earnings growth of {earnings_growth:.1%} limits dividend growth potential")
        
        # Company maturity
        company_age = row.get('company_age', 10)
        payout_ratio = row.get('payout_ratio', 0.5)
        if company_age > 30 and payout_ratio > 0.7:
            reasoning.append(f"Mature company profile (age: {company_age} years, payout: {payout_ratio:.1%})")
        elif company_age < 15 and payout_ratio < 0.5:
            reasoning.append(f"Young growing company (age: {company_age} years, payout: {payout_ratio:.1%})")
        
        return reasoning
    
    def _get_growth_features(self, row: pd.Series) -> Dict[str, float]:
        """Get key growth features"""
        feature_dict = {}
        
        key_features = [
            'dividend_growth_3yr', 'earnings_growth_3yr', 'revenue_growth_3yr',
            'growth_momentum', 'maturity_score', 'innovation_score'
        ]
        
        for feature in key_features:
            if feature in row:
                feature_dict[feature] = float(row[feature])
        
        return feature_dict


def main():
    """Main execution function for command line usage"""
    parser = argparse.ArgumentParser(description='Dividend Classification Models')
    parser.add_argument('--input', type=str, required=True, help='Input data file (JSON)')
    parser.add_argument('--mode', type=str, required=True, choices=['train', 'predict'], help='Mode: train or predict')
    parser.add_argument('--model_type', type=str, required=True, choices=['safety', 'growth'], help='Model type: safety or growth')
    parser.add_argument('--output', type=str, required=True, help='Output directory')
    parser.add_argument('--params', type=str, help='Parameters file (JSON)')
    
    args = parser.parse_args()
    
    print(f"🚀 Starting {args.model_type} classification in {args.mode} mode...")
    
    # Load input data
    try:
        with open(args.input, 'r') as f:
            input_data = json.load(f)
        print(f"📊 Loaded {len(input_data)} records from {args.input}")
    except Exception as e:
        print(f"❌ Error loading input data: {e}")
        sys.exit(1)
    
    # Load parameters if provided
    params = {}
    if args.params and os.path.exists(args.params):
        try:
            with open(args.params, 'r') as f:
                params = json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading parameters: {e}")
    
    # Convert to DataFrame
    df = pd.DataFrame(input_data)
    
    try:
        if args.model_type == 'safety':
            classifier = DividendSafetyClassifier()
            
            if args.mode == 'train':
                # Train safety classifier
                results = classifier.train_safety_classifier(df)
                
                # Save model
                model_file = os.path.join(args.output, 'dividend_safety_classifier.joblib')
                joblib.dump(classifier, model_file)
                
                # Save results
                results_file = os.path.join(args.output, 'safety_training_results.json')
                with open(results_file, 'w') as f:
                    json.dump(results, f, indent=2)
                
                print(f"✅ Safety classifier saved to {model_file}")
                
            elif args.mode == 'predict':
                # Load trained model
                model_file = os.path.join(args.output, 'dividend_safety_classifier.joblib')
                if os.path.exists(model_file):
                    classifier = joblib.load(model_file)
                    predictions = classifier.predict_safety(df)
                    
                    # Save predictions
                    pred_file = os.path.join(args.output, 'safety_predictions.json')
                    with open(pred_file, 'w') as f:
                        json.dump(predictions, f, indent=2)
                    
                    print(f"✅ Safety predictions saved to {pred_file}")
                else:
                    print(f"❌ Model file not found: {model_file}")
                    sys.exit(1)
        
        elif args.model_type == 'growth':
            classifier = DividendGrowthClassifier()
            
            if args.mode == 'train':
                # Train growth classifier
                results = classifier.train_growth_classifier(df)
                
                # Save model
                model_file = os.path.join(args.output, 'dividend_growth_classifier.joblib')
                joblib.dump(classifier, model_file)
                
                # Save results
                results_file = os.path.join(args.output, 'growth_training_results.json')
                with open(results_file, 'w') as f:
                    json.dump(results, f, indent=2)
                
                print(f"✅ Growth classifier saved to {model_file}")
                
            elif args.mode == 'predict':
                # Load trained model
                model_file = os.path.join(args.output, 'dividend_growth_classifier.joblib')
                if os.path.exists(model_file):
                    classifier = joblib.load(model_file)
                    predictions = classifier.predict_growth_stage(df)
                    
                    # Save predictions
                    pred_file = os.path.join(args.output, 'growth_predictions.json')
                    with open(pred_file, 'w') as f:
                        json.dump(predictions, f, indent=2)
                    
                    print(f"✅ Growth predictions saved to {pred_file}")
                else:
                    print(f"❌ Model file not found: {model_file}")
                    sys.exit(1)
    
    except Exception as e:
        print(f"❌ Error during {args.mode}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("🎉 Classification completed successfully!")


if __name__ == "__main__":
    main()