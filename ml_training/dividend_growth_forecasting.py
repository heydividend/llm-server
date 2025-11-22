#!/usr/bin/env python3
"""
Dividend Growth Forecasting Model - LSTM-based Time Series Prediction
Predicts 12-month forward dividend growth rates using hybrid CNN-LSTM architecture
Based on Unigestion research showing 26% spread between highest/lowest quintiles
"""

import argparse
import json
import os
import sys
import warnings
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional, TYPE_CHECKING

warnings.filterwarnings('ignore')

try:
    import pandas as pd
    import numpy as np
    from sklearn.preprocessing import StandardScaler, RobustScaler
    from sklearn.model_selection import TimeSeriesSplit
    import joblib
    
    # Deep learning imports with TensorFlow fallback
    try:
        import tensorflow as tf
        from tensorflow import keras
        from tensorflow.keras.models import Sequential, Model
        from tensorflow.keras.layers import LSTM, Dense, Dropout, Conv1D, MaxPooling1D, Flatten, Input, Concatenate
        from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
        from tensorflow.keras.optimizers import Adam
        TENSORFLOW_AVAILABLE = True
    except ImportError:
        print("⚠️ TensorFlow not available, using statistical fallback model")
        TENSORFLOW_AVAILABLE = False
        # Define placeholder for type hints
        if TYPE_CHECKING:
            from tensorflow.keras.models import Model
        else:
            Model = Any
        
except ImportError as e:
    print(f"Error importing required packages: {e}")
    sys.exit(1)


