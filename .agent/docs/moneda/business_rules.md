# Documentación de Reglas de Negocio

## Lógica de Clasificación de Monedas

### Moneda_Calculada (Moneda Calculada)
**Origen:** Allocations Externos (Refinitiv)  
**Cálculo:**
1. Obtener todas las allocations externas para el instrumento
2. Encontrar el porcentaje máximo entre todas las monedas
3. **Si el porcentaje máximo >= 90%**: Clasificar como esa moneda específica
4. **Si el porcentaje máximo < 90%**: Clasificar como "balanceado"

**Código de Referencia:** `src/pipeline.py` líneas 464-473

**Ejemplo:**
- USD: 92%, CLP: 5%, EUR: 3% → `Moneda_Calculada = "USD"` (USD >= 90%)
- USD: 85%, CLP: 10%, EUR: 5% → `Moneda_Calculada = "balanceado"` (ninguna >= 90%)
- CLP: 70%, USD: 20%, EUR: 10% → `Moneda_Calculada = "balanceado"` (ninguna >= 90%)

### Moneda_Antigua (Moneda Dominante Interna)
**Origen:** Allocations Internos  
**Cálculo:**
1. Obtener todas las allocations internas para el instrumento
2. Encontrar el porcentaje máximo entre todas las monedas
3. **Si el porcentaje máximo >= 90%**: Usar esa moneda
4. **Si el porcentaje máximo < 90%**: Usar "balanceado"

**Código de Referencia:** `src/pipeline.py` líneas 617-624

---

## Lógica de Flag (Semáforo)

**Propósito:** Validar la calidad de cobertura de allocations  
**Basado en:** `Total_Pct_Ext` (suma de porcentajes de allocations externas)

**Reglas:**
- **60% - 120%** → `VALIDO` (verde)
- **40% - 60%** O **> 120%** → `REVISION` (amarillo)
- **< 40%** → `ERROR` (rojo)

**Código de Referencia:** `src/pipeline.py` líneas 698-709

**Justificación:**
- 60-120%: Buena cobertura (permite redondeo/problemas de calidad de datos)
- 40-60% o >120%: Necesita revisión (datos incompletos o duplicados)
- <40%: Error crítico (datos insuficientes)

---

## Escalado Proporcional de Allocations

**Propósito:** Normalizar los porcentajes de allocations externas para que sumen exactamente 100%

**Cuándo se aplica:**
- Solo para instrumentos con `Flag != 'ERROR'`
- Después de calcular el Flag
- Antes de generar los exports

**Lógica:**
1. Calcular suma actual de porcentajes por instrumento: `suma_actual = Σ percentage_num`
2. Calcular factor de escalado: `factor = 100 / suma_actual`
3. Aplicar escalado proporcional: `percentage_escalado = percentage_num × factor`

**Ejemplo:**
```
Instrumento: ABC123
Allocations originales:
  - USD: 50%
  - CLP: 30%
  - EUR: 15%
  - Total: 95%

Factor de escalado: 100 / 95 = 1.0526

Allocations escaladas:
  - USD: 50 × 1.0526 = 52.63%
  - CLP: 30 × 1.0526 = 31.58%
  - EUR: 15 × 1.0526 = 15.79%
  - Total: 100.00%
```

**Características:**
- ✅ Mantiene proporciones relativas entre monedas
- ✅ Resultado siempre suma 100%
- ✅ No afecta instrumentos con Flag = 'ERROR'
- ✅ Preserva la clasificación (balanceado/no balanceado)

**Código de Referencia:** `src/pipeline.py` (similar a pipeline_region)

---

## Cálculo de Fecha de Export

**Para Validación de Moneda:**
- **Si `Moneda:` = "FALTA ALLOCATION"**: `Fecha = "31-12-2019"`
- **Caso contrario**: `Fecha = "01-01-2026"`
- Formato: DD-MM-YYYY

**Para Validación de Región:**
- `Fecha` = Valor de la columna `F. Proceso` (fecha original del proceso)

