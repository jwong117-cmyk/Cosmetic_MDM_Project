import pandas as pd

print("1. Loading final cleaned databases...")
master_db = pd.read_csv('data_middle/master_db_FINAL.csv')
aliases_db = pd.read_csv('data_middle/aliases_db_FINAL.csv')

# Separate the database into "Has CAS" and "No CAS"
# We only want to deduplicate the ones that actually have a CAS number!
has_cas = master_db[master_db['cas_number'].notna()]
no_cas = master_db[master_db['cas_number'].isna()]

print("2. Searching for duplicate CAS numbers...")
# Group by the CAS number
grouped = has_cas.groupby('cas_number')

new_aliases = []
golden_records = []
duplicate_count = 0

for cas, group in grouped:
    if len(group) > 1:
        duplicate_count += (len(group) - 1)
        
        # Pick the first one in the group to be the "Golden Record"
        golden = group.iloc[0]
        golden_records.append(golden)
        
        # Take the REST of the ingredients in this group and turn them into aliases!
        for idx, row in group.iloc[1:].iterrows():
            new_aliases.append({
                'master_id': golden['cleaned_name'], 
                'alias_name': row['cleaned_name'] # The alternative name is now an alias
            })
    else:
        # If there's only one ingredient for this CAS, it's already a Golden Record
        golden_records.append(group.iloc[0])

print(f"   -> Found and resolved {duplicate_count} duplicates!")

# 3. Rebuild the perfectly clean Master Database
golden_df = pd.DataFrame(golden_records)
final_master_db = pd.concat([golden_df, no_cas])

# 4. Update the Aliases Database with the new alternative names
if new_aliases:
    aliases_db = pd.concat([aliases_db, pd.DataFrame(new_aliases)]).drop_duplicates()

# 5. Save the ultimate versions
print("3. Saving the DEDUPLICATED Gold Standard databases...")
final_master_db.to_csv('data_match_reference/master_db_GOLD.csv', index=False)
aliases_db.to_csv('data_match_reference/aliases_db_GOLD.csv', index=False)

print("SUCCESS! Your Master Data is now perfectly resolved.")