# Documentación de Estructuras de Archivos - Validación de Regiones

> [!IMPORTANT]
> **Esta documentación es EXCLUSIVA para Validación de Regiones.**  
> **NO confundir con la validación de Monedas** (ver `.agent/docs/moneda/`)

---

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
- **Misma estructura y lógica que en validación de Monedas**
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
- **`base-region`**: Clasificación de región almacenada en BD (ej: "LATAM", "ASIA", "balanceado", etc.)

**Diferencias con Monedas:**
- ✅ **Usa `base-region` en lugar de `SubMoneda`**
- ✅ Misma lógica de cruce y filtrado que Monedas
- ✅ `base-region` es el campo que se actualiza con los exports de región

**Notas:**
- Este es el maestro de referencia para todos los instrumentos
- Contiene la clasificación "oficial" de región
- Se usa para enriquecer los datos de posiciones con metadata del instrumento
- Las columnas `Tipo_Grupo` y `Tipo_Nombre` se calculan en el pipeline a partir de `Tipo instrumento`

**Código de Referencia:** `src/pipeline_region.py` línea 142

---

### 3. Allocations Internos (Allocations Internas de Región)
**Origen:** Base de datos interna  
**Formato:** CSV  
**Separador:** `;` (punto y coma)  
**Encoding:** `latin-1`  
**Motor de lectura:** `python` (más tolerante con líneas problemáticas)  
**Propósito:** Allocations internas de región por instrumento (formato ancho)

**Estructura del Archivo:**
El archivo tiene un formato **ancho** (wide format) donde cada región es una columna.

**Columnas Identificadoras:**
- `ID`: Identificador único interno
- `Nombre`: Nombre del instrumento
- `Isin`: Código ISIN
- `Cusip`: Código CUSIP
- `RIC`: Código Reuters
- `Nemo`: Nemotécnico

**Columnas de Metadata:**
- **`Base Región:`**: Estado de allocation de región con valores posibles:
  - `FALTA ALLOCATION`: No tiene allocations definidas
  - `ASIGNADO`: Tiene una región específica asignada (no balanceado)
  - `DISTRIBUIDOS`: Allocations distribuidas entre múltiples regiones
- `Tipo Instrumento`: Tipo del instrumento
- `Creado`: Fecha de creación
- `Ticker_BB`: Ticker Bloomberg
- `Currency`: Moneda base

**Columnas de Regiones (Allocations):**
Cada región tiene su propia columna con el porcentaje de allocation:
- `LATAM`: Porcentaje en Latinoamérica
- `ASIA`: Porcentaje en Asia
- `EUROPA`: Porcentaje en Europa
- `AFRICA`: Porcentaje en África
- `NORTEAMERICA`: Porcentaje en Norteamérica
- ... (y otras regiones según disponibilidad)

**Diferencias con Monedas:**
- ✅ **Usa `Base Región:` en lugar de `Moneda:`**
- ✅ Columnas de regiones en lugar de monedas
- ✅ Misma transformación a formato largo

**Transformación en el Pipeline:**
El archivo se lee en formato **ancho** (wide format) pero se transforma inmediatamente a formato **largo** (long format) en el `data_loader.py` para facilitar el procesamiento:

**Formato resultante (long format):**
- `ID`: Identificador del instrumento
- `Nombre`: Nombre del instrumento
- `Isin`, `Cusip`, `RIC`: Identificadores
- `Region_Interna_Mapped`: Código de región normalizado
- `percentage_num`: Porcentaje numérico de allocation

**¿Por qué se transforma a formato largo?**
- Permite comparar fácilmente región por región con las allocations externas
- Facilita el cálculo de la región dominante interna (encontrar el `max(percentage_num)`)
- Simplifica la detección de inconsistencias entre lo declarado (`base-region`) y lo calculado

**Código de Referencia:** `src/data_loader.py` líneas 229-260 (carga y transformación)  
**Uso en Pipeline:** `src/pipeline_region.py` líneas 40-48 (detección de columnas de región)

**Notas:**
- Representa los datos de allocation "actuales" o "antiguos" en la base de datos
- Se usa para comparar contra las allocations calculadas de Refinitiv
- El campo `base-region` del maestro es el que se actualiza en la base de datos con los exports
- Solo se procesan filas donde `percentage_num > 0`
- La transformación a formato largo ocurre en el `data_loader`, no en el pipeline principal

---

### 4. Allocations Externos (Allocations de Refinitiv - Regiones)
**Origen:** Feed de datos de Refinitiv/FIRSTRATE  
**Formato:** CSV  
**Separador:** `,` (coma) - **DIFERENTE A MONEDAS**  
**Encoding:** `latin-1`  
**Propósito:** Allocations externas de región desde Refinitiv

