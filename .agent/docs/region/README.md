# Validación de Regiones - Documentación

> [!IMPORTANT]
> **Esta documentación es EXCLUSIVA para Validación de Regiones.**  
> **NO confundir con la validación de Monedas** (ver `../moneda/`)

---

Esta carpeta contiene toda la documentación relacionada con la **Validación de Regiones**.

## Archivos

### [file_structures.md](file_structures.md)
Estructura de archivos de entrada para validación de regiones:
- Posiciones (misma que monedas)
- Instrumentos (maestro) - usa `base-region` en lugar de `SubMoneda`
- Allocations Internos (regiones) - usa `Base Región:` en lugar de `Moneda:`
- Allocations Externos (Refinitiv - regiones) - **formato ANCHO**, diferente a monedas
- Reglas de cruce de datos

### [business_rules.md](business_rules.md)
Reglas de negocio específicas para validación de regiones:
- Clasificación de Region_Calculada (umbral 90%)
- Lógica de Flag/Semáforo (60-120% VALIDO)
- Cálculo de fechas de export
- División Balanceado vs No Balanceado
- Detección de inconsistencias
- Normalización de regiones (en revisión)

### [pipeline_flow.md](pipeline_flow.md)
Flujo del pipeline de validación de regiones:
- 6 pasos del pipeline (filtrar, cruzar, clasificar, validar)
- Preparación de exports (balanceados vs no balanceados)
- Diagrama de flujo de datos
- Comparación detallada con pipeline de monedas

## Diferencias Clave con Monedas

| Aspecto | Monedas | Regiones |
|---------|---------|----------|
| **Columna en Maestro** | `SubMoneda` | `base-region` |
| **Columna en Allocations Internos** | `Moneda:` | `Base Región:` |
| **Formato Allocations Externos** | Largo (long) | **Ancho (wide)** |
| **Separador Allocations Externos** | `;` (punto y coma) | `,` (coma) |
| **Columnas de datos** | USD, CLP, EUR, etc. | LATAM, ASIA, EUROPA, etc. |

## Resumen Rápido

**Objetivo:** Validar y clasificar instrumentos por región usando datos de Refinitiv

**Umbral de Clasificación:** 90% (mismo que monedas)
- >= 90% en una región → Región específica
- < 90% → Balanceado

**Formato Crítico:**
- ⚠️ **Allocations externas vienen en formato ANCHO** (cada región es una columna)
- ⚠️ La primera columna viene SIN NOMBRE y debe renombrarse a `instrument`
- ⚠️ Se transforma a formato largo en el `data_loader.py`

**Última Actualización:** 2026-02-02
