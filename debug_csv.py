
import pandas as pd
import os

file_path = r'c:\Users\Santiago\Documents\proyecto_conciliacion_fintech\data\allocations_region.csv'
print(f"Reading {file_path}...")

try:
    # Try reading with pandas, guessing separator
    df = pd.read_csv(file_path, sep=';', encoding='latin1')
    print("Columns:", df.columns.tolist())
    
    # Check for 'Base Región:'
    print(f"'Base Región:' in columns? {'Base Región:' in df.columns}")
    
    # Search for ID 9842
    # Convert ID to string for comparison
    df['ID'] = df['ID'].astype(str)
    row = df[df['ID'] == '9842']
    
    if not row.empty:
        print("Found ID 9842:")
        print(row[['ID', 'Base Región:']].to_string())
        # Check actual value bytes if needed
        val = row.iloc[0]['Base Región:']
        print(f"Value: '{val}'")
    else:
        print("ID 9842 NOT found in dataframe.")
        print("First 5 IDs:", df['ID'].head().tolist())

except Exception as e:
    print(f"Error reading file: {e}")
