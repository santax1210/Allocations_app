# Documentación de Flujo del Pipeline

## Resumen
El pipeline de conciliación procesa datos de posiciones y allocations a través de múltiples pasos para validar y clasificar instrumentos.

---

## Pasos del Pipeline (Validación de Moneda)

### PASO 1: Filtrar Posiciones
**Entrada:** Archivo Posiciones  
**Salida:** Posiciones filtradas  
**Proceso:**
- Aplicar filtros necesarios a los datos de posiciones
- Preparar para cruce con instrumentos

---

### PASO 2: Cruzar con Instrumentos
**Entrada:** Posiciones filtradas, Maestro Instrumentos  
**Salida:** Posiciones enriquecidas con metadata de instrumentos  
**Proceso:**
1. Normalizar identificadores (Cusip, Isin, RIC)
2. Cruzar posiciones con instrumentos usando identificadores disponibles
3. Agregar `ID`, `Nombre`, `Tipo_Grupo`, etc. a cada posición

**Columnas Clave de Salida:**
- Todas las columnas originales de posiciones
- `ID` (del maestro)
- `Nombre` (del maestro)
- `RIC`, `Isin`, `Cusip` (del maestro)
- `Id_ti`, `Id_ti_valor` (del maestro)

---

### PASO 3: Filtrar por Tipo de Instrumento
**Entrada:** Posiciones cruzadas  
**Salida:** Posiciones filtradas por tipo de instrumento  
**Proceso:**
- Filtrar basado en `Tipo_Grupo` u otros criterios de tipo
- Remover instrumentos no relevantes para validación de moneda

---

### PASO 4: Obtener Allocations Externas
**Entrada:** Instrumentos filtrados, Allocations Externos  
**Salida:** `df_alloc_ext` con allocations cruzadas  
**Proceso:**
1. Normalizar campo `instrument` de Refinitiv
2. Crear conjuntos de RIC, ISIN, Cusip válidos de instrumentos
3. Filtrar allocations externas solo a las que coinciden con nuestros instrumentos
4. **Cruzar por RIC primero, luego ISIN, luego Cusip**
5. Agregar `ID` y `Nombre` del maestro a cada allocation
6. Filtrar a la fecha más reciente por instrumento
7. Normalizar códigos de moneda (nombres Refinitiv → códigos ISO)
8. Calcular `percentage_num` (porcentaje numérico)

**Columnas Críticas de Salida:**
- `ID`: Del maestro de instrumentos
- `Nombre`: Del maestro de instrumentos  
- `instrument`: Código original de Refinitiv
- `currency_code`: Moneda normalizada (USD, CLP, etc.)
- `percentage_num`: Porcentaje numérico
- `date`: Fecha de allocation
- `matched_by`: Qué identificador se usó (RIC/Isin/Cusip)

**Guardado en:** `st.session_state.df_alloc_ext_moneda`

---

### PASO 5: Identificar Moneda Principal
**Entrada:** Instrumentos filtrados, `df_alloc_ext`  
**Salida:** Instrumentos con clasificación de moneda  
**Proceso:**

Para cada instrumento:
1. Obtener todas las allocations externas para ese instrumento
2. Calcular `Total_Pct_Ext` (suma de todos los porcentajes)
3. Determinar si es balanceado:
   - Si alguna moneda >= 90%: No balanceado (moneda específica)
   - De lo contrario: Balanceado
4. Calcular `Moneda_Calculada`:
   - Si balanceado: "balanceado"
   - De lo contrario: Moneda con mayor porcentaje
5. Obtener allocations internas de Allocations Internos
6. Copiar `Moneda_Interna` desde campo `SubMoneda` del maestro

**Columnas Clave de Salida:**
- `ID`: Identificador único del instrumento
- `Moneda_Calculada`: Moneda de allocation externa dominante
- `Moneda_Interna`: Moneda actual en base de datos (desde SubMoneda)
- `Total_Pct_Ext`: Suma de porcentajes externos
- `Es_Balanceado`: Flag booleano

---

### PASO 6: Validación de Inconsistencias
**Entrada:** Instrumentos clasificados  
**Salida:** Resultados finales de validación  
**Proceso:**
1. Comparar `Moneda_Calculada` vs `Moneda_Interna`
2. Generar `Detalle_Inconsistencia` si difieren
3. Renombrar columnas para export:
   - `Nombre` → `Instrumento`
   - etc.

**Columnas Clave de Salida:**
- `ID`
- `Instrumento`
- `Moneda_Calculada`
- `Moneda_Interna`
- `Detalle_Inconsistencia`
- `Total_Pct_Ext`
- `Moneda_Interna`

**Nota:** El `Flag` se calcula en la fase de export, no en el pipeline.

**Guardado en:** `st.session_state.df_final_moneda`

---

