# TODO - Smart Swap safety + improvements

## Step 1
- [ ] Fix veg_pref TypeError by making `_apply_diet_filter()` parameter names consistent everywhere in `utils/smart_swap.py`.

## Step 2
- [ ] Replace Smart Swap free-typed input with a searchable dropdown/selectbox based on `nutrition_df.index` (dataset foods) in `utils/smart_swap.py`.

## Step 3
- [ ] Improve swap suggestions ranking so alternatives are realistic healthy meal options (avoid boring outputs) in `utils/smart_swap.py`.

## Step 4
- [ ] Remove the banned Tip line from `utils/nutrition_assistant.py`.

## Step 5
- [ ] Add safe error handling + minor duplicate/robustness improvements where needed in swap/assistant logic.

## Step 6
- [ ] Run `python -m py_compile` checks for syntax/import errors.

## Step 7
- [ ] (Optional) Run `streamlit run app.py` if lightweight in this environment.

