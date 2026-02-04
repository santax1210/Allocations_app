# Documentación de Estructuras de Archivos - Validación de Monedas

## Archivos de Entrada

### 1. Posiciones (Archivo de Posiciones)
**Origen:** Exportación de sistema externo  
**Formato:** CSV  
**Separador:** `;` (punto y coma)  
**Encoding:** `latin-1`  
**Propósito:** Contiene las posiciones del portafolio a conciliar

**Columnas Clave:**
- `Cusip`: Identificador CUSIP del instrumento
- `Isin`: Identificador ISIN del instrumento  
- `RIC`: Código de Instrumento Reuters
- Datos adicionales de posición (cantidades, valores, etc.)

**Notas:**
- Se usa como punto de partida para la conciliación
- Se cruza con el archivo maestro de Instrumentos usando los identificadores

---

### 2. Instrumentos (Archivo Maestro de Instrumentos)
**Origen:** Base de datos maestra interna  
**Formato:** CSV  
**Separador:** `;` (punto y coma)  
**Encoding:** `latin-1`  
**Propósito:** Catálogo maestro de todos los instrumentos con metadata

**Columnas Clave:**
- `ID`: Identificador único interno (clave primaria)
- `Nombre`: Nombre del instrumento
- `Cusip`: Código CUSIP
- `Isin`: Código ISIN
- `RIC`: Código Reuters
- `Id_ti`: Tipo de identificador usado (RIC/Isin/Cusip)
- `Id_ti_valor`: El valor real del identificador
- `Tipo instrumento`: Código de tipo de instrumento (C02, C04, etc.)
- `SubMoneda`: Clasificación de moneda almacenada en BD ("balanceado", "USD", "CLP", etc.)

**Notas:**
- Este es el maestro de referencia para todos los instrumentos
- Contiene la clasificación "oficial"
- Se usa para enriquecer los datos de posiciones con metadata del instrumento
- `SubMoneda` es el campo que se actualiza con los exports
- Las columnas `Tipo_Grupo` y `Tipo_Nombre` se calculan en el pipeline a partir de `Tipo instrumento`
- La columna `Moneda:` **NO** pertenece a este archivo, sino al archivo de **Allocations Internos** o al de **Posiciones**

**Código de Referencia:** `src/pipeline.py` línea 179

---

### 3. Allocations Internos (Allocations Internas de Moneda)
**Origen:** Base de datos interna  
**Formato:** CSV  
**Separador:** `;` (punto y coma)  
**Encoding:** `latin-1`  
**Motor de lectura:** `python` (más tolerante con líneas problemáticas)  
**Propósito:** Allocations internas de moneda por instrumento (formato ancho)

**Estructura del Archivo:**
El archivo tiene un formato **ancho** (wide format) donde cada moneda es una columna.

**Columnas Identificadoras:**
- `ID`: Identificador único interno
- `Nombre`: Nombre del instrumento
- `Isin`: Código ISIN
- `Cusip`: Código CUSIP
- `RIC`: Código Reuters
- `Nemo`: Nemotécnico

**Columnas de Metadata:**
- `Moneda:`: Estado de allocation con valores posibles:
  - `FALTA ALLOCATION`: No tiene allocations definidas
  - `ASIGNADO`: Tiene una moneda específica asignada (no balanceado)
  - `DISTRIBUIDOS`: Allocations distribuidas entre múltiples monedas
- `Tipo Instrumento`: Tipo del instrumento
- `Creado`: Fecha de creación
- `Ticker_BB`: Ticker Bloomberg
- `Currency`: Moneda base

**Columnas de Monedas (Allocations):**
Cada moneda tiene su propia columna con el porcentaje de allocation:
- `USD`: Porcentaje en dólares estadounidenses
- `CLP`: Porcentaje en pesos chilenos
- `EUR`: Porcentaje en euros
- `GBP`: Porcentaje en libras esterlinas
- `JPY`: Porcentaje en yenes japoneses
- ... (y otras monedas según disponibilidad)

**Transformación en el Pipeline:**
El archivo se lee en formato **ancho** (wide format) pero se transforma inmediatamente a formato **largo** (long format) en el `data_loader.py` para facilitar el procesamiento:

**Formato resultante (long format):**
- `ID`: Identificador del instrumento
- `Nombre`: Nombre del instrumento
- `Isin`, `Cusip`, `RIC`: Identificadores
- `currency_code`: Código de moneda (USD, CLP, EUR, etc.)
- `percentage_num`: Porcentaje numérico de allocation

**¿Por qué se transforma a formato largo?**
- Permite comparar fácilmente moneda por moneda con las allocations externas
- Facilita el cálculo de la moneda dominante interna (encontrar el `max(percentage_num)`)
- Simplifica la detección de inconsistencias entre lo declarado (`SubMoneda`) y lo calculado

**Código de Referencia:** `src/data_loader.py` líneas 115-121 (transformación melt)  
**Uso en Pipeline:** `src/pipeline.py` líneas 599-617 (cálculo de moneda dominante interna)

**Notas:**
- Representa los datos de allocation "actuales" o "antiguos" en la base de datos
- Se usa para comparar contra las allocations calculadas de Refinitiv
- El campo `SubMoneda` del maestro es el que se actualiza en la base de datos con los exports
- Solo se procesan filas donde `percentage_num > 0`
- La transformación a formato largo ocurre en el `data_loader`, no en el pipeline principal