**DIFERENCIA CRÍTICA CON MONEDAS:**
> [!WARNING]
> **Las allocations externas de región vienen en formato ANCHO (wide format)**  
> Esto es diferente a las allocations de moneda que vienen en formato largo.

**Estructura del Archivo (Wide Format):**
- **Primera columna (sin nombre)**: Identificador del instrumento (código RIC o ISIN)
  - **IMPORTANTE:** Esta columna viene vacía/sin nombre y debe renombrarse a `instrument`
- **Columnas de regiones**: Cada región tiene su propia columna con el porcentaje
  - Ejemplos: `Africa Eme.`, `Europa Eme.`, `Asia Eme.`, `Latam`, `Norteamérica`, etc.

**Ejemplo de estructura:**
```
[columna vacía] | Africa Eme. | Asia Eme. | Europa Eme. | Latam | ...
LP65145598      | 5.2         | 12.8      | 45.3        | 36.7  | ...
US1234567890    | 0.0         | 8.5       | 91.5        | 0.0   | ...
```

**Transformación en el Pipeline:**
El archivo se lee en formato **ancho** y se transforma a formato **largo** (long format) en el `data_loader.py`:

1. **Renombrar primera columna:** La columna vacía se renombra a `instrument`
2. **Detectar formato:** Se verifica si contiene keywords de región (africa, asia, europe, latam, etc.)
3. **Transformación melt:** Se convierte a formato largo con columnas:
   - `instrument`: Identificador del instrumento
   - `class`: Nombre de la región (ej: "Africa Eme.", "Asia Eme.")
   - `percentage`: Porcentaje de allocation (convertido a numérico)

**Código de Referencia:** `src/data_loader.py` líneas 170-227 (carga y transformación wide → long)

**Notas:**
- **CRÍTICO:** La primera columna viene SIN NOMBRE y debe renombrarse a `instrument`
- **CRÍTICO:** El formato es ANCHO (wide), no largo como en monedas
- La columna `instrument` contiene un código RIC o ISIN
- Esta es la ÚNICA forma de cruzar con el maestro de Instrumentos (vía RIC o ISIN)
- Los porcentajes pueden venir con coma decimal (`,`) que se convierte a punto (`.`)
- La transformación a formato largo facilita el procesamiento posterior

---

## Reglas de Cruce de Datos

### Allocations Externos → Maestro de Instrumentos
**Proceso de Cruce:**
1. Normalizar campo `instrument` de Refinitiv (mayúsculas, trim)
2. Intentar cruzar contra columna `RIC` en Instrumentos
3. Si no hay match, intentar columna `Isin`
4. Si no hay match, intentar columna `Cusip`
5. Cuando hay match, copiar `ID`, `Nombre` y otra metadata al registro de allocation

**Código de Referencia:** `src/pipeline_region.py` (similar a pipeline de monedas)

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
| `base-region` | Maestro Instrumentos | Región actual en base de datos |
| `Base Región:` | Posiciones / Allocations Internos | Estado de allocation ("FALTA ALLOCATION", "ASIGNADO", "DISTRIBUIDOS") |
| `Tipo_Grupo` | Calculado en pipeline | Grupo del instrumento (Acciones, Bonos, Fondos/ETF) |
| `Tipo_Nombre` | Calculado en pipeline | Nombre descriptivo del tipo |
| `Region_Calculada` | Calculado desde Allocations Externos | Nueva región calculada |
| `Region_Antigua` | Calculado desde Allocations Internos | Región interna dominante |
| `Total_Pct_Ext` | Calculado desde Allocations Externos | Suma de % de allocations externas |
| `Flag` / `Semáforo` | Calculado basado en Total_Pct_Ext | Estado de validación |
| Columnas de regiones (LATAM, ASIA, etc.) | Pivoteado desde Allocations Externos | Porcentajes individuales por región |

---

## Notas Importantes

1. **ID es la Clave Universal:** Una vez que los instrumentos están cruzados, `ID` se usa para todos los joins
2. **Solo RIC/ISIN para Exports:** Las columnas de export `Id_ti` e `Id_ti_valor` solo deben contener RIC o ISIN (no Cusip)
3. **Region_Calculada es la Fuente de Verdad:** Para clasificación, siempre usar el valor calculado desde datos de Refinitiv
4. **Actualizaciones de base-region:** Los archivos de export se usan para actualizar el campo `base-region` en la base de datos
5. **Formato Ancho vs Largo:** 
   - Allocations Internos: viene en formato ancho, se transforma a largo
   - **Allocations Externos: viene en formato ancho (DIFERENTE A MONEDAS), se transforma a largo**
6. **Separador Diferente:** Allocations externos de región usan separador `,` (coma), no `;` como en monedas
