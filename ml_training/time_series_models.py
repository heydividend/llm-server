#!/usr/bin/env python3
"""
Advanced Time Series Models for Dividend Payout Ratio Forecasting
Implements ARIMA, SARIMA, Prophet, LSTM for robust payout ratio predictions
"""

import argparse
import json
import os
import sys
import time
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Union, Optional

# Suppress warnings
warnings.filterwarnings('ignore')

try:
    import pandas as pd
    import numpy as np
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    from sklearn.model_selection import TimeSeriesSplit
    import joblib
    
    # Statistical models
    try:
        from statsmodels.tsa.arima.model import ARIMA
        from statsmodels.tsa.statespace.sarimax import SARIMAX
        from statsmodels.tsa.seasonal import seasonal_decompose
        from statsmodels.tsa.stattools import adfuller, acf, pacf
        from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
        STATSMODELS_AVAILABLE = True
    except ImportError:
        STATSMODELS_AVAILABLE = False
        print("⚠️ Statsmodels not available - ARIMA/SARIMA models disabled")
    
    # Facebook Prophet
    try:
        from prophet import Prophet
        PROPHET_AVAILABLE = True
    except ImportError:
        PROPHET_AVAILABLE = False
        print("⚠️ Prophet not available - Prophet models disabled")
    
    # TensorFlow/Keras for LSTM
    try:
        import tensorflow as tf
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import LSTM, Dense, Dropout
        from tensorflow.keras.optimizers import Adam
        TENSORFLOW_AVAILABLE = True
    except ImportError:
        TENSORFLOW_AVAILABLE = False
        print("⚠️ TensorFlow not available - LSTM models disabled")
    
    # Exponential smoothing
    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing
        EXPONENTIAL_SMOOTHING_AVAILABLE = True
    except ImportError:
        EXPONENTIAL_SMOOTHING_AVAILABLE = False
        print("⚠️ Exponential Smoothing not available")
        
except ImportError as e:
    print(f"Error importing required packages: {e}")
    print("Please ensure packages are installed:")
    print("pip install pandas numpy scikit-learn joblib")
    print("Optional: pip install statsmodels prophet tensorflow")
    sys.exit(1)