### PASO 7: Calcular Total Pre-Escalado y Escalar Allocations
**Entrada:** `df_final_moneda`, `df_alloc_ext_moneda`  
**Salida:** `df_alloc_ext_escalado` con porcentajes normalizados  
**Proceso:**
1. **Calcular `Total_Pre_Escalado`:**
   - Agrupar allocations por `ID`
   - Sumar `percentage_num` para obtener total antes de escalar
   - Agregar columna `Total_Pre_Escalado` al DataFrame

2. **Escalar solo instrumentos con cobertura suficiente:**
   - Filtrar instrumentos con `Total_Pct_Ext >= 40%`
   - Para cada instrumento:
     - Calcular factor: `factor = 100 / Total_Pct_Ext`
     - Aplicar: `percentage_escalado = percentage_num × factor`
   - Instrumentos con `Total_Pct_Ext < 40%` NO se escalan

3. **Resultado:**
   - Porcentajes suman exactamente 100% (cuando Total_Pct_Ext >= 40%)
   - Proporciones relativas se mantienen

**Columnas de Salida:**
- Todas las columnas originales de allocations
- `Total_Pre_Escalado`: Suma original antes del escalado
- `percentage_escalado`: Porcentaje normalizado (suma 100% por instrumento)

**Guardado en:** `st.session_state.df_alloc_ext_moneda` (sobrescribe con versión escalada)

**Código de Referencia:** Similar a `src/pipeline_region.py` paso_7_escalar_allocations

**Justificación:**
- Normaliza datos para exports consistentes
- Mantiene proporciones relativas
- Solo afecta instrumentos con cobertura suficiente (>= 40%)
- `Total_Pre_Escalado` permite análisis pre y post escalado

---

## Preparación de Exports

### Export General (📥 Descargar Excel)
**Entrada:** `df_final_moneda`, `df_alloc_ext_moneda`  
**Proceso:**
1. Pivotar `df_alloc_ext` a formato ancho (monedas como columnas)
2. Hacer merge de allocations pivoteadas con resultados finales usando `ID`
3. Calcular `Fecha` (último día del mes anterior)
4. Establecer `Clasificacion = "SubMoneda"`
5. Corregir `Id_ti` e `Id_ti_valor` para usar solo RIC/Isin
6. Combinar `Detalle_Inconsistencia` y `Detalle_Validacion` en una sola `Inconsistencia`
7. Seleccionar y renombrar columnas

**Columnas de Salida:**
- ID, Id_ti_valor, Id_ti, Fecha, Clasificacion, moneda_antigua, Flag, Inconsistencia
- Columnas de monedas: USD, CLP, EUR, etc. (del pivot)

---

### Export de Balanceados
**Filtro:** `Moneda_Calculada == "balanceado"`  
**Formato:** Formato completo con todas las columnas de monedas  
**Propósito:** Actualizar base de datos con instrumentos clasificados como balanceados

**Columnas principales:**
- ID, Id_ti_valor, Id_ti, Fecha, Clasificacion, moneda_antigua, Flag, Inconsistencia, **Sobreescribir**
- Columnas de monedas: USD, CLP, EUR, etc.

**Archivo:** `Balanceados_Moneda.xlsx`

---

### Export de No Balanceados  
**Filtro:** `Moneda_Calculada != "balanceado"` Y `Moneda_Calculada != "Sin Datos"`  
**Formato:** Formato simple de 5 columnas  
**Columnas:**
- `ID`: Identificador interno
- `Instrumento`: Nombre del instrumento
- `SubMoneda`: **Moneda_Calculada** (valor nuevo a actualizar)
- `Moneda_Anterior`: **SubMoneda/Moneda_Interna** (valor viejo)
- `Inconsistencia`: Detalles del error o vacío
- `Sobreescribir`: "y" o "n" (basado en Flag)

**Propósito:** Actualizar campo SubMoneda en base de datos con nueva moneda calculada

**Archivo:** `No_Balanceados_Moneda.xlsx`

---

### Export de Sin Datos
**Filtro:** `Moneda_Calculada == "Sin Datos"`  
**Formato:** Formato mínimo de 5 columnas  
**Columnas:**
- `ID`: Identificador interno
- `Nombre`: Nombre del instrumento
- `Id_ti_valor`: Valor del identificador (RIC o ISIN)
- `Id_ti`: Tipo de identificador
- `Moneda_Calculada`: "Sin Datos"

**Propósito:** Identificar instrumentos no encontrados en Refinitiv para revisión manual

**Archivo:** `Sin_Datos_Moneda.xlsx`

---

## Diagrama de Flujo de Datos

```
Posiciones → [PASO 1: Filtrar] → Posiciones Filtradas
                                        ↓
Maestro Instrumentos ← [PASO 2: Cruzar] ← Posiciones Filtradas
                                        ↓
                            [PASO 3: Filtrar por Tipo]
                                        ↓
Allocations Externos → [PASO 4: Obtener Allocations] → df_alloc_ext
                                        ↓                    ↓
Allocations Internos → [PASO 5: Clasificar] ← Instrumentos  ↓
                                        ↓                    ↓
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
```
