import pandas as pd
import numpy as np
import re

# 1. Import your downloaded python file as a module
# This allows us to access all the lists you defined in that file!
from data_raw import top_10_ingredients_across_sephora_ulta_yes as top10

def clean_ingredient_text(text):
    """Cleans ingredient strings to match your GOLD database format."""
    text = str(text)
    # Remove text in parentheses like "(Shea) Butter" -> " Butter"
    text = re.sub(r'\(.*?\)', '', text)
    # Strip extra spaces and convert to lowercase
    return text.strip().lower()

def main():
    print("Loading Master Database for CAS lookup...")
    master_gold = pd.read_csv('data_match_reference/master_db_GOLD.csv')
    
    # Create a mapping dictionary: {cleaned_name: cas_number}
    name_to_cas = dict(zip(master_gold['cleaned_name'].astype(str).str.lower(), master_gold['cas_number']))

    print("Extracting and mapping product lists...")
    
    # 2. Map the variables from your file to their Retailer and Product Name
    product_mappings = [
        # SEPHORA PRODUCTS
        {"retailer": "Sephora", "product": "Rhode Glazing Milk", "ingredients": top10.rhode_milk_ingredients},
        {"retailer": "Sephora", "product": "Rhode Peptide Lip Treatment", "ingredients": top10.rhode_lip_ingredients},
        {"retailer": "Sephora", "product": "Biodance Bio-Collagen Real Deep Mask", "ingredients": top10.biodance_ingredients},
        {"retailer": "Sephora", "product": "The Ordinary Glycolic Acid 7% Toning Solution", "ingredients": top10.ordinary_ingredients},
        {"retailer": "Sephora", "product": "Tower 28 SOS Daily Rescue Facial Spray", "ingredients": top10.so_soft_ingredients},
        {"retailer": "Sephora", "product": "Touchland Power Mist Hydrating Hand Sanitizer", "ingredients": top10.touchland_ingredients},
        {"retailer": "Sephora", "product": "Summer Fridays Lip Butter Balm", "ingredients": top10.summer_fridays_ingredients},
        {"retailer": "Sephora", "product": "The Ordinary Niacinamide 10% + Zinc 1%", "ingredients": top10.ordinary_nia_ingredients},
        {"retailer": "Sephora", "product": "Sephora Collection Blackhead Peel-Off Mask", "ingredients": top10.blackhead_ingredients},
        
        # YESSTYLE PRODUCTS
        {"retailer": "YesStyle", "product": "Dr. Althea 345 Relief Cream", "ingredients": top10.dr_althea_345_ingredients},
        {"retailer": "YesStyle", "product": "Celimax Vita-A Retinal", "ingredients": top10.celimax_vita_a_ingredients},
        {"retailer": "YesStyle", "product": "SKIN1004 Hyalu-Cica Water-Fit Sun Serum", "ingredients": top10.skin1004_sunscreen_ingredients},
        {"retailer": "YesStyle", "product": "Beauty of Joseon Relief Sun", "ingredients": top10.BOJ_sunscreen_ingredients},
        {"retailer": "YesStyle", "product": "Purito Wonder Releaf Centella Cream", "ingredients": top10.purito_bamboo_cream},
        {"retailer": "YesStyle", "product": "APLB Glutathione Niacinamide Mask", "ingredients": top10.aplb_glutathione_sheet_ingredients},
        {"retailer": "YesStyle", "product": "Anua Peach 70 Niacin Serum", "ingredients": top10.anua_azelaic_serum_ingredients},
        {"retailer": "YesStyle", "product": "APLB Collagen Peptite Mask", "ingredients": top10.aplb_collagen_sheet},
        {"retailer": "YesStyle", "product": "SKIN1004 Madagascar Centella Ampoule", "ingredients": top10.skin1004_madagascar_ampoule_ingredients},
        {"retailer": "YesStyle", "product": "SKIN1004 Quick Clay Stick Mask", "ingredients": top10.skin1004_madagascar_quick_clay},
        
        # ULTA PRODUCTS
        {"retailer": "Ulta", "product": "IT Cosmetics CC+ Nude Glow SPF 40", "ingredients": top10.IT_LightweightSPF_list},
        {"retailer": "Ulta", "product": "La Roche-Posay Toleriane Foaming Face Wash", "ingredients": top10.laroshe_oily_list},
        {"retailer": "Ulta", "product": "Bobbi Brown Vitamin Enriched Face Base", "ingredients": top10.bobbibrown_list},
        {"retailer": "Ulta", "product": "OLEHENRIKSEN Pout Preserve", "ingredients": top10.peptide_lip_treatment_list},
        {"retailer": "Ulta", "product": "bareMinerals Tinted Moisturizer", "ingredients": top10.bareminerals_tint_moisturizer},
        {"retailer": "Ulta", "product": "The Ordinary Glycolic Acid 7% Exfoliating Toner", "ingredients": top10.ordinary_acid_list},
        {"retailer": "Ulta", "product": "Clinique Even Better Makeup SPF 15", "ingredients": top10.clinique_spf_15_ingredients},
        {"retailer": "Ulta", "product": "medicube Zero Pore Pad 2.0", "ingredients": top10.zeroporepad_list},
        {"retailer": "Ulta", "product": "TATCHA The Dewy Skin Cream", "ingredients": top10.tatcha_list},
        {"retailer": "Ulta", "product": "La Roche-Posay Toleriane Double Repair", "ingredients": top10.la_roche_moist_list}
    ]

    print("Exploding data into relational format...")
    # 3. Flatten the data into rows
    flattened_data = []
    for item in product_mappings:
        for ingredient in item['ingredients']:
            flattened_data.append({
                'ingredient_name': ingredient,
                'retailer': item['retailer'],
                'product_name': item['product']
            })

    # Convert to a Pandas DataFrame
    df = pd.DataFrame(flattened_data)

    # Clean the ingredient names using our custom function so they match GOLD perfectly
    df['cleaned_ingredient'] = df['ingredient_name'].apply(clean_ingredient_text)

    # 4. Map the CAS numbers!
    df['cas_number'] = df['cleaned_ingredient'].map(name_to_cas)

    # 5. Final Formatting
    # Reorder columns as requested and drop our temporary 'cleaned' column
    final_db = df[['ingredient_name', 'retailer', 'product_name', 'cas_number']]
    
    # Export the final database into your clean folder
    output_path = 'data_middle/top_10_product_ingrd.csv'
    final_db.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    print(f"\n✅ Success! Created {output_path} with {len(final_db)} ingredient entries.")
    print(f"Number of exact CAS number matches found: {final_db['cas_number'].notna().sum()}")

if __name__ == "__main__":
    main()