class PayoutRatioForecaster:
    """
    Advanced time series forecaster for dividend payout ratios
    Combines multiple algorithms for robust forecasting
    """
    
    def __init__(self, random_state: int = 42):
        """Initialize the payout ratio forecaster"""
        self.random_state = random_state
        np.random.seed(random_state)
        
        if TENSORFLOW_AVAILABLE:
            tf.random.set_seed(random_state)
        
        # Model ensemble
        self.models = {}
        self.ensemble_weights = {
            'arima': 0.20,
            'sarima': 0.25,
            'prophet': 0.20,
            'lstm': 0.20,
            'exponential_smoothing': 0.15
        }
        
        # Data preprocessing
        self.scalers = {}
        self.feature_columns = []
        
        # Time series parameters
        self.frequency = 'Q'  # Quarterly data
        self.seasonal_periods = 4  # 4 quarters in a year
        
        # Performance tracking
        self.training_metrics = {}
        self.validation_scores = {}
        
    def prepare_time_series_data(self, data: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Prepare time series data for forecasting
        
        Args:
            data: Raw financial data
            symbol: Stock symbol to process
            
        Returns:
            Prepared time series DataFrame
        """
        print(f"🔧 Preparing time series data for {symbol}...")
        
        # Filter for specific symbol
        if 'symbol' in data.columns:
            df = data[data['symbol'] == symbol].copy()
        else:
            df = data.copy()
        
        # Ensure date column exists and is datetime
        if 'date' not in df.columns:
            if 'quarter' in df.columns and 'year' in df.columns:
                df['date'] = pd.to_datetime(df['year'].astype(str) + '-' + 
                                          (df['quarter'] * 3).astype(str) + '-01')
            else:
                # Create synthetic quarterly dates
                df['date'] = pd.date_range(start='2010-01-01', periods=len(df), freq='Q')
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Set date as index
        df = df.set_index('date')
        
        # Ensure we have payout ratio column
        if 'payout_ratio' not in df.columns:
            print("⚠️ No payout_ratio column found. Creating synthetic data...")
            # Create synthetic payout ratio based on other metrics
            df['payout_ratio'] = self._create_synthetic_payout_ratio(df)
        
        # Fill missing values
        df['payout_ratio'] = df['payout_ratio'].fillna(df['payout_ratio'].median())
        
        # Clip extreme values (payout ratios should be reasonable)
        df['payout_ratio'] = df['payout_ratio'].clip(0, 3.0)  # Max 300% payout
        
        # Create additional features for multivariate forecasting
        df = self._create_time_series_features(df)
        
        # Resample to quarterly frequency to ensure consistency
        df = df.resample('Q').last().fillna(method='ffill')
        
        return df
    
    def _create_synthetic_payout_ratio(self, df: pd.DataFrame) -> pd.Series:
        """Create synthetic payout ratio from available data"""
        
        # Try to calculate from dividends and earnings
        if 'dividend_per_share' in df.columns and 'earnings_per_share' in df.columns:
            return df['dividend_per_share'] / df['earnings_per_share'].clip(lower=0.01)
        
        # Try to calculate from dividend yield and other metrics
        if 'dividend_yield' in df.columns:
            base_payout = df['dividend_yield'] * 10  # Rough approximation
            
            # Adjust based on growth stage
            if 'growth_stage' in df.columns:
                growth_adjustment = df['growth_stage'].map({
                    'Growth': 0.3,
                    'Mature': 0.6,
                    'Declining': 0.8
                }).fillna(0.6)
                return base_payout * growth_adjustment
            
            return base_payout.clip(0.2, 1.2)  # Reasonable range
        
        # Default synthetic payout ratio with trend and seasonality
        n = len(df)
        base_ratio = 0.6
        trend = np.linspace(-0.1, 0.1, n)  # Slight upward trend
        seasonal = 0.05 * np.sin(2 * np.pi * np.arange(n) / 4)  # Quarterly seasonality
        noise = np.random.normal(0, 0.05, n)
        
        return pd.Series(base_ratio + trend + seasonal + noise, index=df.index)
    
    def _create_time_series_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create additional features for time series forecasting"""
        
        # Lagged features
        for lag in [1, 2, 4, 8]:
            df[f'payout_ratio_lag_{lag}'] = df['payout_ratio'].shift(lag)
        
        # Rolling statistics
        for window in [4, 8, 12]:
            df[f'payout_ratio_mean_{window}'] = df['payout_ratio'].rolling(window).mean()
            df[f'payout_ratio_std_{window}'] = df['payout_ratio'].rolling(window).std()
        
        # Trend features
        df['payout_ratio_trend'] = df['payout_ratio'].rolling(4).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) >= 2 else 0
        )
        
        # Seasonal decomposition features
        if len(df) >= 8:  # Need at least 2 years of quarterly data
            try:
                decomposition = seasonal_decompose(
                    df['payout_ratio'].fillna(method='ffill'), 
                    model='additive', 
                    period=4
                )
                df['payout_trend'] = decomposition.trend
                df['payout_seasonal'] = decomposition.seasonal
                df['payout_residual'] = decomposition.resid
            except Exception as e:
                print(f"⚠️ Seasonal decomposition failed: {e}")
                df['payout_trend'] = df['payout_ratio']
                df['payout_seasonal'] = 0
                df['payout_residual'] = 0
        
        # Economic indicators (if available)
        economic_features = [
            'interest_rate_10yr', 'gdp_growth', 'inflation_rate', 
            'market_volatility', 'sector_performance'
        ]
        for feature in economic_features:
            if feature not in df.columns:
                # Create synthetic economic indicators
                if feature == 'interest_rate_10yr':
                    df[feature] = 0.04 + 0.02 * np.sin(2 * np.pi * np.arange(len(df)) / 20)
                elif feature == 'market_volatility':
                    df[feature] = 0.15 + 0.05 * np.random.randn(len(df))
                else:
                    df[feature] = np.random.randn(len(df)) * 0.1
        
        # Company-specific features
        company_features = [
            'earnings_volatility', 'revenue_growth', 'free_cash_flow_growth',
            'debt_to_equity', 'roe', 'company_age'
        ]
        for feature in company_features:
            if feature not in df.columns:
                if feature == 'earnings_volatility':
                    df[feature] = 0.2 + 0.1 * np.random.randn(len(df))
                elif feature == 'company_age':
                    df[feature] = 25 + np.arange(len(df)) * 0.25  # Aging company
                else:
                    df[feature] = np.random.randn(len(df)) * 0.1
        
        return df
    
    def train_arima_model(self, ts_data: pd.Series, exog_data: pd.DataFrame = None) -> Dict[str, Any]:
        """Train ARIMA model"""
        if not STATSMODELS_AVAILABLE:
            return {'success': False, 'error': 'Statsmodels not available'}
        
        print("📈 Training ARIMA model...")
        
        try:
            # Find optimal parameters using AIC
            best_aic = float('inf')
            best_params = (1, 1, 1)
            
            for p in range(3):
                for d in range(2):
                    for q in range(3):
                        try:
                            model = ARIMA(ts_data, order=(p, d, q), exog=exog_data)
                            fitted = model.fit()
                            if fitted.aic < best_aic:
                                best_aic = fitted.aic
                                best_params = (p, d, q)
                        except:
                            continue
            
            # Train final model with best parameters
            model = ARIMA(ts_data, order=best_params, exog=exog_data)
            fitted = model.fit()
            
            self.models['arima'] = {
                'model': fitted,
                'params': best_params,
                'aic': best_aic
            }
            
            return {
                'success': True,
                'params': best_params,
                'aic': best_aic,
                'summary': str(fitted.summary())
            }
            
        except Exception as e:
            print(f"❌ ARIMA training failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def train_sarima_model(self, ts_data: pd.Series, exog_data: pd.DataFrame = None) -> Dict[str, Any]:
        """Train SARIMA model with seasonal components"""
        if not STATSMODELS_AVAILABLE:
            return {'success': False, 'error': 'Statsmodels not available'}
        
        print("📊 Training SARIMA model...")
        
        try:
            # Find optimal parameters
            best_aic = float('inf')
            best_params = ((1, 1, 1), (1, 1, 1, 4))
            
            for p in range(2):
                for d in range(2):
                    for q in range(2):
                        for P in range(2):
                            for D in range(2):
                                for Q in range(2):
                                    try:
                                        model = SARIMAX(
                                            ts_data,
                                            order=(p, d, q),
                                            seasonal_order=(P, D, Q, 4),
                                            exog=exog_data
                                        )
                                        fitted = model.fit(disp=False)
                                        if fitted.aic < best_aic:
                                            best_aic = fitted.aic
                                            best_params = ((p, d, q), (P, D, Q, 4))
                                    except:
                                        continue
            
            # Train final model
            model = SARIMAX(
                ts_data,
                order=best_params[0],
                seasonal_order=best_params[1],
                exog=exog_data
            )
            fitted = model.fit(disp=False)
            
            self.models['sarima'] = {
                'model': fitted,
                'params': best_params,
                'aic': best_aic
            }
            
            return {
                'success': True,
                'params': best_params,
                'aic': best_aic
            }
            
        except Exception as e:
            print(f"❌ SARIMA training failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def train_prophet_model(self, ts_data: pd.Series, additional_regressors: pd.DataFrame = None) -> Dict[str, Any]:
        """Train Facebook Prophet model"""
        if not PROPHET_AVAILABLE:
            return {'success': False, 'error': 'Prophet not available'}
        
        print("🔮 Training Prophet model...")
        
        try:
            # Prepare data for Prophet
            prophet_df = pd.DataFrame({
                'ds': ts_data.index,
                'y': ts_data.values
            })
            
            # Initialize Prophet with quarterly seasonality
            model = Prophet(
                yearly_seasonality=True,
                quarterly_seasonality=True,
                weekly_seasonality=False,
                daily_seasonality=False,
                seasonality_mode='additive',
                interval_width=0.95
            )
            
            # Add additional regressors if provided
            if additional_regressors is not None:
                for col in additional_regressors.columns:
                    model.add_regressor(col)
                    prophet_df[col] = additional_regressors[col].values
            
            # Fit the model
            model.fit(prophet_df)
            
            self.models['prophet'] = {
                'model': model,
                'training_data': prophet_df
            }
            
            return {'success': True, 'components': model.component_modes}
            
        except Exception as e:
            print(f"❌ Prophet training failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def train_lstm_model(self, ts_data: pd.Series, features: pd.DataFrame = None, 
                        sequence_length: int = 8) -> Dict[str, Any]:
        """Train LSTM neural network model"""
        if not TENSORFLOW_AVAILABLE:
            return {'success': False, 'error': 'TensorFlow not available'}
        
        print("🧠 Training LSTM model...")
        
        try:
            # Prepare sequences for LSTM
            X, y = self._create_lstm_sequences(ts_data, features, sequence_length)
            
            if len(X) < 10:  # Need minimum data for training
                return {'success': False, 'error': 'Insufficient data for LSTM training'}
            
            # Split data
            split_point = int(len(X) * 0.8)
            X_train, X_test = X[:split_point], X[split_point:]
            y_train, y_test = y[:split_point], y[split_point:]
            
            # Scale data
            scaler_X = MinMaxScaler()
            scaler_y = MinMaxScaler()
            
            X_train_scaled = scaler_X.fit_transform(X_train.reshape(-1, X_train.shape[-1])).reshape(X_train.shape)
            X_test_scaled = scaler_X.transform(X_test.reshape(-1, X_test.shape[-1])).reshape(X_test.shape)
            y_train_scaled = scaler_y.fit_transform(y_train.reshape(-1, 1)).flatten()
            y_test_scaled = scaler_y.transform(y_test.reshape(-1, 1)).flatten()
            
            # Build LSTM model
            model = Sequential([
                LSTM(50, return_sequences=True, input_shape=(sequence_length, X_train.shape[2])),
                Dropout(0.2),
                LSTM(50, return_sequences=False),
                Dropout(0.2),
                Dense(25),
                Dense(1)
            ])
            
            model.compile(optimizer=Adam(learning_rate=0.001), loss='mse', metrics=['mae'])
            
            # Train model
            history = model.fit(
                X_train_scaled, y_train_scaled,
                epochs=100,
                batch_size=16,
                validation_data=(X_test_scaled, y_test_scaled),
                verbose=0,
                shuffle=False
            )
            
            self.models['lstm'] = {
                'model': model,
                'scaler_X': scaler_X,
                'scaler_y': scaler_y,
                'sequence_length': sequence_length,
                'history': history.history
            }
            
            # Calculate validation metrics
            y_pred_scaled = model.predict(X_test_scaled, verbose=0)
            y_pred = scaler_y.inverse_transform(y_pred_scaled).flatten()
            
            mse = mean_squared_error(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            
            return {
                'success': True,
                'validation_mse': mse,
                'validation_mae': mae,
                'training_history': history.history
            }
            
        except Exception as e:
            print(f"❌ LSTM training failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def train_exponential_smoothing(self, ts_data: pd.Series) -> Dict[str, Any]:
        """Train Exponential Smoothing (Holt-Winters) model"""
        if not EXPONENTIAL_SMOOTHING_AVAILABLE:
            return {'success': False, 'error': 'Exponential Smoothing not available'}
        
        print("📉 Training Exponential Smoothing model...")
        
        try:
            # Try different configurations
            configurations = [
                {'seasonal': 'add', 'seasonal_periods': 4},
                {'seasonal': 'mul', 'seasonal_periods': 4},
                {'seasonal': None}
            ]
            
            best_aic = float('inf')
            best_model = None
            best_config = None
            
            for config in configurations:
                try:
                    model = ExponentialSmoothing(
                        ts_data,
                        trend='add',
                        **config
                    )
                    fitted = model.fit()
                    
                    if fitted.aic < best_aic:
                        best_aic = fitted.aic
                        best_model = fitted
                        best_config = config
                except:
                    continue
            
            if best_model is None:
                return {'success': False, 'error': 'No valid configuration found'}
            
            self.models['exponential_smoothing'] = {
                'model': best_model,
                'config': best_config,
                'aic': best_aic
            }
            
            return {
                'success': True,
                'config': best_config,
                'aic': best_aic
            }
            
        except Exception as e:
            print(f"❌ Exponential Smoothing training failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _create_lstm_sequences(self, ts_data: pd.Series, features: pd.DataFrame = None, 
                              sequence_length: int = 8) -> Tuple[np.ndarray, np.ndarray]:
        """Create sequences for LSTM training"""
        
        # Combine target with features
        if features is not None:
            # Align features with time series
            aligned_features = features.reindex(ts_data.index, method='ffill')
            combined_data = pd.concat([ts_data, aligned_features], axis=1)
        else:
            combined_data = pd.DataFrame({'target': ts_data})
        
        # Fill missing values
        combined_data = combined_data.fillna(method='ffill').fillna(method='bfill')
        
        # Create sequences
        X, y = [], []
        for i in range(sequence_length, len(combined_data)):
            X.append(combined_data.iloc[i-sequence_length:i].values)
            y.append(ts_data.iloc[i])
        
        return np.array(X), np.array(y)
    
    def train_ensemble(self, data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """
        Train ensemble of time series models
        
        Args:
            data: Historical financial data
            symbol: Stock symbol to forecast
            
        Returns:
            Training results and metrics
        """
        print(f"🏋️ Training Time Series Ensemble for {symbol}...")
        
        # Prepare time series data
        ts_df = self.prepare_time_series_data(data, symbol)
        
        if len(ts_df) < 8:  # Need minimum data
            return {
                'success': False,
                'error': f'Insufficient data for {symbol}: {len(ts_df)} periods (need >= 8)'
            }
        
        # Extract target series and features
        target_series = ts_df['payout_ratio'].dropna()
        
        # Select features for multivariate models
        feature_cols = [col for col in ts_df.columns 
                       if col.startswith('payout_ratio_lag_') or 
                          col in ['earnings_volatility', 'revenue_growth', 'debt_to_equity', 'roe']]
        features = ts_df[feature_cols].dropna()
        
        print(f"📊 Training with {len(target_series)} periods, {len(feature_cols)} features")
        
        # Train individual models
        results = {}
        
        # 1. ARIMA
        arima_result = self.train_arima_model(target_series)
        results['arima'] = arima_result
        
        # 2. SARIMA
        sarima_result = self.train_sarima_model(target_series)
        results['sarima'] = sarima_result
        
        # 3. Prophet
        prophet_result = self.train_prophet_model(target_series, features if not features.empty else None)
        results['prophet'] = prophet_result
        
        # 4. LSTM
        lstm_result = self.train_lstm_model(target_series, features if not features.empty else None)
        results['lstm'] = lstm_result
        
        # 5. Exponential Smoothing
        exp_smooth_result = self.train_exponential_smoothing(target_series)
        results['exponential_smoothing'] = exp_smooth_result
        
        # Evaluate ensemble performance
        ensemble_metrics = self._evaluate_ensemble(target_series, features)
        
        # Store training metadata
        self.training_metrics = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'data_periods': len(target_series),
            'feature_count': len(feature_cols),
            'models_trained': [name for name, result in results.items() if result.get('success', False)],
            'individual_results': results,
            'ensemble_metrics': ensemble_metrics
        }
        
        successful_models = [name for name, result in results.items() if result.get('success', False)]
        print(f"✅ Training completed. Successful models: {successful_models}")
        
        return self.training_metrics
    
    def _evaluate_ensemble(self, target_series: pd.Series, features: pd.DataFrame) -> Dict[str, float]:
        """Evaluate ensemble performance using walk-forward validation"""
        
        if len(target_series) < 12:  # Need enough data for validation
            return {'error': 'Insufficient data for validation'}
        
        # Use last 25% of data for validation
        split_point = int(len(target_series) * 0.75)
        train_data = target_series[:split_point]
        test_data = target_series[split_point:]
        
        try:
            # Get predictions from each model
            predictions = {}
            
            for model_name in self.models:
                if model_name in self.models:
                    pred = self._predict_single_model(model_name, len(test_data), train_data, features)
                    if pred is not None:
                        predictions[model_name] = pred
            
            # Ensemble prediction (weighted average)
            if predictions:
                ensemble_pred = np.zeros(len(test_data))
                total_weight = 0
                
                for model_name, pred in predictions.items():
                    weight = self.ensemble_weights.get(model_name, 0.0)
                    ensemble_pred += weight * pred[:len(test_data)]
                    total_weight += weight
                
                if total_weight > 0:
                    ensemble_pred /= total_weight
                
                # Calculate metrics
                mse = mean_squared_error(test_data, ensemble_pred)
                mae = mean_absolute_error(test_data, ensemble_pred)
                rmse = np.sqrt(mse)
                
                # Calculate additional time series metrics
                forecast_bias = np.mean(ensemble_pred - test_data)
                mape = np.mean(np.abs((test_data - ensemble_pred) / np.clip(test_data, 0.01, None))) * 100
                
                return {
                    'rmse': rmse,
                    'mae': mae,
                    'mse': mse,
                    'mape': mape,
                    'forecast_bias': forecast_bias,
                    'successful_models': len(predictions)
                }
            
        except Exception as e:
            print(f"❌ Ensemble evaluation failed: {e}")
        
        return {'error': 'Ensemble evaluation failed'}
    
    def _predict_single_model(self, model_name: str, periods: int, 
                             train_data: pd.Series, features: pd.DataFrame) -> Optional[np.ndarray]:
        """Get prediction from a single model"""
        
        try:
            model_info = self.models.get(model_name)
            if not model_info:
                return None
            
            if model_name == 'arima' and STATSMODELS_AVAILABLE:
                forecast = model_info['model'].forecast(steps=periods)
                return np.array(forecast)
            
            elif model_name == 'sarima' and STATSMODELS_AVAILABLE:
                forecast = model_info['model'].forecast(steps=periods)
                return np.array(forecast)
            
            elif model_name == 'prophet' and PROPHET_AVAILABLE:
                model = model_info['model']
                future = model.make_future_dataframe(periods=periods, freq='Q')
                forecast = model.predict(future)
                return forecast['yhat'].tail(periods).values
            
            elif model_name == 'lstm' and TENSORFLOW_AVAILABLE:
                model = model_info['model']
                scaler_X = model_info['scaler_X']
                scaler_y = model_info['scaler_y']
                sequence_length = model_info['sequence_length']
                
                # Prepare last sequence for prediction
                last_sequence = train_data.tail(sequence_length).values.reshape(1, sequence_length, 1)
                last_sequence_scaled = scaler_X.transform(last_sequence.reshape(-1, 1)).reshape(last_sequence.shape)
                
                predictions = []
                current_sequence = last_sequence_scaled
                
                for _ in range(periods):
                    pred_scaled = model.predict(current_sequence, verbose=0)[0, 0]
                    pred = scaler_y.inverse_transform([[pred_scaled]])[0, 0]
                    predictions.append(pred)
                    
                    # Update sequence for next prediction
                    new_sequence = np.roll(current_sequence, -1, axis=1)
                    new_sequence[0, -1, 0] = pred_scaled
                    current_sequence = new_sequence
                
                return np.array(predictions)
            
            elif model_name == 'exponential_smoothing' and EXPONENTIAL_SMOOTHING_AVAILABLE:
                forecast = model_info['model'].forecast(steps=periods)
                return np.array(forecast)
            
        except Exception as e:
            print(f"❌ Prediction failed for {model_name}: {e}")
        
        return None
    
    def forecast_payout_ratio(self, symbol: str, quarters: int = 4) -> Dict[str, Any]:
        """
        Forecast payout ratio for specified quarters
        
        Args:
            symbol: Stock symbol
            quarters: Number of quarters to forecast
            
        Returns:
            Forecast results with confidence intervals
        """
        print(f"🔮 Forecasting payout ratio for {symbol}, {quarters} quarters ahead...")
        
        if not self.models:
            raise ValueError("Models not trained. Please train the ensemble first.")
        
        # Get predictions from all available models
        predictions = {}
        confidence_intervals = {}
        
        for model_name in self.models:
            try:
                if model_name == 'arima' and 'arima' in self.models:
                    forecast = self.models['arima']['model'].forecast(steps=quarters)
                    conf_int = self.models['arima']['model'].get_forecast(steps=quarters).conf_int()
                    predictions[model_name] = forecast.values
                    confidence_intervals[model_name] = {
                        'lower': conf_int.iloc[:, 0].values,
                        'upper': conf_int.iloc[:, 1].values
                    }
                
                elif model_name == 'sarima' and 'sarima' in self.models:
                    forecast = self.models['sarima']['model'].forecast(steps=quarters)
                    conf_int = self.models['sarima']['model'].get_forecast(steps=quarters).conf_int()
                    predictions[model_name] = forecast.values
                    confidence_intervals[model_name] = {
                        'lower': conf_int.iloc[:, 0].values,
                        'upper': conf_int.iloc[:, 1].values
                    }
                
                elif model_name == 'prophet' and 'prophet' in self.models:
                    model = self.models['prophet']['model']
                    future = model.make_future_dataframe(periods=quarters, freq='Q')
                    forecast = model.predict(future)
                    predictions[model_name] = forecast['yhat'].tail(quarters).values
                    confidence_intervals[model_name] = {
                        'lower': forecast['yhat_lower'].tail(quarters).values,
                        'upper': forecast['yhat_upper'].tail(quarters).values
                    }
                
                # Add other models as needed
                
            except Exception as e:
                print(f"⚠️ Forecast failed for {model_name}: {e}")
                continue
        
        if not predictions:
            return {
                'success': False,
                'error': 'No models available for forecasting'
            }
        
        # Ensemble forecast (weighted average)
        ensemble_forecast = np.zeros(quarters)
        ensemble_lower = np.zeros(quarters)
        ensemble_upper = np.zeros(quarters)
        total_weight = 0
        
        for model_name, pred in predictions.items():
            weight = self.ensemble_weights.get(model_name, 0.0)
            ensemble_forecast += weight * pred
            
            if model_name in confidence_intervals:
                ensemble_lower += weight * confidence_intervals[model_name]['lower']
                ensemble_upper += weight * confidence_intervals[model_name]['upper']
            
            total_weight += weight
        
        if total_weight > 0:
            ensemble_forecast /= total_weight
            ensemble_lower /= total_weight
            ensemble_upper /= total_weight
        
        # Generate forecast dates
        last_date = datetime.now().replace(day=1, month=((datetime.now().month - 1) // 3) * 3 + 1)
        forecast_dates = [last_date + timedelta(days=90*i) for i in range(1, quarters + 1)]
        
        # Determine trend direction
        if len(ensemble_forecast) >= 2:
            trend_slope = np.polyfit(range(len(ensemble_forecast)), ensemble_forecast, 1)[0]
            if trend_slope > 0.01:
                trend_direction = 'increasing'
            elif trend_slope < -0.01:
                trend_direction = 'decreasing'
            else:
                trend_direction = 'stable'
        else:
            trend_direction = 'stable'
        
        return {
            'success': True,
            'symbol': symbol,
            'forecast_quarters': quarters,
            'predicted_ratios': ensemble_forecast.tolist(),
            'confidence_bands': {
                'lower': ensemble_lower.tolist(),
                'upper': ensemble_upper.tolist()
            },
            'forecast_dates': [d.isoformat() for d in forecast_dates],
            'trend_direction': trend_direction,
            'individual_predictions': {
                name: pred.tolist() for name, pred in predictions.items()
            },
            'model_weights': self.ensemble_weights,
            'timestamp': datetime.now().isoformat()
        }
    
    def save_models(self, model_dir: str = 'models') -> str:
        """Save trained models to disk"""
        os.makedirs(model_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save models
        for name, model_info in self.models.items():
            filename = f'payout_forecaster_{name}_{timestamp}.joblib'
            filepath = os.path.join(model_dir, filename)
            joblib.dump(model_info, filepath)
            print(f"💾 Saved {name} model to {filepath}")
        
        # Save ensemble metadata
        metadata_file = os.path.join(model_dir, f'payout_ensemble_metadata_{timestamp}.json')
        metadata = {
            'ensemble_weights': self.ensemble_weights,
            'training_metrics': self.training_metrics,
            'timestamp': timestamp,
            'model_files': {
                name: f'payout_forecaster_{name}_{timestamp}.joblib' 
                for name in self.models.keys()
            }
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"📋 Saved ensemble metadata to {metadata_file}")
        return timestamp
    
    def load_models(self, model_dir: str, timestamp: str) -> bool:
        """Load trained models from disk"""
        try:
            # Load metadata
            metadata_file = os.path.join(model_dir, f'payout_ensemble_metadata_{timestamp}.json')
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            self.ensemble_weights = metadata['ensemble_weights']
            self.training_metrics = metadata['training_metrics']
            
            # Load individual models
            for name, filename in metadata['model_files'].items():
                filepath = os.path.join(model_dir, filename)
                self.models[name] = joblib.load(filepath)
                print(f"📂 Loaded {name} model from {filepath}")
            
            print(f"✅ Successfully loaded ensemble from {timestamp}")
            return True
        except Exception as e:
            print(f"❌ Failed to load models: {e}")
            return False


def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description='Payout Ratio Time Series Forecasting')
    parser.add_argument('--mode', choices=['train', 'predict'], required=True,
                      help='Mode: train or predict')
    parser.add_argument('--input', required=True,
                      help='Input data file (JSON)')
    parser.add_argument('--symbol', required=True,
                      help='Stock symbol to process')
    parser.add_argument('--output', default='.',
                      help='Output directory')
    parser.add_argument('--model-dir', default='models',
                      help='Model directory')
    parser.add_argument('--quarters', type=int, default=4,
                      help='Number of quarters to forecast')
    parser.add_argument('--load-timestamp', 
                      help='Timestamp of models to load for prediction')
    
    args = parser.parse_args()
    
    # Load input data
    with open(args.input, 'r') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    
    # Initialize forecaster
    forecaster = PayoutRatioForecaster()
    
    if args.mode == 'train':
        # Train models
        results = forecaster.train_ensemble(df, args.symbol)
        
        # Save models
        timestamp = forecaster.save_models(args.model_dir)
        
        # Save results
        output_file = os.path.join(args.output, 'payout_forecast_results.json')
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"✅ Training completed. Results saved to {output_file}")
        
    elif args.mode == 'predict':
        if not args.load_timestamp:
            print("❌ --load-timestamp required for prediction mode")
            return
        
        # Load models
        if not forecaster.load_models(args.model_dir, args.load_timestamp):
            print("❌ Failed to load models")
            return
        
        # Make forecast
        forecast = forecaster.forecast_payout_ratio(args.symbol, args.quarters)
        
        # Save forecast
        output_file = os.path.join(args.output, 'payout_forecast.json')
        with open(output_file, 'w') as f:
            json.dump(forecast, f, indent=2)
        
        print(f"✅ Forecasting completed. Results saved to {output_file}")


if __name__ == '__main__':
    main()