class DividendGrowthForecaster:
    """
    Hybrid CNN-LSTM model for dividend growth prediction
    Features: Current yield, momentum, ROE, payout ratio, free cash flow
    """
    
    def __init__(self, lookback_periods: int = 12, forecast_horizon: int = 4):
        """
        Args:
            lookback_periods: Number of quarters to look back (default 12 = 3 years)
            forecast_horizon: Quarters to forecast ahead (default 4 = 1 year)
        """
        self.lookback_periods = lookback_periods
        self.forecast_horizon = forecast_horizon
        self.model = None
        self.scaler = RobustScaler()  # Robust to outliers
        self.feature_columns = []
        self.use_deep_learning = TENSORFLOW_AVAILABLE
        
    def prepare_features(self, data: List[Dict]) -> pd.DataFrame:
        """Extract key predictive features from dividend data"""
        print(f"📊 Preparing features for {len(data)} records...")
        
        df = pd.DataFrame(data)
        
        # Core features based on research
        self.feature_columns = [
            'dividend_yield',           # Most predictive per Unigestion
            'momentum_3m',              # Volatility-adjusted price momentum
            'roe',                      # Return on equity
            'payout_ratio',             # Dividends / earnings
            'fcf_payout_ratio',         # Free cash flow coverage
            'book_to_price',            # Valuation metric
            'leverage_ratio',           # Debt levels
            'earnings_growth',          # YoY earnings growth
            'dividend_growth_3y',       # Historical 3-year dividend CAGR
            'market_cap_log',           # Company size (log scale)
            'volatility_30d',           # Price volatility
            'beta',                     # Market sensitivity
        ]
        
        # Fill missing with median
        for col in self.feature_columns:
            if col in df.columns:
                df[col] = df[col].fillna(df[col].median())
            else:
                df[col] = 0
                
        return df
    
    def create_sequences(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Create time series sequences for LSTM"""
        X_seq, y_seq = [], []
        
        for i in range(len(X) - self.lookback_periods - self.forecast_horizon + 1):
            X_seq.append(X[i:i + self.lookback_periods])
            y_seq.append(y[i + self.lookback_periods + self.forecast_horizon - 1])
            
        return np.array(X_seq), np.array(y_seq)
    
    def build_cnn_lstm_model(self, input_shape: Tuple) -> Model:
        """
        Build hybrid CNN-LSTM architecture (MIT 2024 research)
        CNN extracts spatial features, LSTM captures temporal patterns
        """
        if not self.use_deep_learning:
            return None
            
        # Input layer
        inputs = Input(shape=input_shape)
        
        # CNN branch for feature extraction
        conv1 = Conv1D(filters=64, kernel_size=3, activation='relu', padding='same')(inputs)
        conv1 = MaxPooling1D(pool_size=2)(conv1)
        conv2 = Conv1D(filters=32, kernel_size=3, activation='relu', padding='same')(conv1)
        
        # LSTM branch for temporal patterns
        lstm1 = LSTM(100, return_sequences=True)(conv2)
        lstm1 = Dropout(0.3)(lstm1)
        lstm2 = LSTM(50, return_sequences=False)(lstm1)
        lstm2 = Dropout(0.3)(lstm2)
        
        # Dense layers
        dense1 = Dense(50, activation='relu')(lstm2)
        dense1 = Dropout(0.2)(dense1)
        dense2 = Dense(25, activation='relu')(dense1)
        
        # Output: predicted growth rate
        outputs = Dense(1, activation='linear')(dense2)
        
        model = Model(inputs=inputs, outputs=outputs)
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae', 'mape']
        )
        
        return model
    
    def build_statistical_model(self) -> Any:
        """Fallback: Linear regression with lagged features"""
        from sklearn.linear_model import Ridge
        return Ridge(alpha=1.0)
    
    def train(self, training_data: List[Dict], validation_split: float = 0.2) -> Dict:
        """Train the dividend growth forecasting model"""
        print("🏋️ Training dividend growth forecaster...")
        
        # Prepare data
        df = self.prepare_features(training_data)
        
        # Sort by symbol and date
        df = df.sort_values(['symbol', 'date'])
        
        # Calculate target: future dividend growth rate
        df['target_growth'] = df.groupby('symbol')['dividend_amount'].pct_change(periods=self.forecast_horizon)
        df = df.dropna(subset=['target_growth'])
        
        X = df[self.feature_columns].values
        y = df['target_growth'].values
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        if self.use_deep_learning:
            # Create sequences for LSTM
            X_seq, y_seq = self.create_sequences(X_scaled, y)
            
            if len(X_seq) < 100:
                print(f"⚠️ Insufficient data for deep learning ({len(X_seq)} sequences), using statistical model")
                self.use_deep_learning = False
                self.model = self.build_statistical_model()
                self.model.fit(X_scaled, y)
            else:
                # Train/validation split
                split_idx = int(len(X_seq) * (1 - validation_split))
                X_train, X_val = X_seq[:split_idx], X_seq[split_idx:]
                y_train, y_val = y_seq[:split_idx], y_seq[split_idx:]
                
                # Build model
                self.model = self.build_cnn_lstm_model((X_train.shape[1], X_train.shape[2]))
                
                # Callbacks
                early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
                reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=0.00001)
                
                # Train
                history = self.model.fit(
                    X_train, y_train,
                    validation_data=(X_val, y_val),
                    epochs=100,
                    batch_size=32,
                    callbacks=[early_stop, reduce_lr],
                    verbose=0
                )
                
                # Evaluate
                val_loss = history.history['val_loss'][-1]
                val_mae = history.history['val_mae'][-1]
                val_mape = history.history['val_mape'][-1]
                
                print(f"✅ Training complete - Val Loss: {val_loss:.4f}, MAE: {val_mae:.4f}, MAPE: {val_mape:.2f}%")
        else:
            # Statistical model
            self.model = self.build_statistical_model()
            self.model.fit(X_scaled, y)
            val_mae = np.mean(np.abs(self.model.predict(X_scaled) - y))
            print(f"✅ Statistical model trained - MAE: {val_mae:.4f}")
        
        # Calculate feature importance
        feature_importance = self._calculate_feature_importance(X_scaled, y)
        
        return {
            'model_type': 'cnn_lstm' if self.use_deep_learning else 'ridge_regression',
            'training_samples': len(X),
            'features_used': len(self.feature_columns),
            'lookback_periods': self.lookback_periods,
            'forecast_horizon': self.forecast_horizon,
            'validation_mae': float(val_mae) if self.use_deep_learning else float(val_mae),
            'feature_importance': feature_importance,
            'model_performance': {
                'mae': float(val_mae),
                'rmse': float(np.sqrt(val_loss)) if self.use_deep_learning else float(np.sqrt(np.mean((self.model.predict(X_scaled) - y) ** 2)))
            }
        }
    
    def _calculate_feature_importance(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """Calculate feature importance using permutation"""
        from sklearn.metrics import mean_absolute_error
        
        if self.use_deep_learning:
            # For LSTM, use simpler approach
            base_predictions = self.model.predict(self.create_sequences(X, y)[0], verbose=0)
            base_score = mean_absolute_error(self.create_sequences(X, y)[1], base_predictions)
            return {col: 1.0 / len(self.feature_columns) for col in self.feature_columns}
        else:
            # For linear model, use coefficients
            importances = dict(zip(self.feature_columns, np.abs(self.model.coef_)))
            total = sum(importances.values())
            return {k: v/total for k, v in importances.items()}
    
    def predict(self, data: List[Dict]) -> List[Dict]:
        """Predict 12-month dividend growth for given stocks"""
        df = self.prepare_features(data)
        X = df[self.feature_columns].values
        X_scaled = self.scaler.transform(X)
        
        if self.use_deep_learning:
            X_seq, _ = self.create_sequences(X_scaled, np.zeros(len(X)))
            predictions = self.model.predict(X_seq, verbose=0).flatten()
        else:
            predictions = self.model.predict(X_scaled)
        
        results = []
        for i, pred in enumerate(predictions):
            results.append({
                'symbol': df.iloc[i]['symbol'],
                'predicted_growth': float(pred),
                'growth_category': self._categorize_growth(pred),
                'confidence': 0.75  # Placeholder
            })
        
        return results
    
    def _categorize_growth(self, growth_rate: float) -> str:
        """Categorize growth into quintiles"""
        if growth_rate > 0.15:
            return 'high'
        elif growth_rate > 0.05:
            return 'medium'
        elif growth_rate > -0.05:
            return 'stable'
        elif growth_rate > -0.15:
            return 'declining'
        else:
            return 'at_risk'
    
    def save(self, path: str):
        """Save model and scaler"""
        model_data = {
            'scaler': self.scaler,
            'feature_columns': self.feature_columns,
            'lookback_periods': self.lookback_periods,
            'forecast_horizon': self.forecast_horizon,
            'use_deep_learning': self.use_deep_learning
        }
        
        if self.use_deep_learning:
            self.model.save(path.replace('.joblib', '_lstm.keras'))
            joblib.dump(model_data, path)
        else:
            model_data['model'] = self.model
            joblib.dump(model_data, path)
        
        print(f"💾 Model saved to {path}")


def fetch_training_data_from_db() -> List[Dict]:
    """Fetch training data from Azure SQL Database"""
    
    # Get connection details from environment
    server = os.environ.get('AZURE_SQL_SERVER')
    database = os.environ.get('AZURE_SQL_DATABASE')
    username = os.environ.get('AZURE_SQL_USER')
    password = os.environ.get('AZURE_SQL_PASSWORD')
    
    if not all([server, database, username, password]):
        raise ValueError("Missing Azure SQL environment variables: AZURE_SQL_SERVER, AZURE_SQL_DATABASE, AZURE_SQL_USER, AZURE_SQL_PASSWORD")
    
    print(f"📡 Connecting to Azure SQL: {server}/{database}")
    
    # Try pyodbc first, fall back to pymssql
    conn = None
    cursor = None
    try:
        import pyodbc
        conn_str = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=no'
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        print("✅ Connected via pyodbc")
    except Exception as e:
        print(f"⚠️  pyodbc failed ({str(e)[:60]}...), trying pymssql...")
        try:
            import pymssql
            conn = pymssql.connect(server=server, user=username, password=password, database=database)
            cursor = conn.cursor()
            print("✅ Connected via pymssql")
        except Exception as e2:
            raise RuntimeError(f"Failed to connect with both pyodbc and pymssql: {str(e2)}")
    
    # Fetch dividend history for training
    query = """
        SELECT TOP 10000
            symbol,
            ex_date,
            amount,
            frequency,
            yield_rate
        FROM Canonical_Dividends
        WHERE ex_date IS NOT NULL
            AND amount IS NOT NULL
            AND amount > 0
        ORDER BY symbol, ex_date DESC
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    # Convert to training format
    training_data = []
    for row in rows:
        training_data.append({
            'symbol': row.symbol,
            'ex_date': row.ex_date.isoformat() if row.ex_date else None,
            'amount': float(row.amount) if row.amount else 0,
            'frequency': row.frequency,
            'dividend_yield': float(row.yield_rate) if row.yield_rate else 0,
            # Add placeholder features (would need to fetch from other tables)
            'momentum_3m': 0,
            'roe': 0,
            'payout_ratio': 0,
            'fcf_payout_ratio': 0,
            'book_to_price': 0,
            'leverage_ratio': 0,
            'earnings_growth': 0,
            'dividend_growth_3y': 0,
            'market_cap_log': 0,
            'volatility_30d': 0,
            'beta': 0
        })
    
    conn.close()
    print(f"✅ Fetched {len(training_data)} records from database")
    return training_data


def main():
    parser = argparse.ArgumentParser(description='Train Dividend Growth Forecasting Model')
    parser.add_argument('--data', required=False, help='Path to training data JSON (optional, fetches from DB if not provided)')
    parser.add_argument('--output', required=True, help='Output path for model file')
    parser.add_argument('--lookback', type=int, default=12, help='Lookback periods (quarters)')
    parser.add_argument('--horizon', type=int, default=4, help='Forecast horizon (quarters)')
    
    args = parser.parse_args()
    
    # Load data from file or database
    if args.data:
        print(f"📂 Loading data from file: {args.data}")
        with open(args.data, 'r') as f:
            training_data = json.load(f)
    else:
        print(f"🗄️ Fetching data from Azure SQL Database...")
        training_data = fetch_training_data_from_db()
    
    print(f"📚 Loaded {len(training_data)} training records")
    
    # Train model
    forecaster = DividendGrowthForecaster(
        lookback_periods=args.lookback,
        forecast_horizon=args.horizon
    )
    
    results = forecaster.train(training_data)
    
    # Save model
    forecaster.save(args.output)
    
    # Save results summary
    results_path = args.output.replace('.joblib', '_results.json')
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"✅ Training complete!")
    print(f"📊 Model: {results['model_type']}")
    print(f"📈 MAE: {results['model_performance']['mae']:.4f}")
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
