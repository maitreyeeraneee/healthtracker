# TODO - HealthTracker Fixes & Improvements

## Meal generation (meal_generator.py)
- [x] Step 1: Inspect current meal generation constraints and where item counts are limited.
- [ ] Step 2: Implement dynamic item count selection (Breakfast/Lunch/Dinner: 2–5; Snack: 1–3) without changing UI structure.
- [ ] Step 3: Replace/expand slot recipe constraints and candidate keywords to include requested healthy foods (fruits, smoothies, oats, eggs, paneer, poha, upma, dosa/idli, sprouts, nuts, yogurt bowls, rice+dal, roti+sabzi, salads, boiled eggs, makhana, roasted chana, chilla, etc.).
- [ ] Step 4: Expand junk/unhealthy keyword hard-bans to include user-requested items (noodles, fried momos, chips, sugary drinks, desserts/excess desserts, processed junk keywords).
- [ ] Step 5: Improve logical food combining with conservative compatibility rules (keep lemon+curd ban; add light/heavy and curd pairing avoidance carefully).
- [ ] Step 6: Improve goal-aware selection tweaks (fiber/protein preferences; keep minimal structural changes).
- [ ] Step 7: Ensure generated meals never degrade to “protein shake only” for breakfast/snacks; enforce at least one carb/veg component for complete meals.

## BMI & Daily Calorie Needs tab (app.py)
- [ ] Step 8: Add validation for height/weight/age inputs and ensure values render (no hidden/missing state issues).
- [ ] Step 9: Fix any incorrect function imports/uses so BMI + categories + BMR + daily calories always appear.
- [ ] Step 10: Add safe fallbacks (N/A) so tab rendering never crashes when session_state keys are missing.

## Quality & verification
- [ ] Step 11: Run Streamlit app and resolve runtime/UI errors.
- [ ] Step 12: Smoke test meal generation for veg/vegan and confirm no banned/unhealthy items show.

