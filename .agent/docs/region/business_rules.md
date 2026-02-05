# Documentación de Reglas de Negocio - Validación de Regiones

> [!IMPORTANT]
> **Esta documentación es EXCLUSIVA para Validación de Regiones.**  
> **NO confundir con la validación de Monedas** (ver `../moneda/business_rules.md`)

---

## Lógica de Clasificación de Regiones

### Region_Calculada (Región Calculada)
**Origen:** Allocations Externos (Refinitiv)  
**Cálculo:**
1. Obtener todas las allocations externas para el instrumento
2. Encontrar el porcentaje máximo entre todas las regiones
3. **Si el porcentaje máximo >= 90%**: Clasificar como esa región específica
4. **Si el porcentaje máximo < 90%**: Clasificar como "balanceado"

**Código de Referencia:** `src/pipeline_region.py` (lógica similar a monedas)

**Ejemplo:**
- Norteamérica: 92%, LATAM: 5%, Europa: 3% → `Region_Calculada = "Norteamérica"` (Norteamérica >= 90%)
- Norteamérica: 85%, LATAM: 10%, Europa: 5% → `Region_Calculada = "balanceado"` (ninguna >= 90%)
- LATAM: 70%, Asia: 20%, Europa: 10% → `Region_Calculada = "balanceado"` (ninguna >= 90%)

### Region_Antigua (Región Dominante Interna)
**Origen:** Allocations Internos  
**Cálculo:**
1. Obtener todas las allocations internas para el instrumento
2. Encontrar el porcentaje máximo entre todas las regiones
3. **Si el porcentaje máximo >= 90%**: Usar esa región
4. **Si el porcentaje máximo < 90%**: Usar "balanceado"

**Código de Referencia:** `src/pipeline_region.py` (lógica similar a monedas)

---

## Lógica de Flag (Semáforo)

**Propósito:** Identificar el tipo de cambio entre la región anterior y la calculada.
**Basado en:** Comparación entre `Region_Anterior` y `Region_Calculada`.

**Reglas:**
(Ver definición detallada de Casos abajo)

**Casos de Flag (Semáforo de Cambio):**

**A. Contexto Balanceados (`Region_Calculada` == "balanceado"):**
- **Caso 1 (Confirmación):** `Region_Anterior` era "balanceado" -> Sigue "balanceado". (Sin cambio).
- **Caso 2 (Cambio a Balanceado):** `Region_Anterior` era una Región Específica -> Ahora es "balanceado".
- **Caso 3 (Inconsistencia Histórica):** `Region_Anterior` era "balanceado" pero `Base Región` dice "FALTA ALLOCATION".

**B. Contexto No Balanceados (`Region_Calculada` != "balanceado"):**
- **Caso 1 (Confirmación):** `Region_Anterior` era misma Región A -> Sigue Región A. (Sin cambio).
- **Caso 2 (Cambio a Región):** `Region_Anterior` era "balanceado" -> Ahora es Región Específica.
- **Caso 3 (Cambio de Región):** `Region_Anterior` era Región A -> Ahora es Región B.

**Justificación:**

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
  - LATAM: 45%
  - ASIA: 30%
  - EUROPA: 20%
  - Total: 95%

Factor de escalado: 100 / 95 = 1.0526

Allocations escaladas:
  - LATAM: 45 × 1.0526 = 47.37%
  - ASIA: 30 × 1.0526 = 31.58%
  - EUROPA: 20 × 1.0526 = 21.05%
  - Total: 100.00%
