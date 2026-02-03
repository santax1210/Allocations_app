import streamlit as st
import pandas as pd
import logging
import sys
from pathlib import Path
from datetime import datetime
import io

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'utils'))

from data_loader import DataLoader
from pipeline import ConciliacionPipeline
from pipeline_region import ConciliacionPipelineRegion
from session_state import init_session_state
from currency_mapping import CURRENCY_MAP_REFINITIV_TO_ISO

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('ui_allocations')

# Configuración de la página
st.set_page_config(
    page_title="Conciliación Fintech - Validación Allocations",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar session state
init_session_state()

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .stApp {
        background-color: #f5f7fa;
    }
    .main-header {
        font-size: 2.5rem;
        color: #ffffff; 
        margin-bottom: 0.5rem;
    }
    .separator {
        width: 100%; 
        height: 3px; 
        background: linear-gradient(90deg, #1e88e5 0%, #ff6f00 50%, #1e88e5 100%); 
        margin-bottom: 1.5rem; 
        border-radius: 2px;
    }
    /* Badges */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-verde { background-color: #d1fae5; color: #065f46; }
    .badge-amarillo { background-color: #fef3c7; color: #92400e; }
    .badge-rojo { background-color: #fee2e2; color: #991b1b; }
    .badge-gris { background-color: #e5e7eb; color: #374151; }
    
    /* Metrics */
    .metric-card {
        background-color: white;
        border: 1px solid #dee2e6;
        border-radius: 6px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .metric-card h3 { margin: 0; font-size: 2rem; color: #212529; }
    .metric-card p { margin: 5px 0 0 0; color: #6c757d; font-size: 0.9rem; }
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("""
<h1 style='text-align: left; color: white; font-size: 2.5rem; margin-bottom: 0.5rem;'>Validación de Allocations</h1>
<div style='width: 100%; height: 3px; background: linear-gradient(90deg, #1e88e5 0%, #ff6f00 50%, #1e88e5 100%); margin-bottom: 1.5rem; border-radius: 2px;'></div>
""", unsafe_allow_html=True)

# --- SIDEBAR & SETUP ---
st.sidebar.title("Configuración")

# Detectar default desde carga de archivos
default_idx = 0
if 'tipo_validacion_detectado' in st.session_state:
    if st.session_state.tipo_validacion_detectado == "Región":
        default_idx = 1
    elif st.session_state.tipo_validacion_detectado == "Moneda":
        default_idx = 0

tipo_validacion = st.sidebar.radio(
    "Tipo de Validación",
    ["Moneda", "Región"],
    index=default_idx
)

# --- LOGIC: DATA & PIPELINE ---
@st.cache_resource
def get_data_loader():
    return DataLoader()

loader = get_data_loader()

# Verificar si hay datos cargados
if 'data' not in st.session_state or not st.session_state.data_loaded:
    st.info("👋 Para comenzar, por favor carga los archivos de entrada.")
    if st.button("📂 Ir a Carga de Archivos", type="primary"):
        st.switch_page("pages/1_Carga_Archivos.py")
    st.stop()
        
data = st.session_state.data

# Ejecutar pipeline según selección
if tipo_validacion == "Moneda":
    if 'df_final_moneda' not in st.session_state:
        with st.spinner("Ejecutando pipeline de Monedas..."):
            pipeline = ConciliacionPipeline(data)
            df_final, stats = pipeline.ejecutar_pipeline_completo()
            st.session_state.df_final_moneda = df_final
            st.session_state.stats_moneda = stats
            st.session_state.df_alloc_ext_moneda = pipeline.df_alloc_ext
    
    df_display = st.session_state.df_final_moneda
    stats_display = st.session_state.stats_moneda
    key_prefix = "moneda"
    
elif tipo_validacion == "Región":
    if 'df_final_region' not in st.session_state:
        with st.spinner("Ejecutando pipeline de Región..."):
            pipeline = ConciliacionPipelineRegion(data)
            df_final, stats = pipeline.ejecutar_pipeline_completo()
            st.session_state.df_final_region = df_final
            st.session_state.stats_region = stats
            st.session_state.df_alloc_ext_region = getattr(pipeline, 'df_alloc_ext_agrupado', pd.DataFrame())

    df_display = st.session_state.df_final_region
    stats_display = st.session_state.stats_region
    key_prefix = "region"

# --- UI DISPLAY ---

if df_display.empty:
    st.warning("No se generaron resultados de validación.")
    st.stop()

# 1. KPIs
st.subheader(f"Resumen General ({tipo_validacion})")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.markdown(f"""<div class='metric-card'><h3>{len(df_display)}</h3><p>Total Instrumentos</p></div>""", unsafe_allow_html=True)

with kpi2:
    # Manejar tanto 'Semáforo' (moneda) como 'Flag' (región)
    flag_col = 'Flag' if 'Flag' in df_display.columns else 'Semáforo'
    if flag_col in df_display.columns:
        aprobados = len(df_display[df_display[flag_col].str.contains('VALIDO', case=False, na=False)])
    else:
        aprobados = 0
    st.markdown(f"""<div class='metric-card'><h3>{aprobados}</h3><p>✅ Válidos</p></div>""", unsafe_allow_html=True)

with kpi3:
    flag_col = 'Flag' if 'Flag' in df_display.columns else 'Semáforo'
    if flag_col in df_display.columns:
        revision = len(df_display[df_display[flag_col].str.contains('REVISION', case=False, na=False)])
    else:
        revision = 0
    st.markdown(f"""<div class='metric-card'><h3>{revision}</h3><p>⚠️ A Revisar</p></div>""", unsafe_allow_html=True)

with kpi4:
    # Para Sin Datos, buscar en la columna calculada (Moneda_Calculada o Region_Calculada)
    calc_col = 'Region_Calculada' if 'Region_Calculada' in df_display.columns else 'Moneda_Calculada'
    if calc_col in df_display.columns:
        sin_datos = len(df_display[df_display[calc_col].str.contains('Sin Datos', case=False, na=False)])
    else:
        sin_datos = 0
    st.markdown(f"""<div class='metric-card'><h3>{sin_datos}</h3><p>❓ Sin Datos Externos</p></div>""", unsafe_allow_html=True)

st.markdown("---")

# 2. Filtros
st.subheader("🔍 Explorador de Resultados")

col_f1, col_f2 = st.columns(2)
with col_f1:
    # Detectar columna de flag (Semáforo para moneda, Flag para región)
    flag_col = 'Flag' if 'Flag' in df_display.columns else 'Semáforo'
    if flag_col in df_display.columns:
        filtro_semaforo = st.multiselect(
            f"Filtrar por {flag_col}",
            options=df_display[flag_col].unique(),
            default=df_display[flag_col].unique(),
            key=f"{key_prefix}_sem"
        )
    else:
        filtro_semaforo = []

with col_f2:
    if 'Tipo_Grupo' in df_display.columns:
        filtro_tipo = st.multiselect(
            "Filtrar por Tipo",
            options=df_display['Tipo_Grupo'].unique(),
            default=df_display['Tipo_Grupo'].unique(),
            key=f"{key_prefix}_tipo"
        )
    else:
        filtro_tipo = []

# Aplicar filtros
flag_col = 'Flag' if 'Flag' in df_display.columns else 'Semáforo'
if flag_col in df_display.columns and filtro_semaforo:
    df_filtered = df_display[df_display[flag_col].isin(filtro_semaforo)]
else:
    df_filtered = df_display.copy()
    
if filtro_tipo and 'Tipo_Grupo' in df_display.columns:
    df_filtered = df_filtered[df_filtered['Tipo_Grupo'].isin(filtro_tipo)]

# Búsqueda
busqueda = st.text_input("Buscar por nombre, ISIN o RIC", key=f"{key_prefix}_search")
if busqueda:
    mask = (
        df_filtered['Instrumento'].astype(str).str.contains(busqueda, case=False, na=False) |
        df_filtered['Isin'].astype(str).str.contains(busqueda, case=False, na=False) |
        df_filtered['RIC'].astype(str).str.contains(busqueda, case=False, na=False)
    )
    df_filtered = df_filtered[mask]

st.info(f"Mostrando {len(df_filtered)} registros")

# 3. Tabla Principal
# Definir columnas a mostrar según tipo
flag_col = 'Flag' if 'Flag' in df_filtered.columns else 'Semáforo'
common_cols = ['ID', 'Instrumento', 'Tipo_Grupo', flag_col]
if tipo_validacion == "Moneda":
    specific_cols = ['Moneda_Interna', 'Moneda_Calculada']
    if 'Detalle_Inconsistencia' in df_filtered.columns:
        specific_cols.append('Detalle_Inconsistencia')
elif tipo_validacion == "Región":
    specific_cols = ['base-region', 'Region_Calculada']
    if 'Detalle_Inconsistencia' in df_filtered.columns:
        specific_cols.append('Detalle_Inconsistencia')
else:
    specific_cols = []

cols_to_show = common_cols + specific_cols
cols_present = [c for c in cols_to_show if c in df_filtered.columns]

st.dataframe(
    df_filtered[cols_present].style.applymap(lambda x: 
        'background-color: #d1fae5; color: #065f46' if 'VALIDO' in str(x) else 
        ('background-color: #fef3c7; color: #92400e' if 'REVISION' in str(x) else 
         ('background-color: #fee2e2; color: #991b1b' if 'ERROR' in str(x) else '')), 
    subset=[flag_col] if flag_col in cols_present else []),
    use_container_width=True,
    height=600
)

# 4. Exportación
st.markdown("### 📤 Exportar Datos")

def preparar_dataframe_exportacion(df_final, pipeline_obj, tipo_validacion):
    """
    Prepara el DataFrame para exportación replicando el formato antiguo solicitado.
    Incluye columnas pivoteadas de allocations (monedas o regiones).
    """
    try:
        logger.info(f"[EXPORT DEBUG] preparar_dataframe_exportacion llamada con tipo_validacion='{tipo_validacion}'")
        df_export = df_final.copy()
        
        # 1. Recuperar Allocations Externos en formato ancho (pivot)
        df_alloc_wide = pd.DataFrame()
        
        # El radio button devuelve "Moneda" o "Región"
        if tipo_validacion == "Moneda":
            # Verificar si el pipeline tiene df_alloc_ext
            logger.info(f"[EXPORT DEBUG] Verificando pipeline_obj.df_alloc_ext...")
            logger.info(f"[EXPORT DEBUG] hasattr(pipeline_obj, 'df_alloc_ext'): {hasattr(pipeline_obj, 'df_alloc_ext')}")
            
            if hasattr(pipeline_obj, 'df_alloc_ext'):
                logger.info(f"[EXPORT DEBUG] pipeline_obj.df_alloc_ext existe. Empty? {pipeline_obj.df_alloc_ext.empty if pipeline_obj.df_alloc_ext is not None else 'None'}")
                if pipeline_obj.df_alloc_ext is not None:
                    logger.info(f"[EXPORT DEBUG] Tamaño: {len(pipeline_obj.df_alloc_ext)} filas")
            
            # Usar df_alloc_ext del pipeline (Long format: ID, currency_code, percentage_num)
            if hasattr(pipeline_obj, 'df_alloc_ext') and not pipeline_obj.df_alloc_ext.empty:
                df_alloc_long = pipeline_obj.df_alloc_ext.copy()
                
                # DEBUG: Ver qué columnas tenemos
                logger.info(f"[EXPORT DEBUG] Columnas en df_alloc_ext: {list(df_alloc_long.columns)}")
                logger.info(f"[EXPORT DEBUG] Primeras filas:\n{df_alloc_long.head()}")
                
                # Verificar que tenemos las columnas necesarias
                if 'ID' not in df_alloc_long.columns:
                    logger.error("[EXPORT ERROR] df_alloc_ext NO tiene columna 'ID'!")
                    logger.error(f"[EXPORT ERROR] Columnas disponibles: {list(df_alloc_long.columns)}")
                elif 'currency_code' not in df_alloc_long.columns:
                    logger.error("[EXPORT ERROR] df_alloc_ext NO tiene columna 'currency_code'!")
                else:
                    # Agrupar por ID y moneda para evitar duplicados en pivot
                    # Usar percentage_escalado si existe, sino percentage_num
                    pct_col = 'percentage_escalado' if 'percentage_escalado' in df_alloc_long.columns else 'percentage_num'
                    logger.info(f"[EXPORT DEBUG] Usando columna: {pct_col}")
                    
                    try:
                        df_alloc_long = df_alloc_long.groupby(['ID', 'currency_code'])[pct_col].sum().reset_index()
                        df_alloc_wide = df_alloc_long.pivot(index='ID', columns='currency_code', values=pct_col)
                        logger.info(f"[EXPORT DEBUG] Pivot exitoso. Columnas de monedas: {list(df_alloc_wide.columns)}")
                        logger.info(f"[EXPORT DEBUG] Número de instrumentos con allocations: {len(df_alloc_wide)}")
                    except Exception as e:
                        logger.error(f"[EXPORT ERROR] Error en pivot: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                
        elif tipo_validacion == "Región":
             # Usar df_alloc_ext_agrupado del pipeline (Long format: ID, Region_Interna_Mapped, percentage_escalado)
             logger.info(f"[EXPORT DEBUG] Verificando df_alloc_ext_agrupado para región...")
             logger.info(f"[EXPORT DEBUG] hasattr(pipeline_obj, 'df_alloc_ext_agrupado'): {hasattr(pipeline_obj, 'df_alloc_ext_agrupado')}")
             
             if hasattr(pipeline_obj, 'df_alloc_ext_agrupado'):
                 logger.info(f"[EXPORT DEBUG] pipeline_obj.df_alloc_ext_agrupado existe")
                 logger.info(f"[EXPORT DEBUG] Es None? {pipeline_obj.df_alloc_ext_agrupado is None}")
                 if pipeline_obj.df_alloc_ext_agrupado is not None:
                     logger.info(f"[EXPORT DEBUG] Empty? {pipeline_obj.df_alloc_ext_agrupado.empty}")
                     logger.info(f"[EXPORT DEBUG] Tamaño: {len(pipeline_obj.df_alloc_ext_agrupado)} filas")
             
             if hasattr(pipeline_obj, 'df_alloc_ext_agrupado') and pipeline_obj.df_alloc_ext_agrupado is not None and not pipeline_obj.df_alloc_ext_agrupado.empty:
                df_alloc_long = pipeline_obj.df_alloc_ext_agrupado.copy()
                
                logger.info(f"[EXPORT DEBUG] df_alloc_ext_agrupado para región: {len(df_alloc_long)} filas")
                logger.info(f"[EXPORT DEBUG] Columnas: {list(df_alloc_long.columns)}")
                
                # Asegurar que ID existe
                if 'ID' in df_alloc_long.columns and 'Region_Interna_Mapped' in df_alloc_long.columns:
                    # Usar percentage_escalado si existe, sino percentage_num
                    pct_col = 'percentage_escalado' if 'percentage_escalado' in df_alloc_long.columns else 'percentage_num'
                    logger.info(f"[EXPORT DEBUG] Usando columna: {pct_col}")
                    
                    df_alloc_long = df_alloc_long.groupby(['ID', 'Region_Interna_Mapped'])[pct_col].sum().reset_index()
                    df_alloc_wide = df_alloc_long.pivot(index='ID', columns='Region_Interna_Mapped', values=pct_col)
                    
                    logger.info(f"[EXPORT DEBUG] Pivot exitoso. Columnas de regiones: {list(df_alloc_wide.columns)}")
                    logger.info(f"[EXPORT DEBUG] Número de instrumentos con allocations: {len(df_alloc_wide)}")
                else:
                    logger.error(f"[EXPORT ERROR] Faltan columnas necesarias en df_alloc_ext_agrupado")
                    logger.error(f"[EXPORT ERROR] Columnas disponibles: {list(df_alloc_long.columns)}")
             else:
                 logger.error(f"[EXPORT ERROR] df_alloc_ext_agrupado NO disponible o vacío")

        # 2. Merge con df_final usando 'ID' (el identificador único más fiable)
        if not df_alloc_wide.empty:
            logger.info(f"[EXPORT DEBUG] Iniciando merge. df_export tiene {len(df_export)} filas")
            df_alloc_wide_reset = df_alloc_wide.reset_index()
            # Asegurar que ambos ID sean string para el merge
            df_export['ID'] = df_export['ID'].astype(str)
            df_alloc_wide_reset['ID'] = df_alloc_wide_reset['ID'].astype(str)
            
            df_export = df_export.merge(df_alloc_wide_reset, on='ID', how='left')
            logger.info(f"[EXPORT DEBUG] Merge completado. df_export ahora tiene {len(df_export)} filas y columnas: {list(df_export.columns)}")
            
            # Llenar NaNs en columnas de datos con 0
            cols_datos = [c for c in df_alloc_wide.columns if c in df_export.columns]
            if cols_datos:
                df_export[cols_datos] = df_export[cols_datos].fillna(0)
                logger.info(f"[EXPORT DEBUG] Rellenados NaNs en columnas: {cols_datos}")
        else:
            logger.warning("[EXPORT WARNING] df_alloc_wide está vacío, no se agregarán columnas de allocations")
            
        # --- LÓGICA PERSONALIZADA SOLICITADA ---
        
        # 1. Fecha
        def calc_fecha(row):
            if tipo_validacion == 'Moneda':
                # Lógica para Moneda
                meta_mon = str(row.get('Moneda:', '')).strip().upper()
                if not meta_mon or meta_mon == 'NAN':
                    meta_mon = str(row.get('Moneda', '')).strip().upper()
                    
                if meta_mon == 'FALTA ALLOCATION':
                    return '31-12-2019'
                return '01-01-2026'
            else:
                # Lógica para Región (según documentación)
                base_region = str(row.get('Base Región:', '')).strip().upper()
                if base_region == 'FALTA ALLOCATION':
                    return '31-12-2019'
                return '01-01-2026'
        
        df_export['Fecha_Calc'] = df_export.apply(calc_fecha, axis=1)
        
        # 2. Clasificacion y Moneda Antigua
        if tipo_validacion == 'Moneda':
            # moneda_antigua = Valor del catálogo (SubMoneda)
            if 'SubMoneda' in df_export.columns:
                 df_export['moneda_antigua_export'] = df_export['SubMoneda']
            elif 'Moneda_Interna' in df_export.columns:
                 df_export['moneda_antigua_export'] = df_export['Moneda_Interna']
            else:
                 df_export['moneda_antigua_export'] = ''
            
            # Clasificación = Texto literal "SubMoneda"
            df_export['Clasificacion_Calc'] = 'SubMoneda'
        else:
            # Región: Clasificación = "base-region" (según documentación)
            df_export['Clasificacion_Calc'] = 'base-region'
            df_export['moneda_antigua_export'] = ''

        # 3. Fix Id_ti_valor e Id_ti - Usar el código que REALMENTE se usó en el match
        # Primero, obtener la info de matched_by desde df_alloc_ext si está disponible
        if hasattr(pipeline_obj, 'df_alloc_ext') and not pipeline_obj.df_alloc_ext.empty:
            # Extraer matched_by por ID (tomar el primero si hay múltiples)
            df_matched = pipeline_obj.df_alloc_ext[['ID', 'matched_by']].drop_duplicates(subset=['ID'], keep='first')
            df_matched['ID'] = df_matched['ID'].astype(str)
            df_export['ID'] = df_export['ID'].astype(str)
            df_export = df_export.merge(df_matched, on='ID', how='left')
        
        def fix_id_valor_y_tipo(row):
            # Obtener qué tipo de match se usó
            matched_by = str(row.get('matched_by', '')).strip().upper()
            
            # Si se usó RIC o ISIN, usar ese
            if matched_by == 'RIC' and 'RIC' in row:
                ric = str(row['RIC']).strip()
                if ric and ric.upper() not in ['NAN', 'NONE', '']:
                    return ric, 'RIC'
            elif matched_by == 'ISIN' and 'Isin' in row:
                isin = str(row['Isin']).strip()
                if isin and isin.upper() not in ['NAN', 'NONE', '']:
                    return isin, 'Isin'  # Cambiar de ISIN a Isin
            
            # Si matched_by es Cusip, priorizar RIC/ISIN de todas formas
            if matched_by == 'CUSIP':
                for col, tipo in [('RIC', 'RIC'), ('Isin', 'Isin')]:  # Cambiar ISIN a Isin
                    if col in row:
                        val = str(row[col]).strip()
                        if val and val.upper() not in ['NAN', 'NONE', '']:
                            return val, tipo
            
            # Fallback: priorizar RIC, luego ISIN
            for col, tipo in [('RIC', 'RIC'), ('Isin', 'Isin')]:  # Cambiar ISIN a Isin
                if col in row:
                    val = str(row[col]).strip()
                    if val and val.upper() not in ['NAN', 'NONE', '']:
                        return val, tipo
            
            return '', ''
        
        # Aplicar la función y separar en dos columnas
        df_export[['Id_ti_valor_fixed', 'Id_ti_fixed']] = df_export.apply(
            lambda row: pd.Series(fix_id_valor_y_tipo(row)), axis=1
        )
             
        # 4. Preparar columnas finales - ELIMINAR duplicados antes de renombrar
        cols_to_drop = []
        
        # CRÍTICO: Eliminar la columna booleana 'Inconsistencia' del pipeline
        if 'Inconsistencia' in df_export.columns:
            cols_to_drop.append('Inconsistencia')
        
        # Si ya existe 'Id_ti_valor' en df_export (del pipeline), la eliminamos para usar la fixed
        if 'Id_ti_valor' in df_export.columns:
            cols_to_drop.append('Id_ti_valor')
        
        # Si ya existe 'Id_ti' en df_export (del pipeline), la eliminamos para usar la fixed
        if 'Id_ti' in df_export.columns:
            cols_to_drop.append('Id_ti')
        
        # Si ya existe 'moneda_antigua' del pipeline, la eliminamos para usar moneda_antigua_export
        if 'moneda_antigua' in df_export.columns:
            cols_to_drop.append('moneda_antigua')
        
        # Renombrar Detalle_Inconsistencia a Inconsistencia_Calc para export
        if 'Detalle_Inconsistencia' in df_export.columns:
            df_export['Inconsistencia_Calc'] = df_export['Detalle_Inconsistencia']
            cols_to_drop.append('Detalle_Inconsistencia')
        
        # Eliminar columnas que causarían duplicados
        df_export = df_export.drop(columns=cols_to_drop, errors='ignore')
        
        # NUEVO: Agregar columna Sobreescribir
        # "y" para todos los instrumentos excepto los que tienen Flag = "ERROR" (que tendrán "n")
        def calcular_sobreescribir(row):
            # Buscar Flag en cualquiera de sus posibles nombres
            flag = str(row.get('Flag', row.get('Semáforo', ''))).strip().upper()
            return 'n' if flag == 'ERROR' else 'y'
        
        df_export['Sobreescribir'] = df_export.apply(calcular_sobreescribir, axis=1)
        
        # Renombrar columnas al formato estricto solicitado
        col_mapping = {
            'ID': 'ID',
            'Id_ti_valor_fixed': 'Id_ti_valor',
            'Id_ti_fixed': 'Id_ti',
            'Fecha_Calc': 'Fecha',
            'Clasificacion_Calc': 'Clasificacion',
            'moneda_antigua_export': 'moneda_antigua',
            'Semáforo': 'Flag',
            'Inconsistencia_Calc': 'Inconsistencia'
        }
        
        # Aplicar renombre solo a las que existen
        rename_dict = {k: v for k, v in col_mapping.items() if k in df_export.columns}
        df_export = df_export.rename(columns=rename_dict)
        
        # 5. Seleccionar columnas en orden prioritario (sin duplicados)
        base_cols = ['ID', 'Id_ti_valor', 'Id_ti', 'Fecha', 'Clasificacion', 'moneda_antigua', 'Flag', 'Inconsistencia', 'Sobreescribir']
        
        # Identificar columnas de allocations (las que estaban en df_alloc_wide)
        alloc_cols = list(df_alloc_wide.columns) if not df_alloc_wide.empty else []
        
        # Construir lista final de columnas presentes (sin duplicados)
        final_cols = []
        for c in base_cols:
            if c in df_export.columns and c not in final_cols:
                final_cols.append(c)
        
        # Agregar columnas de monedas/regiones al final
        for c in alloc_cols:
            if c in df_export.columns and c not in final_cols:
                final_cols.append(c)
        
        # IMPORTANTE: Deduplicar por ID para evitar filas repetidas
        df_export_final = df_export[final_cols].drop_duplicates(subset=['ID'], keep='first')
        logger.info(f"[EXPORT DEBUG] Filas antes: {len(df_export)}, después: {len(df_export_final)}")
        
        # Agregar columna Total para verificación (suma de todas las columnas de allocations)
        if alloc_cols:
            # Sumar solo las columnas de allocations que estén presentes
            alloc_cols_presentes = [c for c in alloc_cols if c in df_export_final.columns]
            if alloc_cols_presentes:
                df_export_final['Total'] = df_export_final[alloc_cols_presentes].sum(axis=1)
                logger.info(f"[EXPORT DEBUG] Columna 'Total' agregada. Rango: {df_export_final['Total'].min():.2f}% - {df_export_final['Total'].max():.2f}%")
        
        return df_export_final
        
    except Exception as e:
        logger.error(f"Error preparando exportación: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return df_final # Fallback al original

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Validacion')
    return output.getvalue()

if df_filtered is not None and not df_filtered.empty: # Ensure df_filtered exists and is not empty
    col1, col2 = st.columns([1, 4])
    with col1:
        # Preparar datos
        try:
            # Recuperar df_alloc_ext según tipo de validación
            if tipo_validacion == "Moneda":
                df_alloc_ext = st.session_state.get('df_alloc_ext_moneda', pd.DataFrame())
            else:
                df_alloc_ext = st.session_state.get('df_alloc_ext_region', pd.DataFrame())
            
            # Crear objeto mock para compatibilidad con la función
            class PipelineMock:
                def __init__(self, df_alloc_ext):
                    self.df_alloc_ext = df_alloc_ext
                    self.df_alloc_ext_agrupado = df_alloc_ext
            
            pipeline_obj = PipelineMock(df_alloc_ext)
            df_export = preparar_dataframe_exportacion(df_filtered, pipeline_obj, tipo_validacion)
            excel_data = to_excel(df_export)
            
            st.download_button(
                label="📥 Descargar Excel",
                data=excel_data,
                file_name=f"validacion_{tipo_validacion.lower()}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.error(f"Error al generar Excel: {e}")

# Exportaciones especiales para Monedas: Balanceados y No Balanceados
if tipo_validacion == "Moneda":
    st.markdown("---")
    st.markdown("### 📊 Exportaciones Especiales")
    
    col_bal, col_no_bal = st.columns(2)
    
    with col_bal:
        st.markdown("#### Instrumentos Balanceados")
        if st.button("📥 Exportar Balanceados", key="export_bal"):
            try:
                # Filtrar balanceados: Moneda_Calculada == "balanceado"
                balanceados = df_filtered[
                    df_filtered['Moneda_Calculada'].str.lower() == 'balanceado'
                ]
                
                if not balanceados.empty:
                    # Usar la función de exportación completa (con allocations)
                    df_alloc_ext = st.session_state.get('df_alloc_ext_moneda', pd.DataFrame())
                    
                    class PipelineMock:
                        def __init__(self, df_alloc_ext):
                            self.df_alloc_ext = df_alloc_ext
                            self.df_alloc_ext_agrupado = df_alloc_ext
                    
                    pipeline_obj = PipelineMock(df_alloc_ext)
                    df_export_bal = preparar_dataframe_exportacion(balanceados, pipeline_obj, tipo_validacion)
                    excel_bal = to_excel(df_export_bal)
                    
                    st.download_button(
                        label="⬇️ Descargar Balanceados",
                        data=excel_bal,
                        file_name=f"balanceados_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_bal"
                    )
                    st.success(f"✅ {len(balanceados)} instrumentos balanceados listos para descargar")
                else:
                    st.info("No hay instrumentos balanceados en la selección actual.")
            except Exception as e:
                st.error(f"Error al generar reporte de balanceados: {e}")
    
    with col_no_bal:
        st.markdown("#### Instrumentos No Balanceados")
        if st.button("📥 Exportar No Balanceados", key="export_no_bal"):
            try:
                # Filtrar no balanceados: Moneda_Calculada != "balanceado" Y != "Sin Datos"
                no_balanceados = df_filtered[
                    (df_filtered['Moneda_Calculada'].str.lower() != 'balanceado') &
                    (df_filtered['Moneda_Calculada'].str.lower() != 'sin datos')
                ]
                
                if not no_balanceados.empty:
                    # Preparar export simple con solo 5 columnas
                    df_export_no_bal = no_balanceados.copy()
                    
                    # SubMoneda = Moneda Calculada (NUEVO valor a actualizar en BD)
                    if 'Moneda_Calculada' in df_export_no_bal.columns:
                        df_export_no_bal['SubMoneda_Nueva'] = df_export_no_bal['Moneda_Calculada']
                    else:
                        df_export_no_bal['SubMoneda_Nueva'] = ''
                    
                    # Moneda_Anterior = Moneda que estaba en BD (VIEJO valor)
                    # Buscar en SubMoneda o Moneda_Interna (el valor original de la BD)
                    if 'SubMoneda' in df_export_no_bal.columns:
                        df_export_no_bal['Moneda_Anterior'] = df_export_no_bal['SubMoneda']
                    elif 'Moneda_Interna' in df_export_no_bal.columns:
                        df_export_no_bal['Moneda_Anterior'] = df_export_no_bal['Moneda_Interna']
                    else:
                        df_export_no_bal['Moneda_Anterior'] = ''
                    
                    # Crear columna Inconsistencia desde Detalle_Inconsistencia
                    if 'Detalle_Inconsistencia' in df_export_no_bal.columns:
                        df_export_no_bal['Inconsistencia_Final'] = df_export_no_bal['Detalle_Inconsistencia']
                    else:
                        df_export_no_bal['Inconsistencia_Final'] = ''
                    
                    # Agregar columna Sobreescribir
                    def calcular_sobreescribir(row):
                        flag = str(row.get('Flag', row.get('Semáforo', ''))).strip().upper()
                        return 'n' if flag == 'ERROR' else 'y'
                    
                    df_export_no_bal['Sobreescribir'] = df_export_no_bal.apply(calcular_sobreescribir, axis=1)
                    
                    # IMPORTANTE: Eliminar columna SubMoneda original para evitar duplicados
                    # (ya guardamos su valor en Moneda_Anterior)
                    if 'SubMoneda' in df_export_no_bal.columns:
                        df_export_no_bal = df_export_no_bal.drop(columns=['SubMoneda'])
                    
                    # Seleccionar y renombrar columnas finales
                    columnas_finales = {
                        'ID': 'ID',
                        'Instrumento': 'Instrumento',
                        'SubMoneda_Nueva': 'SubMoneda',  # La moneda calculada (nueva)
                        'Moneda_Anterior': 'Moneda_Anterior',  # La moneda vieja de BD
                        'Inconsistencia_Final': 'Inconsistencia',
                        'Sobreescribir': 'Sobreescribir'
                    }
                    
                    # Renombrar
                    df_export_no_bal = df_export_no_bal.rename(columns=columnas_finales)
                    
                    # Seleccionar columnas finales en el orden correcto
                    cols_disponibles = ['ID', 'Instrumento', 'SubMoneda', 'Moneda_Anterior', 'Inconsistencia', 'Sobreescribir']
                    cols_presentes = [c for c in cols_disponibles if c in df_export_no_bal.columns]
                    df_export_no_bal = df_export_no_bal[cols_presentes]
                    
                    excel_no_bal = to_excel(df_export_no_bal)
                    
                    st.download_button(
                        label="⬇️ Descargar No Balanceados",
                        data=excel_no_bal,
                        file_name=f"no_balanceados_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_no_bal"
                    )
                    st.success(f"✅ {len(no_balanceados)} instrumentos no balanceados listos para descargar")
                else:
                    st.info("No hay instrumentos no balanceados en la selección actual.")
            except Exception as e:
                st.error(f"Error al generar reporte de no balanceados: {e}")

    # Tercer export: Sin Datos
    st.markdown("---")
    st.markdown("#### Instrumentos Sin Datos (No encontrados en Refinitiv)")
    if st.button("📥 Exportar Sin Datos", key="export_sin_datos"):
        try:
            # Filtrar instrumentos sin datos: Moneda_Calculada == "Sin Datos"
            sin_datos = df_filtered[
                df_filtered['Moneda_Calculada'].str.lower() == 'sin datos'
            ]
            
            if not sin_datos.empty:
                # Preparar export simple con solo 5 columnas
                df_export_sin_datos = sin_datos.copy()
                
                # Mapear columnas correctas
                if 'Instrumento' in df_export_sin_datos.columns and 'Nombre' not in df_export_sin_datos.columns:
                    df_export_sin_datos['Nombre'] = df_export_sin_datos['Instrumento']
                
                # Validar y priorizar Id_ti e Id_ti_valor
                # Prioridad: RIC > ISIN > otros (Cusip, etc.)
                # NUNCA usar Currency (es inválido)
                def fix_id_ti_sin_datos(row):
                    # Intentar usar RIC primero
                    ric = str(row.get('RIC', '')).strip()
                    if ric and ric.upper() not in ['NAN', 'NONE', '']:
                        return 'RIC', ric
                    
                    # Si no hay RIC, intentar ISIN
                    isin = str(row.get('Isin', '')).strip()
                    if isin and isin.upper() not in ['NAN', 'NONE', '']:
                        return 'ISIN', isin
                    
                    # Si no hay RIC ni ISIN, usar Id_ti original SOLO si NO es Currency
                    id_ti = str(row.get('Id_ti', '')).strip().upper()
                    id_ti_valor = str(row.get('Id_ti_valor', '')).strip()
                    
                    if id_ti and id_ti != 'CURRENCY' and id_ti_valor:
                        return id_ti, id_ti_valor
                    
                    # Si todo falla o es Currency, dejar vacío
                    return '', ''
                
                # Aplicar validación
                df_export_sin_datos[['Id_ti', 'Id_ti_valor']] = df_export_sin_datos.apply(
                    lambda row: pd.Series(fix_id_ti_sin_datos(row)), axis=1
                )
                
                # Seleccionar solo las columnas necesarias
                columnas_export = ['ID', 'Nombre', 'Id_ti_valor', 'Id_ti', 'Moneda_Calculada']
                
                # Si falta alguna columna, crearla vacía
                for col in columnas_export:
                    if col not in df_export_sin_datos.columns:
                        df_export_sin_datos[col] = ''
                
                # Seleccionar columnas en el orden correcto
                df_export_sin_datos = df_export_sin_datos[columnas_export]
                
                excel_sin_datos = to_excel(df_export_sin_datos)
                
                st.download_button(
                    label="⬇️ Descargar Sin Datos",
                    data=excel_sin_datos,
                    file_name=f"sin_datos_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_sin_datos"
                )
                st.success(f"✅ {len(sin_datos)} instrumentos sin datos listos para descargar")
            else:
                st.info("No hay instrumentos sin datos en la selección actual.")
        except Exception as e:
            st.error(f"Error al generar reporte de sin datos: {e}")

# Exportaciones especiales para Regiones: Balanceados, No Balanceados y Sin Datos
if tipo_validacion == "Región":
    st.markdown("---")
    st.markdown("### 📊 Exportaciones Especiales")
    
    col_bal, col_no_bal = st.columns(2)
    
    with col_bal:
        st.markdown("#### Instrumentos Balanceados")
        if st.button("📥 Exportar Balanceados", key="export_bal_region"):
            try:
                # Filtrar balanceados: Region_Calculada == "balanceado"
                balanceados = df_filtered[
                    df_filtered['Region_Calculada'].str.lower() == 'balanceado'
                ]
                
                if not balanceados.empty:
                    # Usar la función de exportación completa (con allocations)
                    df_alloc_ext = st.session_state.get('df_alloc_ext_region', pd.DataFrame())
                    
                    class PipelineMock:
                        def __init__(self, df_alloc_ext):
                            self.df_alloc_ext = df_alloc_ext
                            self.df_alloc_ext_agrupado = df_alloc_ext
                    
                    pipeline_obj = PipelineMock(df_alloc_ext)
                    df_export_bal = preparar_dataframe_exportacion(balanceados, pipeline_obj, tipo_validacion)
                    excel_bal = to_excel(df_export_bal)
                    
                    st.download_button(
                        label="⬇️ Descargar Balanceados",
                        data=excel_bal,
                        file_name=f"balanceados_region_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_bal_region"
                    )
                    st.success(f"✅ {len(balanceados)} instrumentos balanceados listos para descargar")
                else:
                    st.info("No hay instrumentos balanceados en la selección actual.")
            except Exception as e:
                st.error(f"Error al generar reporte de balanceados: {e}")
    
    with col_no_bal:
        st.markdown("#### Instrumentos No Balanceados")
        if st.button("📥 Exportar No Balanceados", key="export_no_bal_region"):
            try:
                # Filtrar no balanceados: Region_Calculada != "balanceado" Y != "Sin Datos"
                no_balanceados = df_filtered[
                    (df_filtered['Region_Calculada'].str.lower() != 'balanceado') &
                    (df_filtered['Region_Calculada'].str.lower() != 'sin datos')
                ]
                
                if not no_balanceados.empty:
                    # Preparar export simple con solo 5 columnas
                    df_export_no_bal = no_balanceados.copy()
                    
                    # base-region = Region_Calculada (NUEVO valor a actualizar en BD)
                    if 'Region_Calculada' in df_export_no_bal.columns:
                        df_export_no_bal['base-region_Nueva'] = df_export_no_bal['Region_Calculada']
                    else:
                        df_export_no_bal['base-region_Nueva'] = ''
                    
                    # Region_Anterior = Región que estaba en BD (VIEJO valor)
                    if 'base-region' in df_export_no_bal.columns:
                        df_export_no_bal['Region_Anterior'] = df_export_no_bal['base-region']
                    elif 'Region_Antigua' in df_export_no_bal.columns:
                        df_export_no_bal['Region_Anterior'] = df_export_no_bal['Region_Antigua']
                    else:
                        df_export_no_bal['Region_Anterior'] = ''
                    
                    # Crear columna Inconsistencia
                    if 'Detalle_Inconsistencia' in df_export_no_bal.columns:
                        df_export_no_bal['Inconsistencia_Final'] = df_export_no_bal['Detalle_Inconsistencia']
                    elif 'Detalle_Validacion' in df_export_no_bal.columns:
                        df_export_no_bal['Inconsistencia_Final'] = df_export_no_bal['Detalle_Validacion']
                    else:
                        df_export_no_bal['Inconsistencia_Final'] = ''
                    
                    # Agregar columna Sobreescribir
                    def calcular_sobreescribir(row):
                        flag = str(row.get('Flag', row.get('Semáforo', ''))).strip().upper()
                        return 'n' if flag == 'ERROR' else 'y'
                    
                    df_export_no_bal['Sobreescribir'] = df_export_no_bal.apply(calcular_sobreescribir, axis=1)
                    
                    # Seleccionar y renombrar columnas finales
                    columnas_finales = {
                        'ID': 'ID',
                        'Instrumento': 'Instrumento',
                        'base-region_Nueva': 'base-region',
                        'Region_Anterior': 'Region_Anterior',
                        'Inconsistencia_Final': 'Inconsistencia',
                        'Sobreescribir': 'Sobreescribir'
                    }
                    
                    # Renombrar
                    df_export_no_bal = df_export_no_bal.rename(columns=columnas_finales)
                    
                    # Seleccionar columnas finales en el orden correcto
                    cols_disponibles = ['ID', 'Instrumento', 'base-region', 'Region_Anterior', 'Inconsistencia', 'Sobreescribir']
                    cols_presentes = [c for c in cols_disponibles if c in df_export_no_bal.columns]
                    df_export_no_bal = df_export_no_bal[cols_presentes]
                    
                    excel_no_bal = to_excel(df_export_no_bal)
                    
                    st.download_button(
                        label="⬇️ Descargar No Balanceados",
                        data=excel_no_bal,
                        file_name=f"no_balanceados_region_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_no_bal_region"
                    )
                    st.success(f"✅ {len(no_balanceados)} instrumentos no balanceados listos para descargar")
                else:
                    st.info("No hay instrumentos no balanceados en la selección actual.")
            except Exception as e:
                st.error(f"Error al generar reporte de no balanceados: {e}")

    # Tercer export: Sin Datos
    st.markdown("---")
    st.markdown("#### Instrumentos Sin Datos (No encontrados en Refinitiv)")
    if st.button("📥 Exportar Sin Datos", key="export_sin_datos_region"):
        try:
            # Filtrar instrumentos sin datos: Region_Calculada == "Sin Datos"
            sin_datos = df_filtered[
                df_filtered['Region_Calculada'].str.lower() == 'sin datos'
            ]
            
            if not sin_datos.empty:
                # Preparar export simple con solo 5 columnas
                df_export_sin_datos = sin_datos.copy()
                
                # Seleccionar solo las columnas necesarias
                columnas_export = ['ID', 'Nombre', 'Id_ti_valor', 'Id_ti', 'Region_Calculada']
                columnas_disponibles = [c for c in columnas_export if c in df_export_sin_datos.columns]
                
                # Si falta alguna columna, crearla vacía
                for col in columnas_export:
                    if col not in df_export_sin_datos.columns:
                        df_export_sin_datos[col] = ''
                
                # Seleccionar columnas en el orden correcto
                df_export_sin_datos = df_export_sin_datos[columnas_export]
                
                excel_sin_datos = to_excel(df_export_sin_datos)
                
                st.download_button(
                    label="⬇️ Descargar Sin Datos",
                    data=excel_sin_datos,
                    file_name=f"sin_datos_region_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_sin_datos_region"
                )
                st.success(f"✅ {len(sin_datos)} instrumentos sin datos listos para descargar")
            else:
                st.info("No hay instrumentos sin datos en la selección actual.")
        except Exception as e:
            st.error(f"Error al generar reporte de sin datos: {e}")