---

### 4. Allocations Externos (Allocations de Refinitiv)
**Origen:** Feed de datos de Refinitiv/FIRSTRATE  
**Formato:** CSV  
**Separador:** `;` (punto y coma)  
**Encoding:** `latin-1`  
**Propósito:** Allocations externas de moneda/región desde Refinitiv

**Columnas:**
- `instrument`: Identificador del instrumento (código RIC o ISIN)
- `date`: Fecha de los datos de allocation
- `class`: Nombre de moneda de Refinitiv (ej: "US Dollar", "Chilean Peso")
- `percentage`: Porcentaje de allocation (como string, ej: "45.5%")
- `Fuente`: Columna fuente (ej: "FundCurrencyAllocation")
- `classif`: Clasificación (ej: "currency")

**Transformación en el Pipeline:**
- `class` se normaliza a códigos ISO (ej: "US Dollar" → "USD")
- `percentage` se convierte a numérico (`percentage_num`)
- Se filtra por fecha más reciente por instrumento
- Se agrupa por `instrument` y `currency_code`

**Código de Referencia:** `src/data_loader.py` líneas 136-180

**Notas:**
- **CRÍTICO:** La columna `instrument` contiene un código RIC o ISIN
- **CRÍTICO:** Esta es la ÚNICA forma de cruzar con el maestro de Instrumentos (vía RIC o ISIN)
- La columna `class` se normaliza a códigos ISO de moneda (USD, CLP, etc.)
- Pueden existir múltiples fechas; el pipeline usa la fecha más reciente por instrumento

---

## Reglas de Cruce de Datos

### Allocations Externos → Maestro de Instrumentos
**Proceso de Cruce:**
1. Normalizar campo `instrument` de Refinitiv (mayúsculas, trim)
2. Intentar cruzar contra columna `RIC` en Instrumentos
3. Si no hay match, intentar columna `Isin`
4. Si no hay match, intentar columna `Cusip`
5. Cuando hay match, copiar `ID`, `Nombre` y otra metadata al registro de allocation

**Código de Referencia:** `src/pipeline.py` líneas 220-370

**Resultado:**
- Cada fila de allocation externa se enriquece con `ID` y `Nombre` del maestro
- El campo `matched_by` indica qué identificador se usó (RIC/Isin/Cusip)
- **Este `ID` se usa para todos los joins y exports subsecuentes**

---

## Referencia de Origen de Columnas

| Nombre de Columna | Origen | Descripción |
|-------------------|--------|-------------|
| `ID` | Maestro Instrumentos | Identificador único interno |
| `Nombre` / `Instrumento` | Maestro Instrumentos | Nombre del instrumento |
| `RIC` | Maestro Instrumentos | Código Reuters |
| `Isin` | Maestro Instrumentos | Código ISIN |
| `Cusip` | Maestro Instrumentos | Código CUSIP |
| `Id_ti` | Calculado en export | Tipo de identificador usado para el match (RIC/Isin) |
| `Id_ti_valor` | Calculado en export | El valor real de RIC o ISIN usado |
| `Moneda_Interna` / `SubMoneda` | Maestro Instrumentos | Moneda actual en base de datos |
| `Moneda:` | Posiciones / Allocations Internos | Estado de allocation ("FALTA ALLOCATION", "ASIGNADO", "DISTRIBUIDOS") |
| `Tipo_Grupo` | Calculado en pipeline | Grupo del instrumento (Acciones, Bonos, Fondos/ETF) |
| `Tipo_Nombre` | Calculado en pipeline | Nombre descriptivo del tipo |
| `Moneda_Calculada` | Calculado desde Allocations Externos | Nueva moneda calculada |
| `Moneda_Interna` | Maestro Instrumentos (campo SubMoneda) | Moneda actual en base de datos |
| `Total_Pct_Ext` | Calculado desde Allocations Externos | Suma de % de allocations externas |
| `Total_Pre_Escalado` | Calculado en pipeline | Suma de % antes del escalado (solo export Balanceados) |
| `Estado` | Calculado en export | Clasificación de calidad de allocations (ERROR/Revisión/Validado, solo export Balanceados) |
| `Flag` | Calculado en export | Estado de cambio (Caso_1, Caso_2, Caso_3) entre Moneda_Anterior y SubMoneda |
| Columnas de monedas (USD, CLP, etc.) | Pivoteado desde Allocations Externos | Porcentajes individuales por moneda (escalados a 100%) |

---

## Notas Importantes

1. **ID es la Clave Universal:** Una vez que los instrumentos están cruzados, `ID` se usa para todos los joins
2. **Solo RIC/ISIN para Exports:** Las columnas de export `Id_ti` e `Id_ti_valor` solo deben contener RIC o ISIN (no Cusip)
3. **Moneda_Calculada es la Fuente de Verdad:** Para clasificación, siempre usar el valor calculado desde datos de Refinitiv
4. **Actualizaciones de SubMoneda:** Los archivos de export se usan para actualizar el campo `SubMoneda` en la base de datos
5. **Formato Ancho vs Largo:** Allocations Internos viene en formato ancho (monedas como columnas), se transforma a largo para procesamiento
