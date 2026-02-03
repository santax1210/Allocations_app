# Scripts de Verificación y Testing

Este directorio contiene scripts para verificar el funcionamiento de la aplicación sin necesidad de correr Streamlit.

## Estructura

```
tests/
├── README.md                    # Este archivo
├── test_mappings.py            # Verifica mapeos de monedas y regiones
├── test_data_loading.py        # Verifica carga de archivos
├── test_pipeline_moneda.py     # Prueba pipeline de moneda
├── test_pipeline_region.py     # Prueba pipeline de región
└── test_inconsistencies.py     # Verifica detección de inconsistencias
```

## Uso

Ejecutar todos los tests:
```bash
python -m pytest tests/
```

Ejecutar un test específico:
```bash
python tests/test_mappings.py
```

## Tests Disponibles

### 1. `test_mappings.py`
Verifica que todos los mapeos estén completos:
- ✓ Todas las monedas de Refinitiv tienen mapeo
- ✓ Todas las regiones de Refinitiv tienen mapeo
- ✓ No hay duplicados en los diccionarios

### 2. `test_data_loading.py`
Verifica que los archivos de datos se carguen correctamente:
- ✓ Archivos existen
- ✓ Columnas requeridas presentes
- ✓ Tipos de datos correctos
- ✓ No hay filas completamente vacías

### 3. `test_pipeline_moneda.py`
Prueba el pipeline de moneda con datos de ejemplo:
- ✓ Matching de instrumentos funciona
- ✓ Cálculo de moneda dominante correcto
- ✓ Detección de inconsistencias funciona
- ✓ Escalado proporcional suma 100%

### 4. `test_pipeline_region.py`
Prueba el pipeline de región con datos de ejemplo:
- ✓ Matching de instrumentos funciona
- ✓ Mapeo de regiones correcto
- ✓ Cálculo de región dominante correcto
- ✓ Detección de inconsistencias funciona

### 5. `test_inconsistencies.py`
Verifica la lógica de detección de inconsistencias:
- ✓ Caso 1: BALANCEADO sin allocations
- ✓ Caso 2: BALANCEADO pero dominante
- ✓ Caso 3: Específico pero balanceado
- ✓ Caso 4: Específico incorrecto
