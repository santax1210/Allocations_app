"""
Página para cargar archivos CSV/Excel al sistema.
"""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime
import logging

# Agregar src y utils al path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'utils'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'components'))

from styles import apply_common_styles, render_header
from session_state import init_session_state, reset_validation_state
from data_loader import DataLoader
from pipeline import ConciliacionPipeline

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de página
st.set_page_config(
    page_title="Carga de Archivos",
    page_icon="📁",
    layout="wide"
)

# Aplicar estilos
apply_common_styles()
init_session_state()

# Header personalizado más pequeño
st.markdown("""
<h2 style='text-align: left; color: #ffffff; font-size: 1.8rem; margin-bottom: 1rem; font-weight: 700;'>📁 Carga de Archivos</h2>
<div style='width: 100%; height: 2px; background: linear-gradient(90deg, #1e88e5 0%, #ff6f00 50%, #1e88e5 100%); margin-bottom: 2rem; border-radius: 2px;'></div>
""", unsafe_allow_html=True)

# Aplicar tema oscuro con gradiente
st.markdown("""
<style>
/* Fondo general de la app con gradiente radial */
.stApp {
    background: radial-gradient(ellipse at top, #555555 0%, #3d3d3d 50%, #2a2a2a 100%) !important;
    background-attachment: fixed !important;
}

/* Ajustar textos para tema oscuro - títulos en blanco */
h1, h2, h3, h4, h5, h6 {
    color: #ffffff !important;
}

p, span, label {
    color: #e0e0e0 !important;
}

/* Multiselect - fondo oscuro y texto claro */
div[data-baseweb="select"] {
    background-color: #2d2d2d !important;
}

div[data-baseweb="select"] input {
    color: #ffffff !important;
}

div[data-baseweb="select"] span {
    color: #ffffff !important;
}

/* Tags seleccionados en multiselect */
span[data-baseweb="tag"] {
    background-color: #4a4a4a !important;
    color: #ffffff !important;
}

/* Dropdown del multiselect */
ul[role="listbox"] {
    background-color: #2d2d2d !important;
}

ul[role="listbox"] li {
    color: #ffffff !important;
}

ul[role="listbox"] li:hover {
    background-color: #4a4a4a !important;
}

/* Labels */
label[data-testid="stWidgetLabel"] {
    color: #e0e0e0 !important;
}

/* DataFrames con fondo claro */
div[data-testid="stDataFrame"] {
    background-color: #f8f9fa !important;
}

/* Achicar padding de file uploaders */
div[data-testid="stFileUploader"] {
    padding: 15px !important;
    margin-bottom: 10px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
    transition: all 0.3s ease !important;
}

div[data-testid="stFileUploader"]:hover {
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
    transform: translateY(-2px);
}

/* Ocultar el label "Cargar Archivo" dentro del uploader */
div[data-testid="stFileUploader"] > label > div[data-testid="stMarkdownContainer"] {
    display: none !important;
}

/* Mejorar visibilidad de botones Eliminar con estilo moderno */
button[kind="secondary"] {
    padding: 0.4rem 1rem !important;
    font-size: 0.875rem !important;
    min-height: 2.2rem !important;
    border-radius: 6px !important;
    transition: all 0.2s ease !important;
    background: linear-gradient(135deg, #f87171 0%, #ef4444 100%) !important;
    border: none !important;
    box-shadow: 0 2px 4px rgba(239, 68, 68, 0.3) !important;
}

button[kind="secondary"]:hover {
    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(239, 68, 68, 0.4) !important;
}

button[kind="secondary"] p {
    color: #ffffff !important;
    font-weight: 600 !important;
}

/* Ocultar file uploader cuando hay archivo cargado */
.hide-uploader {
    display: none !important;
}

/* Cuadro verde que simula el file uploader - mismo tamaño exacto */
.success-box {
    border: 2px solid #10b981;
    border-radius: 10px;
    padding: 15px;
    background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
    margin-bottom: 10px;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    transition: all 0.3s ease;
    min-height: 94px;
    height: 94px;
    display: flex;
    align-items: center;
    justify-content: flex-start;
    box-sizing: border-box;
    animation: successAppear 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
    position: relative;
    overflow: hidden;
}

/* Animación de aparición con bounce suave */
@keyframes successAppear {
    0% {
        opacity: 0;
        transform: scale(0.9);
    }
    50% {
        transform: scale(1.02);
    }
    100% {
        opacity: 1;
        transform: scale(1);
    }
}

/* Efecto shimmer cuando aparece */
.success-box::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
    animation: shimmer 1.5s ease-in-out;
}

@keyframes shimmer {
    0% {
        left: -100%;
    }
    100% {
        left: 100%;
    }
}

.success-box p {
    font-size: 0.875rem;
    margin: 0;
    color: #1f2937 !important;
    font-weight: 600;
    line-height: 1.4;
    position: relative;
    z-index: 1;
}

.success-box p span {
    color: #1f2937 !important;
}

/* Animación de fade-out para el file uploader */
.fade-out {
    animation: fadeOut 0.3s ease-out forwards;
}

@keyframes fadeOut {
    from {
        opacity: 1;
        transform: scale(1);
    }
    to {
        opacity: 0;
        transform: scale(0.95);
    }
}

/* Mejorar transiciones del file uploader */
div[data-testid="stFileUploader"] {
    padding: 15px !important;
    margin-bottom: 10px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
    opacity: 1;
    transform: scale(1);
}

/* Estado de carga - efecto pulse */
.uploading {
    animation: pulse 1.5s ease-in-out infinite;
    border: 2px solid #3b82f6;
    box-shadow: 0 0 20px rgba(59, 130, 246, 0.4) !important;
}

@keyframes pulse {
    0%, 100% {
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.4);
    }
    50% {
        box-shadow: 0 0 30px rgba(59, 130, 246, 0.8);
    }
}

/* Línea separadora más clara */
hr {
    border-color: #6b7280 !important;
    opacity: 0.4 !important;
}

/* Estilos para Sidebar con relieve y profundidad */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #555555 0%, #3d3d3d 50%, #2a2a2a 100%) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
    box-shadow: 4px 0 20px rgba(0, 0, 0, 0.5), inset -1px 0 0 rgba(255, 255, 255, 0.05) !important;
}

section[data-testid="stSidebar"] > div {
    background: transparent !important;
    padding: 1rem 0.5rem !important;
}

/* Título del sidebar */
section[data-testid="stSidebar"] h1 {
    font-size: 1.3rem !important;
    margin-bottom: 1.5rem !important;
    padding: 0.5rem 1rem !important;
    background: linear-gradient(135deg, rgba(30, 136, 229, 0.2), rgba(255, 111, 0, 0.2)) !important;
    border-radius: 8px !important;
    border-left: 3px solid #1e88e5 !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
}

/* Links de navegación en sidebar con efecto de elevación */
section[data-testid="stSidebar"] a {
    font-size: 1.05rem !important;
    color: #e2e8f0 !important;
    font-weight: 500 !important;
    padding: 0.85rem 1.2rem !important;
    margin: 0.3rem 0.5rem !important;
    border-radius: 8px !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    background: rgba(255, 255, 255, 0.03) !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2) !important;
    display: block !important;
}

section[data-testid="stSidebar"] a:hover {
    background: linear-gradient(135deg, rgba(66, 153, 225, 0.3), rgba(30, 136, 229, 0.2)) !important;
    color: #90cdf4 !important;
    transform: translateX(5px) !important;
    box-shadow: 0 4px 12px rgba(66, 153, 225, 0.4), 0 0 20px rgba(30, 136, 229, 0.2) !important;
    border-color: rgba(66, 153, 225, 0.5) !important;
}

/* Link activo en sidebar */
section[data-testid="stSidebar"] a[aria-current="page"] {
    background: linear-gradient(135deg, rgba(30, 136, 229, 0.4), rgba(255, 111, 0, 0.2)) !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    border-left: 4px solid #1e88e5 !important;
    box-shadow: 0 4px 12px rgba(30, 136, 229, 0.5) !important;
}

/* Header de Streamlit con efecto de elevación */
header[data-testid="stHeader"] {
    background: linear-gradient(90deg, #555555 0%, #3d3d3d 50%, #2a2a2a 100%) !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5), inset 0 -1px 0 rgba(255, 255, 255, 0.05) !important;
    backdrop-filter: blur(10px) !important;
}

/* Toolbar del header */
div[data-testid="stToolbar"] {
    background: transparent !important;
}

/* Botones del toolbar con efecto de profundidad */
header[data-testid="stHeader"] button {
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 6px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2) !important;
}

header[data-testid="stHeader"] button:hover {
    background: rgba(255, 255, 255, 0.1) !important;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3) !important;
    transform: translateY(-1px) !important;
}

/* Botón Primary (Validar Allocations) con efectos profesionales */
button[kind="primary"] {
    background: linear-gradient(135deg, #1e88e5 0%, #1565c0 100%) !important;
    border: none !important;
    box-shadow: 0 4px 12px rgba(30, 136, 229, 0.4), 0 0 20px rgba(30, 136, 229, 0.2) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    font-weight: 600 !important;
    padding: 0.75rem 1.5rem !important;
    border-radius: 8px !important;
    position: relative !important;
    overflow: hidden !important;
}

button[kind="primary"]::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
    transition: left 0.5s ease;
}

button[kind="primary"]:hover::before {
    left: 100%;
}

button[kind="primary"]:hover {
    background: linear-gradient(135deg, #1565c0 0%, #0d47a1 100%) !important;
    box-shadow: 0 6px 20px rgba(30, 136, 229, 0.6), 0 0 30px rgba(30, 136, 229, 0.4) !important;
    transform: translateY(-2px) scale(1.02) !important;
}

button[kind="primary"]:active {
    transform: translateY(0) scale(0.98) !important;
    box-shadow: 0 2px 8px rgba(30, 136, 229, 0.4) !important;
}

button[kind="primary"] p {
    color: #ffffff !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    position: relative;
    z-index: 1;
}

/* Estilos para tabla de estado de archivos */
.status-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
}

.status-table thead {
    background: linear-gradient(135deg, #1e3a5f 0%, #2d4a6f 100%);
}

.status-table th {
    padding: 16px 20px;
    text-align: left;
    color: #93c5fd;
    font-weight: 600;
    font-size: 0.95rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 2px solid rgba(30, 136, 229, 0.3);
}

.status-table tbody tr {
    transition: all 0.2s ease;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.status-table tbody tr:hover {
    background: rgba(30, 136, 229, 0.1);
    transform: translateX(3px);
}

.status-table tbody tr:last-child {
    border-bottom: none;
}

.status-table td {
    padding: 14px 20px;
    color: #e2e8f0;
    font-size: 0.9rem;
}

.status-badge {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.85rem;
    text-align: center;
    min-width: 90px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.status-cargado {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: #ffffff;
}

.status-pendiente {
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    color: #ffffff;
}

.archivo-nombre {
    font-family: 'Courier New', monospace;
    background: rgba(0, 0, 0, 0.2);
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.85rem;
    color: #93c5fd;
}
</style>
""", unsafe_allow_html=True)

