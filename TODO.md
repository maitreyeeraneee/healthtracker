# TODO - NutriVerse Final Cleanup & Optimization

## Completed ✅

### Step 1: Rename app/project to "NutriVerse"
- [x] Update `st.set_page_config(page_title=...)` in `app.py` → Already set to "NutriVerse"
- [x] Update main header markdown in `app.py` → Already set to "NutriVerse"
- [x] Update README.md title and content to "NutriVerse"

### Step 2: Validate latest nutrition dataset integration
- [x] Confirmed all modules use `data/nutrition_data_optimized.csv` loaded via `utils/data_loader.py`
- [x] Cleaned dataset: removed 10 category-header entries and 147 duplicate rows (1749 foods remain)
- [x] Required columns exist at runtime (kcal, protein, carbs, fat, fiber, category, meal_types, unit_options)

### Step 3: Verify calculations/formulas
- [x] Fixed BMR/TDEE calculation - was returning same value for both (activity multiplier not applied)
- [x] Fixed calculate_macros - was using hardcoded user values, now uses goal-based ratios
- [x] Verified BMI, body fat %, ideal weight, protein target, water intake calculations
- [x] Verified macro ratios match goal (lose weight: 35/40/25, maintain: 25/50/25, gain muscle: 30/50/20)

### Step 4: Remove duplicates/repetitive/unrealistic dishes
- [x] Dataset deduplication: removed 147 duplicate food entries
- [x] Hard ban list in meal generator prevents exotic/unrealistic items
- [x] Protein shake limit enforced (max 1 per day)
- [x] Meal variety enforced via enforce_max_repeats (max 2 repeats per food per week)

### Step 5: Ensure filtering correctness everywhere
- [x] Unified veg/vegan/allergy filtering semantics across:
  - `utils/meal_generator.py` (filter_meals, _filter_by_category)
  - `utils/smart_swap.py` (_apply_diet_filter)
  - `utils/nutrition_assistant.py` (_apply_diet_filter)
- [x] Fixed veg_flag parameter passing ("None" → "none")

### Step 6: Remove unused code/dead code/temp/debug files
- [x] Rewrote root `utils.py` as compatibility shim (was broken with orphan functions)
- [x] Fixed `utils/__init__.py` (removed duplicate imports)
- [x] All functions properly exported from utils package

### Step 7: Run full app + tests
- [x] All imports verified successfully
- [x] BMR/TDEE calculations verified (BMR=1642, TDEE=2258 for test case)
- [x] Macro calculations verified (totals match target calories)
- [x] Meal generator produces 77 items across 7 days (realistic meal plans)
- [x] Smart swaps working correctly with dietary filters
- [x] Streamlit app launches successfully (HTTP 200)

## Summary of Changes

### Files Modified:
1. **data/nutrition_data_optimized.csv** - Cleaned: removed 10 category headers, 147 duplicates
2. **utils.py** - Rewritten as compatibility shim to utils/ package
3. **utils/__init__.py** - Fixed duplicate imports
4. **utils/meal_generator.py**:
   - Fixed `calculate_bmr_tdee()` - now correctly applies activity multiplier
   - Fixed `calculate_macros()` - now uses goal-based ratios directly
5. **app.py** - Added `random` import, fixed veg_flag parameter passing
6. **README.md** - Updated title to "NutriVerse"

### Key Bug Fixes:
1. **BMR/TDEE Bug**: Both returned same value because function used `calculate_targets()` which returned TDEE as daily_calories. Now calculates BMR and TDEE separately.
2. **Macros Bug**: Used hardcoded user profile (25yo male, 70kg, 170cm) regardless of input. Now uses goal-based macro ratios.
3. **Veg Filter Bug**: Passing "None" string instead of "none" caused filtering issues.

### Dataset Stats:
- Original: 1896 rows
- After cleanup: 1749 unique foods
- Removed: 10 category headers + 147 duplicates = 157 entries
- Categories: fruit, veg, grain, dairy, protein, snack, street-food, cafe, restaurant, quick-meal, drinks, gym, dessert, bakery, homemade

### Verification Results:
- All Python imports successful
- All calculation tests passed
- Meal generator produces realistic, varied meal plans
- Smart swaps respect dietary preferences
- Streamlit app launches without errors