
import pandas as pd

file_path = r'c:\Users\Santiago\Documents\proyecto_conciliacion_fintech\data\allocations_region.csv'
print(f"Reading {file_path} with utf-8...")

try:
    df = pd.read_csv(file_path, sep=';', encoding='utf-8')
    print("Columns:", df.columns.tolist())
    
    # Check for variants of Base Region
    cols = [c for c in df.columns if 'Region' in c or 'RegiÃ³n' in c or 'Región' in c]
    print("Region columns found:", cols)
    
    val_col = 'Base Región:'
    if val_col not in df.columns:
        # Try to find the matching column
        for c in cols:
            if 'Base' in c:
                val_col = c
                break
    print(f"Using column: {val_col}")
    
    # Filter ID
    df['ID'] = df['ID'].astype(str)
    row = df[df['ID'] == '9842']
    
    if not row.empty:
        print("Found ID 9842:")
        print(row[['ID', val_col]].to_string())
        val = row.iloc[0][val_col]
        print(f"Value raw: '{val}'")
    else:
        print("ID 9842 NOT found.")
        
except Exception as e:
    print(f"Error: {e}")
