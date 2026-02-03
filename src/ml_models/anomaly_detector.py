"""
Módulo de Detección de Anomalías usando Isolation Forest.

Este módulo implementa un detector de anomalías no supervisado que identifica
instrumentos con PROBLEMAS REALES DE NEGOCIO usando features específicos que
capturan: diferencias por moneda, monedas faltantes, inconsistencias lógicas
y patrones anómalos según tipo de instrumento.
"""

from sklearn.ensemble import IsolationForest
import pandas as pd
import numpy as np
import logging
from pathlib import Path
import joblib

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Detector de anomalías basado en Isolation Forest con features de negocio.
    
    A diferencia de un Isolation Forest tradicional que detecta patrones estadísticamente
    raros, este modelo está entrenado con features que capturan problemas reales:
    - Diferencias significativas por moneda individual
    - Monedas presentes en una fuente pero no en otra
    - Inconsistencias lógicas (suma != 100%, distribución vs sin distribución)
    - Patrones anómalos según tipo de instrumento
    """
    
    def __init__(self, contamination=0.05, random_state=42):
        """
        Inicializa el detector de anomalías.
        
        Args:
            contamination: Proporción esperada de anomalías (default 5%)
            random_state: Semilla para reproducibilidad
        """
        self.contamination = contamination
        self.random_state = random_state
        self.model = None
        self.feature_columns = None
        self.is_trained = False
        
    def detect_anomalies(self, df_final):
        """
        Detecta anomalías en el DataFrame de instrumentos.
        
        Este método:
        1. Selecciona features de negocio relevantes
        2. Entrena el modelo Isolation Forest
        3. Predice anomalías
        4. Agrega columnas con resultados
        
        Args:
            df_final: DataFrame con features ya calculados
        
        Returns:
            df_final enriquecido con columnas:
                - anomaly_score: -1 (anomalía) o 1 (normal)
                - anomaly_score_value: score continuo (más negativo = más anómalo)
                - es_anomalia: True/False
        """
        logger.info("Iniciando detección de anomalías con features de negocio...")
        
        # Seleccionar features para el modelo
        self.feature_columns = self._select_features(df_final)
        logger.info(f"Features seleccionados: {len(self.feature_columns)} columnas")
        
        # Extraer matriz de features
        X = self._prepare_feature_matrix(df_final)
        
        # Verificar que hay datos suficientes
        if len(X) < 10:
            logger.warning(f"Insuficientes datos para entrenar ({len(X)} instrumentos). "
                          "Se requieren al menos 10. Marcando todos como normales.")
            df_final['anomaly_score'] = 1
            df_final['anomaly_score_value'] = 0.0
            df_final['es_anomalia'] = False
            return df_final
        
        # Entrenar modelo
        self._train_model(X)
        
        # Predecir anomalías
        df_final = self._predict_anomalies(df_final, X)
        
        # Estadísticas
        num_anomalias = df_final['es_anomalia'].sum()
        pct_anomalias = (num_anomalias / len(df_final)) * 100
        logger.info(f"Detección completada: {num_anomalias} anomalías detectadas "
                   f"({pct_anomalias:.1f}% del total)")
        
        return df_final
    
    def _select_features(self, df_final):
        """
        Selecciona features para Isolation Forest.
        
        El modelo APRENDE automáticamente qué combinaciones son anómalas:
        - Métricas de diferencias por moneda
        - Monedas faltantes
        - Inconsistencias (suma != 100%)
        - Tipo de instrumento (C01=Caja, C04=Bonos, C09=ETF, etc.)
        
        El árbol descubre patrones como:
        - "C04 (Bono) + max_diferencia=50% = anómalo"
        - "C09 (ETF) + 10 monedas = normal"
        - "C01 (Caja) + desviacion_suma != 0 = anómalo"
        """
        # Métricas puras de diferencias y problemas
        business_features = [
            # Diferencias por moneda
            'max_diferencia_moneda',
            'discrepancia_total',
            'num_diferencias_gt_10pct',
            'num_diferencias_gt_20pct',
            
            # Monedas faltantes
            'num_monedas_solo_interno',
            'num_monedas_solo_externo',
            'pct_monedas_solo_interno',
            'pct_monedas_solo_externo',
            
            # Inconsistencias
            'desviacion_suma_100_interno',
            'desviacion_suma_100_externo',
            'tiene_dist_vs_sin_dist',
        ]
        
        # Tipo de instrumento (one-hot encoding de grupos)
        tipo_features = [col for col in df_final.columns if col.startswith('tipo_grupo_')]
        
        # Fallback a tipo_es_* si no existen tipo_grupo_*
        if not tipo_features:
            tipo_features = [col for col in df_final.columns if col.startswith('tipo_es_')]
        
        # Combinar
        all_features = business_features + tipo_features
        
        # Filtrar solo los que existen
        available_features = [f for f in all_features if f in df_final.columns]
        
        # Log
        num_tipos = len([f for f in tipo_features if f in df_final.columns])
        logger.info(f"Features usados: {len(available_features)} ({len(business_features)} métricas + {num_tipos} grupos de tipo)")
        
        return available_features
    
    def _prepare_feature_matrix(self, df_final):
        """
        Prepara la matriz de features para el modelo.
        
        - Selecciona columnas de features
        - Maneja valores faltantes (fillna con 0)
        - Convierte a numpy array
        """
        X = df_final[self.feature_columns].copy()
        
        # Manejar NaN (rellenar con 0)
        X = X.fillna(0)
        
        # Verificar si hay valores infinitos
        if np.isinf(X.values).any():
            logger.warning("Detectados valores infinitos en features. Reemplazando por 0.")
            X = X.replace([np.inf, -np.inf], 0)
        
        return X
    
    def _train_model(self, X):
        """
        Entrena el modelo Isolation Forest.
        
        Args:
            X: Matriz de features (numpy array o DataFrame)
        """
        logger.info(f"Entrenando Isolation Forest con {len(X)} instrumentos...")
        
        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state,
            n_estimators=100,
            max_samples='auto',
            max_features=1.0,
            bootstrap=False,
            n_jobs=-1,  # Usar todos los cores disponibles
            verbose=0
        )
        
        self.model.fit(X)
        self.is_trained = True
        logger.info("Modelo entrenado exitosamente")
    
    def _predict_anomalies(self, df_final, X):
        """
        Predice anomalías y agrega columnas al DataFrame.
        
        Args:
            df_final: DataFrame original
            X: Matriz de features
        
        Returns:
            df_final con columnas de predicción agregadas
        """
        # Predicción: -1 = anomalía, 1 = normal
        predictions = self.model.predict(X)
        df_final['anomaly_score'] = predictions
        
        # Score continuo (más negativo = más anómalo)
        scores = self.model.score_samples(X)
        df_final['anomaly_score_value'] = scores
        
        # Conversión a booleano
        df_final['es_anomalia'] = (predictions == -1)
        
        return df_final
    
    def save_model(self, filepath='data/models/isolation_forest_v1.pkl'):
        """
        Guarda el modelo entrenado en disco.
        
        Args:
            filepath: Ruta donde guardar el modelo
        """
        if not self.is_trained:
            logger.warning("No se puede guardar: modelo no entrenado")
            return
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            'model': self.model,
            'feature_columns': self.feature_columns,
            'contamination': self.contamination,
            'random_state': self.random_state
        }
        
        joblib.dump(model_data, filepath)
        logger.info(f"Modelo guardado en: {filepath}")
    
    def load_model(self, filepath='data/models/isolation_forest_v1.pkl'):
        """
        Carga un modelo previamente entrenado desde disco.
        
        Args:
            filepath: Ruta del modelo guardado
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            logger.warning(f"Archivo no encontrado: {filepath}")
            return False
        
        model_data = joblib.load(filepath)
        self.model = model_data['model']
        self.feature_columns = model_data['feature_columns']
        self.contamination = model_data['contamination']
        self.random_state = model_data['random_state']
        self.is_trained = True
        
        logger.info(f"Modelo cargado desde: {filepath}")
        return True
    
    def get_feature_importance(self, df_final):
        """
        Calcula la importancia relativa de cada feature.
        
        Nota: Isolation Forest no tiene feature importance nativo como Random Forest.
        Esta es una aproximación basada en la varianza de los scores cuando
        se permuta cada feature.
        
        Returns:
            DataFrame con features ordenados por importancia
        """
        if not self.is_trained:
            logger.warning("Modelo no entrenado. No se puede calcular importancia.")
            return None
        
        X = self._prepare_feature_matrix(df_final)
        base_scores = self.model.score_samples(X)
        base_variance = np.var(base_scores)
        
        importances = {}
        for i, feature in enumerate(self.feature_columns):
            # Permutar feature
            X_permuted = X.copy()
            X_permuted.iloc[:, i] = np.random.permutation(X_permuted.iloc[:, i])
            
            # Calcular nuevo score
            permuted_scores = self.model.score_samples(X_permuted)
            permuted_variance = np.var(permuted_scores)
            
            # Importancia = cambio en varianza
            importances[feature] = abs(permuted_variance - base_variance)
        
        # Convertir a DataFrame y ordenar
        importance_df = pd.DataFrame(
            list(importances.items()),
            columns=['Feature', 'Importance']
        ).sort_values('Importance', ascending=False)
        
        return importance_df
