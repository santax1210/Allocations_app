# Documentación de Flujo del Pipeline - Validación de Regiones

> [!IMPORTANT]
> **Esta documentación es EXCLUSIVA para Validación de Regiones.**  
> **NO confundir con la validación de Monedas** (ver `../moneda/pipeline_flow.md`)

---

## Resumen
El pipeline de conciliación de regiones procesa datos de posiciones y allocations a través de múltiples pasos para validar y clasificar instrumentos por región geográfica.

**Diferencia Principal:** Las allocations externas vienen en formato **ancho** (wide) y se transforman a formato largo en el data_loader.

---

## Pasos del Pipeline (Validación de Región)

### PASO 1: Filtrar Posiciones
**Entrada:** Archivo Posiciones  
**Salida:** Posiciones filtradas  
**Proceso:**
- Filtrar posiciones por fecha (`F. Proceso >= fecha_minima`)
- Preparar para cruce con instrumentos

**Código de Referencia:** `src/pipeline_region.py` líneas 52-66

**Nota:** Idéntico al paso 1 de validación de monedas

---

### PASO 2: Cruzar con Instrumentos
**Entrada:** Posiciones filtradas, Maestro Instrumentos  
**Salida:** Posiciones enriquecidas con metadata de instrumentos  
**Proceso:**
1. Normalizar identificadores (Cusip, Isin, RIC)
2. Intentar match por Nombre primero
3. Intentar match por ID (RIC, Isin, Cusip) para los que no matchearon
4. Agregar `ID`, `Nombre`, `Tipo instrumento`, `base-region`, etc. a cada posición
5. Deduplicar resultados

**Columnas Clave de Salida:**
- Todas las columnas originales de posiciones
- `ID` (del maestro)
- `Nombre` (del maestro)
- `RIC`, `Isin`, `Cusip` (del maestro)
- `Id_ti`, `Id_ti_valor` (del maestro)
- `base-region` (del maestro) - **DIFERENTE A MONEDAS**
- `matched_by`: Indica qué identificador se usó para el match

**Código de Referencia:** `src/pipeline_region.py` líneas 68-133

**Nota:** Lógica idéntica a monedas, pero incluye `base-region` en lugar de `SubMoneda`

---

### PASO 3: Filtrar por Tipo de Instrumento
**Entrada:** Posiciones cruzadas  
**Salida:** Instrumentos filtrados por tipo  
**Proceso:**
1. Extraer instrumentos únicos del cruce de posiciones
2. Filtrar basado en `Tipo instrumento` (solo tipos en `tipos_filtro`)
3. Validar que tengan ISIN o RIC válido
4. Asignar `Tipo_Grupo` (Acciones, Bonos, Fondos/ETF)
5. Renombrar `Tipo instrumento` a `Tipo`

**Columnas Clave de Salida:**
- `ID`, `Nombre`, `Cusip`, `Isin`, `RIC`
- `Tipo`: Código de tipo (C02, C04, etc.)
- `Tipo_Grupo`: Grupo del instrumento
- `Tipo_Nombre`: Nombre descriptivo del tipo
- `base-region`: Región actual en BD

**Código de Referencia:** `src/pipeline_region.py` líneas 135-170

**Nota:** Idéntico a monedas excepto por el uso de `base-region`

---

### PASO 4: Obtener Allocations Externas
**Entrada:** Instrumentos filtrados, Allocations Externos (Regiones)  
**Salida:** `df_alloc_ext` con allocations cruzadas  

> [!WARNING]
> **DIFERENCIA CRÍTICA CON MONEDAS:**  
> Las allocations externas de región vienen en **formato ANCHO** (wide format) y se transforman a formato largo en el `data_loader.py`.
>
> **MEJORA RECIENTE (FALTA ALLOCATION):**
> Se preservan filas con `Base Región: FALTA ALLOCATION` incluso si sus porcentajes son 0. Esto es crítico para detectar el Caso 3 más adelante.