**Código de Referencia:** `pages/2_Validacion_Allocations.py` líneas 320-335

**Nota:** La lógica de fecha para monedas no usa el último día del mes anterior, sino valores fijos según el estado de allocation.

---

## Campo de Clasificación en Export

**Para Validación de Moneda:**
- `Clasificacion` = Texto literal "SubMoneda"

**Para Validación de Región:**
- `Clasificacion` = Valor de la columna `Tipo_Nombre`

**Código de Referencia:** `pages/2_Validacion_Allocations.py` líneas 337-352

---

## División de Exports: Balanceado / No Balanceado / Sin Datos

**Criterio de División:** Valor de `Moneda_Calculada`

> [!IMPORTANT]
> Los instrumentos se dividen en **3 categorías** para exports:
> 1. **Balanceados** - Diversificados entre monedas
> 2. **No Balanceados** - Moneda específica dominante
> 3. **Sin Datos** - No encontrados en Refinitiv

### 1. Instrumentos Balanceados
- **Condición:** `Moneda_Calculada == "balanceado"`
- **Significado:** Ninguna moneda supera el 90%
- **Export:** Formato completo con todas las columnas de monedas
- **Archivo:** `Balanceados_Moneda.xlsx`

### 2. Instrumentos No Balanceados
- **Condición:** `Moneda_Calculada != "balanceado"` Y `Moneda_Calculada != "Sin Datos"`
- **Significado:** Una moneda específica domina (>= 90%)
- **Export:** Formato simple de 5 columnas
- **Archivo:** `No_Balanceados_Moneda.xlsx`

### 3. Instrumentos Sin Datos
- **Condición:** `Moneda_Calculada == "Sin Datos"`
- **Significado:** Instrumento no encontrado en Refinitiv (allocations externas)
- **Export:** Formato mínimo de 5 columnas
- **Archivo:** `Sin_Datos_Moneda.xlsx`
- **Columnas:**
  - `ID`: Identificador interno
  - `Nombre`: Nombre del instrumento
  - `Id_ti_valor`: Valor del identificador (RIC o ISIN)
  - `Id_ti`: Tipo de identificador
  - `Moneda_Calculada`: "Sin Datos"

---

## Columna "Sobreescribir" en Exports

**Propósito:** Indicar si los datos del instrumento deben actualizarse en la base de datos.

**Valores:**
- `"y"` (yes): El instrumento DEBE actualizarse en la base de datos
- `"n"` (no): El instrumento NO debe actualizarse en la base de datos

**Lógica de Asignación:**
```python
if Flag == "ERROR":
    Sobreescribir = "n"  # NO actualizar instrumentos con errores
else:
    Sobreescribir = "y"  # Actualizar todos los demás (VALIDO, REVISION)
```

**Aplicación:**
- ✅ Export de **Balanceados**: Incluye columna Sobreescribir
- ✅ Export de **No Balanceados**: Incluye columna Sobreescribir
- ❌ Export de **Sin Datos**: NO incluye (son instrumentos sin información de Refinitiv)

**Justificación:**
- Instrumentos con `Flag = "ERROR"` tienen datos inconsistentes o incompletos
- No deben actualizarse automáticamente en la base de datos
- Requieren revisión manual antes de cualquier actualización
- Instrumentos con `Flag = "VALIDO"` o `"REVISION"` pueden actualizarse de forma segura

**Código de Referencia:** `pages/2_Validacion_Allocations.py` función `preparar_dataframe_exportacion`

---

## División Balanceado vs No Balanceado

**Criterio:** Basado SOLO en la columna `Moneda_Calculada`

### Balanceados
- **Filtro:** `Moneda_Calculada == "balanceado"`
- **Formato de Export:** Formato completo con todas las columnas de allocations
- **Propósito:** Actualizar base de datos con instrumentos clasificados como balanceados
- **Columnas:** ID, Id_ti_valor, Id_ti, Fecha, Clasificacion, moneda_antigua, Flag, Inconsistencia, + todas las columnas de monedas (USD, CLP, EUR, etc.)

