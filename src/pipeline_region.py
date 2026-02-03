"""
Pipeline de procesamiento de datos para conciliación de allocations de regiones.
"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
import logging
from datetime import datetime
from src.region_mapping import get_internal_region_name, REGION_MAP_REFINITIV_TO_INTERNAL

logger = logging.getLogger(__name__)

class ConciliacionPipelineRegion:
    """Pipeline completo de procesamiento y conciliación de allocations por región."""
    
    def __init__(self, data: Dict[str, pd.DataFrame]):
        """
        Inicializa el pipeline con los datos cargados.
        
        Args:
            data: Diccionario con los DataFrames necesarios
        """
        self.posiciones = data['posiciones']
        self.instrumentos = data['instrumentos']
        self.tipo_map = data['tipo_map']
        # Priorizar datos de región si existen (cargados para validación de región)
        # Si no, intentar usar los genéricos (por compatibilidad)
        self.allocations_externo = data.get('allocations_region_externo')
        if self.allocations_externo is None or self.allocations_externo.empty:
            self.allocations_externo = data.get('allocations_externo', pd.DataFrame())
            
        self.allocations_interno = data.get('allocations_region_interno')
        if self.allocations_interno is None or self.allocations_interno.empty:
            self.allocations_interno = data.get('allocations_interno', pd.DataFrame())
            
        self.tipos_filtro = data['tipos_filtro']
        
        # Validar que allocations_interno tenga las columnas de región necesarias
        # Se asume que las columnas de región empiezan después de 'Base Región:'
        if not self.allocations_interno.empty and 'Base Región:' in self.allocations_interno.columns:
            cols = list(self.allocations_interno.columns)
            try:
                idx_base = cols.index('Base Región:')
                self.region_columns = cols[idx_base+1:]
                logger.info(f"Columnas de región interna detectadas: {self.region_columns}")
            except ValueError:
                self.region_columns = []
                logger.warning("No se pudieron detectar las columnas de región interna.")
        else:
            self.region_columns = []
    
    def paso_1_filtrar_posiciones(self, fecha_minima: str = "2025-01-01") -> pd.DataFrame:
        """
        PASO 1: Filtrar posiciones valorizadas por fecha.
        Reutiliza lógica de currency pipeline pero es independiente.
        """
        logger.info(f"PASO 1 (Región): Filtrando posiciones con F. Proceso >= {fecha_minima}")
        
        fecha_min = pd.to_datetime(fecha_minima)
        
        df_filtrado = self.posiciones[
            self.posiciones['F. Proceso'] >= fecha_min
        ].copy()
        
        logger.info(f"Posiciones filtradas: {len(df_filtrado)} de {len(self.posiciones)}")
        return df_filtrado
    
    def paso_2_cruce_instrumentos(self, df_posiciones: pd.DataFrame) -> pd.DataFrame:
        """
        PASO 2: Cruzar posiciones con instrumentos internos.
        Idéntico al pipeline de monedas.
        """
        logger.info("PASO 2 (Región): Cruzando posiciones con instrumentos internos")
        
        instrumentos = self.instrumentos.copy()
        
        # Normalizar nombres para match
        df_posiciones['Instrumento_norm'] = df_posiciones['Instrumento'].astype(str).str.strip().str.upper()
        instrumentos['Nombre_norm'] = instrumentos['Nombre'].astype(str).str.strip().str.upper()
        
        # Eliminar columnas conflictivas
        columnas_a_eliminar = [col for col in ['ID', 'Cusip', 'Isin', 'RIC'] if col in df_posiciones.columns]
        if columnas_a_eliminar:
            df_posiciones = df_posiciones.drop(columns=columnas_a_eliminar)
        
        # Match por NOMBRE
        df_match_nombre = df_posiciones.merge(
            instrumentos,
            left_on='Instrumento_norm',
            right_on='Nombre_norm',
            how='inner'
        )
        df_match_nombre['matched_by'] = 'Nombre'
        
        # Match por ID (para los que no combinan por nombre)
        posiciones_matcheadas = set(df_match_nombre['Id_ti_valor'].unique())
        df_sin_match = df_posiciones[~df_posiciones['Id_ti_valor'].isin(posiciones_matcheadas)].copy()
        
        cruces_por_id = []
        if not df_sin_match.empty:
            tipos_id_disponibles = df_sin_match['Id_ti'].dropna().unique()
            df_sin_match['Id_ti_valor_norm'] = df_sin_match['Id_ti_valor'].astype(str).str.strip().str.upper()
            
            for tipo_id in tipos_id_disponibles:
                df_tipo = df_sin_match[df_sin_match['Id_ti'] == tipo_id].copy()
                if df_tipo.empty or tipo_id not in instrumentos.columns:
                    continue
                
                instrumentos[f'{tipo_id}_norm'] = instrumentos[tipo_id].astype(str).str.strip().str.upper()
                merge_temp = df_tipo.merge(
                    instrumentos,
                    left_on='Id_ti_valor_norm',
                    right_on=f'{tipo_id}_norm',
                    how='inner'
                )
                if len(merge_temp) > 0:
                    merge_temp['matched_by'] = tipo_id
                    cruces_por_id.append(merge_temp)
        
        if cruces_por_id:
            df_match_id = pd.concat(cruces_por_id, ignore_index=True)
            df_cruzado = pd.concat([df_match_nombre, df_match_id], ignore_index=True)
        else:
            df_cruzado = df_match_nombre
            
        # Deduplicar
        columnas_dedup = [col for col in ['ID', 'Cliente', 'Activo', 'F. Proceso', 'Id_ti_valor'] if col in df_cruzado.columns]
        if columnas_dedup:
            df_cruzado = df_cruzado.drop_duplicates(subset=columnas_dedup, keep='first')
        else:
            df_cruzado = df_cruzado.drop_duplicates(keep='first')
            
        return df_cruzado

    def paso_3_filtrar_tipo_instrumento(self, df_cruzado: pd.DataFrame) -> pd.DataFrame:
        """
        PASO 3: Filtrar por tipo de instrumento.
        """
        logger.info("PASO 3 (Región): Filtrando por tipo de instrumento")
        
        # Primero extraer instrumentos únicos del cruce de posiciones
        columnas_instrumento = ['ID', 'Nombre', 'Cusip', 'Isin', 'RIC', 'Tipo instrumento', 'SubMoneda', 'Id_ti', 'Id_ti_valor']
        df_instrumentos = df_cruzado[columnas_instrumento].drop_duplicates(subset=['Cusip', 'Isin'], keep='first').copy()
        
        df_filtrado = df_instrumentos[
            df_instrumentos['Tipo instrumento'].isin(self.tipos_filtro)
        ].copy()
        
        df_filtrado = df_filtrado[
            (df_filtrado['Isin'].notna() & (df_filtrado['Isin'] != '')) |
            (df_filtrado['RIC'].notna() & (df_filtrado['RIC'] != ''))
        ].copy()
        
        df_filtrado = df_filtrado.rename(columns={'Tipo instrumento': 'Tipo'})
        df_filtrado['Tipo_Nombre'] = df_filtrado['Tipo'].map(self.tipo_map)
        
        def asignar_grupo_tipo(codigo):
            if codigo in ['C02', 'C14']: return 'Acciones'
            elif codigo == 'C04': return 'Bonos'
            elif codigo in ['C03', 'C09', 'C10']: return 'Fondos/ETF'
            else: return 'Otros'
        
        df_filtrado['Tipo_Grupo'] = df_filtrado['Tipo'].apply(asignar_grupo_tipo)
        return df_filtrado

    def paso_4_obtener_allocations_externo(self, df_filtrado: pd.DataFrame) -> pd.DataFrame:
        """
        PASO 4: Obtener allocations externos de REGIÓN.
        Cruza con allocations externos (FundCountryAllocation) y mapea a regiones internas.
        """
        logger.info("PASO 4 (Región): Obtener allocations externos")
        
        if self.allocations_externo.empty:
            logger.warning("  No hay allocations externos cargados.")
            return pd.DataFrame()
            
        alloc_ext = self.allocations_externo.copy()
        
        # Normalización de instrument
        alloc_ext['instrument_norm'] = alloc_ext['instrument'].astype(str).str.strip().str.upper()
        
        df_filtrado['Cusip_norm'] = df_filtrado['Cusip'].astype(str).str.strip().str.upper()
        df_filtrado['Isin_norm'] = df_filtrado['Isin'].astype(str).str.strip().str.upper()
        df_filtrado['RIC_norm'] = df_filtrado['RIC'].astype(str).str.strip().str.upper()
        
        # Match procedure (similar to currency pipeline)
        matches = []
        
        # Filtrar solo allocations relevantes
        identificadores_validos = set()
        for col in ['Cusip_norm', 'Isin_norm', 'RIC_norm']:
            ids = df_filtrado[col].unique()
            identificadores_validos.update([x for x in ids if pd.notna(x) and x != 'NAN'])
            
        alloc_ext_filtrado = alloc_ext[alloc_ext['instrument_norm'].isin(identificadores_validos)].copy()
        
        if alloc_ext_filtrado.empty:
            logger.warning("  No se encontraron allocations externos para los instrumentos del portafolio.")
            return pd.DataFrame()
        
        # MATCH 1: RIC
        df_ids = df_filtrado[['ID', 'Cusip', 'Isin', 'RIC', 'RIC_norm', 'Isin_norm', 'Cusip_norm', 'Nombre']].drop_duplicates()
        
        df_ric = df_ids[df_ids['RIC_norm'].notna() & (df_ids['RIC_norm'] != 'NAN')]
        if not df_ric.empty:
            match_ric = alloc_ext_filtrado.merge(
                df_ric[['ID', 'Nombre', 'RIC_norm']],
                left_on='instrument_norm',
                right_on='RIC_norm',
                how='inner'
            )
            match_ric['matched_by'] = 'RIC'
            matches.append(match_ric)

        # MATCH 2: ISIN
        df_isin = df_ids[df_ids['Isin_norm'].notna() & (df_ids['Isin_norm'] != 'NAN')]
        if not df_isin.empty:
             match_isin = alloc_ext_filtrado.merge(
                df_isin[['ID', 'Nombre', 'Isin_norm']],
                left_on='instrument_norm',
                right_on='Isin_norm',
                how='inner'
            )
             match_isin['matched_by'] = 'ISIN'
             matches.append(match_isin)

        # MATCH 3: CUSIP
        df_cusip = df_ids[df_ids['Cusip_norm'].notna() & (df_ids['Cusip_norm'] != 'NAN')]
        if not df_cusip.empty:
             match_cusip = alloc_ext_filtrado.merge(
                df_cusip[['ID', 'Nombre', 'Cusip_norm']],
                left_on='instrument_norm',
                right_on='Cusip_norm',
                how='inner'
            )
             match_cusip['matched_by'] = 'CUSIP'
             matches.append(match_cusip)
             
        if not matches:
             return pd.DataFrame()
             
        alloc_con_nombre = pd.concat(matches, ignore_index=True)
        
        # Filtrar por fecha más reciente
        if 'date' in alloc_con_nombre.columns:
            fecha_reciente = alloc_con_nombre.groupby('Nombre')['date'].max().reset_index()
            alloc_con_nombre = alloc_con_nombre.merge(fecha_reciente, on=['Nombre', 'date'], how='inner')
        
        # Deduplicar
        alloc_con_nombre = alloc_con_nombre.drop_duplicates(subset=['Nombre', 'class'], keep='first') # 'class' here is country/region
        
        # --- MAPEO DE REGIONES ---
        # 1. Mapear 'class' (nombre refinitiv) a Región Interna
        alloc_con_nombre['Region_Interna_Mapped'] = alloc_con_nombre['class'].apply(get_internal_region_name)
        
        # 2. Manejar regiones no mapeadas ('N/A' o None) -> Opción: dejarlas como 'Otros' o mantenerlas para reporte
        alloc_con_nombre['Region_Interna_Mapped'] = alloc_con_nombre['Region_Interna_Mapped'].fillna('Sin Clasificar')
        
        # 3. Convertir porcentaje
        alloc_con_nombre['percentage_num'] = alloc_con_nombre['percentage'].astype(str).str.replace(',', '.').astype(float)
        
        # 4. Agrupar por (ID, Nombre Instrumento, Región Interna) y sumar porcentajes
        #    Esto es vital porque un fondo puede tener 'France', 'Germany' -> Ambos mapean a 'Europa Des.'
        #    IMPORTANTE: Incluir ID y matched_by para que estén disponibles en exports
        #    Para matched_by, tomar el primero (ya que un instrumento puede tener múltiples matches)
        df_agrupado = alloc_con_nombre.groupby(['ID', 'Nombre', 'Region_Interna_Mapped']).agg({
            'percentage_num': 'sum',
            'matched_by': 'first'
        }).reset_index()
        
        logger.info(f"  Allocations de regiones procesados: {len(df_agrupado)} registros agrupados")
        return df_agrupado

    def paso_5_identificar_region_principal(self, df_filtrado: pd.DataFrame, df_alloc_ext_agrupado: pd.DataFrame) -> pd.DataFrame:
        """
        PASO 5: Identificar región principal (Dominante) vs clasificación interna.
        
        Internal Source: data/allocations 2.csv (Base Región: + columnas de % por region)
        External Source: df_alloc_ext_agrupado (Result of Step 4)
        """
        logger.info("PASO 5 (Región): Identificando región principal interna vs calculada")
        
        # Preparar dataframe base
        required_res = ['ID', 'Nombre', 'Tipo', 'Tipo_Grupo', 'Tipo_Nombre', 'Cusip', 'Isin', 'RIC', 'Id_ti', 'Id_ti_valor', 'base-region']
        optional_res = ['Base Región:']  # Columna de allocations internas
        cols_res = [c for c in required_res + optional_res if c in df_filtrado.columns]
        df_resultado = df_filtrado[cols_res].drop_duplicates()
        df_resultado['ID'] = df_resultado['ID'].astype(str)
        
        # --- CARGAR INFO INTERNA ---
        if not self.allocations_interno.empty:
            internal_cols = ['ID', 'Base Región:'] + [c for c in self.region_columns if c in self.allocations_interno.columns]
            internal_data = self.allocations_interno[internal_cols].copy()
            internal_data['ID'] = internal_data['ID'].astype(str)
            
            # Merge
            df_resultado = df_resultado.merge(internal_data, on='ID', how='left')
        else:
            df_resultado['Base Región:'] = None
            
        # --- CALCULAR REGIÓN DOMINANTE EXTERNA ---
        # Definir dominante si > 90% en una sola región mapeada. Si no, es "Diversificado" (o Balanceado/Global)
        
        resultados_externos = []
        if not df_alloc_ext_agrupado.empty:
            for nombre in df_alloc_ext_agrupado['Nombre'].unique():
                data_inst = df_alloc_ext_agrupado[df_alloc_ext_agrupado['Nombre'] == nombre]
                
                # Obtener la región con mayor %
                if not data_inst.empty:
                    idx_max = data_inst['percentage_num'].idxmax()
                    max_region = data_inst.loc[idx_max, 'Region_Interna_Mapped']
                    max_pct = data_inst.loc[idx_max, 'percentage_num']
                    total_pct = data_inst['percentage_num'].sum()
                    
                    # Umbral 90% para clasificación (documentado)
                    es_concentrado = max_pct >= 90.0
                    
                    resultados_externos.append({
                        'Nombre': nombre,
                        'Region_Calculada': max_region if es_concentrado else 'balanceado',  # Usar 'balanceado' no 'Diversificado'
                        'Max_Region_Ext': max_region,
                        'Max_Pct_Ext': max_pct,
                        'Total_Pct_Ext': total_pct  # Suma total de porcentajes
                    })
        
        df_calc_ext = pd.DataFrame(resultados_externos)
        
        if not df_calc_ext.empty:
            df_resultado = df_resultado.merge(df_calc_ext, on='Nombre', how='left')
        else:
            df_resultado['Region_Calculada'] = 'Sin Datos'
            df_resultado['Max_Region_Ext'] = None
            df_resultado['Max_Pct_Ext'] = 0.0
            df_resultado['Total_Pct_Ext'] = 0.0
            
        df_resultado['Region_Calculada'] = df_resultado['Region_Calculada'].fillna('Sin Datos')
        df_resultado['Total_Pct_Ext'] = df_resultado['Total_Pct_Ext'].fillna(0.0)
        
        return df_resultado

    def paso_6_comparacion_y_validacion(self, df_clasificacion: pd.DataFrame) -> pd.DataFrame:
        """
        PASO 6: Generar semáforo (Flag) y detectar inconsistencias.
        
        Lógica documentada:
        - Flag basado en Total_Pct_Ext (60-120% VALIDO, 40-60% o >120% REVISION, <40% ERROR)
        - Comparar Region_Calculada vs base-region
        - Detectar inconsistencias específicas
        """
        logger.info("PASO 6 (Región): Validación y semáforo")
        
        if df_clasificacion.empty:
            return pd.DataFrame()
        
        # Generar Flag (Semáforo) basado en Total_Pct_Ext
        def generar_flag(row):
            try:
                total_pct = float(row.get('Total_Pct_Ext', 0.0))
                if pd.isna(total_pct):
                    total_pct = 0.0
            except:
                total_pct = 0.0
            
            # Lógica documentada para Flag
            if 60 <= total_pct <= 120:
                return 'VALIDO'
            elif (40 <= total_pct < 60) or (total_pct > 120):
                return 'REVISION'
            else:  # < 40
                return 'ERROR'
        
        df_clasificacion['Flag'] = df_clasificacion.apply(generar_flag, axis=1)
        
        # Calcular Region_Antigua (región dominante interna)
        def calcular_region_antigua(row):
            """Calcular región dominante desde allocations internas"""
            max_val = 0
            max_region = None
            
            if self.region_columns:
                for col in self.region_columns:
                    val = row.get(col, 0)
                    try:
                        val = float(val) if pd.notna(val) and val != '' else 0.0
                    except:
                        val = 0.0
                    
                    if val > max_val:
                        max_val = val
                        max_region = col
            
            # Aplicar umbral 90%
            if max_val >= 90.0 and max_region:
                return max_region
            else:
                return 'balanceado'
        
        df_clasificacion['Region_Antigua'] = df_clasificacion.apply(calcular_region_antigua, axis=1)
        
        # Detectar inconsistencias (comparar base-region vs Region_Antigua INTERNA)
        def detectar_inconsistencia(row):
            """
            Detectar inconsistencias según documentación:
            Compara base-region (catálogo) vs Region_Antigua (calculada desde allocations INTERNAS)
            
            1. BALANCEADO sin allocations
            2. BALANCEADO pero región dominante interna
            3. Región específica pero balanceado interno
            4. Región incorrecta vs interna
            """
            base_region = str(row.get('base-region', '')).strip().upper()
            region_antigua = str(row.get('Region_Antigua', '')).strip()  # Calculada desde INTERNAS
            base_estrategia = str(row.get('Base Región:', '')).strip().upper()
            
            # Caso 1: BALANCEADO sin allocations
            if base_region == 'BALANCEADO' and base_estrategia == 'FALTA ALLOCATION':
                return "Definido como BALANCEADO pero no tiene allocations internas"
            
            # Caso 2: BALANCEADO pero región dominante en allocations internas
            if base_region == 'BALANCEADO' and region_antigua != 'balanceado':
                # Region_Antigua tiene el nombre de la región dominante si >= 90%
                return f"Definido como BALANCEADO pero {region_antigua} domina en allocations internas"
            
            # Caso 3: Región específica pero balanceado en allocations internas
            if base_region != 'BALANCEADO' and base_region != '' and region_antigua == 'balanceado':
                return f"Definido como {base_region} pero es balanceado en allocations internas"
            
            # Caso 4: Región incorrecta vs allocations internas
            if (base_region != 'BALANCEADO' and base_region != '' and 
                region_antigua != 'balanceado' and 
                base_region != region_antigua.upper()):
                return f"Definido como {base_region} pero {region_antigua} domina en allocations internas"
            
            return ''  # Sin inconsistencia
            
            return ''  # Sin inconsistencia
        
        df_clasificacion['Detalle_Inconsistencia'] = df_clasificacion.apply(detectar_inconsistencia, axis=1)
        
        # Marcar si tiene inconsistencia
        df_clasificacion['Inconsistencia'] = df_clasificacion['Detalle_Inconsistencia'] != ''
        
        logger.info(f"Validación completada. Flags: {df_clasificacion['Flag'].value_counts().to_dict()}")
        logger.info(f"Inconsistencias detectadas: {df_clasificacion['Inconsistencia'].sum()}")
        
        return df_clasificacion

    def paso_7_escalar_allocations(self, df_validado: pd.DataFrame, df_alloc_ext_agrupado: pd.DataFrame) -> pd.DataFrame:
        """
        PASO 7: Escalar allocations externas proporcionalmente para que sumen 100%.
        
        Solo se escalan instrumentos con Flag != 'ERROR'.
        El escalado es proporcional para mantener las proporciones relativas.
        """
        logger.info("PASO 7 (Región): Escalando allocations proporcionalmente")
        
        if df_validado.empty or df_alloc_ext_agrupado.empty:
            return df_alloc_ext_agrupado
        
        # Identificar instrumentos que NO son ERROR
        instrumentos_validos = df_validado[df_validado['Flag'] != 'ERROR']['Nombre'].unique()
        
        logger.info(f"  Instrumentos a escalar: {len(instrumentos_validos)} de {len(df_validado)}")
        
        # Crear copia para no modificar el original
        df_escalado = df_alloc_ext_agrupado.copy()
        df_escalado['percentage_escalado'] = df_escalado['percentage_num']
        
        # Escalar por instrumento
        for nombre in instrumentos_validos:
            # Obtener allocations de este instrumento
            mask = df_escalado['Nombre'] == nombre
            allocations_inst = df_escalado[mask]
            
            if allocations_inst.empty:
                continue
            
            # Calcular suma actual
            suma_actual = allocations_inst['percentage_num'].sum()
            
            if suma_actual > 0:
                # Factor de escalado para llegar a 100%
                factor_escalado = 100.0 / suma_actual
                
                # Aplicar escalado proporcional
                df_escalado.loc[mask, 'percentage_escalado'] = df_escalado.loc[mask, 'percentage_num'] * factor_escalado
                
                # Verificar suma (para logging)
                suma_escalada = df_escalado.loc[mask, 'percentage_escalado'].sum()
                logger.debug(f"  {nombre}: {suma_actual:.2f}% → {suma_escalada:.2f}% (factor: {factor_escalado:.4f})")
        
        logger.info(f"  Escalado completado para {len(instrumentos_validos)} instrumentos")
        
        return df_escalado

    def ejecutar_pipeline_completo(self, fecha_minima: str = "2025-01-01") -> Tuple[pd.DataFrame, Dict]:
        logger.info("=== INICIANDO PIPELINE REGIÓN ===")
        
        df_pos = self.paso_1_filtrar_posiciones(fecha_minima)
        df_cruzado = self.paso_2_cruce_instrumentos(df_pos)
        
        if df_cruzado.empty:
            return pd.DataFrame(), {}
            
        df_filtrado = self.paso_3_filtrar_tipo_instrumento(df_cruzado)
        
        if df_filtrado.empty:
            return pd.DataFrame(), {}
            
        df_alloc_ext_agrupado = self.paso_4_obtener_allocations_externo(df_filtrado)
        
        # Guardar para uso externo
        self.df_alloc_ext = df_alloc_ext_agrupado
        
        df_clasif = self.paso_5_identificar_region_principal(df_filtrado, df_alloc_ext_agrupado)
        df_final = self.paso_6_comparacion_y_validacion(df_clasif)
        
        # PASO 7: Escalar allocations (solo para instrumentos con Flag != ERROR)
        df_alloc_ext_escalado = self.paso_7_escalar_allocations(df_final, df_alloc_ext_agrupado)
        
        # Guardar ambos para uso externo
        self.df_alloc_ext_agrupado = df_alloc_ext_escalado  # Usar el escalado para exports
        self.df_alloc_ext = df_alloc_ext_escalado  # Compatibilidad
        
        estadisticas = {
            'total_instrumentos': len(df_final),
            'con_datos_externos': len(df_final[df_final['Region_Calculada'] != 'Sin Datos']),
            'balanceados': len(df_final[df_final['Region_Calculada'] == 'balanceado']),
            'no_balanceados': len(df_final[df_final['Region_Calculada'] != 'balanceado']),
            'flag': df_final['Flag'].value_counts().to_dict() if 'Flag' in df_final.columns else {},
            'inconsistencias': df_final['Inconsistencia'].sum() if 'Inconsistencia' in df_final.columns else 0,
            'instrumentos_escalados': len(df_final[df_final['Flag'] != 'ERROR'])
        }
        
        logger.info(f"Pipeline Región Finalizado. Stats: {estadisticas}")
        return df_final, estadisticas