**Proceso:**
1. **Cargar allocations externas** (ya transformadas a formato largo por data_loader)
   - Formato original: Columnas por región (LATAM, ASIA, EUROPA, etc.)
   - Formato transformado: `instrument`, `class` (región), `percentage`
2. Normalizar campo `instrument` de Refinitiv (mayúsculas, trim)
3. Crear conjuntos de RIC, ISIN, Cusip válidos de instrumentos
4. **Cruzar por RIC primero, luego ISIN, luego Cusip**
5. Agregar `ID` y `Nombre` del maestro a cada allocation
6. Filtrar a la fecha más reciente por instrumento (si hay columna `date`)
7. Normalizar nombres de regiones (mapeo Refinitiv → interno)
8. Convertir `percentage` a numérico (`percentage_num`)

**Columnas Críticas de Salida:**
- `ID`: Del maestro de instrumentos
- `Nombre`: Del maestro de instrumentos  
- `instrument`: Código original de Refinitiv
- `Region_Interna_Mapped`: Región normalizada (LATAM, ASIA, EUROPA, etc.)
- `percentage_num`: Porcentaje numérico
- `date`: Fecha de allocation (si existe)
- `matched_by`: Qué identificador se usó (RIC/Isin/Cusip)

**Guardado en:** `st.session_state.df_alloc_ext_region`

**Código de Referencia:** 
- Transformación wide→long: `src/data_loader.py` líneas 170-227
- Cruce con maestro: `src/pipeline_region.py` (similar a monedas)

---

### PASO 5: Identificar Región Principal
**Entrada:** Instrumentos filtrados, `df_alloc_ext`, Allocations Internos  
**Salida:** Instrumentos con clasificación de región  
**Proceso:**

Para cada instrumento:
1. Obtener todas las allocations externas para ese instrumento
2. Calcular `Total_Pct_Ext` (suma de todos los porcentajes)
3. Determinar si es balanceado:
   - Si alguna región >= 90%: No balanceado (región específica)
   - De lo contrario: Balanceado
4. Calcular `Region_Calculada`:
   - Si balanceado: "balanceado"
   - De lo contrario: Región con mayor porcentaje
5. Obtener allocations internas de Allocations Internos (regiones)
   - **IMPORTANTE:** Se aplica `drop_duplicates(subset=['ID'])` para evitar multiplicar filas, ya que la fuente ahora preserva múltiples filas (melted) y filas especiales (FALTA ALLOCATION).
6. Calcular `Region_Antigua` (región interna dominante)
7. Hacer merge de `Base Región:` desde allocations internas

**Columnas Clave de Salida:**
- Todas las columnas anteriores
- `Region_Calculada`: Región calculada desde Refinitiv
- `base-region`: Región actual desde base de datos
- `Region_Antigua`: Región de allocation interna dominante
- `Total_Pct_Ext`: Suma de porcentajes externos
- `Es_Balanceado`: Flag booleano
- `Base Región:`: Estado de allocation ("FALTA ALLOCATION", "ASIGNADO", "DISTRIBUIDOS")

**Código de Referencia:** `src/pipeline_region.py` (similar a monedas)

**Diferencias con Monedas:**
- Usa `Region_Calculada` en lugar de `Moneda_Calculada`
- Usa `Region_Antigua` en lugar de `Moneda_Antigua`
- Usa `Base Región:` en lugar de `Moneda:`
- Procesa regiones (LATAM, ASIA, etc.) en lugar de monedas (USD, CLP, etc.)

---

### PASO 6: Validación y Generación de Flag
**Entrada:** Instrumentos clasificados  
**Salida:** Resultados finales de validación  
**Proceso:**
1. Generar `Estado` (Calidad) basado en `Total_Pct_Ext`:
   - 60-120%: VALIDO
   - 40-60% o >120%: REVISION
   - <40%: ERROR
