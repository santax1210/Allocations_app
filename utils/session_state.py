"""
Gestión centralizada del session state de Streamlit.
"""
import streamlit as st

def init_session_state():
    """Inicializa todas las variables de session state necesarias."""
    
    if 'validaciones' not in st.session_state:
        st.session_state.validaciones = {}  # {id_activo: 'aprobado'|'rechazado'|'saltado'}
    
    if 'comentarios' not in st.session_state:
        st.session_state.comentarios = {}  # {id_activo: 'comentario'}
    
    if 'seleccionados' not in st.session_state:
        st.session_state.seleccionados = []  # [id_activo1, id_activo2, ...]
    
    if 'archivos_cargados' not in st.session_state:
        st.session_state.archivos_cargados = {
            'allocations': None,  # {'df': DataFrame, 'nombre': str}
            'instruments': None,
            'allocations_refinitiv': None,
            'posiciones': None
        }
    
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False

def reset_validation_state():
    """Resetea el estado de validación cuando se cargan nuevos datos."""
    st.session_state.validaciones = {}
    st.session_state.comentarios = {}
    st.session_state.seleccionados = []
    st.session_state.data_loaded = False