```

**Características:**
- ✅ Mantiene proporciones relativas entre regiones
- ✅ Resultado siempre suma 100%
- ✅ No afecta instrumentos con Flag = 'ERROR'
- ✅ Preserva la clasificación (balanceado/no balanceado)

**Código de Referencia:** `src/pipeline_region.py` paso_7_escalar_allocations

---

## Cálculo de Fecha de Export

**Para Validación de Región:**
- **Si `Base Región:` = "FALTA ALLOCATION"**: `Fecha = "31-12-2019"`
- **Caso contrario**: `Fecha = "01-01-2026"`
- Formato: DD-MM-YYYY

**Código de Referencia:** Similar a `pages/2_Validacion_Allocations.py` pero adaptado para región

**Nota:** La lógica de fecha para regiones no usa el último día del mes anterior, sino valores fijos según el estado de allocation.

---

## Campo de Clasificación en Export

**Para Validación de Región:**
- `Clasificacion` = Texto literal **"base-region"**

---

## Estado de Validación (Nueva Lógica)

**Campo:** `Estado`  
**Basado en:** `Total_Pre_Escalado` (Suma de % allocation RAW, sin escalar) o `Flag`.

**Reglas:**
**Reglas de Validación (Porcentajes):**
- **Validado**: Total entre 60% y 120%.
- **Revisión**: Total entre 40% y 60%, o mayor a 120%.
- **ERROR**: Total menor a 40%.

**Propósito:** Proporcionar un estado claro de la calidad del dato para el dashboard de gestión.

---

## Total Pre-Escalado

**Definición:** Suma de los porcentajes de allocation *antes* de cualquier normalización matematica.
**Importancia:** Es la métrica real de calidad de datos.
**Regla de Negocio:**
- Se debe calcular usando los datos `RAW` del pipeline (`df_alloc_ext`).
- NO se debe usar el dataframe final agrupado que podría tener redondeos.
- Es la base para el cálculo del semáforo/Flag.
## División de Exports: Balanceado / No Balanceado / Sin Datos

**Criterio de División:** Valor de `Region_Calculada`

> [!IMPORTANT]
> Los instrumentos se dividen en **3 categorías** para exports:
> 1. **Balanceados** - Diversificados entre regiones
> 2. **No Balanceados** - Región específica dominante
> 3. **Sin Datos** - No encontrados en Refinitiv

### 1. Instrumentos Balanceados
- **Condición:** `Region_Calculada == "balanceado"`
- **Significado:** Ninguna región supera el 90%
- **Export:** Formato completo con todas las columnas de regiones
- **Archivo:** `Balanceados_Region.xlsx`
- **Columnas:** ID, Id_ti_valor, Id_ti, Fecha, Clasificacion, region_antigua, Flag, Estado, Total_Pre_Escalado, + todas las columnas de regiones (LATAM, ASIA, EUROPA, etc.)
- **Propósito:** Actualizar base de datos con instrumentos clasificados como balanceados

### 2. Instrumentos No Balanceados
- **Condición:** `Region_Calculada != "balanceado"` Y `Region_Calculada != "Sin Datos"`
- **Significado:** Una región específica domina (>= 90%)
- **Export:** Formato simple de 5 columnas
- **Archivo:** `No_Balanceados_Region.xlsx`
- **Columnas:**
  - `ID`: Identificador interno
  - `Instrumento`: Nombre del instrumento
  - `base-region`: Valor **NUEVO** (Región de Destino para actualizar BD)
  - `Region_Anterior`: Valor **VIEJO** (de allocations internas)
  - `Flag`: Semáforo de cambio
  - `Sobreescribir`: 'y' o 'n'

> [!IMPORTANT]
> **Doble Significado de `base-region`**:
> - En el **Maestro de Instrumentos**, `base-region` es la región **ACTUAL/ORIGINAL**.
> - En el **Export de No Balanceados**, la columna `base-region` contiene la **NUEVA REGIÓN** (calculada) que sobrescribirá el valor anterior.
> - La región original se mueve a la columna `Region_Anterior` en el export.

**Código de Referencia:** Similar a `pages/2_Validacion_Allocations.py` pero adaptado para región

---

## Reglas de Id_ti e Id_ti_valor

**Propósito:** Mostrar qué identificador se usó para cruzar datos de Refinitiv con el maestro

**Reglas:**
1. Usar el campo `matched_by` del cruce de allocations
2. Si el match fue por RIC: `Id_ti = "RIC"`, `Id_ti_valor = <código RIC>`
3. Si el match fue por ISIN: `Id_ti = "Isin"`, `Id_ti_valor = <código ISIN>`
4. **NUNCA usar Cusip** en estas columnas de export (incluso si el match fue por Cusip, hacer fallback a RIC/ISIN)

**Código de Referencia:** Similar a `pages/2_Validacion_Allocations.py` (misma lógica que monedas)

**Justificación:** Estos exports actualizan la base de datos, y la base de datos solo acepta identificadores RIC o ISIN para el matching con Refinitiv.

---

---

## Normalización de Regiones


**Estado Actual:**
- Existe archivo `src/region_mapping.py` con mapeo de regiones
- Mapea nombres de Refinitiv a nombres internos
- Ejemplo: "North America" → "NORTEAMERICA"

**Código de Referencia:** `src/region_mapping.py`



---

## Diferencias Clave con Validación de Monedas

| Aspecto | Monedas | Regiones |
|---------|---------|----------|
| **Columna Calculada** | `Moneda_Calculada` | `Region_Calculada` |
| **Columna Antigua** | `Moneda_Antigua` | `Region_Antigua` |
| **Columna en Maestro** | `SubMoneda` | `base-region` |
| **Columna en Allocations Internos** | `Moneda:` | `Base Región:` |
| **Campo Clasificación** | "SubMoneda" | "base-region" |
| **Valores de datos** | USD, CLP, EUR, etc. | LATAM, ASIA, EUROPA, etc. |
| **Formato Allocations Externos** | Largo (long) | Ancho (wide) → transformado a largo |
| **Umbral clasificación** | 90% | 90% (mismo) |
| **Rangos Estado** | 60-120% VALIDO | 60-120% VALIDO (mismo) |
| **Normalización** | `src/currency_mapping.py` | `src/region_mapping.py` (en revisión) |

---

## Notas Importantes

1. **Lógica Idéntica a Monedas:** La mayoría de las reglas son idénticas, solo cambian los nombres de columnas y valores
2. **Umbral 90%:** Se mantiene el mismo umbral que en monedas para clasificación balanceado/no balanceado
3. **Estados de Validación Idénticos:** Los rangos de calidad (60-120% VALIDO, etc.) son los mismos que en monedas.
4. **Exports Separados:** Igual que monedas, hay exports para balanceados y no balanceados
5. **Formato de Entrada Diferente:** La diferencia principal está en que allocations externas vienen en formato ancho