2. Comparar `Region_Calculada` vs `base-region`
3. Renombrar columnas para export:
   - `Nombre` → `Instrumento`
   - `Semáforo` → `Flag`
   - etc.

**Columnas Clave de Salida:**
- `ID`
- `Instrumento`
- `Region_Calculada`
- `base-region`
- `Semáforo` (Estado Calidad)
- `Flag` (Calculado en Export)
- `Total_Pct_Ext`
- `Region_Antigua`

**Guardado en:** `st.session_state.df_final_region`

**Código de Referencia:** `src/pipeline_region.py` (similar a monedas)

**Nota:** Lógica idéntica a monedas, solo cambian nombres de columnas

---

### PASO 7: Escalar Allocations Proporcionalmente
**Entrada:** `df_final` (con Flag calculado), `df_alloc_ext`  
**Salida:** `df_alloc_ext_escalado` con porcentajes normalizados  
**Proceso:**
1. Identificar instrumentos con `Flag != 'ERROR'`
2. Para cada instrumento válido:
   - Calcular suma actual: `suma_actual = Σ percentage_num`
   - Calcular factor de escalado: `factor = 100 / suma_actual`
   - Aplicar escalado: `percentage_escalado = percentage_num × factor`
3. Crear nueva columna `percentage_escalado`
4. Instrumentos con Flag = 'ERROR' mantienen porcentajes originales

**Columnas de Salida:**
- Todas las columnas originales de allocations
- `percentage_escalado`: Porcentaje normalizado (suma 100% por instrumento)

**Guardado en:** `self.df_alloc_ext` (sobrescribe con versión escalada)

**Código de Referencia:** `src/pipeline_region.py` líneas 438-483

**Justificación:**
- Normaliza datos para exports consistentes
- Mantiene proporciones relativas
- Solo afecta instrumentos con datos válidos (no ERROR)

---

## Preparación de Exports

### Export General (📥 Descargar Excel)
**Entrada:** `df_final_region`, `df_alloc_ext_region`  
**Proceso:**
1. Pivotar `df_alloc_ext` a formato ancho (regiones como columnas)
2. Hacer merge de allocations pivoteadas con resultados finales usando `ID`
3. Calcular `Fecha`:
   - Si `Base Región:` = "FALTA ALLOCATION": `Fecha = "31-12-2019"`
   - Caso contrario: `Fecha = "01-01-2026"`
4. Establecer `Clasificacion = "base-region"` (literal)
5. Corregir `Id_ti` e `Id_ti_valor` para usar solo RIC/Isin
6. Seleccionar y renombrar columnas

**Columnas de Salida:**
- ID, Id_ti_valor, Id_ti, Fecha, Clasificacion, region_antigua, Flag
- Columnas de regiones: LATAM, ASIA, EUROPA, NORTEAMERICA, etc. (del pivot)

**Diferencias con Monedas:**
- `Clasificacion = "base-region"` (no "SubMoneda")
- Columnas de regiones en lugar de monedas
- Cálculo de fecha diferente (valores fijos, no último día del mes)

**Código de Referencia:** `pages/2_Validacion_Allocations.py` (adaptado para región)

---

### Export de Balanceados
**Filtro:** `Region_Calculada == "balanceado"`  
**Formato:** Formato completo con todas las columnas de regiones  
**Propósito:** Actualizar base de datos con instrumentos clasificados como balanceados

**Columnas principales:**
- ID, Id_ti_valor, Id_ti, Fecha, Clasificacion, region_antigua, Flag, **Sobreescribir**
- Columnas de regiones: LATAM, ASIA, EUROPA, NORTEAMERICA, AFRICA, etc.

**Archivo:** `Balanceados_Region.xlsx`

---

