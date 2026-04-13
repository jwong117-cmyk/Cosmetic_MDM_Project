
import pandas as pd
import numpy as np
import re # <-- Import for text cleaning
import unicodedata # <-- The ultimate unicode normalizer

def clean_cas(cas_series):
    """Removes hidden spaces, dashes, and standardizes blank CAS numbers."""
    clean = cas_series.astype(str).str.strip()
    return clean.replace(['nan', 'NaN', 'None', '', '-', '—'], np.nan)

def fix_punctuation(series):
    """Globally fixes full-width English letters, weird dashes, and curly quotes."""
    series = series.astype(str)
    
    # Chinese full-width punctuation
    series = series.str.replace('，', ', ', regex=False)
    series = series.str.replace('。', '. ', regex=False)
    series = series.str.replace('（', '(', regex=False)
    series = series.str.replace('）', ')', regex=False)
    
    # Curly other punctuation - curly quotations with straight, em-dashes with dash
    series = series.str.replace('‘', "'", regex=False)  # Left single
    series = series.str.replace('’', "'", regex=False)  # Right single
    series = series.str.replace('“', '"', regex=False)  # Left double (swapped to straight double)
    series = series.str.replace('”', '"', regex=False)  # Right double (swapped to straight double)
    series = series.str.replace('—', '-', regex=False) # Em-dash
    series = series.str.replace('–', '-', regex=False) # En-dash

    # Normalize full-width English letters (ａ -> a) and numbers
    series = series.apply(lambda x: unicodedata.normalize('NFKC', str(x)) if pd.notna(x) else x)
    
    return series.replace('nan', np.nan)

def clean_taiwan_text(text):
    """Strips Chinese characters to leave only the English ingredient names."""
    text = str(text)
    text = re.sub(r'[（\(].*?[）\)]', '', text) # Removes text in parentheses
    text = re.sub(r'[^\x00-\x7F]+', '', text)  # Removes non-English characters
    return text.strip().lower()

def main():
    print("Loading databases from data_raw and data_clean folders...")
    
    # 1. Load files (Added utf-8 encoding to handle Asian characters)
    ca_df = pd.read_csv('data_raw/Califronia_Banned_Chemiccals.csv', encoding='utf-8')
    tw_df = pd.read_csv('data_raw/Taiwan_Cosmetics_Prohibited_Ingredients.csv', encoding='utf-8')
    eu_df = pd.read_csv('data_raw/eu_annex.csv', encoding='utf-8')
    master_gold = pd.read_csv('data_clean/master_db_GOLD.csv', encoding='utf-8')
    aliases_gold = pd.read_csv('data_clean/aliases_db_GOLD.csv', encoding='utf-8')

    # Clean CAS in master for accurate mapping
    master_gold['cas_number'] = clean_cas(master_gold['cas_number'])

    print("Cleaning and standardizing regional lists to match GOLD language...")
    
    # ---------------------------------------------------------
    # 2. Clean California
    # ---------------------------------------------------------
    ca_clean = ca_df[['ingredient', 'cas_number', 'ban_year']].copy()
    ca_clean.columns = ['cleaned_name', 'cas_number', 'notes']
    ca_clean['cas_number'] = clean_cas(ca_clean['cas_number'])
    ca_clean['region'] = 'California'
    ca_clean['notes'] = 'Ban Year: ' + ca_clean['notes'].astype(str)

    # Apply Global Punctuation Fixer
    ca_clean['cleaned_name'] = fix_punctuation(ca_clean['cleaned_name']).str.strip().str.lower()
    ca_clean['notes'] = fix_punctuation(ca_clean['notes'])
    
    # ---------------------------------------------------------
    # 2. Clean Taiwan
    # ---------------------------------------------------------
    tw_clean = tw_df[['成分名稱', 'CAS_Number', '備註']].copy()
    tw_clean.columns = ['cleaned_name', 'cas_number', 'notes']
    tw_clean['cas_number'] = clean_cas(tw_clean['cas_number'])
    tw_clean['region'] = 'Taiwan'
    
    # Apply our Regex cleaning function to the ingredient names & Global Punctuation Fixer
    tw_clean['cleaned_name'] = fix_punctuation(tw_clean['cleaned_name']).apply(clean_taiwan_text)
    tw_clean['notes'] = fix_punctuation(tw_clean['notes'])

    # ---------------------------------------------------------
    # 4. Clean EU (UPGRADED for Bracketed Groupings - exploxded logic)
    # ---------------------------------------------------------
    eu_clean = eu_df[['Chemical name / INN', 'CAS Number', 'Regulation']].copy()
    eu_clean.columns = ['cleaned_name', 'cas_number', 'notes']
    eu_clean['region'] = 'EU'

    # Apply Global Punctuation Fixer FIRST before we explode
    eu_clean['cleaned_name'] = fix_punctuation(eu_clean['cleaned_name'])
    eu_clean['notes'] = fix_punctuation(eu_clean['notes'])
    
    # A. Remove the [1], [2], etc. reference tags from both columns
    eu_clean['cleaned_name'] = eu_clean['cleaned_name'].astype(str).str.replace(r'\[\d+\]', '', regex=True)
    eu_clean['cas_number'] = eu_clean['cas_number'].astype(str).str.replace(r'\[\d+\]', '', regex=True)

    # B. Intelligently extract ALL valid CAS numbers from the messy string
    # This looks for the strict CAS pattern (e.g., 123-45-6) and creates a clean list
    eu_clean['cas_number'] = eu_clean['cas_number'].apply(lambda x: re.findall(r'\b\d{2,7}-\d{2}-\d\b', str(x)))
    
    # If the list is empty (no CAS found), replace with [np.nan] so we don't lose the ingredient
    eu_clean['cas_number'] = eu_clean['cas_number'].apply(lambda x: x if len(x) > 0 else [np.nan])
    
    # Explode the CAS numbers into their own rows
    eu_clean = eu_clean.explode('cas_number')

    # C. Split multiple Ingredient Names separated by semicolons or newlines
    eu_clean['cleaned_name'] = eu_clean['cleaned_name'].astype(str).str.split(r'[;\n]')
    
    # Explode the names into their own rows
    eu_clean = eu_clean.explode('cleaned_name')
    
    # D. Final cleanup of the resulting rows
    eu_clean['cleaned_name'] = eu_clean['cleaned_name'].str.strip().str.lower()
    eu_clean = eu_clean[eu_clean['cleaned_name'] != ''] # Drop empty strings
    eu_clean = eu_clean.drop_duplicates()
    
    # ---------------------------------------------------------
    # 5. Save Cleaned Individual Files (Added utf-8-sig encoding here!)
    # ---------------------------------------------------------
    ca_clean.to_csv('data_clean/cleaned_california_banned.csv', index=False, encoding='utf-8-sig')
    tw_clean.to_csv('data_clean/cleaned_taiwan_banned.csv', index=False, encoding='utf-8-sig')
    eu_clean.to_csv('data_clean/cleaned_eu_banned.csv', index=False, encoding='utf-8-sig')
    print("Saved 3 cleaned regional lists into data_clean/")
    
    # ---------------------------------------------------------
    # 6. Build the Overarching Regulatory Table
    # ---------------------------------------------------------
    print("Mapping ingredients to build the overarching table...")
    combined_banned = pd.concat([ca_clean, tw_clean, eu_clean], ignore_index=True)

    # Create mapping dictionaries from GOLD datasets
    cas_to_gold_name = dict(zip(master_gold.dropna(subset=['cas_number'])['cas_number'], master_gold.dropna(subset=['cas_number'])['name']))
    cleaned_name_to_gold_name = dict(zip(master_gold['cleaned_name'], master_gold['name']))
    alias_to_cleaned_name = dict(zip(aliases_gold['alias_name'].astype(str).str.lower(), aliases_gold['master_id']))

    def find_gold_name(row):
        cas = row['cas_number']
        name = row['cleaned_name']
        
        # Priority 1: Match by CAS
        if pd.notna(cas) and cas in cas_to_gold_name:
            return cas_to_gold_name[cas]
        
        # Priority 2: Exact name match to GOLD
        if name in cleaned_name_to_gold_name:
            return cleaned_name_to_gold_name[name]
        
        # Priority 3: Match via Aliases database
        if name in alias_to_cleaned_name:
            master_id = alias_to_cleaned_name[name]
            if master_id in cleaned_name_to_gold_name:
                return cleaned_name_to_gold_name[master_id]
        
        # Priority 4: No match found, just Title Case the ingredient name
        return str(name).title()

    combined_banned['gold_ingredient_name'] = combined_banned.apply(find_gold_name, axis=1)

    # 6. Group and Aggregate the Overarching Data
    overarching_data = []

    for gold_name, group in combined_banned.groupby('gold_ingredient_name'):
        cas_list = group['cas_number'].dropna().unique()
        cas_val = ", ".join(cas_list) if len(cas_list) > 0 else np.nan
        
        regions = group['region'].unique()
        banned_ca = 'Yes' if 'California' in regions else 'No'
        banned_tw = 'Yes' if 'Taiwan' in regions else 'No'
        banned_eu = 'Yes' if 'EU' in regions else 'No'
        
        source_names = group['cleaned_name'].str.title().unique()
        aliases_list = [n for n in source_names if n.lower() != gold_name.lower()]
        
        master_id_matches = master_gold[master_gold['name'] == gold_name]['cleaned_name']
        if not master_id_matches.empty:
            master_id = master_id_matches.values[0]
            gold_aliases = aliases_gold[aliases_gold['master_id'] == master_id]['alias_name'].tolist()
            aliases_list.extend(gold_aliases)
            
        aliases_list = list(set(aliases_list))
        aliases_str = " | ".join(aliases_list) if aliases_list else np.nan
        
        notes_list = group['notes'].dropna().astype(str).unique()
        notes_str = " | ".join(notes_list) if len(notes_list) > 0 else np.nan
        
        overarching_data.append({
            'Gold_Ingredient_Name': gold_name,
            'CAS_Number': cas_val,
            'Banned_in_California': banned_ca,
            'Banned_in_Taiwan': banned_tw,
            'Banned_in_EU': banned_eu,
            'Aliases': aliases_str,
            'Notes': notes_str
        })

    overarching_df = pd.DataFrame(overarching_data)
    overarching_df = overarching_df.sort_values(by='Gold_Ingredient_Name').reset_index(drop=True)

    # Save the final table into data_clean
    overarching_df.to_csv('data_clean/Overarching_Regulatory_Table.csv', index=False)
    print(f"Success! Overarching table generated with {len(overarching_df)} unique ingredients in data_clean/")

if __name__ == "__main__":
    main()