# Información de archivos requeridos con diseño mejorado
st.markdown("""
<div style='background: linear-gradient(135deg, #1e3a5f 0%, #2d4a6f 100%); border-left: 4px solid #3b82f6; padding: 18px 20px; border-radius: 8px; margin-bottom: 30px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);'>
    <div style='display: flex; align-items: center; margin-bottom: 10px;'>
        <span style='font-size: 1.5rem; margin-right: 10px;'>📋</span>
        <strong style='color: #93c5fd; font-size: 1.05rem;'>Archivos Requeridos</strong>
    </div>
    <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 12px; color: #bfdbfe; font-size: 0.9rem;'>
    <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 12px; color: #bfdbfe; font-size: 0.9rem;'>
        <div style='padding: 8px; background: rgba(255,255,255,0.05); border-radius: 4px;'>
            <strong style='color: #93c5fd;'>• Allocations Internos</strong><br>
            <span style='font-size: 0.85rem; color: #a3c5e8;'>Distribución de monedas calculada internamente</span>
        </div>
        <div style='padding: 8px; background: rgba(255,255,255,0.05); border-radius: 4px;'>
            <strong style='color: #93c5fd;'>• Instruments</strong><br>
            <span style='font-size: 0.85rem; color: #a3c5e8;'>Catálogo de instrumentos financieros</span>
        </div>
        <div style='padding: 8px; background: rgba(255,255,255,0.05); border-radius: 4px;'>
            <strong style='color: #93c5fd;'>• Allocations Refinitiv</strong><br>
            <span style='font-size: 0.85rem; color: #a3c5e8;'>Distribución de monedas desde proveedor externo</span>
        </div>
        <div style='padding: 8px; background: rgba(255,255,255,0.05); border-radius: 4px;'>
            <strong style='color: #93c5fd;'>• Posiciones Consolidadas</strong><br>
            <span style='font-size: 0.85rem; color: #a3c5e8;'>Posiciones actuales del sistema</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Función para validar estructura del archivo
def validar_estructura(df: pd.DataFrame, tipo_archivo: str) -> tuple[bool, str]:
    """
    Valida que el archivo tenga las columnas esperadas.
    
    Returns:
        (es_valido, mensaje)
    """
    # Definir requerimientos por tipo
    if tipo_archivo == 'allocations':
        # Allocations internos pueden ser Moneda o Región
        # Moneda: ID, Moneda...
        # Región: ID, Base Región...
        if 'ID' in df.columns:
            return True, f"✅ Estructura válida ({len(df):,} registros)"
        else:
            return False, "❌ Falta columna 'ID'"
            
    elif tipo_archivo == 'instruments':
        if 'ID' in df.columns and 'Nombre' in df.columns:
            return True, f"✅ Estructura válida ({len(df):,} registros)"
        else:
            return False, "❌ Faltan columnas ID/Nombre"
            
    elif tipo_archivo == 'allocations_refinitiv':
        # Puede ser formato largo (currency) o ancho (region)
        # Largo: instrument, class, percentage
        cols = [c.lower() for c in df.columns]
        
        # Caso 1: Formato Largo (Currency)
        if 'instrument' in cols and 'class' in cols and 'percentage' in cols:
             return True, f"✅ Estructura válida (Formato Standard) ({len(df):,} registros)"
        
        # Caso 2: Formato Ancho (Región) - Muchas columnas numéricas
        # Asumimos que la primera columna es el instrumento
        # Verificamos si parece archivo de regiones (headers como Africa, Asia, etc.)
        headers_str = "".join(cols).lower()
        keywords_region = ['africa', 'asia', 'europe', 'latam', 'america']
        if any(k in headers_str for k in keywords_region):
             return True, f"✅ Estructura válida (Formato Región Wide) ({len(df):,} registros)"
             
        return False, "❌ Formato desconocido (faltan instrument/class/percentage o columnas de regiones)"
        
    elif tipo_archivo == 'posiciones':
        if 'Id_ti_valor' in df.columns or 'Instrumento' in df.columns:
             return True, f"✅ Estructura válida ({len(df):,} registros)"
        else:
             return False, "❌ Faltan columnas clave (Id_ti_valor o Instrumento)"
             
             
    return True, "Archivo cargado correctamente"

def procesar_posiciones(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica transformaciones al DataFrame de posiciones (igual que DataLoader)."""
    df = df.copy()
    if 'F. Proceso' in df.columns:
        df['F. Proceso'] = pd.to_datetime(df['F. Proceso'], errors='coerce')
    return df

def procesar_allocations_interno(df: pd.DataFrame) -> pd.DataFrame:
    """Transforma allocations interno a formato largo (igual que DataLoader)."""
    
    # 1. Normalizar columna Base Región si existe con nombre corrupto
    column_mapping = {}
    for col in df.columns:
        if 'BASE REG' in str(col).upper():
            column_mapping[col] = 'Base Región:'
    
    if column_mapping:
         df = df.rename(columns=column_mapping)
    
    # Columnas de monedas (todas las que no son identificadoras ni metadatos)
    exclude_cols = ['ID', 'Nombre', 'Creado', 'Tipo Instrumento', 'Moneda', 'Nemo', 
                   'Isin', 'Cusip', 'Ticker_BB', 'Currency', 'RIC', 'Moneda:', 'Base Región:']
    
    # Detectar columnas de valores (monedas o regiones)
    value_cols = [col for col in df.columns if col not in exclude_cols and col.strip() != '']
    
    # Preservar columna "Moneda:" y "Base Región:" para detección de inconsistencias
    id_vars = ['ID', 'Nombre', 'Isin', 'Cusip', 'RIC']
    if 'Moneda:' in df.columns:
        id_vars.append('Moneda:')
    if 'Base Región:' in df.columns:
        id_vars.append('Base Región:')
    
    # Asegurar que las columnas id existan
    id_vars = [c for c in id_vars if c in df.columns]
    
    # Transformar a formato largo
    df_long = df.melt(
        id_vars=id_vars,
        value_vars=value_cols,
        var_name='currency_code', # Se usa generico para currency o region
        value_name='percentage_num'
    )
    
    # Convertir porcentaje a numérico PRIMERO (antes de filtrar)
    # Manejar comas decimales si vienen como string
    if df_long['percentage_num'].dtype == object:
        df_long['percentage_num'] = df_long['percentage_num'].str.replace(',', '.', regex=False)
        
    df_long['percentage_num'] = pd.to_numeric(df_long['percentage_num'], errors='coerce')
    
    # Ahora sí filtrar valores válidos
    df_long = df_long[df_long['percentage_num'].notna()].copy()
    df_long = df_long[df_long['percentage_num'] > 0].copy()
    
    return df_long

def procesar_allocations_externo(df: pd.DataFrame) -> pd.DataFrame:
    """Filtra allocations externo y normaliza."""
    df = df.copy()
    
    # Normalizar headers a minúsculas para chequeos
    df.columns = df.columns.str.strip()
    original_cols = df.columns.tolist()
    
    # DETECTAR SI ES FORMATO ANCHO (REGION)
    # Pista: No tiene columna 'class' ni 'percentage', y la primera col suele ser el ID
    if 'class' not in df.columns and 'percentage' not in df.columns:
        # Se asume formato Wide (Regiones)
        # La primera columna es el instrumento
        id_col = df.columns[0]
        
        # Melt
        df_melt = df.melt(
            id_vars=[id_col],
            var_name='class',
            value_name='percentage'
        )
        
        # Renombrar id col a 'instrument'
        df_melt = df_melt.rename(columns={id_col: 'instrument'})
        
        # El resto del proceso asume formato long
        df = df_melt
        
    # LOGICA ESTANDAR (Formato Long)
    
    # Convertir date a datetime si existe
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    
    # Filtrar solo FundCurrencyAllocation si existe esa columna
    if 'Columna Fuente' in df.columns:
        df = df[df['Columna Fuente'] == 'FundCurrencyAllocation'].copy()
    
    # Convertir percentage a numérico
    if 'percentage' in df.columns:
        if df['percentage'].dtype == object:
            df['percentage'] = df['percentage'].str.replace(',', '.', regex=False)
        df['percentage'] = pd.to_numeric(df['percentage'], errors='coerce')
    
    return df

# Función para leer archivo con manejo robusto de errores
def leer_archivo_robusto(file, nombre_archivo: str):
    """
    Lee un archivo CSV/Excel con manejo robusto de errores.
    Usa la misma lógica que DataLoader.
    """
    try:
        # Determinar si es CSV o Excel
        if nombre_archivo.endswith('.csv'):
            # Intentar varios encodings comunes
            encodings = ['latin-1', 'utf-8', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    # Usar las mismas opciones que DataLoader
                    df = pd.read_csv(
                        file,
                        sep=';',
                        encoding=encoding,
                        on_bad_lines='skip',  # Saltar líneas con problemas
                        engine='python'  # Motor más tolerante con errores
                    )
                    logger.info(f"Archivo leído exitosamente con encoding: {encoding}")
                    return df, None
                except UnicodeDecodeError:
                    file.seek(0)  # Reiniciar el puntero del archivo
                    continue
                except Exception as e:
                    file.seek(0)
                    if encoding == encodings[-1]:  # Último intento
                        raise e
                    continue
            
            return None, "No se pudo leer el archivo con ningún encoding"
        else:
            # Excel
            df = pd.read_excel(file)
            return df, None
            
    except Exception as e:
        return None, str(e)

# Función para guardar archivo
def guardar_archivo(df: pd.DataFrame, nombre_archivo: str, tipo: str):
    """Guarda el archivo en la carpeta data/."""
    data_path = Path(__file__).parent.parent / 'data'
    data_path.mkdir(exist_ok=True)
    
    # Agregar timestamp al nombre
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_base = Path(nombre_archivo).stem
    extension = Path(nombre_archivo).suffix
    
    nuevo_nombre = f"{nombre_base}_{timestamp}{extension}"
    filepath = data_path / nuevo_nombre
    
    # Guardar según extensión
    if extension.lower() == '.csv':
        df.to_csv(filepath, index=False, sep=';')
    else:
        df.to_excel(filepath, index=False)
    
    return str(filepath)

# Crear columnas para los 4 uploaders
col1, col2 = st.columns(2)

with col1:
    st.markdown("<h4 style='margin-bottom: 0.8rem; color: #e2e8f0; font-weight: 600; text-shadow: 0 2px 4px rgba(0,0,0,0.3);'>Allocations Internos</h4>", unsafe_allow_html=True)
    
    # Si hay archivo cargado, mostrar cuadro verde
    if st.session_state.archivos_cargados['allocations']:
        st.markdown(f"""
        <div class="success-box">
            <p>✅ {st.session_state.archivos_cargados['allocations']['nombre']}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("❌ Eliminar", key="cancel_alloc_saved", help="Eliminar archivo"):
            st.session_state.archivos_cargados['allocations'] = None
            st.rerun()
    else:
        # File uploader solo visible cuando NO hay archivo
        file_alloc = st.file_uploader(
            "​",  # Caracter invisible para ocultar label
            type=['csv', 'xlsx', 'xls'],
            key="upload_alloc",
            label_visibility="collapsed"
        )
    
    # Si hay archivo cargado desde el uploader, procesar
    if 'file_alloc' in locals() and file_alloc:
        try:
            # Leer archivo con manejo robusto
            df_alloc, error = leer_archivo_robusto(file_alloc, file_alloc.name)
            
            if error:
                st.error(f"❌ Error al leer archivo: {error}")
            else:
                # Validar
                es_valido, mensaje = validar_estructura(df_alloc, 'allocations')
                
                if not es_valido:
                    st.error(mensaje)
                else:
                    # Guardar en memoria (no en disco)
                    st.session_state.archivos_cargados['allocations'] = {
                        'df': procesar_allocations_interno(df_alloc),  # Aplicar transformaciones
                        'nombre': file_alloc.name
                    }
                    st.success(f"✅ {file_alloc.name} cargado exitosamente")
                    st.rerun()
                
        except Exception as e:
            st.error(f"❌ Error inesperado: {str(e)}")

with col2:
    st.markdown("<h4 style='margin-bottom: 0.8rem; color: #e2e8f0; font-weight: 600; text-shadow: 0 2px 4px rgba(0,0,0,0.3);'>Instruments</h4>", unsafe_allow_html=True)
    
    if st.session_state.archivos_cargados['instruments']:
        st.markdown(f"""
        <div class="success-box">
            <p>✅ {st.session_state.archivos_cargados['instruments']['nombre']}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("❌ Eliminar", key="cancel_inst_saved", help="Eliminar archivo"):
            st.session_state.archivos_cargados['instruments'] = None
            st.rerun()
    else:
        file_inst = st.file_uploader(
            "​",
            type=['csv', 'xlsx', 'xls'],
            key="upload_inst",
            label_visibility="collapsed"
        )
    
    if 'file_inst' in locals() and file_inst:
        try:
            df_inst, error = leer_archivo_robusto(file_inst, file_inst.name)
            
            if error:
                st.error(f"❌ Error al leer archivo: {error}")
            else:
                es_valido, mensaje = validar_estructura(df_inst, 'instruments')
                
                if not es_valido:
                    st.error(mensaje)
                else:
                    # Guardar en memoria (no en disco)
                    st.session_state.archivos_cargados['instruments'] = {
                        'df': df_inst,
                        'nombre': file_inst.name
                    }
                    st.success(f"✅ {file_inst.name} cargado exitosamente")
                    st.rerun()
                
        except Exception as e:
            st.error(f"❌ Error inesperado: {str(e)}")

# Línea separadora más clara
st.markdown('<hr style="border-color: #6b7280; opacity: 0.4; margin: 2rem 0;">', unsafe_allow_html=True)

col3, col4 = st.columns(2)

with col3:
    st.markdown("<h4 style='margin-bottom: 0.8rem; color: #e2e8f0; font-weight: 600; text-shadow: 0 2px 4px rgba(0,0,0,0.3);'>Allocations Refinitiv</h4>", unsafe_allow_html=True)
    
    if st.session_state.archivos_cargados['allocations_refinitiv']:
        st.markdown(f"""
        <div class="success-box">
            <p>✅ {st.session_state.archivos_cargados['allocations_refinitiv']['nombre']}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("❌ Eliminar", key="cancel_ref_saved", help="Eliminar archivo"):
            st.session_state.archivos_cargados['allocations_refinitiv'] = None
            st.rerun()
    else:
        file_refinitiv = st.file_uploader(
            "​",
            type=['csv', 'xlsx', 'xls'],
            key="upload_ref",
            label_visibility="collapsed"
        )
    
    if 'file_refinitiv' in locals() and file_refinitiv:
        try:
            df_ref, error = leer_archivo_robusto(file_refinitiv, file_refinitiv.name)
            
            if error:
                st.error(f"❌ Error al leer archivo: {error}")
            else:
                es_valido, mensaje = validar_estructura(df_ref, 'allocations_refinitiv')
                
                if not es_valido:
                    st.error(mensaje)
                else:
                    # Guardar en memoria (no en disco)
                    st.session_state.archivos_cargados['allocations_refinitiv'] = {
                        'df': procesar_allocations_externo(df_ref),  # Aplicar transformaciones
                        'nombre': file_refinitiv.name
                    }
                    st.success(f"✅ {file_refinitiv.name} cargado exitosamente")
                    st.rerun()
                
        except Exception as e:
            st.error(f"❌ Error inesperado: {str(e)}")

with col4:
    st.markdown("<h4 style='margin-bottom: 0.8rem; color: #e2e8f0; font-weight: 600; text-shadow: 0 2px 4px rgba(0,0,0,0.3);'>Posiciones Consolidadas</h4>", unsafe_allow_html=True)
    
    if st.session_state.archivos_cargados['posiciones']:
        st.markdown(f"""
        <div class="success-box">
            <p>✅ {st.session_state.archivos_cargados['posiciones']['nombre']}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("❌ Eliminar", key="cancel_pos_saved", help="Eliminar archivo"):
            st.session_state.archivos_cargados['posiciones'] = None
            st.rerun()
    else:
        file_pos = st.file_uploader(
            "​",
            type=['csv', 'xlsx', 'xls'],
            key="upload_pos",
            label_visibility="collapsed"
        )
    
    if 'file_pos' in locals() and file_pos:
        try:
            df_pos, error = leer_archivo_robusto(file_pos, file_pos.name)
            
            if error:
                st.error(f"❌ Error al leer archivo: {error}")
            else:
                es_valido, mensaje = validar_estructura(df_pos, 'posiciones')
                
                if not es_valido:
                    st.error(mensaje)
                else:
                    # Guardar en memoria (no en disco)
                    st.session_state.archivos_cargados['posiciones'] = {
                        'df': procesar_posiciones(df_pos),  # Aplicar transformaciones
                        'nombre': file_pos.name
                    }
                    st.success(f"✅ {file_pos.name} cargado exitosamente")
                    st.rerun()
                    
        except Exception as e:
            st.error(f"❌ Error inesperado: {str(e)}")


# Resumen de archivos cargados con diseño mejorado
st.markdown("---")
st.markdown("<h4 style='font-size: 1.2rem; font-weight: 600; margin-bottom: 1rem;'>📋 Estado de Archivos</h4>", unsafe_allow_html=True)

# Construir filas de la tabla
filas_tabla = []
for tipo, data in st.session_state.archivos_cargados.items():
    if tipo in ['allocations_region_interno', 'allocations_region_externo']: continue # Skip hidden internal keys if any remains
    
    tipo_formateado = tipo.replace('_', ' ').title()
    if data:
        estado_html = '<span class="status-badge status-cargado">✅ Cargado</span>'
        archivo_html = f'<span class="archivo-nombre">{data["nombre"]}</span>'
    else:
        estado_html = '<span class="status-badge status-pendiente">⏳ Pendiente</span>'
        archivo_html = '<span style="color: #6b7280;">-</span>'
    
    filas_tabla.append(f"""        <tr>
            <td>{tipo_formateado}</td>
            <td>{estado_html}</td>
            <td>{archivo_html}</td>
        </tr>""")

# Crear tabla completa
tabla_html = f"""
<table class="status-table">
    <thead>
        <tr>
            <th>Tipo de Archivo</th>
            <th>Estado</th>
            <th>Archivo</th>
        </tr>
    </thead>
    <tbody>
{''.join(filas_tabla)}
    </tbody>
</table>
"""

st.markdown(tabla_html, unsafe_allow_html=True)

# Botón para procesar
todos_cargados = all(st.session_state.archivos_cargados.get(k) for k in ['posiciones', 'instruments', 'allocations', 'allocations_refinitiv'])

if todos_cargados:
    # Botón para procesar y validar
    if not st.session_state.data_loaded:
        if st.button("🔄 Procesar y Validar", type="primary", width="stretch"):
            with st.spinner("Analizando y procesando archivos..."):
                try:
                    loader = DataLoader(data_path="data")
                    tipo_df, tipo_map = loader.load_tipo_instrumento()
                    tipos_filtro = loader.get_tipos_filtro(tipo_map)
                    
                    # 1. Obtener DataFrames
                    df_pos = st.session_state.archivos_cargados['posiciones']['df']
                    df_inst = st.session_state.archivos_cargados['instruments']['df']
                    df_alloc_int = st.session_state.archivos_cargados['allocations']['df']
                    df_alloc_ext = st.session_state.archivos_cargados['allocations_refinitiv']['df']
                    
                    # 2. AUTODETECCIÓN DE TIPO ROBUSTA
                    tipo_detectado = "Moneda" # Default
                    
                    if df_alloc_int is not None and not df_alloc_int.empty:
                        # Normalizar columnas para detectar
                        cols_norm = [str(c).upper().strip() for c in df_alloc_int.columns]
                        
                        logger.info(f"Columnas detectadas (norm): {cols_norm}")
                        
                        # Lógica de detección ultra-robusta:
                        # Buscamos "BASE REG" que coincide con "Base Región", "Base Region", "Base RegiÃ³n", etc.
                        
                        tiene_region = any('BASE REG' in c for c in cols_norm)
                        
                        if tiene_region:
                            tipo_detectado = "Región"
                            st.toast("🌍 Validación de REGIONES detectada (Header encontrado)")
                        else:
                            tipo_detectado = "Moneda"
                            st.toast("💰 Validación de MONEDAS detectada")
                    else:
                        st.warning("⚠️ No se cargó Allocation Interno - Asumiendo Moneda")
                        
                    logger.info(f"Tipo de validación final: {tipo_detectado}")
                    
                    # 3. Preparar diccionario 'data' según tipo detectado
                    data = {
                        'posiciones': df_pos,
                        'instrumentos': df_inst,
                        'tipo_instrumento': tipo_df,
                        'tipo_map': tipo_map,
                        'tipos_filtro': tipos_filtro
                    }
                    
                    if tipo_detectado == "Región":
                        # Asignar a slots de región
                        data['allocations_region_interno'] = df_alloc_int
                        data['allocations_region_externo'] = df_alloc_ext
                        # Slots de moneda vacíos
                        data['allocations_interno'] = pd.DataFrame()
                        data['allocations_externo'] = pd.DataFrame()
                    else:
                        # Asignar a slots de moneda
                        data['allocations_interno'] = df_alloc_int
                        data['allocations_externo'] = df_alloc_ext
                        # Slots de región vacíos
                        data['allocations_region_interno'] = pd.DataFrame()
                        data['allocations_region_externo'] = pd.DataFrame()

                    # 4. Guardar en Session State
                    st.session_state.data = data
                    st.session_state.data_loaded = True
                    st.session_state.tipo_validacion_detectado = tipo_detectado
                    
                    # Limpiar resultados previos
                    if 'df_final' in st.session_state: del st.session_state.df_final
                    if 'df_final_moneda' in st.session_state: del st.session_state.df_final_moneda
                    if 'df_final_region' in st.session_state: del st.session_state.df_final_region
                    
                    st.success(f"✅ Datos de {tipo_detectado} procesados exitosamente!")
                    st.balloons()
                    
                    # Redirigir
                    st.switch_page("pages/2_Validacion_Allocations.py")
                    
                except Exception as e:
                    st.error(f"❌ Error al procesar datos: {str(e)}")
                    logger.error(f"Error en carga: {e}", exc_info=True)
    else:
        tipo = st.session_state.get('tipo_validacion_detectado', 'Datos')
        st.info(f"✅ {tipo} cargados en memoria")
        if st.button("🔄 Ir a Validación", type="primary", width="stretch"):
            st.switch_page("pages/2_Validacion_Allocations.py")
else:
    faltantes = []
    for k in ['posiciones', 'instruments', 'allocations', 'allocations_refinitiv']:
        if not st.session_state.archivos_cargados.get(k):
            faltantes.append(k.replace('_', ' ').title())
            
    st.warning(f"⏳ Faltan archivos: {', '.join(faltantes)}")
