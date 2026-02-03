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

**Propósito:** Validar la calidad de cobertura de allocations  
**Basado en:** `Total_Pct_Ext` (suma de porcentajes de allocations externas)

**Reglas:**
- **60% - 120%** → `VALIDO` (verde)
- **40% - 60%** O **> 120%** → `REVISION` (amarillo)
- **< 40%** → `ERROR` (rojo)

**Código de Referencia:** `src/pipeline_region.py` (misma lógica que monedas)

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

**Diferencia con Monedas:**
- Monedas usa: `Clasificacion = "SubMoneda"`
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
- **Columnas:** ID, Id_ti_valor, Id_ti, Fecha, Clasificacion, region_antigua, Flag, Inconsistencia, + todas las columnas de regiones (LATAM, ASIA, EUROPA, etc.)
- **Propósito:** Actualizar base de datos con instrumentos clasificados como balanceados

### 2. Instrumentos No Balanceados
- **Condición:** `Region_Calculada != "balanceado"` Y `Region_Calculada != "Sin Datos"`
- **Significado:** Una región específica domina (>= 90%)
- **Export:** Formato simple de 5 columnas
- **Archivo:** `No_Balanceados_Region.xlsx`
- **Columnas:**
  - `ID`: Identificador interno
  - `Instrumento`: Nombre del instrumento
  - `base-region`: Valor **NUEVO** (de `Region_Calculada`)
  - `Region_Anterior`: Valor **VIEJO** (de allocations internas)
  - `Inconsistencia`: Detalle del error o vacío

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

## Columna Inconsistencia

**Origen:** Combina `Detalle_Inconsistencia` y `Detalle_Validacion`  
**Lógica:**
- Para validación de Región: Usar `Detalle_Validacion`
- Muestra mensaje de error detallado si la validación falla
- Vacío si no hay inconsistencia

**Código de Referencia:** Similar a `pages/2_Validacion_Allocations.py` pero adaptado para región

**Valores Comunes (adaptados a regiones):**
- "Definido como BALANCEADO pero Norteamérica domina con 92.0%"
- "Definido como LATAM pero es balanceado (máx 85.0%)"
- "Definido como LATAM pero Asia domina con 91.0%"
- String vacío (sin error)

---

## Detección de Inconsistencias (Validación Interna)

**Casos de Inconsistencia:**

1. **BALANCEADO sin allocations:**
   - `base-region = "BALANCEADO"` pero no hay allocations internas
   - Mensaje: "Definido como BALANCEADO pero no tiene allocations internas"

2. **BALANCEADO pero dominante:**
   - `base-region = "BALANCEADO"` pero una región >= 90%
   - Mensaje: "Definido como BALANCEADO pero {región} domina con {%}"
   - Ejemplo: "Definido como BALANCEADO pero Norteamérica domina con 95.0%"

3. **Región específica pero balanceado:**
   - `base-region = {región}` pero ninguna región >= 90%
   - Mensaje: "Definido como {región} pero es balanceado (máx {%})"
   - Ejemplo: "Definido como LATAM pero es balanceado (máx 85.0%)"

4. **Región incorrecta:**
   - `base-region = {región_A}` pero `{región_B}` >= 90%
   - Mensaje: "Definido como {región_A} pero {región_B} domina con {%}"
   - Ejemplo: "Definido como LATAM pero Asia domina con 92.0%"

**Código de Referencia:** Similar a `src/pipeline.py` líneas 604-663 pero adaptado para región

---

## Normalización de Regiones

> [!WARNING]
> **EN REVISIÓN**  
> Pendiente determinar si es necesario realizar mapeo de nombres de regiones entre Refinitiv y sistema interno.

**Estado Actual:**
- Existe archivo `src/region_mapping.py` con mapeo de regiones
- Mapea nombres de Refinitiv a nombres internos
- Ejemplo: "North America" → "NORTEAMERICA"

**Código de Referencia:** `src/region_mapping.py`

**Pendiente:**
- Revisar si el mapeo actual es suficiente
- Validar consistencia de nombres entre fuentes
- Documentar mapeo completo si se confirma necesidad

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
| **Rangos Flag** | 60-120% VALIDO | 60-120% VALIDO (mismo) |
| **Normalización** | `src/currency_mapping.py` | `src/region_mapping.py` (en revisión) |

---

## Notas Importantes

1. **Lógica Idéntica a Monedas:** La mayoría de las reglas son idénticas, solo cambian los nombres de columnas y valores
2. **Umbral 90%:** Se mantiene el mismo umbral que en monedas para clasificación balanceado/no balanceado
3. **Flags Idénticos:** Los rangos de validación (60-120% VALIDO, etc.) son los mismos
4. **Exports Separados:** Igual que monedas, hay exports para balanceados y no balanceados
5. **Formato de Entrada Diferente:** La diferencia principal está en que allocations externas vienen en formato ancho
6. **Mapeo en Revisión:** Pendiente confirmar si el mapeo de regiones es necesario o suficiente
