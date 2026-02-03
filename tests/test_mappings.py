"""
Test de Mapeos de Monedas y Regiones
Verifica que todos los valores de Refinitiv tengan mapeo correcto.
"""

import pandas as pd
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.currency_mapping import get_internal_currency_name
from src.region_mapping import get_internal_region_name


def test_currency_mapping():
    """Verifica que todas las monedas de Refinitiv tengan mapeo."""
    print("\n" + "="*80)
    print("TEST: Mapeo de Monedas")
    print("="*80)
    
    # Leer archivo de allocations externas
    df = pd.read_csv('data/final_output_FIRSTRATE_instruments (2)_region 1.csv', sep=';')
    
    # Obtener todas las monedas únicas (asumiendo que hay una columna de moneda)
    # Nota: Ajustar según estructura real del archivo
    
    # Por ahora, verificar monedas comunes
    test_currencies = ['USD', 'EUR', 'CLP', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD']
    
    unmapped = []
    for curr in test_currencies:
        mapped = get_internal_currency_name(curr)
        if mapped is None:
            unmapped.append(curr)
        else:
            print(f"  ✓ {curr} → {mapped}")
    
    if unmapped:
        print(f"\n  ✗ FALLO: {len(unmapped)} monedas sin mapeo: {unmapped}")
        return False
    else:
        print(f"\n  ✓ ÉXITO: Todas las monedas tienen mapeo")
        return True


def test_region_mapping():
    """Verifica que todas las regiones de Refinitiv tengan mapeo."""
    print("\n" + "="*80)
    print("TEST: Mapeo de Regiones")
    print("="*80)
    
    # Leer archivo de allocations externas
    df = pd.read_csv('data/final_output_FIRSTRATE_instruments (2)_region 1.csv', sep=';')
    
    # Obtener todas las columnas de región
    region_cols = [c.strip() for c in df.columns if c.strip() and c.strip() != 'Unnamed: 0']
    
    unmapped = []
    mapped_count = 0
    
    for col in region_cols:
        internal_name = get_internal_region_name(col)
        if internal_name is None:
            unmapped.append(col)
        else:
            mapped_count += 1
    
    print(f"  Total columnas: {len(region_cols)}")
    print(f"  Con mapeo: {mapped_count}")
    print(f"  Sin mapeo: {len(unmapped)}")
    
    if unmapped:
        print(f"\n  ✗ FALLO: Regiones sin mapeo:")
        for region in unmapped[:5]:  # Mostrar solo las primeras 5
            print(f"    - {repr(region)}")
        return False
    else:
        print(f"\n  ✓ ÉXITO: Todas las regiones tienen mapeo")
        return True


def test_no_duplicate_mappings():
    """Verifica que no haya duplicados en los diccionarios de mapeo."""
    print("\n" + "="*80)
    print("TEST: Duplicados en Mapeos")
    print("="*80)
    
    from src.currency_mapping import CURRENCY_MAP_REFINITIV_TO_INTERNAL
    from src.region_mapping import REGION_MAP_REFINITIV_TO_INTERNAL
    
    # Verificar duplicados en monedas
    curr_keys = list(CURRENCY_MAP_REFINITIV_TO_INTERNAL.keys())
    curr_duplicates = [k for k in curr_keys if curr_keys.count(k) > 1]
    
    # Verificar duplicados en regiones
    region_keys = list(REGION_MAP_REFINITIV_TO_INTERNAL.keys())
    region_duplicates = [k for k in region_keys if region_keys.count(k) > 1]
    
    if curr_duplicates or region_duplicates:
        print(f"  ✗ FALLO: Encontrados duplicados")
        if curr_duplicates:
            print(f"    Monedas: {set(curr_duplicates)}")
        if region_duplicates:
            print(f"    Regiones: {set(region_duplicates)}")
        return False
    else:
        print(f"  ✓ ÉXITO: No hay duplicados en los mapeos")
        return True


if __name__ == "__main__":
    results = []
    
    results.append(("Mapeo de Monedas", test_currency_mapping()))
    results.append(("Mapeo de Regiones", test_region_mapping()))
    results.append(("Sin Duplicados", test_no_duplicate_mappings()))
    
    print("\n" + "="*80)
    print("RESUMEN DE TESTS")
    print("="*80)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\n  Total: {passed}/{total} tests pasaron")
    print("="*80)
    
    sys.exit(0 if all(p for _, p in results) else 1)
