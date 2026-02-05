"""
Módulo para cargar todos los archivos de entrada del pipeline de conciliación.
"""
import pandas as pd
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class DataLoader:
    """Carga y prepara los archivos de entrada necesarios para el pipeline."""
    
    def __init__(self, data_path: str = "data"):
        self.data_path = Path(data_path)
        
    def load_posiciones_valorizadas(self, filepath: Optional[str] = None) -> pd.DataFrame:
        """
        Carga el archivo de Posiciones Valorizadas.
        
        Columnas clave:
        - Id_ti_valor: Identificador del instrumento
        - F. Proceso: Fecha de proceso (para filtrar >= 2025-01-01)
        - Cliente, Grupo, Activo, Cantidad, Monto (CLP), etc.
        """
        if filepath is None:
            filepath = self.data_path / "posiciones_2025-11-30_sistema.csv"
        
        logger.info(f"Cargando Posiciones Valorizadas desde: {filepath}")
        
        df = pd.read_csv(filepath, sep=';', encoding='latin-1')
        
        # Convertir F. Proceso a datetime
        df['F. Proceso'] = pd.to_datetime(df['F. Proceso'], errors='coerce')
        
        logger.info(f"Posiciones cargadas: {len(df)} registros")
        return df
    
    def load_instrumentos_internos(self, filepath: Optional[str] = None) -> pd.DataFrame:
        """
        Carga el catálogo maestro de Instrumentos Internos.
        
        Columnas clave:
        - ID: Identificador único interno
        - Isin, RIC, Cusip, Ticker_BB: Identificadores externos
        - Tipo instrumento: Código del tipo (C01, C02, etc.)
        - SubMoneda: Indica si es "balanceado" o una moneda específica
        - Moneda: CLP, USD, EUR, etc.
        """
        if filepath is None:
            filepath = self.data_path / "instruments.csv"
        
        logger.info(f"Cargando Instrumentos Internos desde: {filepath}")
        
        df = pd.read_csv(filepath, sep=';', encoding='latin-1')
        
        logger.info(f"Instrumentos internos cargados: {len(df)} registros")
        return df
    
    def load_tipo_instrumento(self, filepath: Optional[str] = None) -> pd.DataFrame:
        """
        Carga el diccionario de Tipos de Instrumento.
        
        Columnas:
        - Id: ID del tipo
        - Nombre: Nombre descriptivo (Acciones, Bonos, etc.)
        - Código: Código tipo (C01, C02, etc.)
        """
        if filepath is None:
            filepath = self.data_path / "instrument-types-2025-08-28.csv"
        
        logger.info(f"Cargando Tipos de Instrumento desde: {filepath}")
        
        df = pd.read_csv(filepath, sep=',', encoding='utf-8')
        
        # Crear diccionario de mapeo Código -> Nombre
        tipo_map = dict(zip(df['Código'], df['Nombre']))
        
        logger.info(f"Tipos de instrumento cargados: {len(df)} tipos")
        return df, tipo_map
    
    def load_allocations_interno(self, filepath: Optional[str] = None) -> pd.DataFrame:
        """
        Carga los datos de Allocations Internos.
        
        Estructura:
        - Columnas identificadoras: ID, Nombre, Isin, Cusip, RIC, etc.
        - Columnas de monedas: USD, EUR, CLP, etc. (cada una con su porcentaje)
        
        Returns:
            DataFrame en formato largo (una fila por instrumento-moneda)
        """
        if filepath is None:
            filepath = self.data_path / "allocations_currency.csv"
        
        logger.info(f"Cargando Allocations Internos desde: {filepath}")
        
        # Leer con manejo de errores para columnas inconsistentes
        df = pd.read_csv(
            filepath, 
            sep=';', 
            encoding='latin-1',
            on_bad_lines='skip',  # Saltar líneas con problemas
            engine='python'  # Motor más tolerante
        )
        
        # Columnas identificadoras
        id_cols = ['ID', 'Nombre', 'Isin', 'Cusip', 'RIC', 'Nemo']
        
        # Columnas de monedas (todas las que no son identificadoras ni metadatos)
        exclude_cols = ['ID', 'Nombre', 'Creado', 'Tipo Instrumento', 'Moneda', 'Nemo', 
                       'Isin', 'Cusip', 'Ticker_BB', 'Currency', 'RIC', 'Moneda:']
        currency_cols = [col for col in df.columns if col not in exclude_cols and col.strip() != '']
        
        # Transformar a formato largo
        df_long = df.melt(
            id_vars=['ID', 'Nombre', 'Isin', 'Cusip', 'RIC'],
            value_vars=currency_cols,
            var_name='currency_code',
            value_name='percentage_num'
        )
        
        # Eliminar filas sin porcentaje o con NaN
        df_long = df_long[df_long['percentage_num'].notna()].copy()
        df_long = df_long[df_long['percentage_num'] > 0].copy()
        
        # Convertir porcentaje a numérico
        df_long['percentage_num'] = pd.to_numeric(df_long['percentage_num'], errors='coerce')
        
        # Eliminar filas donde la conversión falló
        df_long = df_long[df_long['percentage_num'].notna()].copy()
        
        logger.info(f"Allocations internos cargados: {len(df_long)} registros de currency allocation")
        return df_long
    
    def load_allocations_externo(self, filepath: Optional[str] = None) -> pd.DataFrame:
        """
        Carga los datos de Allocations Externos (Refinitiv/FIRSTRATE).
        
        Columnas:
        - instrument: Identificador del instrumento (Cusip, LP code, etc.)
        - date: Fecha de los datos
        - class: Tipo de allocation (currency, country, sector, etc.)
        - percentage: Porcentaje de allocation
        - Columna Fuente: FundCurrencyAllocation, FundCountryAllocation, etc.
        - classif: Clasificación (currency, country, etc.)
        """
        if filepath is None:
            filepath = self.data_path / "raw_output_FIRSTRATE_instruments (2).csv"
        
        logger.info(f"Cargando Allocations Externos desde: {filepath}")
        
        df = pd.read_csv(filepath, sep=';', encoding='latin-1')
        # Eliminar filas donde instrument está presente pero date, class o percentage están vacíos, nulos o <NA>
        df = df[~(
            df['instrument'].notna() & (
                df['date'].isna() | (df['date'].astype(str).str.strip() == '') |
                df['class'].isna() | (df['class'].astype(str).str.strip() == '') |
                df['percentage'].isna() | (df['percentage'].astype(str).str.strip() == '') |
                (df['percentage'].astype(str).str.upper() == '<NA>')
            )
        )]
        # Convertir date a datetime
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        # Filtrar solo FundCurrencyAllocation
        df_currency = df[df['Columna Fuente'] == 'FundCurrencyAllocation'].copy()
        logger.info(f"Allocations externos cargados: {len(df_currency)} registros de currency allocation")
        return df_currency
    
    def get_tipos_filtro(self, tipo_map: Dict[str, str]) -> list:
        """
        Retorna la lista de códigos de tipo de instrumento para filtrar.
        
        Incluye:
        - Acciones: C02 (Acciones), C14 (Acciones Pref.)
        - Bonos: C04 (Bonos)
        - Fondos/ETF: C03 (Fondos Mutuos), C09 (ETF), C10 (Fondos de Inversión)
        """
        tipos_incluir = [
            'C02',  # Acciones
            'C14',  # Acciones Pref.
            'C04',  # Bonos
            'C03',  # Fondos Mutuos
            'C09',  # ETF
            'C10',  # Fondos de Inversión
        ]
        
        # Validar que existan en el tipo_map
        tipos_validos = [t for t in tipos_incluir if t in tipo_map]
        
        logger.info(f"Tipos de instrumento a filtrar: {tipos_validos}")
        return tipos_validos
    
    def load_all(self) -> Dict[str, pd.DataFrame]:
        """
        Carga todos los archivos necesarios y retorna un diccionario.
        
        Returns:
            dict con keys: 'posiciones', 'instrumentos', 'tipo_instrumento', 
                          'tipo_map', 'allocations_externo', 'allocations_interno', 'tipos_filtro'
        """
        tipo_df, tipo_map = self.load_tipo_instrumento()
        
        data = {
            'posiciones': self.load_posiciones_valorizadas(),
            'instrumentos': self.load_instrumentos_internos(),
            'tipo_instrumento': tipo_df,
            'tipo_map': tipo_map,
            'allocations_externo': self.load_allocations_externo(),
            'allocations_interno': self.load_allocations_interno(),
            'tipos_filtro': self.get_tipos_filtro(tipo_map)
        }
        
        logger.info("Todos los archivos cargados exitosamente")
        return data
