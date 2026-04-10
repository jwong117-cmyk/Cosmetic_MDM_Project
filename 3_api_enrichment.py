import pandas as pd
import requests
import urllib.parse
import time
import re

print("1. Loading databases...")
master_db = pd.read_csv('data_clean/master_db_v2.csv')
aliases_df = pd.read_csv('data_clean/aliases_db.csv')
new_aliases = []

# Function to ping the PubChem API
def fetch_pubchem(name):
    # Encode the name so it can be safely put into a URL (e.g., handles spaces)
    encoded_name = urllib.parse.quote(name)
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{encoded_name}/synonyms/JSON"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            synonyms = data['InformationList']['Information'][0].get('Synonym', [])
            
            # Use a Regular Expression (Regex) to find the strict CAS Number format
            cas_pattern = re.compile(r'^\d{2,7}-\d{2}-\d$')
            cas_numbers = [syn for syn in synonyms if cas_pattern.match(syn)]
            
            # If we find a CAS, return it and the top 5 synonyms
            if cas_numbers:
                return cas_numbers[0], synonyms[:5]
    except Exception:
        pass # If the API fails or the ingredient isn't found, just quietly pass
        
    return None, []

# Filter to ONLY the rows that are still missing a CAS number
missing_cas = master_db[master_db['cas_number'].isna()]

print(f"2. Hunting down {len(missing_cas)} missing CAS numbers via PubChem...")
print("   (This will take a few minutes to respect the API speed limits)")

found_count = 0

for idx, row in missing_cas.iterrows():
    cas, syns = fetch_pubchem(row['cleaned_name'])
    
    if cas:
        print(f"   [SUCCESS] Found {cas} for {row['name']}")
        master_db.at[idx, 'cas_number'] = cas
        found_count += 1
        
        # Add the new synonyms to our aliases list so our database gets smarter
        for syn in syns:
            new_aliases.append({'master_id': row['cleaned_name'], 'alias_name': syn})
            
    # CRITICAL: Wait 0.3 seconds before the next search so PubChem doesn't ban our IP address
    time.sleep(0.3) 

# ---------------------------------------------------------
# SAVE THE FINAL DATABASES
# ---------------------------------------------------------
print("\n3. Saving FINAL databases...")

# Append our new PubChem synonyms to the aliases table
if new_aliases:
    aliases_df = pd.concat([aliases_df, pd.DataFrame(new_aliases)]).drop_duplicates()

master_db.to_csv('data_clean/master_db_FINAL.csv', index=False)
aliases_df.to_csv('data_clean/aliases_db_FINAL.csv', index=False)

still_missing = master_db['cas_number'].isna().sum()
print(f"\nPIPELINE COMPLETE! Found {found_count} new CAS numbers.")
print(f"There are {still_missing} stubborn ingredients left.")
print("Check your 'data_clean' folder for the FINAL files!")