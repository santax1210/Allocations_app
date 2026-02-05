import logging
import sys
import pandas as pd
from pathlib import Path

# Agregar directorios al path para importar módulos locales
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / 'src'))
sys.path.insert(0, str(BASE_DIR / 'utils'))

from src.pipeline import ConciliacionPipeline
from src.data_loader import DataLoader
from utils.logging_utils import log_df_status

# Configurar logging detallado
LOG_FILE = "pipeline_debug.log"

# Limpiar log anterior limpiando el archivo
with open(LOG_FILE, 'w') as f:
    f.write('')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("debug_runner")

def run_debug():
    logger.info("="*80)
    logger.info("INICIANDO DEBUGGING EXTENDIDO DEL PIPELINE")
    logger.info("="*80)
    
    try:
        # 1. Cargar Datos
        loader = DataLoader(data_path=str(BASE_DIR / 'data'))
        logger.info("Cargando datos usando DataLoader...")
        data = loader.load_all()
        
        # Log del estado inicial de los datos cargados
        for key, df in data.items():
            if isinstance(df, pd.DataFrame):
                log_df_status(logger, df, f"DATOS ENTRADA: {key}")
        
        # 2. Inicializar Pipeline
        logger.info("Inicializando ConciliacionPipeline...")
        pipeline = ConciliacionPipeline(data)
        
        # 3. Ejecutar Pipeline
        logger.info("Ejecutando pipeline completo...")
        df_final, stats = pipeline.ejecutar_pipeline_completo()
        
        # 4. Validar Resultado Final
        logger.info("="*80)
        logger.info("RESULTADO FINAL")
        log_df_status(logger, df_final, "DF_FINAL (Salida Pipeline)")
        
        if df_final.empty:
            logger.error("\n[CRITICO] El pipeline retornó un DataFrame vacío!!")
            sys.exit(1)
            
        logger.info(f"\nEstadísticas Finales: {stats}")
        logger.info(f"\nLOG COMPLETO GUARDADO EN: {LOG_FILE}")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"Excepción no controlada durante el debug: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    run_debug()
