# Validación de Monedas - Documentación

Esta carpeta contiene toda la documentación relacionada con la **Validación de Monedas**.

## Archivos

### [business_rules.md](business_rules.md)
Reglas de negocio específicas para validación de monedas:
- Clasificación de Moneda_Calculada (umbral 90%)
- Lógica de FLAG (estado de cambio: Caso_1, Caso_2, Caso_3)
- Escalado proporcional y Total_Pre_Escalado
- Cálculo de fechas de export
- División Balanceado vs No Balanceado
- Detección de inconsistencias

### [file_structures.md](file_structures.md)
Estructura de archivos de entrada para validación de monedas:
- Posiciones
- Instrumentos (maestro)
- Allocations Internos (monedas)
- Allocations Externos (Refinitiv - monedas)
- Reglas de cruce de datos

### [pipeline_flow.md](pipeline_flow.md)
Flujo completo del pipeline de validación de monedas:
- PASO 1-6 del pipeline
- Preparación de exports
- Diagramas de flujo de datos

## Resumen Rápido

**Objetivo:** Validar y clasificar instrumentos por moneda usando datos de Refinitiv

**Umbral de Clasificación:** 90%
- >= 90% en una moneda → Moneda específica
- < 90% → Balanceado

**Exports:**
- **Balanceados:** Formato completo con allocations por moneda
- **No Balanceados:** Formato simple (5 columnas) para actualizar BD

**Última Actualización:** 2026-01-30
