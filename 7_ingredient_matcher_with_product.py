import pandas as pd
import numpy as np
import re

def clean_for_matching(text):
    """Deep cleans ingredient strings to maximize our chances of a match."""
    text = str(text).lower()
    
    # Handle weird multi-names like "Water/Aqua/Eau" by just taking the first one ("water")
    if '/' in text:
        text = text.split('/')[0]
        
    # Remove text in parentheses like "(Shea) Butter" -> " Butter"
    text = re.sub(r'\(.*?\)', '', text)
    
    # Fix weird formatting like "Microcrystalline Wax/Cera Microcristallina"
    text = text.replace('\n', '').strip()
    
    # Remove double spaces that might have been left behind
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def main():
    print("Loading databases...")
    # 1. Load the target product database (the one we made in the last step)
    products_df = pd.read_csv('data_middle/top_10_product_ingrd.csv')
    
    # 2. Load the Reference Databases
    master_gold = pd.read_csv('data_match_reference/master_db_GOLD.csv')
    aliases_gold = pd.read_csv('data_match_reference/aliases_db_GOLD.csv')
    reg_table = pd.read_csv('data_match_reference/Overarching_Regulatory_Table.csv')

    print("Building lookup dictionaries...")
    # --- BUILD LOOKUPS ---
    # Lookup 1: Master DB (Cleaned Name -> CAS)
    master_dict = dict(zip(master_gold['cleaned_name'].astype(str).str.lower(), master_gold['cas_number']))
    
    # Lookup 2: Alias DB (Alias -> Master ID)
    alias_to_master = dict(zip(aliases_gold['alias_name'].astype(str).str.lower(), aliases_gold['master_id']))
    # Master ID -> CAS
    master_id_to_cas = dict(zip(master_gold['name'], master_gold['cas_number']))

    # Lookup 3: Regulatory Table Data (Gold Name -> Ban Status)
    reg_status_dict = reg_table.set_index('Gold_Ingredient_Name')[
        ['Banned_in_California', 'Banned_in_Taiwan', 'Banned_in_EU']
    ].to_dict('index')

    def waterfall_match(raw_ingredient):
        """The Waterfall Engine: Tries multiple databases to find the CAS and Gold Name."""
        clean_name = clean_for_matching(raw_ingredient)
        
        cas = np.nan
        gold_name = clean_name.title()
        
        # Level 1: Check Master DB directly
        if clean_name in master_dict:
            cas = master_dict[clean_name]
            
        # Level 2: Check Aliases DB
        elif clean_name in alias_to_master:
            m_id = alias_to_master[clean_name]
            gold_name = str(m_id).title() # Use the Master ID as the official Gold Name
            if m_id in master_id_to_cas:
                cas = master_id_to_cas[m_id]
                
        # Level 3: Check Overarching Regulatory Table Aliases
        # (This loops through the reg table to see if the name is buried in the 'Aliases' string)
        else:
            for index, row in reg_table.iterrows():
                if pd.notna(row['Aliases']):
                    # Split the "Alias 1 | Alias 2" string into a list and lower case them
                    reg_aliases = [a.strip().lower() for a in str(row['Aliases']).split('|')]
                    if clean_name in reg_aliases:
                        cas = row['CAS_Number']
                        gold_name = row['Gold_Ingredient_Name']
                        break # Stop looking, we found it!
                        
        return pd.Series([clean_name, gold_name, cas])

    print("Running ingredients through the Waterfall Engine. This may take a few seconds...")
    # Apply the matching function to create 3 new columns
    products_df[['cleaned_ingredient_name', 'gold_ingredient_name', 'matched_cas_number']] = products_df['ingredient_name'].apply(waterfall_match)

    print("Pulling Regulatory Ban Status...")
    # Map the ban status using the gold_ingredient_name we just figured out
    def get_ban_status(gold_name, region):
        if pd.isna(gold_name): return 'No'
        # Look up the gold name in our dictionary, default to 'No' if not found
        return reg_status_dict.get(gold_name, {}).get(f'Banned_in_{region}', 'No')

    products_df['Banned_CA'] = products_df['gold_ingredient_name'].apply(lambda x: get_ban_status(x, 'California'))
    products_df['Banned_TW'] = products_df['gold_ingredient_name'].apply(lambda x: get_ban_status(x, 'Taiwan'))
    products_df['Banned_EU'] = products_df['gold_ingredient_name'].apply(lambda x: get_ban_status(x, 'EU'))

    # Organize the final output columns beautifully
    final_cols = [
        'retailer', 
        'product_name', 
        'ingredient_name',        # The raw label name
        'cleaned_ingredient_name', # How our computer read it
        'gold_ingredient_name',    # The official database name
        'matched_cas_number',
        'Banned_CA', 
        'Banned_TW', 
        'Banned_EU'
    ]
    final_df = products_df[final_cols]

    # Save to CSV
    output_path = 'data_clean/Final_Product_Ingredient_Analysis.csv'
    final_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    # Print a fun summary report!
    print("\n" + "="*50)
    print("✨ ANALYSIS COMPLETE ✨")
    print("="*50)
    print(f"Total Ingredients Processed: {len(final_df)}")
    print(f"Successfully Matched with a CAS: {final_df['matched_cas_number'].notna().sum()}")
    
    banned_items = final_df[(final_df['Banned_CA'] == 'Yes') | (final_df['Banned_TW'] == 'Yes') | (final_df['Banned_EU'] == 'Yes')]
    print(f"⚠️ POTENTIAL REGULATORY FLAGS FOUND: {len(banned_items)}")
    print(f"Data saved to: {output_path}")

if __name__ == "__main__":
    main()

