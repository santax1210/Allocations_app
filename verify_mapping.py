import pandas as pd
from src.region_mapping import get_internal_region_name

df = pd.read_csv(r'data\final_output_FIRSTRATE_instruments (2)_region 1.csv', sep=';')
cols = [c.strip() for c in df.columns if c.strip() and c.strip() != 'Unnamed: 0']
unmapped = [c for c in cols if get_internal_region_name(c) is None]

print(f'Regiones sin mapeo: {len(unmapped)}')
if unmapped:
    for c in unmapped:
        print(f"  - {repr(c)}")
else:
    print('✓ Todas las regiones tienen mapeo!')
