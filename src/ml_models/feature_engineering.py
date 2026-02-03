"""
Módulo de Feature Engineering para extracción de características de instrumentos.

Este módulo enriquece el DataFrame final del pipeline con features calculados
que serán utilizados por el modelo de detección de anomalías (Isolation Forest)
y el clasificador supervisado (Random Forest).
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def add_features(df_final, df_alloc_ext, df_alloc_int):
    """
    Enriquece df_final con features calculados para ML.
    
    Args:
        df_final: DataFrame con instrumentos únicos (resultado del pipeline)
        df_alloc_ext: DataFrame con allocations externos (Refinitiv)
        df_alloc_int: DataFrame con allocations internos
    
    Returns:
        df_final enriquecido con ~26 columnas nuevas de features
    """
    logger.info("Iniciando feature engineering...")
    
    # Inicializar columnas de features
    df_final = _initialize_feature_columns(df_final)
    
    # Calcular features de distribución (requiere loop por instrumento)
    df_final = _calculate_distribution_features(df_final, df_alloc_ext, df_alloc_int)
    
    # **NUEVAS FEATURES DE NEGOCIO: Detectan problemas reales**
    df_final = _calculate_currency_differences(df_final, df_alloc_ext, df_alloc_int)
    
    # Calcular features simples (operaciones vectorizadas)
    df_final = _calculate_identifier_features(df_final)
    df_final = _calculate_concordance_features(df_final)
    df_final = _calculate_type_features(df_final)  # One-hot encoding de tipos
    
    logger.info(f"Feature engineering completado. Total columnas: {len(df_final.columns)}")
    return df_final


def _initialize_feature_columns(df_final):
    """Inicializa todas las columnas de features con valores por defecto."""
    
    # Features de distribución externa
    df_final['num_monedas_ext'] = 0
    df_final['entropia_ext'] = 0.0
    df_final['pct_dominante_ext'] = 0.0
    df_final['std_distribucion_ext'] = 0.0
    
    # Features de distribución interna
    df_final['num_monedas_int'] = 0
    df_final['entropia_int'] = 0.0
    df_final['pct_dominante_int'] = 0.0
    
    return df_final


def _calculate_distribution_features(df_final, df_alloc_ext, df_alloc_int):
    """
    Calcula features de distribución de monedas para cada instrumento.
    Requiere iterar sobre cada instrumento individualmente.
    """
    logger.info("Calculando features de distribución de monedas...")
    
    for idx, row in df_final.iterrows():
        # Obtener allocations externos
        allocs_ext = _get_allocations_for_instrument(
            df_alloc_ext,
            ric=row.get('RIC'),
            isin=row.get('Isin'),
            cusip=row.get('Cusip')
        )
        
        # Calcular features externos
        if not allocs_ext.empty:
            percentages_ext = allocs_ext['percentage_num'].values
            df_final.at[idx, 'num_monedas_ext'] = len(allocs_ext)
            df_final.at[idx, 'entropia_ext'] = _calculate_entropy(percentages_ext)
            df_final.at[idx, 'pct_dominante_ext'] = percentages_ext.max()
            df_final.at[idx, 'std_distribucion_ext'] = percentages_ext.std()
        
        # Obtener allocations internos
        allocs_int = _get_allocations_for_instrument(
            df_alloc_int,
            nombre=row.get('Instrumento'),
            ric=row.get('RIC'),
            isin=row.get('Isin'),
            cusip=row.get('Cusip')
        )
        
        # Calcular features internos
        if not allocs_int.empty:
            percentages_int = allocs_int['percentage_num'].values
            df_final.at[idx, 'num_monedas_int'] = len(allocs_int)
            df_final.at[idx, 'entropia_int'] = _calculate_entropy(percentages_int)
            df_final.at[idx, 'pct_dominante_int'] = percentages_int.max()
    
    logger.info("Features de distribución calculados")
    return df_final


def _get_allocations_for_instrument(df_alloc, nombre=None, ric=None, isin=None, cusip=None):
    """
    Busca allocations de un instrumento específico usando sus identificadores.
    
    Args:
        df_alloc: DataFrame de allocations (ext o int)
        nombre: Nombre del instrumento
        ric: Código RIC
        isin: Código ISIN
        cusip: Código CUSIP
    
    Returns:
        DataFrame filtrado con allocations del instrumento
    """
    mask = pd.Series(False, index=df_alloc.index)
    
    # Para allocations internos: buscar por Nombre, RIC, Isin, Cusip
    if pd.notna(nombre) and 'Nombre' in df_alloc.columns:
        mask |= (df_alloc['Nombre'] == nombre)
    if pd.notna(ric) and 'RIC' in df_alloc.columns:
        mask |= (df_alloc['RIC'] == ric)
    if pd.notna(isin) and 'Isin' in df_alloc.columns:
        mask |= (df_alloc['Isin'] == isin)
    if pd.notna(cusip) and 'Cusip' in df_alloc.columns:
        mask |= (df_alloc['Cusip'] == cusip)
    
    # Para allocations externos: buscar por 'instrument' column
    if pd.notna(ric) and 'instrument' in df_alloc.columns:
        mask |= (df_alloc['instrument'] == ric)
    if pd.notna(isin) and 'instrument' in df_alloc.columns:
        mask |= (df_alloc['instrument'] == isin)
    if pd.notna(cusip) and 'instrument' in df_alloc.columns:
        mask |= (df_alloc['instrument'] == cusip)
    
    return df_alloc[mask]


def _calculate_entropy(percentages):
    """
    Calcula la entropía de Shannon de una distribución.
    
    Entropía = -Σ(p × log₂(p))
    
    Args:
        percentages: Array de porcentajes (0-100)
    
    Returns:
        float: Entropía (0.0 = concentrado, alto = balanceado)
    """
    # Convertir a probabilidades [0, 1]
    probs = percentages / 100.0
    
    # Filtrar valores <= 0 (log no está definido)
    probs = probs[probs > 0]
    
    if len(probs) == 0:
        return 0.0
    
    # Calcular entropía
    entropy = -np.sum(probs * np.log2(probs))
    return entropy


def _calculate_identifier_features(df_final):
    """Calcula features relacionados con identificadores y calidad de datos."""
    logger.info("Calculando features de identificadores...")
    
    # Features de identificadores (binarios)
    df_final['tiene_ric'] = df_final['RIC'].notna().astype(int)
    df_final['tiene_isin'] = df_final['Isin'].notna().astype(int)
    df_final['tiene_cusip'] = df_final['Cusip'].notna().astype(int)
    
    # Número total de identificadores disponibles
    df_final['num_identificadores'] = (
        df_final['tiene_ric'] + 
        df_final['tiene_isin'] + 
        df_final['tiene_cusip']
    )
    
    # Features de disponibilidad de datos
    df_final['tiene_alloc_ext'] = (df_final['num_monedas_ext'] > 0).astype(int)
    df_final['tiene_alloc_int'] = (df_final['num_monedas_int'] > 0).astype(int)
    
    logger.info("Features de identificadores calculados")
    return df_final


def _calculate_concordance_features(df_final):
    """Calcula features de concordancia entre datos internos y externos."""
    logger.info("Calculando features de concordancia...")
    
    # ¿Las monedas internas y calculadas coinciden?
    df_final['monedas_coinciden'] = (
        df_final['Moneda_Interna'] == df_final['Moneda_Calculada']
    ).astype(int)
    
    # ¿Ambos son balanceados?
    df_final['ambos_balanceados'] = (
        df_final['Moneda_Interna'].str.lower().str.contains('balanceado', na=False) &
        df_final['Moneda_Calculada'].str.lower().str.contains('balanceado', na=False)
    ).astype(int)
    
    # Coherencia de clasificación "balanceado"
    # Si es "balanceado", el pct dominante debe ser < 90%
    es_balanceado = df_final['Moneda_Calculada'].str.lower().str.contains('balanceado', na=False)
    pct_coherente = df_final['pct_dominante_ext'] < 90
    df_final['coherencia_balanceado'] = (
        (~es_balanceado) |  # Si no es balanceado, siempre coherente
        (es_balanceado & pct_coherente)  # Si es balanceado, verificar pct < 90%
    ).astype(int)
    
    logger.info("Features de concordancia calculados")
    return df_final


def _calculate_currency_differences(df_final, df_alloc_ext, df_alloc_int):
    """
    Calcula diferencias por moneda individual entre allocations internos y externos.
    
    Features críticos para detectar anomalías reales:
    - max_diferencia_moneda: Mayor diferencia en una sola moneda
    - discrepancia_total: Suma de todas las diferencias absolutas
    - num_monedas_solo_interno/externo: Monedas que faltan en una fuente
    - pct_monedas_solo_interno/externo: % de exposición de monedas faltantes
    
    IMPORTANTE: Usa _get_allocations_for_instrument() para buscar por múltiples IDs
    """
    logger.info("Calculando diferencias por moneda individual...")
    
    # Inicializar columnas
    df_final['max_diferencia_moneda'] = 0.0
    df_final['discrepancia_total'] = 0.0
    df_final['num_diferencias_gt_10pct'] = 0
    df_final['num_diferencias_gt_20pct'] = 0
    df_final['num_monedas_solo_interno'] = 0
    df_final['num_monedas_solo_externo'] = 0
    df_final['pct_monedas_solo_interno'] = 0.0
    df_final['pct_monedas_solo_externo'] = 0.0
    df_final['desviacion_suma_100_interno'] = 0.0
    df_final['desviacion_suma_100_externo'] = 0.0
    df_final['tiene_dist_vs_sin_dist'] = 0
    
    for idx, row in df_final.iterrows():
        # Obtener allocations externos usando búsqueda por identificadores
        alloc_ext = _get_allocations_for_instrument(
            df_alloc_ext,
            ric=row.get('RIC'),
            isin=row.get('Isin'),
            cusip=row.get('Cusip')
        )
        
        # Obtener allocations internos usando búsqueda por identificadores
        alloc_int = _get_allocations_for_instrument(
            df_alloc_int,
            nombre=row.get('Instrumento'),
            ric=row.get('RIC'),
            isin=row.get('Isin'),
            cusip=row.get('Cusip')
        )
        
        has_ext = len(alloc_ext) > 0
        has_int = len(alloc_int) > 0
        
        # Feature: uno tiene distribución, el otro no
        if has_ext != has_int:
            df_final.at[idx, 'tiene_dist_vs_sin_dist'] = 1
            continue
        
        if not has_ext and not has_int:
            continue
        
        # Crear diccionarios de distribución por moneda
        # EXTERNO: Usar 'currency_code' (ya normalizado en el pipeline)
        # INTERNO: 'currency_code' y 'percentage_num' (float)
        dist_ext = {}
        dist_int = {}
        
        # Procesar allocations externos - USAR currency_code YA NORMALIZADO
        if has_ext and 'currency_code' in alloc_ext.columns and 'percentage_num' in alloc_ext.columns:
            dist_ext = dict(zip(alloc_ext['currency_code'], alloc_ext['percentage_num']))
        
        # Procesar allocations internos
        if has_int and 'currency_code' in alloc_int.columns and 'percentage_num' in alloc_int.columns:
            dist_int = dict(zip(alloc_int['currency_code'], alloc_int['percentage_num']))
        
        # Verificar suma 100%
        suma_ext = sum(dist_ext.values()) if dist_ext else 0
        suma_int = sum(dist_int.values()) if dist_int else 0
        df_final.at[idx, 'desviacion_suma_100_externo'] = abs(100 - suma_ext)
        df_final.at[idx, 'desviacion_suma_100_interno'] = abs(100 - suma_int)
        
        # Obtener todas las monedas únicas
        all_currencies = set(dist_ext.keys()) | set(dist_int.keys())
        
        # Calcular diferencias por moneda
        diffs = []
        only_int = []
        only_ext = []
        
        for currency in all_currencies:
            pct_ext = dist_ext.get(currency, 0.0)
            pct_int = dist_int.get(currency, 0.0)
            diff = abs(pct_ext - pct_int)
            
            diffs.append(diff)
            
            # Monedas que solo están en una fuente
            if pct_int > 0 and pct_ext == 0:
                only_int.append((currency, pct_int))
            elif pct_ext > 0 and pct_int == 0:
                only_ext.append((currency, pct_ext))
        
        # Métricas agregadas
        if diffs:
            df_final.at[idx, 'max_diferencia_moneda'] = max(diffs)
            df_final.at[idx, 'discrepancia_total'] = sum(diffs)
            df_final.at[idx, 'num_diferencias_gt_10pct'] = sum(1 for d in diffs if d > 10)
            df_final.at[idx, 'num_diferencias_gt_20pct'] = sum(1 for d in diffs if d > 20)
        
        # Monedas faltantes
        df_final.at[idx, 'num_monedas_solo_interno'] = len(only_int)
        df_final.at[idx, 'num_monedas_solo_externo'] = len(only_ext)
        df_final.at[idx, 'pct_monedas_solo_interno'] = sum(pct for _, pct in only_int)
        df_final.at[idx, 'pct_monedas_solo_externo'] = sum(pct for _, pct in only_ext)
    
    logger.info("Diferencias por moneda calculadas")
    return df_final


def _calculate_type_features(df_final):
    """
    Calcula features one-hot encoding para GRUPOS de tipos de instrumento.
    
    Grupos:
    - Acciones: C02, C14
    - Bonos: C04
    - Fondos/ETF: C03, C09, C10
    
    El Isolation Forest usará estos grupos para aprender automáticamente:
    - Qué nivel de diferencias es normal para Fondos/ETF vs Bonos
    - Qué nivel de diversificación es esperado por grupo
    - Qué combinaciones de métricas + grupo son anómalas
    
    NO escribimos reglas manualmente - el árbol las aprende.
    """
    logger.info("Calculando features de grupos de tipo...")
    
    # Usar Tipo_Grupo si existe, sino usar Tipo
    if 'Tipo_Grupo' in df_final.columns:
        # Crear one-hot para los 3 grupos: Acciones, Bonos, Fondos/ETF
        df_final['tipo_grupo_acciones'] = (df_final['Tipo_Grupo'] == 'Acciones').astype(int)
        df_final['tipo_grupo_bonos'] = (df_final['Tipo_Grupo'] == 'Bonos').astype(int)
        df_final['tipo_grupo_fondos_etf'] = (df_final['Tipo_Grupo'] == 'Fondos/ETF').astype(int)
        logger.info(f"Features de grupos de tipo calculados: 3 categorías (Acciones, Bonos, Fondos/ETF)")
    else:
        # Fallback: usar Tipo original
        tipos_unicos = df_final['Tipo'].unique()
        for tipo in tipos_unicos:
            nombre_col = f"tipo_es_{tipo.lower().replace(' ', '_')}"
            df_final[nombre_col] = (df_final['Tipo'] == tipo).astype(int)
        logger.info(f"Features de tipo calculados: {len(tipos_unicos)} categorías")
    
    return df_final


def get_feature_names():
    """
    Retorna la lista de nombres de features calculados (para referencia).
    
    Returns:
        list: Nombres de todas las columnas de features
    """
    return [
        # **FEATURES USADOS POR ISOLATION FOREST (11 métricas + tipos)**
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
        
        # Tipos (dinámico, ~6 categorías)
        # 'tipo_es_c02', 'tipo_es_c03', 'tipo_es_c04', 'tipo_es_c09', 'tipo_es_c10', 'tipo_es_c14'
        
        # **FEATURES CALCULADOS PERO NO USADOS (para otros análisis)**
        # Distribución: num_monedas_ext/int, entropia_ext/int, pct_dominante_ext/int, std_distribucion_ext
        # Identificadores: tiene_ric, tiene_isin, tiene_cusip, num_identificadores, tiene_alloc_ext/int
        # Concordancia: monedas_coinciden, ambos_balanceados, coherencia_balanceado
    ]
