import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib_venn import venn3
import os  # Import os to handle folders

# ---> Ensure the 'data_clean' folder exists before we try saving to it
output_dir = 'data_clean'
os.makedirs(output_dir, exist_ok=True)

# 1. Load the Data
df = pd.read_csv('data_match_reference/Overarching_Regulatory_Table.csv')

# Clean up 'Yes'/'No' strings into boolean values (True/False) for easier counting
df['EU_Ban'] = df['Banned_in_EU'].str.strip().str.title() == 'Yes'
df['TW_Ban'] = df['Banned_in_Taiwan'].str.strip().str.title() == 'Yes'
df['CA_Ban'] = df['Banned_in_California'].str.strip().str.title() == 'Yes'

# ---------------------------------------------------------
# VISUALIZATION 1: Bar Chart of Total Bans
# ---------------------------------------------------------
plt.figure(figsize=(10, 6))
sns.set_theme(style="whitegrid")

# Calculate totals
totals = {
    'EU': df['EU_Ban'].sum(),
    'Taiwan': df['TW_Ban'].sum(),
    'California (US)': df['CA_Ban'].sum()
}

# Create a barplot
ax = sns.barplot(x=list(totals.keys()), y=list(totals.values()), palette=["#415760", "#666666", "#C2DDE8"])
plt.title('Total Number of Banned Cosmetic Ingredients by Region', fontsize=16, fontweight='bold')
plt.ylabel('Number of Banned Ingredients', fontsize=12)
plt.xlabel('Regulatory Body', fontsize=12)

# Add data labels on top of the bars
for p in ax.patches:
    ax.annotate(format(int(p.get_height()), ','), 
                (p.get_x() + p.get_width() / 2., p.get_height()), 
                ha = 'center', va = 'center', 
                xytext = (0, 9), 
                textcoords = 'offset points',
                fontsize=11)

plt.tight_layout()

# ---> Save into the data_clean folder
plt.savefig(f'{output_dir}/Total_Number_Banned_Ingrd_Barchart.png', dpi=300, bbox_inches='tight')
plt.show(block=False)

# ---------------------------------------------------------
# VISUALIZATION 2: Venn Diagram of Regulatory Overlaps
# ---------------------------------------------------------
plt.figure(figsize=(10, 8))

# Get sets of ingredients banned in each region
set_eu = set(df[df['EU_Ban']]['Gold_Ingredient_Name'])
set_tw = set(df[df['TW_Ban']]['Gold_Ingredient_Name'])
set_ca = set(df[df['CA_Ban']]['Gold_Ingredient_Name'])

# Create the Venn diagram
v = venn3([set_eu, set_tw, set_ca], 
          ('EU', 'Taiwan', 'California (US)'),
          set_colors=("#415760", "#666666", "#C2DDE8"), 
          alpha=0.7)

plt.title('Overlap of Banned Cosmetic Ingredients', fontsize=16, fontweight='bold')

# ---> Save into the data_clean folder
plt.savefig(f'{output_dir}/Overlap_Banned_Ingrd_Venn_Diagram.png', dpi=300, bbox_inches='tight')
plt.show(block=False)

# ---------------------------------------------------------
# DATA PROCESSING: Ban Profiles
# ---------------------------------------------------------
# Create a function to label the specific overlap for each ingredient
def get_ban_profile(row):
    bans = []
    if row['EU_Ban']: bans.append('EU')
    if row['TW_Ban']: bans.append('Taiwan')
    if row['CA_Ban']: bans.append('CA')
    return " + ".join(bans) if bans else "None"

# Apply it to create a new column
df['Ban_Profile'] = df.apply(get_ban_profile, axis=1)

# Print a clean summary table of exactly how many ingredients fall into each bucket!
print("\n Summary of Regulatory Overlaps:")
overlap_summary = df['Ban_Profile'].value_counts().reset_index()
overlap_summary.columns = ['Where is it Banned?', 'Total Ingredients']
print(overlap_summary.to_string(index=False))

# ---> Save into the data_clean folder
overlap_summary.to_csv(f'{output_dir}/Regulatory_Overlap_Summary.csv', index=False)
print(f"\n Successfully exported the CSV and PNG charts to your '{output_dir}' folder!")

# Find and print universally banned ingredients
all_three_banned = df[df['EU_Ban'] & df['TW_Ban'] & df['CA_Ban']]
print("\nThe universally banned ingredients are:")
for item in all_three_banned['Gold_Ingredient_Name']:
    print(f"- {item}")

# Keep the pop-up windows open until the user closes them
plt.show()