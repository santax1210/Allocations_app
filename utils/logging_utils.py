import logging
import pandas as pd
import io

def log_df_status(logger: logging.Logger, df: pd.DataFrame, name: str, max_rows: int = 5):
    """
    Loggea el estado de un DataFrame: dimensiones, columnas y muestra de datos.
    
    Args:
        logger: Logger instance to write to
        df: DataFrame to inspect
        name: Name of the step or DataFrame for context
        max_rows: Number of rows to show in the sample
    """
    if df is None:
        logger.warning(f"[{name}] DataFrame es None")
        return
        
    if df.empty:
        logger.warning(f"[{name}] DataFrame está vacío (0 filas)")
        logger.info(f"[{name}] Columnas: {list(df.columns)}")
        return

    # Log dimensiones
    logger.info(f"[{name}] Shape: {df.shape} (Filas: {len(df)}, Cols: {len(df.columns)})")
    
    # Log columnas y tipos
    # Capture info() output
    buffer = io.StringIO()
    df.info(buf=buffer, verbose=False, memory_usage="deep")
    info_str = buffer.getvalue().split('\n')[0] # First line usually has class info
    memory_line = [line for line in buffer.getvalue().split('\n') if 'memory usage' in line]
    memory_usage = memory_line[0] if memory_line else "Unknown memory"
    
    logger.info(f"[{name}] Info: {info_str} | {memory_usage}")
    
    # Log muestra de datos en formato tabla
    try:
        # Convertir a string con tabulate o to_string para que se vea alineado en el log
        sample = df.head(max_rows).to_string()
        logger.info(f"[{name}] Primeras {max_rows} filas:\n{sample}")
    except Exception as e:
        logger.error(f"[{name}] Error al imprimir muestra de datos: {e}")

    # Log estadisticas basicas de columnas clave si existen
    key_cols = ['ID', 'Instrumento', 'Moneda_Calculada', 'Flag', 'Estado']
    present_keys = [c for c in key_cols if c in df.columns]
    if present_keys:
        logger.info(f"[{name}] Valores únicos en claves: { {k: df[k].nunique() for k in present_keys} }")
