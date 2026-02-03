"""
Script Maestro para Ejecutar Todos los Tests
Ejecuta todos los tests de verificación y muestra un resumen.
"""

import subprocess
import sys
from pathlib import Path


def run_test(test_file):
    """Ejecuta un test y retorna si pasó o falló."""
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        return result.returncode == 0, result.stdout
    except Exception as e:
        return False, str(e)


def main():
    print("="*80)
    print("EJECUTANDO TODOS LOS TESTS")
    print("="*80)
    
    tests = [
        ('tests/test_data_loading.py', 'Carga de Datos'),
        ('tests/test_mappings.py', 'Mapeos de Monedas y Regiones'),
    ]
    
    results = []
    
    for test_file, name in tests:
        print(f"\n{'='*80}")
        print(f"Ejecutando: {name}")
        print(f"{'='*80}")
        
        passed, output = run_test(test_file)
        results.append((name, passed))
        
        # Mostrar solo el resumen del test
        if output:
            lines = output.split('\n')
            # Buscar la sección de resumen
            in_summary = False
            for line in lines:
                if 'RESUMEN' in line or in_summary:
                    print(line)
                    in_summary = True
    
    # Resumen final
    print("\n" + "="*80)
    print("RESUMEN FINAL DE TODOS LOS TESTS")
    print("="*80)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
    
    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    
    print(f"\n  Total: {passed_count}/{total} suites de tests pasaron")
    print("="*80)
    
    sys.exit(0 if all(p for _, p in results) else 1)


if __name__ == "__main__":
    main()
