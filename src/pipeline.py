"""
Pipeline completo de procesamiento de datos para conciliación de allocations.
"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
import logging
from datetime import datetime
from src.ml_models import add_features, AnomalyDetector
from src.currency_mapping import CURRENCY_MAP_REFINITIV_TO_ISO, normalize_currency_name

logger = logging.getLogger(__name__)

class ConciliacionPipeline:
    """Pipeline completo de procesamiento y conciliación de datos."""
    
    def __init__(self, data: Dict[str, pd.DataFrame]):
        """
        Inicializa el pipeline con los datos cargados.
        
        Args:
            data: Diccionario con los DataFrames necesarios
        """
        self.posiciones = data['posiciones']
        self.instrumentos = data['instrumentos']
        self.tipo_map = data['tipo_map']
        self.allocations_externo = data['allocations_externo']
        self.allocations_interno = data['allocations_interno']
        self.tipos_filtro = data['tipos_filtro']
        
    def paso_1_filtrar_posiciones(self, fecha_minima: str = "2025-01-01") -> pd.DataFrame:
        """
        PASO 1: Filtrar posiciones valorizadas por fecha.
        
        Filtros:
        - F. Proceso >= fecha_minima
        
        Returns:
            DataFrame con posiciones filtradas
        """
        logger.info(f"PASO 1: Filtrando posiciones con F. Proceso >= {fecha_minima}")
        
        fecha_min = pd.to_datetime(fecha_minima)
        
        df_filtrado = self.posiciones[
            self.posiciones['F. Proceso'] >= fecha_min
        ].copy()
        
        logger.info(f"Posiciones filtradas: {len(df_filtrado)} de {len(self.posiciones)}")
        return df_filtrado
    
    def paso_2_cruce_instrumentos(self, df_posiciones: pd.DataFrame) -> pd.DataFrame:
        """
        PASO 2: Cruzar posiciones con instrumentos internos.
        
        Estrategia híbrida optimizada:
        1. Primero intenta cruce por NOMBRE (Instrumento == Nombre)
        2. Para los no matcheados, usa Id_ti para saber qué columna buscar
        
        Returns:
            DataFrame con posiciones enriquecidas con info de instrumentos
        """
        logger.info("PASO 2: Cruzando posiciones con instrumentos internos")
        
        instrumentos = self.instrumentos.copy()
        
        # Normalizar nombres para match
        df_posiciones['Instrumento_norm'] = df_posiciones['Instrumento'].astype(str).str.strip().str.upper()
        instrumentos['Nombre_norm'] = instrumentos['Nombre'].astype(str).str.strip().str.upper()
        
        # Eliminar columnas que vienen de Posiciones y que necesitamos de Instrumentos
        # (para evitar conflictos de nombres en el merge)
        columnas_a_eliminar = [col for col in ['ID', 'Cusip', 'Isin', 'RIC'] if col in df_posiciones.columns]
        if columnas_a_eliminar:
            df_posiciones = df_posiciones.drop(columns=columnas_a_eliminar)
            logger.info(f"  Eliminadas columnas conflictivas de posiciones: {columnas_a_eliminar}")
        
        # ESTRATEGIA 1: Match por NOMBRE (más rápido y directo)
        df_match_nombre = df_posiciones.merge(
            instrumentos,
            left_on='Instrumento_norm',
            right_on='Nombre_norm',
            how='inner'
        )
        df_match_nombre['matched_by'] = 'Nombre'
        
        logger.info(f"  Cruces por Nombre: {len(df_match_nombre)}")
        
        # Identificar posiciones que NO matchearon
        posiciones_matcheadas = set(df_match_nombre['Id_ti_valor'].unique())
        df_sin_match = df_posiciones[~df_posiciones['Id_ti_valor'].isin(posiciones_matcheadas)].copy()
        
        logger.info(f"  Posiciones sin match por nombre: {len(df_sin_match)}")
        
        # ESTRATEGIA 2: Para los sin match, usar Id_ti como guía
        cruces_por_id = []
        
        if not df_sin_match.empty:
            # Obtener tipos de identificadores únicos en Id_ti
            tipos_id_disponibles = df_sin_match['Id_ti'].dropna().unique()
            logger.info(f"  Tipos de identificadores en Id_ti: {tipos_id_disponibles.tolist()}")
            
            # Normalizar Id_ti_valor
            df_sin_match['Id_ti_valor_norm'] = df_sin_match['Id_ti_valor'].astype(str).str.strip().str.upper()
            
            # Para cada tipo de Id_ti, hacer merge con la columna correspondiente
            for tipo_id in tipos_id_disponibles:
                # Filtrar posiciones de este tipo
                df_tipo = df_sin_match[df_sin_match['Id_ti'] == tipo_id].copy()
                
                if df_tipo.empty:
                    continue
                
                # Verificar si la columna existe en instrumentos
                if tipo_id not in instrumentos.columns:
                    logger.warning(f"  Columna {tipo_id} no existe en instrumentos")
                    continue
                
                # Normalizar la columna del identificador
                instrumentos[f'{tipo_id}_norm'] = instrumentos[tipo_id].astype(str).str.strip().str.upper()
                
                # Hacer merge
                merge_temp = df_tipo.merge(
                    instrumentos,
                    left_on='Id_ti_valor_norm',
                    right_on=f'{tipo_id}_norm',
                    how='inner'
                )
                
                if len(merge_temp) > 0:
                    merge_temp['matched_by'] = tipo_id
                    cruces_por_id.append(merge_temp)
                    logger.info(f"  Cruces por {tipo_id}: {len(merge_temp)}")
        
        # Combinar todos los cruces
        if cruces_por_id:
            df_match_id = pd.concat(cruces_por_id, ignore_index=True)
            df_cruzado = pd.concat([df_match_nombre, df_match_id], ignore_index=True)
        else:
            df_cruzado = df_match_nombre
        
        # Eliminar duplicados usando columnas que sabemos que existen
        columnas_dedup = []
        for col in ['ID', 'Cliente', 'Activo', 'F. Proceso', 'Id_ti_valor']:
            if col in df_cruzado.columns:
                columnas_dedup.append(col)
        
        if columnas_dedup:
            df_cruzado = df_cruzado.drop_duplicates(subset=columnas_dedup, keep='first')
        else:
            # Si no hay columnas para deduplicar, usar todas
            df_cruzado = df_cruzado.drop_duplicates(keep='first')
        
        logger.info(f"Total registros cruzados: {len(df_cruzado)}")
        
        # Estadísticas de coverage
        total_posiciones = len(df_posiciones)
        cobertura = (len(df_cruzado) / total_posiciones * 100) if total_posiciones > 0 else 0
        logger.info(f"Cobertura del cruce: {cobertura:.1f}% ({len(df_cruzado)}/{total_posiciones})")
        
        return df_cruzado
    
    def paso_3_filtrar_tipo_instrumento(self, df_cruzado: pd.DataFrame) -> pd.DataFrame:
        """
        PASO 3: Filtrar por tipo de instrumento.
        
        Filtros:
        - Tipo instrumento IN [C02, C04, C03, C09, C10, C14]
          (Acciones, Bonos, Fondos Mutuos, ETF, Fondos de Inversión, Acciones Pref.)
        - Debe tener ISIN o RIC
        
        Returns:
            DataFrame con instrumentos únicos filtrados
        """
        logger.info("PASO 3: Filtrando por tipo de instrumento")
        
        # Primero extraer instrumentos únicos del cruce de posiciones
        columnas_instrumento = ['ID', 'Nombre', 'Cusip', 'Isin', 'RIC', 'Tipo instrumento', 'SubMoneda']
        df_instrumentos = df_cruzado[columnas_instrumento].drop_duplicates(subset=['Cusip', 'Isin'], keep='first').copy()
        
        logger.info(f"  Instrumentos únicos extraídos: {len(df_instrumentos)} de {len(df_cruzado)} posiciones")
        
        # Filtrar por tipo de instrumento
        df_filtrado = df_instrumentos[
            df_instrumentos['Tipo instrumento'].isin(self.tipos_filtro)
        ].copy()
        
        logger.info(f"  Filtrado por tipo: {len(df_filtrado)} de {len(df_instrumentos)}")
        
        # Filtrar instrumentos que tengan ISIN o RIC
        df_filtrado = df_filtrado[
            (df_filtrado['Isin'].notna() & (df_filtrado['Isin'] != '')) |
            (df_filtrado['RIC'].notna() & (df_filtrado['RIC'] != ''))
        ].copy()
        
        logger.info(f"  Filtrado por ISIN/RIC: {len(df_filtrado)} instrumentos únicos")
        
        # Renombrar 'Tipo instrumento' a 'Tipo' para simplificar
        df_filtrado = df_filtrado.rename(columns={'Tipo instrumento': 'Tipo'})
        
        # Agregar nombre descriptivo del tipo
        df_filtrado['Tipo_Nombre'] = df_filtrado['Tipo'].map(self.tipo_map)
        
        # Agregar grupos de tipos para filtros y ML
        def asignar_grupo_tipo(codigo):
            if codigo in ['C02', 'C14']:  # Acciones + Acciones Pref.
                return 'Acciones'
            elif codigo == 'C04':  # Bonos
                return 'Bonos'
            elif codigo in ['C03', 'C09', 'C10']:  # Fondos Mutuos + ETF + Fondos de Inversión
                return 'Fondos/ETF'
            else:
                return 'Otros'
        
        df_filtrado['Tipo_Grupo'] = df_filtrado['Tipo'].apply(asignar_grupo_tipo)
        
        return df_filtrado
    
    def paso_4_obtener_allocations_externo(self, df_filtrado: pd.DataFrame) -> pd.DataFrame:
        """
        PASO 4: Obtener allocations externos para los instrumentos filtrados.
        
        Cruza con allocations externos por Cusip (instrument).
        Pivotea las monedas (CLP, USD, EUR, etc.) a columnas.
        
        Returns:
            DataFrame con allocations externos por instrumento
        """
        logger.info("PASO 4: Obteniendo allocations externos")
        
        # Preparar allocations externos
        alloc_ext = self.allocations_externo.copy()
        
        # Normalizar instrument en allocations
        alloc_ext['instrument_norm'] = alloc_ext['instrument'].astype(str).str.strip().str.upper()
        
        # Obtener identificadores únicos normalizados (ahora vienen directo de Instrumentos sin sufijos)
        df_filtrado['Cusip_norm'] = df_filtrado['Cusip'].astype(str).str.strip().str.upper()
        df_filtrado['Isin_norm'] = df_filtrado['Isin'].astype(str).str.strip().str.upper()
        df_filtrado['RIC_norm'] = df_filtrado['RIC'].astype(str).str.strip().str.upper()
        
        # Crear set de identificadores válidos para búsqueda rápida
        identificadores_validos = set()
        for col in ['Cusip_norm', 'Isin_norm', 'RIC_norm']:
            ids = df_filtrado[col].unique()
            identificadores_validos.update([x for x in ids if x != 'NAN' and pd.notna(x)])
        
        logger.info(f"  Identificadores únicos a buscar: {len(identificadores_validos)}")
        
        # Filtrar allocations externos solo con identificadores que tenemos
        alloc_ext_filtrado = alloc_ext[alloc_ext['instrument_norm'].isin(identificadores_validos)].copy()
        
        logger.info(f"  Allocations externos encontrados: {len(alloc_ext_filtrado)} registros")
        
        if alloc_ext_filtrado.empty:
            logger.warning("  No se encontraron allocations externos")
            return pd.DataFrame()
        
        # Preparar DataFrame de referencia con todos los identificadores únicos
        df_identificadores = df_filtrado[['ID', 'Cusip', 'Isin', 'RIC', 'Cusip_norm', 'Isin_norm', 'RIC_norm', 'Nombre']].drop_duplicates()
        
        # Hacer 3 merges separados (uno por cada identificador) para maximizar matches
        matches = []
        
        # MERGE 1: Por RIC
        df_ric = df_identificadores[df_identificadores['RIC_norm'].notna() & 
                                     (df_identificadores['RIC_norm'] != 'NAN') & 
                                     (df_identificadores['RIC_norm'] != 'NONE')].copy()
        if not df_ric.empty:
            match_ric = alloc_ext_filtrado.merge(
                df_ric[['ID', 'Cusip', 'Isin', 'RIC', 'RIC_norm', 'Nombre']],
                left_on='instrument_norm',
                right_on='RIC_norm',
                how='inner'
            )
            if not match_ric.empty:
                match_ric['matched_by'] = 'RIC'
                matches.append(match_ric)
                logger.info(f"  Matches por RIC: {len(match_ric)}")
        
        # MERGE 2: Por Isin
        df_isin = df_identificadores[df_identificadores['Isin_norm'].notna() & 
                                      (df_identificadores['Isin_norm'] != 'NAN') & 
                                      (df_identificadores['Isin_norm'] != 'NONE')].copy()
        if not df_isin.empty:
            match_isin = alloc_ext_filtrado.merge(
                df_isin[['ID', 'Cusip', 'Isin', 'RIC', 'Isin_norm', 'Nombre']],
                left_on='instrument_norm',
                right_on='Isin_norm',
                how='inner'
            )
            if not match_isin.empty:
                match_isin['matched_by'] = 'Isin'
                matches.append(match_isin)
                logger.info(f"  Matches por Isin: {len(match_isin)}")
        
        # MERGE 3: Por Cusip
        df_cusip = df_identificadores[df_identificadores['Cusip_norm'].notna() & 
                                       (df_identificadores['Cusip_norm'] != 'NAN') & 
                                       (df_identificadores['Cusip_norm'] != 'NONE')].copy()
        if not df_cusip.empty:
            match_cusip = alloc_ext_filtrado.merge(
                df_cusip[['ID', 'Cusip', 'Isin', 'RIC', 'Cusip_norm', 'Nombre']],
                left_on='instrument_norm',
                right_on='Cusip_norm',
                how='inner'
            )
            if not match_cusip.empty:
                match_cusip['matched_by'] = 'Cusip'
                matches.append(match_cusip)
                logger.info(f"  Matches por Cusip: {len(match_cusip)}")
        
        # Combinar todos los matches
        if not matches:
            logger.warning("  No se encontraron cruces con ningún identificador")
            return pd.DataFrame()
        
        alloc_ext_filtrado = pd.concat(matches, ignore_index=True)
        logger.info(f"  Total allocations cruzados: {len(alloc_ext_filtrado)}")
        
        # CRÍTICO: Filtrar por la fecha más reciente PRIMERO (antes de eliminar duplicados)
        # Esto evita sumar porcentajes de diferentes fechas
        if 'date' in alloc_ext_filtrado.columns:
            # Obtener la fecha más reciente por instrumento
            fecha_reciente_por_inst = alloc_ext_filtrado.groupby('instrument')['date'].max().reset_index()
            fecha_reciente_por_inst.columns = ['instrument', 'fecha_mas_reciente']
            
            # Merge y filtrar solo registros de la fecha más reciente
            alloc_ext_filtrado = alloc_ext_filtrado.merge(
                fecha_reciente_por_inst,
                on='instrument',
                how='inner'
            )
            
            # Filtrar solo registros donde date == fecha_mas_reciente
            alloc_ext_filtrado = alloc_ext_filtrado[
                alloc_ext_filtrado['date'] == alloc_ext_filtrado['fecha_mas_reciente']
            ].copy()
            
            # Eliminar columna auxiliar
            alloc_ext_filtrado = alloc_ext_filtrado.drop(columns=['fecha_mas_reciente'])
            
            logger.info(f"  Allocations filtrados por fecha más reciente: {len(alloc_ext_filtrado)}")
        
        # Eliminar duplicados por instrumento y moneda (por si acaso hay duplicados en la misma fecha)
        alloc_ext_filtrado = alloc_ext_filtrado.drop_duplicates(subset=['instrument', 'class'], keep='first')
        
        # Tomar la fecha más reciente por instrumento
        alloc_ext_filtrado = alloc_ext_filtrado.sort_values('date', ascending=False)
        
        # Normalizar nombres de moneda de Refinitiv a códigos internos (ISO 4217)
        # Usando el mapeo centralizado para asegurar consistencia con allocations internos
        alloc_ext_filtrado['currency_code'] = alloc_ext_filtrado['class'].str.upper().str.strip().map(CURRENCY_MAP_REFINITIV_TO_ISO)
        alloc_ext_filtrado['currency_code'] = alloc_ext_filtrado['currency_code'].fillna(alloc_ext_filtrado['class'])
        
        # Convertir percentage a numérico (reemplazar coma por punto)
        alloc_ext_filtrado['percentage_num'] = alloc_ext_filtrado['percentage'].astype(str).str.replace(',', '.').astype(float)
        
        # Agregar columnas matched para compatibilidad
        alloc_ext_filtrado['matched_cusip'] = alloc_ext_filtrado.get('Cusip', '')
        alloc_ext_filtrado['matched_isin'] = alloc_ext_filtrado.get('Isin', '')
        alloc_ext_filtrado['matched_ric'] = alloc_ext_filtrado.get('RIC', '')
        
        logger.info(f"  Total allocations externos procesados: {len(alloc_ext_filtrado)} registros")
        return alloc_ext_filtrado
    
    def paso_5_identificar_moneda_principal(self, df_filtrado: pd.DataFrame, df_alloc_ext: pd.DataFrame) -> pd.DataFrame:
        """
        PASO 5: Identificar la moneda principal interna vs calculada desde externos.
        
        Para cada instrumento:
        - Moneda Interna (SubMoneda): viene del catálogo (CLP, USD, EUR, o "balanceado")
        - Moneda Calculada: se determina desde allocations externos (mayor % o "balanceado")
        
        Returns:
            DataFrame con un registro por instrumento con ambas clasificaciones
        """
        logger.info("PASO 5: Identificando moneda principal interna vs externa")
        
        # df_filtrado ya viene con instrumentos únicos desde PASO 3
        df_instrumentos = df_filtrado.copy()
        
        # Normalizar SubMoneda interna
        df_instrumentos['Moneda_Interna'] = df_instrumentos['SubMoneda'].astype(str).str.strip()
        df_instrumentos['Es_Balanceado_Interno'] = df_instrumentos['Moneda_Interna'].str.lower() == 'balanceado'
        
        logger.info(f"  Instrumentos a procesar: {len(df_instrumentos)}")
        logger.info(f"  Allocations externos disponibles: {len(df_alloc_ext)}")
        
        # Convertir ID a string para los merges posteriores
        df_instrumentos['ID'] = df_instrumentos['ID'].astype(str)
        
        # Agregar columna "Moneda:" desde allocations internos para detectar FALTA ALLOCATION
        if not self.allocations_interno.empty and 'Moneda:' in self.allocations_interno.columns:
            moneda_metadata = self.allocations_interno[['ID', 'Moneda:']].drop_duplicates(subset=['ID'])
            moneda_metadata['ID'] = moneda_metadata['ID'].astype(str)
            df_instrumentos = df_instrumentos.merge(
                moneda_metadata,
                on='ID',
                how='left'
            )
            logger.info(f"  Columna 'Moneda:' agregada desde allocations internos")
        else:
            df_instrumentos['Moneda:'] = None
        
        # Calcular moneda principal desde allocations externos
        if not df_alloc_ext.empty:
            # CRÍTICO: Filtrar solo por la fecha más reciente para cada instrumento
            # Esto evita sumar porcentajes de múltiples fechas
            if 'date' in df_alloc_ext.columns:
                # Obtener la fecha más reciente por instrumento
                fecha_mas_reciente = df_alloc_ext.groupby('instrument')['date'].max().reset_index()
                fecha_mas_reciente.columns = ['instrument', 'fecha_reciente']
                
                # Hacer merge para quedarnos solo con registros de la fecha más reciente
                df_alloc_ext_filtrado = df_alloc_ext.merge(
                    fecha_mas_reciente,
                    on='instrument',
                    how='inner'
                )
                
                # Filtrar solo registros donde date == fecha_reciente
                df_alloc_ext_filtrado = df_alloc_ext_filtrado[
                    df_alloc_ext_filtrado['date'] == df_alloc_ext_filtrado['fecha_reciente']
                ].copy()
                
                # Eliminar columna auxiliar
                df_alloc_ext_filtrado = df_alloc_ext_filtrado.drop(columns=['fecha_reciente'])
                
                logger.info(f"  Allocations filtrados por fecha más reciente: {len(df_alloc_ext_filtrado)} registros")
            else:
                df_alloc_ext_filtrado = df_alloc_ext.copy()
                logger.warning("  No se encontró columna 'date', no se puede filtrar por fecha más reciente")
            

            # Agrupar allocations por instrument y currency_code
            # Usar sum() por si hay múltiples clases de la misma moneda (aunque no debería)
            alloc_agrupado = df_alloc_ext_filtrado.groupby(['instrument', 'currency_code'])['percentage_num'].sum().reset_index()

            logger.info(f"  Allocations agrupados: {len(alloc_agrupado)} registros")

            # BLOQUE DE DEPURACIÓN PARA LP65145598
            logger.info('========== INICIO LOG DEBUG LP65145598 =========')
            alloc_lp = alloc_agrupado[alloc_agrupado['instrument'] == 'LP65145598']
            if alloc_lp.empty:
                logger.info('No hay datos en allocations agrupados para LP65145598')
            else:
                logger.info(alloc_lp)
            logger.info('========== FIN LOG DEBUG LP65145598 =========')

            # Para cada instrument único, determinar si es balanceado o cuál es la moneda principal
            resultados = []
            for instrument_id in alloc_agrupado['instrument'].unique():
                # Obtener todas las monedas de este instrumento
                monedas_inst = alloc_agrupado[alloc_agrupado['instrument'] == instrument_id]
                # Determinar si es balanceado (ninguna moneda >= 90%)
                max_percentage = monedas_inst['percentage_num'].max()
                es_balanceado = max_percentage < 90
                if es_balanceado:
                    moneda_calculada = 'balanceado'
                else:
                    # Obtener la moneda con mayor porcentaje
                    idx_max = monedas_inst['percentage_num'].idxmax()
                    moneda_calculada = monedas_inst.loc[idx_max, 'currency_code']
                resultados.append({
                    'instrument': instrument_id,
                    'Moneda_Calculada': moneda_calculada,
                    'Es_Balanceado_Externo': es_balanceado
                })
            df_monedas_calc = pd.DataFrame(resultados)
            
            # Normalizar identificadores
            df_instrumentos['RIC_norm'] = df_instrumentos['RIC'].astype(str).str.strip().str.upper()
            df_instrumentos['Isin_norm'] = df_instrumentos['Isin'].astype(str).str.strip().str.upper()
            df_instrumentos['Cusip_norm'] = df_instrumentos['Cusip'].astype(str).str.strip().str.upper()
            df_monedas_calc['instrument_norm'] = df_monedas_calc['instrument'].astype(str).str.strip().str.upper()
            
            # Hacer 3 merges y combinarlos (igual que en PASO 4)
            merges = []
            
            # Merge por RIC
            merge_ric = df_instrumentos.merge(
                df_monedas_calc[['instrument_norm', 'Moneda_Calculada', 'Es_Balanceado_Externo']],
                left_on='RIC_norm',
                right_on='instrument_norm',
                how='inner'
            )
            if not merge_ric.empty:
                merges.append(merge_ric)
            
            # Merge por Isin
            merge_isin = df_instrumentos.merge(
                df_monedas_calc[['instrument_norm', 'Moneda_Calculada', 'Es_Balanceado_Externo']],
                left_on='Isin_norm',
                right_on='instrument_norm',
                how='inner'
            )
            if not merge_isin.empty:
                merges.append(merge_isin)
            
            # Merge por Cusip
            merge_cusip = df_instrumentos.merge(
                df_monedas_calc[['instrument_norm', 'Moneda_Calculada', 'Es_Balanceado_Externo']],
                left_on='Cusip_norm',
                right_on='instrument_norm',
                how='inner'
            )
            if not merge_cusip.empty:
                merges.append(merge_cusip)
            
            # Combinar todos los merges
            if merges:
                df_con_moneda = pd.concat(merges, ignore_index=True)
                # Eliminar duplicados (instrumentos que matchearon por múltiples identificadores)
                df_con_moneda = df_con_moneda.drop_duplicates(subset=['Nombre'], keep='first')
                
                # Hacer left join con todos los instrumentos
                df_resultado = df_instrumentos.merge(
                    df_con_moneda[['Nombre', 'Moneda_Calculada', 'Es_Balanceado_Externo']],
                    on='Nombre',
                    how='left'
                )
            else:
                df_resultado = df_instrumentos.copy()
                df_resultado['Moneda_Calculada'] = 'Sin Datos'
                df_resultado['Es_Balanceado_Externo'] = False
            
            # Rellenar valores faltantes
            df_resultado['Moneda_Calculada'] = df_resultado['Moneda_Calculada'].fillna('Sin Datos')
            df_resultado['Es_Balanceado_Externo'] = df_resultado['Es_Balanceado_Externo'].fillna(False)
            
            monedas_con_valor = (df_resultado['Moneda_Calculada'] != 'Sin Datos').sum()
            logger.info(f"  Instrumentos con data externa (moneda calculada): {monedas_con_valor}")
        else:
            df_resultado = df_instrumentos.copy()
            df_resultado['Moneda_Calculada'] = 'Sin Datos'
            df_resultado['Es_Balanceado_Externo'] = False
            logger.warning("  No hay allocations externos para calcular moneda")
        
        # DETECCIÓN DE INCONSISTENCIAS
        # Comparar SubMoneda (Moneda_Interna) con cálculo matemático desde allocations internos
        df_resultado['Inconsistencia'] = False
        df_resultado['Detalle_Inconsistencia'] = ''
        
        if not self.allocations_interno.empty:
            # Asegurar que ID sea string para las comparaciones
            allocations_interno_temp = self.allocations_interno.copy()
            allocations_interno_temp['ID'] = allocations_interno_temp['ID'].astype(str)
            
            for idx, row in df_resultado.iterrows():
                moneda_interna = str(row.get('Moneda_Interna', '')).strip().upper()
                moneda_metadata = str(row.get('Moneda:', '')).strip().upper()
                
                # Saltar si no hay SubMoneda definida
                if not moneda_interna or moneda_interna in ['SIN DATOS', 'NAN', '', 'NONE']:
                    continue
                
                # CASO ESPECIAL: SubMoneda dice BALANCEADO pero Moneda: indica FALTA ALLOCATION
                if moneda_interna == 'BALANCEADO' and moneda_metadata == 'FALTA ALLOCATION':
                    df_resultado.at[idx, 'Inconsistencia'] = True
                    df_resultado.at[idx, 'Detalle_Inconsistencia'] = (
                        "Definido como BALANCEADO pero no tiene allocations internas"
                    )
                    logger.warning(
                        f"  Inconsistencia en {row['Nombre']}: "
                        f"BALANCEADO pero sin allocations"
                    )
                    continue
                
                # Obtener allocations internos de este instrumento por ID
                alloc_inst = allocations_interno_temp[
                    allocations_interno_temp['ID'] == row['ID']
                ]
                
                if alloc_inst.empty:
                    # Si no hay allocations y está definido como BALANCEADO, es inconsistencia
                    if moneda_interna == 'BALANCEADO':
                        df_resultado.at[idx, 'Inconsistencia'] = True
                        df_resultado.at[idx, 'Detalle_Inconsistencia'] = (
                            "Definido como BALANCEADO pero no tiene allocations internas"
                        )
                        logger.warning(
                            f"  Inconsistencia en {row['Nombre']}: "
                            f"BALANCEADO pero sin allocations"
                        )
                    continue
                
                # Calcular porcentaje máximo y moneda dominante desde datos reales
                max_porcentaje_interno = alloc_inst['percentage_num'].max()
                es_balanceado_calc = max_porcentaje_interno < 90
                
                # Obtener la moneda con mayor porcentaje
                moneda_dominante_calc = alloc_inst.loc[
                    alloc_inst['percentage_num'].idxmax(), 'currency_code'
                ].strip().upper() if not alloc_inst.empty else None
                
                # CASO 1: SubMoneda dice BALANCEADO pero cálculo dice NO balanceado (≥90%)
                if moneda_interna == 'BALANCEADO' and not es_balanceado_calc:
                    df_resultado.at[idx, 'Inconsistencia'] = True
                    df_resultado.at[idx, 'Detalle_Inconsistencia'] = (
                        f"Definido como BALANCEADO pero {moneda_dominante_calc} domina con {max_porcentaje_interno:.1f}%"
                    )
                    logger.warning(
                        f"  Inconsistencia en {row['Nombre']}: "
                        f"BALANCEADO pero {moneda_dominante_calc} {max_porcentaje_interno:.1f}%"
                    )
                
                # CASO 2: SubMoneda dice moneda específica pero cálculo dice balanceado (<90%)
                elif moneda_interna != 'BALANCEADO' and es_balanceado_calc:
                    df_resultado.at[idx, 'Inconsistencia'] = True
                    df_resultado.at[idx, 'Detalle_Inconsistencia'] = (
                        f"Definido como {moneda_interna} pero es balanceado (máx {max_porcentaje_interno:.1f}%)"
                    )
                    logger.warning(
                        f"  Inconsistencia en {row['Nombre']}: "
                        f"{moneda_interna} pero balanceado max {max_porcentaje_interno:.1f}%"
                    )
                
                # CASO 3: SubMoneda dice moneda específica pero cálculo muestra OTRA moneda dominante
                elif (moneda_interna != 'BALANCEADO' and 
                      not es_balanceado_calc and 
                      moneda_dominante_calc and 
                      moneda_interna != moneda_dominante_calc):
                    df_resultado.at[idx, 'Inconsistencia'] = True
                    df_resultado.at[idx, 'Detalle_Inconsistencia'] = (
                        f"Definido como {moneda_interna} pero {moneda_dominante_calc} domina con {max_porcentaje_interno:.1f}%"
                    )
                    logger.warning(
                        f"  Inconsistencia en {row['Nombre']}: "
                        f"{moneda_interna} pero {moneda_dominante_calc} {max_porcentaje_interno:.1f}%"
                    )
            
            num_inconsistencias = df_resultado['Inconsistencia'].sum()
            logger.info(f"  Inconsistencias detectadas: {num_inconsistencias}")
        else:
            logger.info("  No hay allocations internos, no se detectaron inconsistencias")
        
        return df_resultado
    
    def paso_6_comparacion_y_validacion(self, df_clasificacion: pd.DataFrame) -> pd.DataFrame:
        """
        PASO 6: Generar semáforo de validación basado en coincidencia de moneda.
        
        Lógica del semáforo:
        - 🟢 Verde (OK): Balanceado → Balanceado, o Moneda X → Moneda X
        - 🟡 Amarillo (Revisar): Balanceado ↔ No balanceado
        - 🔴 Rojo (Error): Moneda X → Moneda Y (distinta)
        
        Returns:
            DataFrame final con validación por instrumento
        """
        logger.info("PASO 6: Generando semáforo de validación")
        
        if df_clasificacion.empty:
            logger.warning("  No hay datos para validar")
            return pd.DataFrame()
        
        def generar_semaforo(row):
            interno = str(row['Moneda_Interna']).strip().upper()
            calculado = str(row['Moneda_Calculada']).strip().upper()
            es_bal_int = row['Es_Balanceado_Interno']
            es_bal_ext = row['Es_Balanceado_Externo']
            
            # Sin datos externos
            if calculado == 'SIN DATOS' or pd.isna(calculado):
                return 'Sin Datos'
            
            # Caso 1: Ambos balanceados → Verde (Seguro)
            if es_bal_int and es_bal_ext:
                return '🟢 Seguro'
            
            # Caso 2: Balanceado ↔ No balanceado → Amarillo (Cambio)
            if es_bal_int != es_bal_ext:
                return '🟡 Cambio'
            
            # Caso 3: Ambos no balanceados, misma moneda → Verde (Seguro)
            if not es_bal_int and not es_bal_ext:
                if interno == calculado:
                    return '🟢 Seguro'
                else:
                    # Moneda diferente → Rojo (Revisión)
                    return '🔴 Revisión'
            
            return 'Sin Datos'
        
        df_clasificacion['Semáforo'] = df_clasificacion.apply(generar_semaforo, axis=1)
        
        # Seleccionar y renombrar columnas finales (incluir Tipo_Grupo para filtros UI + columnas de inconsistencia)
        columnas_seleccionar = [
            'ID',
            'Nombre',
            'Moneda_Interna',
            'Moneda_Calculada',
            'Semáforo',
            'Tipo',
            'Tipo_Grupo',
            'Cusip',
            'Isin',
            'RIC',
        ]
        
        # Agregar columnas de inconsistencia si existen
        if 'Inconsistencia' in df_clasificacion.columns:
            columnas_seleccionar.append('Inconsistencia')
        if 'Detalle_Inconsistencia' in df_clasificacion.columns:
            columnas_seleccionar.append('Detalle_Inconsistencia')
        
        df_final = df_clasificacion[columnas_seleccionar].copy()
        
        # Renombrar columnas
        nuevos_nombres = [
            'ID',
            'Instrumento',
            'Moneda_Interna',
            'Moneda_Calculada',
            'Semáforo',
            'Tipo',
            'Tipo_Grupo',
            'Cusip',
            'Isin',
            'RIC',
        ]
        
        # Agregar nombres para columnas de inconsistencia si existen
        if 'Inconsistencia' in df_final.columns:
            nuevos_nombres.append('Inconsistencia')
        if 'Detalle_Inconsistencia' in df_final.columns:
            nuevos_nombres.append('Detalle_Inconsistencia')
        
        df_final.columns = nuevos_nombres
        
        logger.info(f"  Validación completada: {len(df_final)} registros")
        
        # Estadísticas
        semaforo_counts = df_final['Semáforo'].value_counts()
        logger.info(f"  Semáforo: {semaforo_counts.to_dict()}")
        
        return df_final
    
    def ejecutar_pipeline_completo(self, fecha_minima: str = "2025-01-01") -> Tuple[pd.DataFrame, Dict]:
        """
        Ejecuta el pipeline completo de principio a fin.
        
        Args:
            fecha_minima: Fecha mínima para filtrar posiciones
            
        Returns:
            Tuple con (df_final, estadisticas)
        """
        logger.info("=" * 80)
        logger.info("INICIANDO PIPELINE COMPLETO DE CONCILIACIÓN")
        logger.info("=" * 80)
        
        # PASO 1: Filtrar posiciones
        df_pos_filtrado = self.paso_1_filtrar_posiciones(fecha_minima)
        
        # PASO 2: Cruce con instrumentos
        df_cruzado = self.paso_2_cruce_instrumentos(df_pos_filtrado)
        
        if df_cruzado.empty:
            logger.error("No se encontraron cruces entre posiciones e instrumentos")
            return pd.DataFrame(), {}
        
        # PASO 3: Filtrar por tipo de instrumento
        df_filtrado = self.paso_3_filtrar_tipo_instrumento(df_cruzado)
        
        if df_filtrado.empty:
            logger.error("No hay instrumentos después de filtrar por tipo")
            return pd.DataFrame(), {}
        
        # PASO 4: Obtener allocations externos
        df_alloc_ext = self.paso_4_obtener_allocations_externo(df_filtrado)
        
        # Guardar allocations externos e internos para uso posterior (gráficos)
        self.df_alloc_ext = df_alloc_ext
        self.df_alloc_int = self.allocations_interno
        
        # PASO 5: Identificar moneda principal interna vs calculada
        df_clasificacion = self.paso_5_identificar_moneda_principal(df_filtrado, df_alloc_ext)
        
        # PASO 6: Comparación y validación (genera semáforo)
        df_final = self.paso_6_comparacion_y_validacion(df_clasificacion)
        
        # PASO 7: Feature Engineering para ML
        logger.info("PASO 7: Generando features para detección de anomalías...")
        df_final = add_features(df_final, df_alloc_ext, self.allocations_interno)
        
        # PASO 8: Detección de anomalías con Isolation Forest
        logger.info("PASO 8: Detectando anomalías con Isolation Forest...")
        detector = AnomalyDetector(contamination=0.05)
        df_final = detector.detect_anomalies(df_final)
        
        # Guardar modelo entrenado para uso futuro
        detector.save_model('data/models/isolation_forest_v1.pkl')
        
        # Estadísticas actualizadas (ahora todo en términos de instrumentos)
        estadisticas = {
            'total_posiciones': len(self.posiciones),
            'posiciones_filtradas': len(df_pos_filtrado),
            'posiciones_cruzadas': len(df_cruzado),
            'instrumentos_unicos_cruzados': len(df_cruzado[['Nombre', 'Cusip', 'Isin']].drop_duplicates()),
            'instrumentos_filtrados': len(df_filtrado),
            'allocations_externos': len(df_alloc_ext),
            'instrumentos_clasificados': len(df_clasificacion),
            'validaciones_finales': len(df_final),
            'semaforo': df_final['Semáforo'].value_counts().to_dict() if not df_final.empty else {}
        }
        
        logger.info("=" * 80)
        logger.info("PIPELINE COMPLETADO")
        logger.info(f"Estadísticas: {estadisticas}")
        logger.info("=" * 80)
        
        return df_final, estadisticas