### Export de No Balanceados  
**Filtro:** `Region_Calculada != "balanceado"`  
**Formato:** Formato simple de 5 columnas  
**Columnas:**
- `ID`: Identificador interno
- `Instrumento`: Nombre del instrumento
- `base-region`: Valor **NUEVO** (de `Region_Calculada`)
- `Region_Anterior`: Valor **VIEJO** (de allocations internas)
- `Sobreescribir`: "y" o "n" (basado en Flag)

**Propósito:** Actualizar campo `base-region` en base de datos con nueva región calculada

**Diferencias con Monedas:**
- Columna `base-region` (no `SubMoneda`)
- Columna `Region_Anterior` (no `Moneda_Anterior`)
- Valores de regiones (LATAM, ASIA, etc.) en lugar de monedas (USD, CLP, etc.)

---

## Diagrama de Flujo de Datos

```
Posiciones → [PASO 1: Filtrar] → Posiciones Filtradas
                                        ↓
Maestro Instrumentos ← [PASO 2: Cruzar] ← Posiciones Filtradas
(con base-region)                       ↓
                            [PASO 3: Filtrar por Tipo]
                                        ↓
Allocations Externos → [PASO 4: Obtener Allocations] → df_alloc_ext
(formato ANCHO)         (transformado a LARGO)              ↓
                                        ↓                    ↓
Allocations Internos → [PASO 5: Clasificar] ← Instrumentos  ↓
(Base Región:)                          ↓                    ↓
                            [PASO 6: Validar] → df_final    ↓
                                        ↓                    ↓
                            [PASO 7: Escalar] ←──────────────┘
                            (Flag != ERROR)
                                        ↓
                                df_alloc_ext_escalado
                                        ↓
                                [Preparación Export]
                                        ↓
                        ┌───────────────┴───────────────┐
                        ↓                               ↓
                Balanceados.xlsx              No_Balanceados.xlsx
                (Formato completo)            (5 columnas)
                (LATAM, ASIA, etc.)           (base-region)
```

---

## Diferencias Clave con Pipeline de Monedas

| Aspecto | Monedas | Regiones |
|---------|---------|----------|
| **Formato Allocations Externos** | Largo (long) | **Ancho (wide) → transformado a largo** |
| **Separador Allocations Externos** | `;` | `,` (coma) |
| **Columna Calculada** | `Moneda_Calculada` | `Region_Calculada` |
| **Columna Antigua** | `Moneda_Antigua` | `Region_Antigua` |
| **Columna en Maestro** | `SubMoneda` | `base-region` |
| **Columna en Allocations Internos** | `Moneda:` | `Base Región:` |
| **Campo Clasificación Export** | "SubMoneda" | "base-region" |
| **Valores de datos** | USD, CLP, EUR | LATAM, ASIA, EUROPA |
| **Cálculo de Fecha Export** | Último día mes anterior | Valores fijos (31-12-2019 o 01-01-2026) |
| **Normalización** | `currency_mapping.py` | `region_mapping.py` |
| **Umbral clasificación** | 90% | 90% (mismo) |
| **Rangos Estado** | 60-120% VALIDO | 60-120% VALIDO (mismo) |
| **Lógica de pasos** | Idéntica | Idéntica (solo nombres cambian) |

---

## Notas Importantes

1. **Formato de Entrada Diferente:** La diferencia más crítica es que allocations externas vienen en formato ancho
2. **Transformación Automática:** El `data_loader.py` transforma automáticamente de ancho a largo
3. **Lógica Idéntica:** Todos los pasos tienen la misma lógica que monedas, solo cambian nombres de columnas
4. **Umbral 90%:** Se mantiene el mismo umbral para clasificación balanceado/no balanceado
5. **Estados Idénticos:** Los rangos de validación (calidad) son los mismos (60-120% VALIDO, etc.)
6. **Separación Total:** Este pipeline es completamente independiente del pipeline de monedas
7. **Mapeo de Regiones:** Existe normalización de nombres de regiones (Refinitiv → interno)
