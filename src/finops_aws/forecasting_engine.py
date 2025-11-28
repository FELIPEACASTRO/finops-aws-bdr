"""
FinOps Forecasting Engine
Previsões de custos baseadas em ML com detecção de anomalias
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import logging

logger = logging.getLogger(__name__)

# Try to import ML libraries with fallback
SKLEARN_AVAILABLE = False
NUMPY_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except Exception:
    np = None
    logger.warning("numpy not available")

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except Exception:
    LinearRegression = None
    StandardScaler = None
    logger.warning("scikit-learn not available - using simple forecasting")


class CostForecaster:
    """Engine de previsão de custos com ML"""
    
    def __init__(self, history_days: int = 30):
        self.history_days = history_days
        self.ml_available = SKLEARN_AVAILABLE
    
    def forecast_service_cost(self, historical_costs: List[float], forecast_days: int = 30) -> Dict[str, Any]:
        """
        Prevê custos futuro de um serviço baseado em histórico
        
        Args:
            historical_costs: Lista de custos diários dos últimos N dias
            forecast_days: Dias para prever
        
        Returns:
            Dicionário com previsões e métricas
        """
        if not historical_costs or len(historical_costs) < 7:
            return {
                'status': 'insufficient_data',
                'minimum_required_days': 7,
                'forecast': None
            }
        
        if self.ml_available:
            return self._forecast_with_sklearn(historical_costs, forecast_days)
        else:
            return self._forecast_simple(historical_costs, forecast_days)
    
    def _forecast_with_sklearn(self, historical_costs: List[float], forecast_days: int) -> Dict[str, Any]:
        """Previsão com scikit-learn - Linear Regression"""
        if not SKLEARN_AVAILABLE or np is None or LinearRegression is None:
            return self._forecast_simple(historical_costs, forecast_days)
        
        try:
            X = np.arange(len(historical_costs)).reshape(-1, 1)
            y = np.array(historical_costs)
            
            model = LinearRegression()
            model.fit(X, y)
            
            future_X = np.arange(len(historical_costs), len(historical_costs) + forecast_days).reshape(-1, 1)
            forecast = model.predict(future_X)
            
            # Calcula intervalo de confiança
            residuals = y - model.predict(X)
            std_error = np.std(residuals)
            
            forecast_result = {
                'status': 'success',
                'method': 'linear_regression',
                'forecast': forecast.tolist(),
                'forecast_days': forecast_days,
                'forecast_mean': float(np.mean(forecast)),
                'forecast_std': float(std_error),
                'confidence_interval_95': {
                    'upper': float(np.mean(forecast) + 1.96 * std_error),
                    'lower': max(0, float(np.mean(forecast) - 1.96 * std_error))
                },
                'trend': 'increasing' if model.coef_[0] > 0 else 'decreasing',
                'trend_rate': float(model.coef_[0])
            }
            
            return forecast_result
        
        except Exception as e:
            logger.error(f"sklearn forecasting error: {e}")
            return self._forecast_simple(historical_costs, forecast_days)
    
    def _forecast_simple(self, historical_costs: List[float], forecast_days: int) -> Dict[str, Any]:
        """Previsão simples - média móvel exponencial"""
        try:
            if np is not None:
                costs_array = np.array(historical_costs, dtype=float)
                mean_cost = float(np.mean(costs_array))
                std_cost = float(np.std(costs_array))
            else:
                mean_cost = sum(historical_costs) / len(historical_costs) if historical_costs else 0
                std_cost = 0
            
            # EMA com decay factor
            alpha = 0.3
            ema = mean_cost
            for cost in historical_costs:
                ema = alpha * cost + (1 - alpha) * ema
            
            forecast = [ema] * forecast_days
            
            # Adiciona variação com tendência
            if len(historical_costs) > 1:
                trend = (historical_costs[-1] - historical_costs[0]) / len(historical_costs)
                forecast = [max(0, ema + (i * trend * 0.1)) for i in range(forecast_days)]
            
            return {
                'status': 'success',
                'method': 'exponential_moving_average',
                'forecast': forecast,
                'forecast_days': forecast_days,
                'forecast_mean': mean_cost,
                'forecast_std': std_cost,
                'confidence_interval_95': {
                    'upper': mean_cost + (1.96 * std_cost if std_cost > 0 else mean_cost * 0.2),
                    'lower': max(0, mean_cost - (1.96 * std_cost if std_cost > 0 else mean_cost * 0.2))
                },
                'trend': 'stable'
            }
        
        except Exception as e:
            logger.error(f"Simple forecasting error: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def detect_anomalies(self, historical_costs: List[float], threshold_std: float = 2.0) -> Dict[str, Any]:
        """
        Detecta anomalias em custos usando Z-score
        
        Args:
            historical_costs: Lista de custos
            threshold_std: Número de desvios padrão para considerar anomalia
        
        Returns:
            Dicionário com anomalias detectadas
        """
        if np is None:
            # Fallback sem numpy
            mean = sum(historical_costs) / len(historical_costs) if historical_costs else 0
            std = 0
            return {
                'anomalies_detected': [],
                'total_anomalies': 0,
                'mean_cost': mean,
                'std_cost': std,
                'note': 'Numpy not available for anomaly detection'
            }
        
        costs_array = np.array(historical_costs, dtype=float)
        mean = float(np.mean(costs_array))
        std = float(np.std(costs_array))
        
        if std == 0:
            return {
                'anomalies_detected': [],
                'total_anomalies': 0,
                'mean_cost': mean,
                'std_cost': std
            }
        
        z_scores = np.abs((costs_array - mean) / std)
        anomalies = []
        
        for i, z_score in enumerate(z_scores):
            if z_score > threshold_std:
                anomalies.append({
                    'day_index': int(i),
                    'cost': float(costs_array[i]),
                    'expected_range': [float(mean - threshold_std * std), float(mean + threshold_std * std)],
                    'z_score': float(z_score),
                    'severity': 'high' if z_score > 3 else 'medium'
                })
        
        return {
            'anomalies_detected': anomalies,
            'total_anomalies': len(anomalies),
            'mean_cost': mean,
            'std_cost': std
        }
    
    def forecast_aggregated_costs(self, service_costs: Dict[str, List[float]], forecast_days: int = 30) -> Dict[str, Any]:
        """Prevê custos agregados por serviço"""
        forecasts = {}
        total_forecast = [0.0] * forecast_days
        
        for service_name, costs in service_costs.items():
            forecast = self.forecast_service_cost(costs, forecast_days)
            if forecast.get('status') == 'success':
                forecasts[service_name] = forecast
                if 'forecast' in forecast:
                    total_forecast = [total_forecast[i] + forecast['forecast'][i] 
                                     for i in range(forecast_days)]
        
        total_mean = sum(total_forecast) / len(total_forecast) if total_forecast else 0
        if np is not None:
            total_mean = float(np.mean(total_forecast))
        
        return {
            'total_forecast': total_forecast,
            'total_forecast_mean': total_mean,
            'service_forecasts': forecasts,
            'timestamp': datetime.utcnow().isoformat()
        }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handler para execução como Lambda"""
    try:
        logger.info("Forecasting engine started")
        
        forecaster = CostForecaster()
        
        # Exemplo: custos históricos
        historical_costs = event.get('historical_costs', [100, 102, 101, 103, 500, 102, 101])
        forecast_days = event.get('forecast_days', 30)
        
        forecast = forecaster.forecast_service_cost(historical_costs, forecast_days)
        anomalies = forecaster.detect_anomalies(historical_costs)
        
        return {
            'status': 'success',
            'forecast': forecast,
            'anomalies': anomalies,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Forecasting error: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }
