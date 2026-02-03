"""
Módulo de Machine Learning para detección de anomalías y clasificación automática.
"""

from .feature_engineering import add_features
from .anomaly_detector import AnomalyDetector

__all__ = ['add_features', 'AnomalyDetector']