**Código de Referencia:** `pages/2_Validacion_Allocations.py` líneas 528-530

### No Balanceados  
- **Filtro:** `Moneda_Calculada != "balanceado"` (tiene moneda específica)
- **Formato de Export:** Formato simple de 5 columnas
- **Propósito:** Actualizar base de datos con la nueva clasificación de moneda específica
- **Columnas:**
  - `ID`: Identificador interno
  - `Instrumento`: Nombre del instrumento
  - `SubMoneda`: Valor **NUEVO** (de `Moneda_Calculada`)
  - `Moneda_Anterior`: Valor **VIEJO** (de allocations internas)
  - `Inconsistencia`: Detalle del error o vacío

**Código de Referencia:** `pages/2_Validacion_Allocations.py` líneas 562-565

---

## Reglas de Id_ti e Id_ti_valor

**Propósito:** Mostrar qué identificador se usó para cruzar datos de Refinitiv con el maestro

**Reglas:**
1. Usar el campo `matched_by` del cruce de allocations
2. Si el match fue por RIC: `Id_ti = "RIC"`, `Id_ti_valor = <código RIC>`
3. Si el match fue por ISIN: `Id_ti = "Isin"`, `Id_ti_valor = <código ISIN>`
4. **NUNCA usar Cusip** en estas columnas de export (incluso si el match fue por Cusip, hacer fallback a RIC/ISIN)

**Código de Referencia:** `pages/2_Validacion_Allocations.py` líneas 363-398

**Justificación:** Estos exports actualizan la base de datos, y la base de datos solo acepta identificadores RIC o ISIN para el matching con Refinitiv.

---

## Columna Inconsistencia

**Origen:** Combina `Detalle_Inconsistencia` y `Detalle_Validacion`  
**Lógica:**
- Para validación de Moneda: Usar `Detalle_Inconsistencia`
- Para validación de Región: Usar `Detalle_Validacion`
- Muestra mensaje de error detallado si la validación falla
- Vacío si no hay inconsistencia

**Código de Referencia:** `pages/2_Validacion_Allocations.py` líneas 414-434

**Valores Comunes:**
- "Definido como BALANCEADO pero USD domina con 92.0%"
- "Definido como USD pero es balanceado (máx 85.0%)"
- "Definido como USD pero CLP domina con 91.0%"
- String vacío (sin error)

---

## Detección de Inconsistencias (Validación Interna)

**Casos de Inconsistencia:**

1. **BALANCEADO sin allocations:**
   - `SubMoneda = "BALANCEADO"` pero no hay allocations internas
   - Mensaje: "Definido como BALANCEADO pero no tiene allocations internas"

2. **BALANCEADO pero dominante:**
   - `SubMoneda = "BALANCEADO"` pero una moneda >= 90%
   - Mensaje: "Definido como BALANCEADO pero {moneda} domina con {%}"

3. **Moneda específica pero balanceado:**
   - `SubMoneda = {moneda}` pero ninguna moneda >= 90%
   - Mensaje: "Definido como {moneda} pero es balanceado (máx {%})"

4. **Moneda incorrecta:**
   - `SubMoneda = {moneda_A}` pero `{moneda_B}` >= 90%
   - Mensaje: "Definido como {moneda_A} pero {moneda_B} domina con {%}"

**Código de Referencia:** `src/pipeline.py` líneas 604-663

---

## Normalización de Monedas

**Refinitiv → Códigos ISO:**
- "US Dollar" → "USD"
- "Chilean Peso" → "CLP"  
- "Euro" → "EUR"
- "British Pound" → "GBP"
- "Japanese Yen" → "JPY"
- etc.

**Mapeo:** Definido en `src/currency_mapping.py`  
**Propósito:** Asegurar consistencia entre nombres de Refinitiv y códigos internos

**Código de Referencia:** `src/currency_mapping.py`
