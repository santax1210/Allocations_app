"""
Test de Carga de Datos
Verifica que los archivos de datos se carguen correctamente.
"""

import pandas as pd
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_files_exist():
    """Verifica que todos los archivos de datos existan."""
    print("\n" + "="*80)
    print("TEST: Existencia de Archivos")
    print("="*80)
    
    required_files = [
        'data/allocations 2.csv',
        'data/allocations_region.csv',
        'data/final_output_FIRSTRATE_instruments (2)_region 1.csv',
        'data/instrument-types-2025-08-28.csv'
    ]
    
    missing = []
    for file in required_files:
        path = Path(file)
        if path.exists():
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} - NO ENCONTRADO")
            missing.append(file)
    
    if missing:
        print(f"\n  ✗ FALLO: {len(missing)} archivos faltantes")
        return False
    else:
        print(f"\n  ✓ ÉXITO: Todos los archivos existen")
        return True


def test_allocations_moneda_structure():
    """Verifica estructura del archivo de allocations de moneda."""
    print("\n" + "="*80)
    print("TEST: Estructura Allocations Moneda")
    print("="*80)
    
    try:
        df = pd.read_csv('data/allocations 2.csv', sep=';')
        
        required_cols = ['ID', 'Nombre', 'SubMoneda']
        missing_cols = [c for c in required_cols if c not in df.columns]
        
        if missing_cols:
            print(f"  ✗ FALLO: Columnas faltantes: {missing_cols}")
            return False
        
        print(f"  ✓ Filas: {len(df)}")
        print(f"  ✓ Columnas: {len(df.columns)}")
        print(f"  ✓ Columnas requeridas presentes")
        
        # Verificar que no haya filas completamente vacías
        empty_rows = df.isna().all(axis=1).sum()
        if empty_rows > 0:
            print(f"  ⚠ Advertencia: {empty_rows} filas completamente vacías")
        
        return True
        
    except Exception as e:
        print(f"  ✗ FALLO: Error al cargar archivo: {e}")
        return False


def test_allocations_region_structure():
    """Verifica estructura del archivo de allocations de región."""
    print("\n" + "="*80)
    print("TEST: Estructura Allocations Región")
    print("="*80)
    
    try:
        df = pd.read_csv('data/allocations_region.csv', sep=';')
        
        required_cols = ['ID', 'Nombre', 'Base Región:']
        missing_cols = [c for c in required_cols if c not in df.columns]
        
        if missing_cols:
            print(f"  ✗ FALLO: Columnas faltantes: {missing_cols}")
            return False
        
        print(f"  ✓ Filas: {len(df)}")
        print(f"  ✓ Columnas: {len(df.columns)}")
        print(f"  ✓ Columnas requeridas presentes")
        
        # Contar columnas de región
        region_cols = [c for c in df.columns if c not in ['ID', 'Nombre', 'Creado', 'Tipo Instrumento', 'Moneda', 'Nemo', 'Isin', 'Cusip', 'Ticker_BB', 'Currency', 'RIC', 'Base Región:']]
        print(f"  ✓ Columnas de región: {len(region_cols)}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ FALLO: Error al cargar archivo: {e}")
        return False


def test_refinitiv_structure():
    """Verifica estructura del archivo de Refinitiv."""
    print("\n" + "="*80)
    print("TEST: Estructura Refinitiv")
    print("="*80)
    
    try:
        df = pd.read_csv('data/final_output_FIRSTRATE_instruments (2)_region 1.csv', sep=';')
        
        print(f"  ✓ Filas: {len(df)}")
        print(f"  ✓ Columnas: {len(df.columns)}")
        
        # Verificar que haya columnas de región
        region_cols = [c for c in df.columns if c.strip() and c.strip() != 'Unnamed: 0']
        print(f"  ✓ Columnas de región: {len(region_cols)}")
        
        if len(region_cols) < 10:
            print(f"  ⚠ Advertencia: Pocas columnas de región detectadas")
        
        return True
        
    except Exception as e:
        print(f"  ✗ FALLO: Error al cargar archivo: {e}")
        return False


if __name__ == "__main__":
    results = []
    
    results.append(("Archivos Existen", test_files_exist()))
    results.append(("Allocations Moneda", test_allocations_moneda_structure()))
    results.append(("Allocations Región", test_allocations_region_structure()))
    results.append(("Refinitiv", test_refinitiv_structure()))
    
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
