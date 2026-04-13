import pandas as pd
import unicodedata
import re

# We reuse the exact same cleaning function so the names match perfectly
def clean_name(name):
    if pd.isna(name): return name
    clean = unicodedata.normalize('NFKD', str(name)).encode('ASCII', 'ignore').decode('utf-8')
    return re.sub(r'\s+', ' ', clean.strip().lower())

print("1. Loading your Master Database...")
master_db = pd.read_csv('data_clean/master_db_v1.csv')

# ---------------------------------------------------------
# MERGE 1: EU CosIng Database (Botanicals & Cosmetics)
# ---------------------------------------------------------
print("2. Loading and cleaning EU CosIng data (This might take a few seconds)...")
try:
    cosing_df = pd.read_csv('data_raw/cosing_data.csv')
    
    # Clean the CosIng names to match our master format
    cosing_df['cleaned_name'] = cosing_df['INCI name'].apply(clean_name)
    
    # Drop duplicates to prevent exploding the merge
    cosing_unique = cosing_df.drop_duplicates(subset=['cleaned_name'])
    
    print("   -> Merging CosIng...")
    master_db = pd.merge(master_db, cosing_unique[['cleaned_name', 'CAS No', 'EC No']], on='cleaned_name', how='left')
    
    # Fill in the blanks: If cas_number is empty, use the 'CAS No' from CosIng
    master_db['cas_number'] = master_db['cas_number'].fillna(master_db['CAS No'])
    master_db['ec_number'] = master_db['ec_number'].fillna(master_db['EC No'])
    
    # Clean up the temporary columns
    master_db.drop(columns=['CAS No', 'EC No'], inplace=True)
except Exception as e:
    print(f"Warning: Issue with CosIng merge. Error: {e}")

# ---------------------------------------------------------
# MERGE 2: US EPA TSCA Database (Pure Chemicals)
# ---------------------------------------------------------
print("3. Loading and cleaning US EPA data (This is a large file)...")
try:
    # EPA data has some mixed data types, so we use low_memory=False
    epa_df = pd.read_csv('data_raw/epa_tsca.csv', low_memory=False)
    
    # Clean the EPA chemical names
    epa_df['cleaned_name'] = epa_df['ChemName'].apply(clean_name)
    epa_unique = epa_df.drop_duplicates(subset=['cleaned_name'])
    
    print("   -> Merging US EPA...")
    master_db = pd.merge(master_db, epa_unique[['cleaned_name', 'CASRN']], on='cleaned_name', how='left')
    
    # Fill in any remaining blank CAS numbers with the EPA's CASRN
    master_db['cas_number'] = master_db['cas_number'].fillna(master_db['CASRN'])
    
    # Clean up the temporary column
    master_db.drop(columns=['CASRN'], inplace=True)
except Exception as e:
    print(f"Warning: Issue with EPA merge. Error: {e}")

# ---------------------------------------------------------
# MERGE 3: Custom Manual Overrides (The 5% Leftovers)
# ---------------------------------------------------------
print("4. Applying Manual Overrides from data_raw/manual_overrides.csv...")
try:
    overrides_df = pd.read_csv('data_raw/manual_overrides.csv')
    
    # Clean the names in your override file just in case you capitalized something
    overrides_df['cleaned_name'] = overrides_df['cleaned_name'].apply(clean_name)
    
    # Drop duplicates just to be safe
    overrides_unique = overrides_df.drop_duplicates(subset=['cleaned_name'])
    
    # Merge with the master database
    master_db = pd.merge(master_db, overrides_unique[['cleaned_name', 'manual_cas_number']], on='cleaned_name', how='left')
    
    # Fill in blanks with your manual research
    master_db['cas_number'] = master_db['cas_number'].fillna(master_db['manual_cas_number'])
    
    # Clean up the temporary column
    master_db.drop(columns=['manual_cas_number'], inplace=True)
    print("   -> Overrides successfully applied!")
except FileNotFoundError:
    print("   -> No manual_overrides.csv file found. Skipping this step.")
except Exception as e:
    print(f"Warning: Issue with Overrides merge. Error: {e}")


# ---------------------------------------------------------
# SAVE VERSION 2
# ---------------------------------------------------------
print("5. Saving enriched database...")
master_db.to_csv('data_clean/master_db_v2.csv', index=False)

# Calculate how many CAS numbers are still missing
missing_count = master_db['cas_number'].isna().sum()
print(f"\nSUCCESS! Created 'master_db_v2.csv'.")
print(f"There are currently {missing_count} ingredients still missing a CAS number.")