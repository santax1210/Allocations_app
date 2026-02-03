"""
Página principal - Dashboard Overview.
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import logging

# Agregar directorios al path
sys.path.insert(0, str(Path(__file__).parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent / 'utils'))

from session_state import init_session_state
from data_loader import DataLoader
from pipeline import ConciliacionPipeline

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de página
st.set_page_config(
    page_title="Refinitiv Automation",
    page_icon="💱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar session state
init_session_state()

# Header
st.markdown("""
<h1 style='text-align: left; color: #ffffff; font-size: 2.5rem; margin-bottom: 0.5rem;'>Refinitiv Automation</h1>
<div style='width: 100%; height: 3px; background: linear-gradient(90deg, #1e88e5 0%, #ff6f00 50%, #1e88e5 100%); margin-bottom: 1.5rem; border-radius: 2px;'></div>
""", unsafe_allow_html=True)

# Estilos CSS con tema oscuro gradiente
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

/* Card container */
.card {
    background-color: #1e293b;
    border: 1px solid #475569;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
}

.metric-card {
    background-color: #1e293b;
    border: 1px solid #475569;
    border-radius: 6px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
}

.metric-card h3 {
    margin: 0;
    font-size: 2rem;
    color: #e0e0e0;
}

.metric-card p {
    margin: 5px 0 0 0;
    color: #a0a0a0;
    font-size: 0.9rem;
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
</style>
""", unsafe_allow_html=True)

# Verificar estado de archivos
todos_cargados = all(st.session_state.archivos_cargados.values())

if not todos_cargados:
    st.info("📁 Para comenzar, ve a **Carga de Archivos** en el menú lateral")
    
    # Mostrar estado de archivos
    st.markdown("### 📋 Estado de Carga")
    
    for tipo, path in st.session_state.archivos_cargados.items():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**{tipo.replace('_', ' ').title()}**")
        with col2:
            if path:
                st.success("✅ Cargado")
            else:
                st.warning("⏳ Pendiente")
else:
    # Todos los archivos cargados
    st.success("✅ Todos los archivos cargados correctamente")
    
    # Mostrar resumen
    st.markdown("### 📋 Archivos Cargados")
    for tipo, path in st.session_state.archivos_cargados.items():
        st.write(f"**{tipo.replace('_', ' ').title()}**: `{Path(path).name}`")
    
    st.markdown("---")
    
    # Información sobre el siguiente paso
    if not st.session_state.data_loaded:
        st.info("🚀 Los archivos están listos. Ve a **Carga de Archivos** y presiona **Validar Allocations** para procesarlos.")
    else:
        st.success("✅ Datos ya procesados - Ve a **Validación de Allocations** para revisar")
        
        # Métricas principales
        if 'df_final' in st.session_state and not st.session_state.df_final.empty:
            df = st.session_state.df_final
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class='metric-card'>
                    <h3>{len(df)}</h3>
                    <p>Instrumentos</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                anomalias = df['es_anomalia'].sum() if 'es_anomalia' in df.columns else 0
                st.markdown(f"""
                <div class='metric-card'>
                    <h3>{anomalias}</h3>
                    <p>Anomalías ML</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                validados = len([v for v in st.session_state.validaciones.values() if v == 'aprobado'])
                st.markdown(f"""
                <div class='metric-card'>
                    <h3>{validados}</h3>
                    <p>Aprobados</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                rechazados = len([v for v in st.session_state.validaciones.values() if v == 'rechazado'])
                st.markdown(f"""
                <div class='metric-card'>
                    <h3>{rechazados}</h3>
                    <p>Rechazados</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Botón para reprocesar
        if st.button("🔄 Reprocesar Datos", type="secondary"):
            st.session_state.data_loaded = False
            st.rerun()
