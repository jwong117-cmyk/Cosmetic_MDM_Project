import pandas as pd
import unicodedata
import re

# 1. Load the raw scraped data
print("Loading raw INCIDecoder data...")
df = pd.read_csv('data_raw/incidecoder_ingredients.csv')

# 2. Define the text-cleaning function
def clean_name(name):
    if pd.isna(name): return name
    
    # Normalize unicode (removes weird accents, trademark symbols, and invisible characters)
    clean = unicodedata.normalize('NFKD', str(name)).encode('ASCII', 'ignore').decode('utf-8')
    
    # Lowercase, strip outer whitespace, and remove double internal spaces
    return re.sub(r'\s+', ' ', clean.strip().lower())

print("Cleaning ingredient names...")
df['cleaned_name'] = df['name'].apply(clean_name)

# 3. Create the Master Database Structure
# We drop duplicates based on the new cleaned_name so every row is 100% unique
print("Building Master Database structure...")
master_db = df[['cleaned_name', 'name', 'cas_number', 'ec_number', 'url']].drop_duplicates(subset=['cleaned_name'])

# 4. Create the Aliases/Synonyms Table
# This maps the original scraped name to the new master cleaned name
aliases_db = master_db[['cleaned_name', 'name']].copy()
aliases_db.rename(columns={'cleaned_name': 'master_id', 'name': 'alias_name'}, inplace=True)

# 5. Save the output to your data_clean folder
master_db.to_csv('data_clean/master_db_v1.csv', index=False)
aliases_db.to_csv('data_clean/aliases_db.csv', index=False)

print("Success! Created 'master_db_v1.csv' and 'aliases_db.csv' in the data_clean folder.")