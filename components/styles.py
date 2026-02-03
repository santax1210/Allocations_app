"""
Estilos CSS centralizados para la aplicación.
"""
import streamlit as st

def apply_common_styles():
    """Aplica estilos CSS comunes a toda la aplicación."""
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
    
    /* Header personalizado */
    .app-header {
        text-align: left;
        color: #ffffff;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        font-weight: 700;
    }
    
    .app-divider {
        width: 100%;
        height: 3px;
        background: linear-gradient(90deg, #1e88e5 0%, #ff6f00 50%, #1e88e5 100%);
        margin-bottom: 1.5rem;
        border-radius: 2px;
    }
    
    /* Tabs personalizados */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        margin-bottom: 1rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-size: 1.2rem !important;
        font-weight: 700 !important;
        padding: 14px 28px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.8rem;
        margin: 2px;
    }
    
    .badge-success {
        background-color: #d1fae5;
        color: #065f46;
    }
    
    .badge-warning {
        background-color: #fef3c7;
        color: #92400e;
    }
    
    .badge-danger {
        background-color: #fee2e2;
        color: #991b1b;
    }
    
    .badge-info {
        background-color: #dbeafe;
        color: #1e40af;
    }
    
    /* Cards */
    .metric-card {
        background-color: #1e293b;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        margin: 10px 0;
        border: 1px solid #475569;
    }
    
    .metric-title {
        font-size: 0.9rem;
        color: #a0a0a0;
        margin-bottom: 8px;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #e0e0e0;
    }
    
    /* File upload area */
    .upload-area {
        border: 2px dashed #64748b;
        border-radius: 10px;
        padding: 30px;
        text-align: center;
        background-color: #1e293b;
        margin: 20px 0;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .upload-area:hover {
        border-color: #3b82f6;
        background-color: #334155;
    }
    
    .upload-area-success {
        border: 2px solid #10b981 !important;
        border-radius: 10px;
        padding: 30px;
        text-align: center;
        background-color: #064e3b !important;
        margin: 20px 0;
        transition: all 0.3s ease;
    }
    
    /* Estilos para file uploader */
    div[data-testid="stFileUploader"] {
        border: 2px dashed #64748b;
        border-radius: 10px;
        padding: 20px;
        background-color: #e2e8f0;
        transition: all 0.3s ease;
    }
    
    div[data-testid="stFileUploader"]:hover {
        border-color: #3b82f6;
        background-color: #cbd5e1;
    }
    
    /* Cuando hay archivo cargado, poner en verde */
    div[data-testid="stFileUploader"]:has(button[kind="primary"]) {
        border: 2px solid #10b981 !important;
        background-color: #d1fae5 !important;
    }
    
    div[data-testid="stFileUploader"] section {
        border: none !important;
        background: transparent !important;
    }
    
    /* Texto dentro del file uploader en negro para visibilidad */
    div[data-testid="stFileUploader"] label {
        font-size: 1.1rem !important;
        color: #1f2937 !important;
        font-weight: 600 !important;
    }
    
    div[data-testid="stFileUploader"] small {
        color: #374151 !important;
    }
    
    div[data-testid="stFileUploader"] span {
        color: #1f2937 !important;
    }
    
    .upload-icon {
        font-size: 3rem;
        color: #1f2937;
        margin-bottom: 10px;
    }
    
    .upload-text {
        color: #1f2937;
        font-size: 1.1rem;
        margin-bottom: 5px;
    }
    
    .upload-subtext {
        color: #374151;
        font-size: 0.9rem;
    }
    
    /* Success/Error messages */
    .success-box {
        background-color: #064e3b;
        border-left: 4px solid #10b981;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
        color: #a7f3d0;
    }
    
    .error-box {
        background-color: #450a0a;
        border-left: 4px solid #ef4444;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
        color: #fca5a5;
    }
    
    /* Progress bar */
    .progress-container {
        background-color: #1e293b;
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        border: 1px solid #475569;
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
    </style>
    """, unsafe_allow_html=True)

def render_header(title: str, subtitle: str = ""):
    """Renderiza el header de la aplicación."""
    st.markdown(f"""
    <h1 class='app-header'>{title}</h1>
    <div class='app-divider'></div>
    """, unsafe_allow_html=True)
    
    if subtitle:
        st.markdown(f"<p style='color: #cbd5e1; font-size: 1.1rem; margin-bottom: 2rem;'>{subtitle}</p>", 
                   unsafe_allow_html=True)
