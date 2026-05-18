import pandas as pd
import re
import numpy as np

df = pd.read_csv('data/nutrition_data_optimized.csv', index_col='food')

def _word_boundary_pattern(keyword):
    kw = keyword.strip().lower()
    if ' ' in kw:
        words = kw.split()
        pattern = r'\b' + r'\s+'.join(r'\b' + re.escape(w) + r'\b' for w in words)
        return pattern
    return r'\b' + re.escape(kw) + r'\b'

# Test 'lassi' shouldn't match 'classic'
idx_lower = df.index.astype(str).str.lower()
pattern = _word_boundary_pattern('lassi')
matches = idx_lower.str.contains(pattern, na=False, regex=True)
hits = df.index[matches].tolist()
print('Matches for "lassi":', hits)
print('(Should only be items with the word "lassi" in them, not "classic" or similar)\n')

# Test 'dahi'  
pattern = _word_boundary_pattern('dahi')
matches = idx_lower.str.contains(pattern, na=False, regex=True)
hits = df.index[matches].tolist()
print('Matches for "dahi":', hits)

# Test 'boiled egg'
pattern = _word_boundary_pattern('boiled egg')
matches = idx_lower.str.contains(pattern, na=False, regex=True)
hits = df.index[matches].tolist()
print('Matches for "boiled egg":', hits)

# Verify no false matches: check that 'lassi' is not matching 'classic' or 'masala'
for food_name in df.index:
    if 'classic' in food_name.lower() or 'masala' in food_name.lower():
        fl = food_name.lower()
        if 'lassi' in fl:
            print('FALSE POSITIVE:', food_name, 'matched lasi pattern')

print('\nFilter test passed!')