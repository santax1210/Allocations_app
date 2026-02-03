# Proyecto Conciliación Fintech - Documentación

## Estructura de Documentación

La documentación está organizada por tipo de validación:

### 📁 [moneda/](moneda/)
Documentación completa para **Validación de Monedas**
- Reglas de negocio (umbral 90%, flags, etc.)
- Estructura de archivos de entrada
- Flujo del pipeline
- Exports (Balanceados vs No Balanceados)

### 📁 [region/](region/)
Documentación para **Validación de Regiones** (pendiente)
- Reglas de negocio específicas para regiones
- Estructura de archivos
- Flujo del pipeline de regiones

---

## Navegación Rápida

### Validación de Monedas
- [Reglas de Negocio](moneda/business_rules.md) - Clasificación, flags, inconsistencias
- [Estructura de Archivos](moneda/file_structures.md) - Inputs, columnas, cruces
- [Flujo del Pipeline](moneda/pipeline_flow.md) - Pasos 1-6, exports

### Validación de Regiones
- [Estructura de Archivos](region/file_structures.md) - Inputs, columnas, cruces (formato ancho)
- [Reglas de Negocio](region/business_rules.md) - Clasificación, flags, inconsistencias (adaptado de monedas)
- [Flujo del Pipeline](region/pipeline_flow.md) - Pasos 1-6, exports (formato ancho → largo)

---

## Reglas Críticas (Monedas)

### 1. Cruce de Allocations Externos
- ✅ Cruzar SOLO por RIC o ISIN (columna `instrument`)
- ✅ El `ID` del maestro es la clave universal después del cruce
- ❌ Nunca asumir otras columnas en datos de Refinitiv

### 2. Identificadores de Export
- ✅ `Id_ti` e `Id_ti_valor` deben contener SOLO RIC o Isin
- ❌ Nunca exportar Cusip en estos campos
- ✅ Usar `matched_by` para determinar cuál se usó

### 3. Clasificación Balanceado
- ✅ Basado SOLO en `Moneda_Calculada`
- ✅ Umbral: 90% (no 60%)
- ❌ Ignorar `Moneda_Interna` para división de exports

### 4. Export de No Balanceados
- ✅ `SubMoneda` = Valor NUEVO (Moneda_Calculada)
- ✅ `Moneda_Anterior` = Valor VIEJO (de BD)
- ✅ Se usa para ACTUALIZAR base de datos

---

## Cuándo Consultar Esta Documentación

- ✅ Antes de modificar lógica del pipeline
- ✅ Al agregar nuevas fuentes de datos
- ✅ Al cambiar formatos de export
- ✅ Al depurar problemas de cruce de datos
- ✅ Antes de hacer suposiciones sobre columnas

---

## Mantenimiento

Actualizar documentación cuando:
- Cambien reglas de negocio
- Se agreguen nuevas fuentes de datos
- Se modifiquen formatos de export
- Se agreguen/cambien pasos del pipeline

**Última Actualización:** 2026-01-30
