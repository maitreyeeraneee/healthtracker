import pandas as pd

import numpy as np
import random
import re
from typing import Dict, List, Tuple, Optional, Any
from .data_loader import get_display_amount_and_unit

# Constants
# Keep app contract: app.py groups/prints Breakfast/Lunch/Dinner/Snack.
MEAL_SLOTS = ['Breakfast', 'Lunch', 'Dinner', 'Snack']


ACTIVITY_MULTIPLIERS = {
    'sedentary': 1.2,
    'lightly active': 1.375,
    'moderately active': 1.55,
    'very active': 1.725,
    'extra active': 1.9
}
GOAL_ADJUSTMENTS = {
    'lose weight': -500,
    'maintain': 0,
    'gain muscle': 500
}
MACRO_RATIOS = {
    'lose weight': {'protein': 0.35, 'carbs': 0.40, 'fat': 0.25},
    'maintain': {'protein': 0.25, 'carbs': 0.50, 'fat': 0.25},
    'gain muscle': {'protein': 0.30, 'carbs': 0.50, 'fat': 0.20}
}

# Strict realistic, commonly eaten Indian foods to avoid exotic/uncommon items.
# Generator will prefer candidates from this allow-list.
INDIAN_REALISTIC_FOOD_ALLOWLIST = {
    # Breakfast / morning + light snacks (India-first)
    'Poha', 'Upma', 'Dhokla', 'Idli', 'Dosa', 'Khichdi', 'Oatmeal',
    'Curd', 'Dahi', 'Lassi', 'Milk', 'Greek Yogurt', 'Yogurt',
    'Sprouts', 'Oats', 'Egg', 'Egg Omelette', 'Veg Omelette',
    'Bread', 'Brown Bread', 'Paratha', 'Chapati', 'Roti', 'Tandoori Roti',
    'Sambar', 'Rasam', 'Misal Pav', 'Idli Sambar',

    # Protein-friendly breakfast bases
    'Paneer', 'Palak Paneer', 'Paneer Butter Masala', 'Paneer Tikka',

    # Lunch/Dinner staples
    'Dal', 'Dal Tadka', 'Dal Fry', 'Moong Dal', 'Masoor Dal',
    'Chana Masala', 'Chole', 'Rajma',
    'Aloo Gobi', 'Bhindi Masala', 'Baingan Bharta', 'Mixed Vegetable Curry',
    'Roti', 'Chapati',
    'Rice', 'Brown Rice', 'Basmati Rice', 'Jeera Rice', 'Curd Rice',
    'Quinoa', 'Biryani', 'Chicken Biryani', 'Veg Biryani',

    # Protein (veg + non-veg)
    'Soya', 'Soybeans', 'Tofu', 'Chickpeas', 'Lentils', 'Tempeh', 'Seitan',
    'Chicken', 'Chicken Breast', 'Chicken Tikka',
    'Eggs', 'Egg',

    # Snacks / healthy bites
    'Fruit', 'Apple', 'Banana', 'Orange', 'Mango', 'Papaya', 'Guava',
    'Strawberries', 'Blueberries', 'Watermelon', 'Dates', 'Grapes',
    'Pomegranate', 'Kiwi', 'Coconut',
    'Roasted Chana', 'Chana', 'Chana Masala',
    'Nuts', 'Almonds', 'Walnuts', 'Peanuts', 'Peanut Butter',
    'Seeds', 'Chia Seeds', 'Flax Seeds',

    # Healthy drinks
    'Green Tea', 'Masala Chai', 'Lemon Water', 'Fruit Smoothie',
    'Protein Smoothie', 'Buttermilk', 'Yogurt Drink',

    # Gym / weight-loss friendly items (commonly available)
    'Skim Milk', 'Low-fat Curd', 'Low-fat Yogurt',
    'Boiled Eggs', 'Egg Whites',
    'Chicken Breast', 'Tuna'
}


# Hard ban list: remove known exotic/unrealistic items even if they exist in data.
INDIAN_EXOTIC_HARDBAN = {
    # Explicit user-requested impractical/exotic removals
    'lobster', 'mahi mahi', 'mahi', 'crab', 'sushi', 'ramen', 'ravioli',

    # Other items that are not desired for this app scope
    'falafel', 'tacos', 'enchiladas', 'pad thai', 'kimchi', 'samosa',

    # Seafood / meats that currently exist in the dataset but should be removed
    'swordfish', 'mackerel', 'shrimp', 'prawns', 'oysters', 'cod', 'tilapia', 'tuna',
    'salmon', 'anchovies', 'sardines', 'calamari', 'octopus',

    # Non-veg meats that are intentionally avoided by name-bans
    'pork', 'beef', 'duck', 'lamb',

    # Ingredient-only / impractical foods to eat alone as a meal
    'ginger', 'garlic', 'turmeric', 'cumin', 'coriander', 'cardamom',
    'clove', 'cinnamon', 'nutmeg', 'saffron', 'mustard seeds',
    'fenugreek', 'asafoetida', 'curry leaves', 'bay leaf',
    'black pepper', 'red chili', 'green chili', 'chili powder',
    'baking soda', 'baking powder', 'vinegar', 'soy sauce',
    'tomato sauce', 'ketchup', 'mayonnaise', 'mustard',
    'raw onion', 'raw tomato', 'raw potato', 'raw carrot',  # raw veggies as meals
    'plain flour', 'maida', 'atta', 'wheat flour', 'rice flour',
    'besan', 'gram flour', 'cornflour', 'corn starch',
}


# Map some alternative spellings to canonical-ish names.
_FOOD_NAME_NORMALIZATION = {
    'Curd Rice': 'Curd',
    'Dahi': 'Curd',
    'Eggs': 'Egg',
    'Roti': 'Roti',
}

# Very small compatibility rules to prevent clearly incompatible pairings.
# (We apply these during multi-item slot composition; current generator uses compatibility-aware picking.)
INCOMPATIBLE_PAIRS = {
    ('lemon', 'curd'),
    ('lemon', 'dahi'),
    ('lemon', 'yogurt'),
}

# Additional strict "junk / unhealthy" ban list for generated meal plans.
# Requirement: keep these items in dataset/search/logging, but NEVER show in generated healthy plans.
JUNK_MEAL_HARDBAN_KEYWORDS = {
    # Instant/processed foods
    'nood', 'maggi', 'chip', 'frie', 'instant noodle',
    # Fast food / street junk
    'pizza', 'burger', 'bhel', 'sev puri', 'vada pav', 'frankie',
    'samosa', 'pakora', 'kachori',
    # desserts / bakery (high sugar/fat)
    'chocolate', 'ice cream', 'cupcake', 'muffin', 'brownie', 'biscuit', 'cookie',
    'donut', 'croissant', 'pastry', 'cake',
    # generic category-like strings
    'dessert', 'bakery', 'soft drink', 'soda',
    # High sugar items
    'milkshake', 'sugar'
}

# Keep legacy constant name, but DO NOT enforce protein-shake-only output.
GENERATOR_ONLY_PROTEIN_SHAKE = 'Protein Smoothie'

# Max protein shakes allowed per day
MAX_PROTEIN_SHAKES_PER_DAY = 1

# Keywords that identify protein shakes
PROTEIN_SHAKE_KEYWORDS = ['protein smoothie', 'protein shake', 'protein powder']


def _is_protein_shake(food_name) -> bool:
    """Check if a food name is a protein shake/smoothie."""
    name = str(food_name or '').lower()
    for kw in PROTEIN_SHAKE_KEYWORDS:
        if kw in name:
            return True
    return False


def calculate_targets(user: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:

    """
    Calculate daily calorie and macro targets using Mifflin-St Jeor formula.

    Args:
        user: Dict with keys: age, sex, weight, height, activity_level, goal

    Returns:
        Tuple of (daily_calories, macro_targets_dict)
    """
    age = user['age']
    sex = user['sex'].lower()
    weight = user['weight']  # kg
    height = user['height']  # cm
    activity_level = user['activity_level'].lower()
    goal = user['goal'].lower()

    # Mifflin-St Jeor BMR
    if sex == 'male':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    # TDEE
    tdee = bmr * ACTIVITY_MULTIPLIERS.get(activity_level, 1.2)

    # Adjust for goal
    daily_calories = tdee + GOAL_ADJUSTMENTS.get(goal, 0)

    # Calculate macro targets
    ratios = MACRO_RATIOS.get(goal, MACRO_RATIOS['maintain'])
    macro_targets = {
        'protein': (daily_calories * ratios['protein']) / 4,  # g
        'carbs': (daily_calories * ratios['carbs']) / 4,     # g
        'fat': (daily_calories * ratios['fat']) / 9          # g
    }

    return daily_calories, macro_targets

def _word_boundary_pattern(keyword: str) -> str:
    """Convert a keyword to a regex pattern with word boundaries.
    This prevents false positives like 'lassi' matching 'classic'.
    For multi-word keywords, we build an appropriate pattern."""
    kw = keyword.strip().lower()
    # For multi-word keywords like "egg white", "paneer butter masala", etc.
    if ' ' in kw:
        words = kw.split()
        # Pattern: each word with word boundaries, allowing spaces between
        pattern = r'\b' + r'\s+'.join(r'\b' + re.escape(w) + r'\b' for w in words)
        return pattern
    return r'\b' + re.escape(kw) + r'\b'


def filter_meals(df: pd.DataFrame, preferences: Dict[str, Any]) -> pd.DataFrame:
    """
    Filter meals based on user preferences.

    Notes:
    - This function is the first line of defense to ensure we never pick exotic/unrealistic foods.
    - Vegan filtering is comprehensive: excludes ALL animal products including dairy, eggs, whey.
    """
    filtered_df = df.copy()

    # Filter by health_level
    health_level = preferences.get('health_level', 'light')
    if health_level == 'light':
        allowed_scores = ['light']
    elif health_level == 'light+moderate':
        allowed_scores = ['light', 'moderate']
    else:
        allowed_scores = ['light', 'moderate', 'heavy']

    if 'health_score' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['health_score'].isin(allowed_scores)]

    # Hard ban by name keywords regardless of veg_flag (exotic/unrealistic items)
    try:
        idx_lower = filtered_df.index.astype(str).str.lower()
        ban_mask = np.zeros(len(filtered_df), dtype=bool)
        for b in INDIAN_EXOTIC_HARDBAN:
            pattern = _word_boundary_pattern(b)
            ban_mask |= idx_lower.str.contains(pattern, na=False, regex=True)
        filtered_df = filtered_df[~ban_mask]
    except Exception:
        pass

    # Filter by veg_flag
    veg_flag = preferences.get('veg_flag', 'none')
    if veg_flag == 'vegetarian':
        # Exclude non-veg foods (meat, fish, chicken, eggs, etc.)
        if 'tags' in filtered_df.columns:
            non_veg_mask = filtered_df['tags'].astype(str).str.contains('non-veg|meat|fish|chicken|beef|pork|egg', case=False, na=False)
            filtered_df = filtered_df[~non_veg_mask]
        else:
            # Use word-boundary regex for keyword-based filtering to catch compound names like "Egg Curry - Mild"
            idx_lower = filtered_df.index.astype(str).str.lower()
            non_veg_keywords = ['chicken', 'meat', 'fish', 'beef', 'pork', 'lamb', 'mutton',
                                'tuna', 'salmon', 'shrimp', 'prawn', 'crab', 'lobster',
                                'egg', 'boiled egg', 'omelette', 'egg white']
            non_veg_mask = np.zeros(len(filtered_df), dtype=bool)
            for kw in non_veg_keywords:
                pattern = _word_boundary_pattern(kw)
                non_veg_mask |= idx_lower.str.contains(pattern, na=False, regex=True)
            filtered_df = filtered_df[~non_veg_mask]
    elif veg_flag == 'vegan':
        # Exclude ALL animal-based foods including dairy, eggs, meat, fish, chicken, whey
        if 'tags' in filtered_df.columns:
            animal_mask = filtered_df['tags'].astype(str).str.contains(
                'dairy|egg|meat|fish|chicken|beef|pork|milk|yogurt|cheese|whey', 
                case=False, na=False
            )
            filtered_df = filtered_df[~animal_mask]
        else:
            idx_lower = filtered_df.index.astype(str).str.lower()
            vegan_exclude_keywords = [
                # meat, fish, poultry
                'chicken', 'meat', 'fish', 'beef', 'pork', 'lamb', 'mutton',
                'tuna', 'salmon', 'shrimp', 'prawn', 'crab', 'lobster',
                # eggs
                'egg', 'boiled egg', 'omelette', 'egg white',
                # dairy - comprehensive list
                'milk', 'curd', 'yogurt', 'greek yogurt', 'paneer', 'cheese',
                'butter', 'buttermilk', 'lassi', 'whey', 'cottage cheese',
                'paneer butter masala', 'palak paneer', 'matar paneer',
                'kadai paneer', 'panner', 'mozzarella',
                'dahi', 'yogurt drink', 'protein smoothie',
                'chai', 'masala chai',  # chai typically has milk
            ]
            animal_mask = np.zeros(len(filtered_df), dtype=bool)
            for kw in vegan_exclude_keywords:
                pattern = _word_boundary_pattern(kw)
                animal_mask |= idx_lower.str.contains(pattern, na=False, regex=True)
            filtered_df = filtered_df[~animal_mask]

    # Allowlist relaxed mode:
    # - Keep app flexible for large realistic database.
    # - We only apply the hard-ban list above; no further allowlist restriction here.


    # Filter by allergens
    allergens = preferences.get('allergens', [])
    if allergens:
        for allergen in allergens:
            allergen = str(allergen).lower().strip()
            if not allergen:
                continue
            if 'tags' in filtered_df.columns:
                allergen_mask = filtered_df['tags'].astype(str).str.contains(allergen, case=False, na=False)
                filtered_df = filtered_df[~allergen_mask]
            else:
                name_mask = filtered_df.index.astype(str).str.lower().str.contains(allergen)
                filtered_df = filtered_df[~name_mask]

    # Filter by cuisine
    cuisine = preferences.get('cuisine', 'any')
    if cuisine != 'any':
        if 'cuisine' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['cuisine'].str.lower() == cuisine.lower()]
        else:
            cuisine_keywords = {
                'american': ['burger', 'pizza', 'pasta', 'tacos', 'enchiladas'],
                'italian': ['pasta', 'pizza'],
                'asian': ['rice', 'pad thai', 'ramen', 'sushi', 'kimchi'],
                'indian': ['dal', 'chana masala', 'rajma', 'paneer', 'chole', 'khichdi',
                          'poha', 'upma', 'idli', 'dosa', 'sambar', 'rasam', 'roti',
                          'chapati', 'naan', 'paratha', 'misal pav', 'dhokla', 'pakora', 'samosa']
            }
            keywords = cuisine_keywords.get(cuisine.lower(), [])
            if keywords:
                cuisine_mask = filtered_df.index.astype(str).str.lower().str.contains('|'.join(keywords))
                filtered_df = filtered_df[cuisine_mask]

    return filtered_df


def score_and_rank(meal_row: pd.Series, user_targets: Dict[str, float]) -> float:
    """
    Score a meal based on how well it fits user targets.

    Args:
        meal_row: Single meal row from dataframe
        user_targets: Dict with protein, carbs, fat targets (daily grams)

    Returns:
        Score (higher is better)
    """
    # Normalize per 100g serving
    protein_per_100g = meal_row['protein']
    carbs_per_100g = meal_row['carbs']
    fat_per_100g = meal_row['fat']
    calories_per_100g = meal_row['kcal']

    # Protein density score (prefer higher protein density)
    protein_density = protein_per_100g / calories_per_100g if calories_per_100g > 0 else 0
    protein_score = min(protein_density * 100, 50)  # Cap at 50 points

    # Macro balance score (how well it fits daily macro ratios)
    daily_protein_ratio = user_targets['protein'] / sum(user_targets.values()) if sum(user_targets.values()) > 0 else 0
    daily_carbs_ratio = user_targets['carbs'] / sum(user_targets.values()) if sum(user_targets.values()) > 0 else 0
    daily_fat_ratio = user_targets['fat'] / sum(user_targets.values()) if sum(user_targets.values()) > 0 else 0

    meal_protein_ratio = protein_per_100g * 4 / calories_per_100g if calories_per_100g > 0 else 0
    meal_carbs_ratio = carbs_per_100g * 4 / calories_per_100g if calories_per_100g > 0 else 0
    meal_fat_ratio = fat_per_100g * 9 / calories_per_100g if calories_per_100g > 0 else 0

    macro_balance_score = 100 - (
        abs(meal_protein_ratio - daily_protein_ratio) +
        abs(meal_carbs_ratio - daily_carbs_ratio) +
        abs(meal_fat_ratio - daily_fat_ratio)
    ) * 100

    # Fiber score (if available)
    fiber_score = 0
    if 'fiber' in meal_row.index:
        fiber_per_100g = meal_row['fiber']
        fiber_score = min(fiber_per_100g * 2, 20)  # Up to 20 points

    # Health score penalty
    health_penalty = 0
    health_score = meal_row.get('health_score', 'moderate')
    if health_score == 'heavy':
        health_penalty = -20
    elif health_score == 'moderate':
        health_penalty = -5

    total_score = protein_score + macro_balance_score + fiber_score + health_penalty

    return max(0, total_score)  # Ensure non-negative

def pick_meal_for_slot(filtered_df: pd.DataFrame, slot_target_kcal: float,
                      used_foods: List[str], ban_list: List[str],
                      prefer_high_protein: bool = True,
                      slot_target_protein_g: Optional[float] = None,
                      protein_shakes_used_today: int = 0) -> List[Dict[str, Any]]:
    """Pick items for a slot and compose a *complete* meal."""

    # Unpack slot name and target calories
    if isinstance(slot_target_kcal, tuple):
        slot_name, target_kcal = slot_target_kcal
    else:
        slot_name = "Breakfast"  # Default fallback
        target_kcal = slot_target_kcal

    # Filter foods available for this slot based on meal_types column
    if 'meal_types' in filtered_df.columns:
        # meal_types contains Python list strings like "['Breakfast', 'Snack']"
        # Parse the string and check if slot_name is in the list
        def meal_type_matches(meal_types_str):
            try:
                # Parse the string representation of a list
                import ast
                meal_list = ast.literal_eval(meal_types_str)
                return slot_name in meal_list
            except (ValueError, SyntaxError):
                # Fallback to string contains if parsing fails
                return slot_name in meal_types_str

        slot_df = filtered_df[filtered_df['meal_types'].apply(meal_type_matches)]
    else:
        # Fallback - assume all foods can go in any slot
        slot_df = filtered_df

    # Remove used and banned foods
    available_df = slot_df[~slot_df.index.isin(used_foods + ban_list)]

    # Generator-side strict bans to guarantee "healthy realistic" output.
    # Keep these foods in dataset/search/logging; only exclude them from generated plans.
    if len(available_df) > 0:
        idx_lower = available_df.index.astype(str).str.lower()
        junk_mask = np.zeros(len(available_df), dtype=bool)
        for kw in JUNK_MEAL_HARDBAN_KEYWORDS:
            junk_mask |= idx_lower.str.contains(kw, na=False)
        available_df = available_df[~junk_mask]

        # Enforce protein shake limits: if already used up for the day, remove all protein shakes
        # Also remove protein shakes from breakfast and snack slots (keep them for post-workout etc.)
        if protein_shakes_used_today >= MAX_PROTEIN_SHAKES_PER_DAY:
            # Remove all protein shakes from available
            shake_mask = np.zeros(len(available_df), dtype=bool)
            for sh_kw in PROTEIN_SHAKE_KEYWORDS:
                shake_mask |= idx_lower.str.contains(sh_kw, na=False)
            available_df = available_df[~shake_mask]


    if len(available_df) == 0:
        return []

    # Calculate scores for all available foods.
    # Use a proxy of the user's daily macro targets so protein/calorie fit is consistent.
    # Prefer protein-heavy meals for most slots.
    dummy_targets = {
        'protein': 1.0,
        'carbs': 1.0,
        'fat': 1.0,
    }


    # Add variety: shuffle order before scoring to avoid always picking the same top items
    shuffled_indices = list(available_df.index)
    random.shuffle(shuffled_indices)
    available_df = available_df.loc[shuffled_indices]

    available_df = available_df.copy()
    available_df['score'] = available_df.apply(lambda row: score_and_rank(row, dummy_targets), axis=1)

    # Sort by score (descending)
    available_df = available_df.sort_values('score', ascending=False)


    # Stochastic sampling: prioritize complete meals with 2-5 items (never 1 for main meals).
    best_combination: List[Dict[str, Any]] = []
    best_score = -1.0
    tolerance = 0.15  # +/-15% tolerance

    # Dynamic item counts: Breakfast/Lunch/Dinner => 2-5; Snack => 1-3
    if slot_name.lower() == 'snack':
        preferred_sizes = [2, 3, 1]
    else:
        preferred_sizes = [3, 4, 2, 5]

    def _food_category_flags(food_name) -> Dict[str, bool]:
        n = str(food_name or '').lower()
        flags = {
            'carb': False,
            'protein': False,
            'veg_or_fiber': False,
            'healthy_fat': False,
            'fruit': False,
            'dairy_or_yogurt': False,
            'seed_or_nut': False,
            'legume_or_dal': False,
        }
        carb_keywords = ['rice', 'roti', 'chapati', 'paratha', 'bread', 'poha', 'upma', 'oats', 'oatmeal', 'idli', 'dosa', 'khichdi']
        protein_keywords = ['paneer', 'egg', 'omelette', 'chicken', 'dal', 'soya', 'tofu', 'chickpeas', 'lentils', 'curd', 'dahi', 'lassi', 'yogurt', 'tuna']
        veg_keywords = ['aloo', 'gobi', 'bhindi', 'baingan', 'sabzi', 'vegetable', 'salad', 'sprouts', 'palak', 'mixed vegetable']
        fiber_keywords = ['sprouts', 'salad']
        fat_keywords = ['nuts', 'almonds', 'walnuts', 'peanuts', 'peanut butter', 'seeds', 'chia seeds', 'flax seeds', 'coconut']
        fruit_keywords = ['apple', 'banana', 'orange', 'mango', 'papaya', 'guava', 'strawberries', 'blueberries', 'watermelon', 'dates', 'grapes', 'pomegranate', 'kiwi']
        dairy_keywords = ['curd', 'dahi', 'lassi', 'yogurt', 'greek yogurt', 'buttermilk', 'milk', 'yogurt drink']
        seed_nut_keywords = ['nuts', 'almonds', 'walnuts', 'peanuts', 'seeds', 'chia seeds', 'flax seeds']
        dal_keywords = ['dal', 'rajma', 'chana masala', 'chole', 'moong', 'masoor', 'lentil', 'chickpeas', 'roasted chana', 'chana']

        flags['carb'] = any(k in n for k in carb_keywords)
        flags['protein'] = any(k in n for k in protein_keywords)
        flags['veg_or_fiber'] = any(k in n for k in veg_keywords) or any(k in n for k in fiber_keywords)
        flags['healthy_fat'] = any(k in n for k in fat_keywords)
        flags['fruit'] = any(k in n for k in fruit_keywords)
        flags['dairy_or_yogurt'] = any(k in n for k in dairy_keywords)
        flags['seed_or_nut'] = any(k in n for k in seed_nut_keywords)
        flags['legume_or_dal'] = any(k in n for k in dal_keywords)
        return flags

    def _combo_quality(meal_items_: List[Dict[str, Any]]) -> bool:
        # Enforce complete meal structure
        names = [m['Food'] for m in meal_items_]
        cats = [_food_category_flags(x) for x in names]
        has_protein = any(c['protein'] or c['legume_or_dal'] for c in cats)
        has_carb = any(c['carb'] for c in cats)
        has_veg_or_fiber = any(c['veg_or_fiber'] for c in cats) or any(c['fruit'] for c in cats)

        if slot_name.lower() == 'snack':
            # Snacks: should include fruit OR yogurt OR nuts/roasted chana.
            has_snack_core = any(
                c['fruit'] or c['dairy_or_yogurt'] or c['seed_or_nut'] or c['legume_or_dal']
                for c in cats
            )
            return has_snack_core

        # Main meals: require protein + carbs; and ideally veg/fiber.
        if not (has_protein and has_carb):
            return False
        return has_veg_or_fiber

    for combo_size in preferred_sizes:
        if combo_size <= 0 or combo_size > len(available_df):
            continue

        # Sample multiple combinations for this size - increased for better variety
        num_samples = min(200, max(50, len(available_df) * 3))
        for _ in range(num_samples):
            # Note: sample without replacement; combo_size items.
            combination = available_df.sample(n=combo_size, replace=False)

            total_calories = 0.0
            meal_items: List[Dict[str, Any]] = []

            for _, food_row in combination.iterrows():
                portion_g = adjust_portion_to_hit_calories(food_row, target_kcal / combo_size)
                nutrition = {
                    'Food': str(food_row.name),
                    'Portion_g': portion_g,
                    'Calories': (portion_g / 100) * food_row['kcal'],
                    'Protein': (portion_g / 100) * food_row['protein'],
                    'Carbs': (portion_g / 100) * food_row['carbs'],
                    'Fat': (portion_g / 100) * food_row['fat']
                }
                meal_items.append(nutrition)
                total_calories += nutrition['Calories']

            # Check if within tolerance
            if abs(total_calories - target_kcal) / target_kcal > tolerance:
                continue

            # Enforce complete meal rules
            if not _combo_quality(meal_items):
                continue

            # Score this combination
            combo_score = sum(item['Protein'] for item in meal_items) if prefer_high_protein else total_calories
            if combo_score > best_score:
                best_combination = meal_items
                best_score = combo_score

        if best_combination:
            break

    # Fallback: build a 2-item complete meal (main meals) or 1-2-item (snack)
    if not best_combination and len(available_df) > 0:
        fallback_size = 1 if slot_name.lower() == 'snack' else 2
        fallback_size = min(fallback_size, len(available_df))
        top_items = available_df.head(min(10, len(available_df)))  # Increased from 5 for more variety

        for _, food_row in top_items.iterrows():
            # keep portion calc reasonable
            portion_g = adjust_portion_to_hit_calories(food_row, target_kcal / fallback_size)
            best_combination.append({
                'Food': str(food_row.name),
                'Portion_g': portion_g,
                'Calories': (portion_g / 100) * food_row['kcal'],
                'Protein': (portion_g / 100) * food_row['protein'],
                'Carbs': (portion_g / 100) * food_row['carbs'],
                'Fat': (portion_g / 100) * food_row['fat']
            })
            if len(best_combination) >= fallback_size:
                break

    return best_combination

def _normalize_food_name(name: str) -> str:
    if not isinstance(name, str):
        return ''
    return name.strip().lower()


def _is_incompatible_pair(food_a: str, food_b: str) -> bool:
    a = _normalize_food_name(food_a)
    b = _normalize_food_name(food_b)
    for (x, y) in INCOMPATIBLE_PAIRS:
        if (a.find(x) != -1 and b.find(y) != -1) or (a.find(y) != -1 and b.find(x) != -1):
            return True
    return False


def _goal_to_slot_protein_fractions(goal: str) -> Dict[str, float]:
    """Return per-slot protein share across the day (sums to 1.0)."""
    goal = (goal or '').lower()
    if goal == 'gain muscle':
        return {'Breakfast': 0.27, 'Lunch': 0.33, 'Dinner': 0.25, 'Snack': 0.15}
    if goal == 'lose weight':
        return {'Breakfast': 0.25, 'Lunch': 0.34, 'Dinner': 0.27, 'Snack': 0.14}
    # maintain / balanced
    return {'Breakfast': 0.23, 'Lunch': 0.36, 'Dinner': 0.27, 'Snack': 0.14}


def _slot_recipe_constraints(slot: str) -> Dict[str, Any]:
    """Hard constraints for which food categories are preferred in each slot."""
    slot = slot.lower()

    if slot == 'breakfast':
        # Explicit breakfast-type foods requested.
        return {
            'allowed_contains': [
                'poha', 'upma', 'idli', 'dosa',
                'oats', 'oatmeal',
                'khichdi',  # ok sometimes as quick breakfast
                'fruit', 'apple', 'banana', 'orange', 'mango', 'guava',
                'egg', 'omelette',
                'bread', 'brown bread',
                'paratha', 'curd', 'dahi', 'lassi',
                'sprouts', 'dhokla',
                'sambar', 'rasam',
                'milk', 'tea', 'coffee',
                'smoothie',
                'buttermilk',
                'protein smoothie',
            ],
            # Avoid lunch mains in breakfast.
            'avoid_contains': ['biryani', 'rajma', 'chole rice', 'pizza', 'nood', 'chip', 'frie', 'dessert', 'bakery'],
        }

    if slot == 'lunch':
        return {
            'allowed_contains': [
                # Balanced lunch staples
                'roti', 'chapati', 'rice',
                'dal', 'rajma', 'chole',
                'paneer', 'chicken',
                'aloo', 'gobi', 'bhindi', 'baingan',
                'sabzi', 'curd',
            ],
            'avoid_contains': ['nood', 'chip', 'frie', 'pizza', 'burger', 'dessert', 'bakery', 'biryani'],
        }

    if slot == 'dinner':
        return {
            'allowed_contains': [
                # Lighter protein-balanced meals
                'khichdi',
                'dal',
                'roti', 'chapati',
                'paneer', 'curd', 'curd rice',
                'egg',
                'rice', 'chicken',
                'salad',
            ],
            'avoid_contains': ['biryani', 'nood', 'chip', 'frie', 'pizza', 'burger', 'dessert', 'bakery'],
        }

    # snack
    return {
        'allowed_contains': [
            'fruit', 'apple', 'banana', 'orange', 'mango', 'guava',
            'nuts', 'almonds', 'walnuts', 'peanuts',
            'curd', 'dahi', 'lassi',
            'buttermilk',
            'roasted chana', 'chana',
            'sprouts',
            'smoothie', 'protein smoothie',
            'milk',
        ],
        'avoid_contains': ['biryani', 'nood', 'chip', 'frie', 'pizza', 'burger', 'dessert', 'bakery'],
    }



def _filter_by_slot_recipes(df: pd.DataFrame, slot: str) -> pd.DataFrame:
    c = _slot_recipe_constraints(slot)
    allowed = c.get('allowed_contains', [])
    avoid = c.get('avoid_contains', [])
    if not allowed and not avoid:
        return df
    idx = df.index.astype(str).str.lower()
    mask_allowed = np.zeros(len(df), dtype=bool)
    for kw in allowed:
        mask_allowed |= idx.str.contains(kw, na=False)
    mask_avoid = np.zeros(len(df), dtype=bool)
    for kw in avoid:
        mask_avoid |= idx.str.contains(kw, na=False)
    # if allowed list is too restrictive, fallback to avoid-only
    filtered = df[mask_allowed & ~mask_avoid]
    if len(filtered) >= max(5, int(0.15 * len(df))):
        return filtered
    return df[~mask_avoid]


def build_day(filtered_df: pd.DataFrame, daily_targets: Dict[str, float],
              used_today: List[str], prev_day_items: List[str],
              day_index: int = 0) -> Dict[str, Any]:
    # Build a complete day's meal plan with timing rules + goal-aware protein distribution.

    day_plan: Dict[str, List[Dict[str, Any]]] = {}
    all_used_today = used_today.copy()
    daily_calories = float(daily_targets.get('calories', 2000))
    daily_protein_g = float(daily_targets.get('protein', 0))

    # Infer goal if not provided by app.py (app.py only passes macro grams).
    goal = (daily_targets.get('goal') or '').lower()
    if not goal:
        protein = float(daily_targets.get('protein', 0))
        carbs = float(daily_targets.get('carbs', 0))
        fat = float(daily_targets.get('fat', 0))
        total_grams = protein + carbs + fat
        if total_grams > 0:
            protein_ratio = protein / total_grams
            # Heuristics based on MACRO_RATIOS
            # lose weight: higher protein than maintain, lower carbs than muscle gain
            if protein_ratio >= 0.33:
                # decide between muscle gain vs weight loss using carbs/grams
                if carbs / total_grams <= 0.42:
                    goal = 'lose weight'
                else:
                    goal = 'gain muscle'
            else:
                goal = 'maintain'
        else:
            goal = 'maintain'

    protein_slot_fractions = _goal_to_slot_protein_fractions(goal)

    # Calorie distributions (realistic)
    slot_distribution = {
        'Breakfast': 0.20,
        'Lunch': 0.40,
        'Snack': 0.10,
        'Dinner': 0.30
    }

    ban_list = prev_day_items if len(prev_day_items) > 0 else []

    # Track protein shakes used across the day
    protein_shakes_used_today = 0

    for slot in MEAL_SLOTS:
        slot_target_kcal = daily_calories * slot_distribution[slot]
        target_slot_protein_g = daily_protein_g * protein_slot_fractions.get(slot, 0.25)

        # Apply slot recipe constraints before picking candidates.
        slot_df = _filter_by_slot_recipes(filtered_df, slot)

        # Prefer higher protein for most slots; snacks slightly less but still healthy.
        prefer_high_protein = slot != 'Snack'

        meal_items = pick_meal_for_slot(
            slot_df,
            (slot, slot_target_kcal),
            all_used_today,
            ban_list,
            prefer_high_protein=prefer_high_protein,
            slot_target_protein_g=target_slot_protein_g,
            protein_shakes_used_today=protein_shakes_used_today,
        )


        # Compatibility check for multi-item slot combos.
        if len(meal_items) > 1:
            ok = True
            foods = [m['Food'] for m in meal_items]
            for i in range(len(foods)):
                for j in range(i + 1, len(foods)):
                    if _is_incompatible_pair(foods[i], foods[j]):
                        ok = False
                        break
                if not ok:
                    break
            if not ok:
                # Fall back to single best protein item in that slot.
                meal_items = pick_meal_for_slot(
                    slot_df,
                    (slot, slot_target_kcal),
                    all_used_today,
                    ban_list,
                    prefer_high_protein=True,
                    protein_shakes_used_today=protein_shakes_used_today,
                )[:1]

        # If protein is far from slot target, try a protein-forward reroll.
        slot_protein = sum(m.get('Protein', 0) for m in meal_items)
        if target_slot_protein_g > 0 and slot_protein < 0.7 * target_slot_protein_g and len(meal_items) < 3:
            reroll = pick_meal_for_slot(
                slot_df,
                (slot, slot_target_kcal),
                all_used_today,
                ban_list,
                prefer_high_protein=True,
                protein_shakes_used_today=protein_shakes_used_today,
            )
            if reroll:
                meal_items = reroll

        # Count protein shakes used in this slot
        for item in meal_items:
            if _is_protein_shake(item['Food']):
                protein_shakes_used_today += 1

        day_plan[slot] = meal_items
        for item in meal_items:
            all_used_today.append(item['Food'])

    totals = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0}
    all_meals = []
    for slot, slot_meals in day_plan.items():
        for meal in slot_meals:
            totals['calories'] += meal['Calories']
            totals['protein'] += meal['Protein']
            totals['carbs'] += meal['Carbs']
            totals['fat'] += meal['Fat']
            all_meals.append({
                'Meal': slot,
                'Food': meal['Food'],
                'Amount': f"{meal['Portion_g']:.1f}g",
                'Calories': meal['Calories'],
                'Protein': meal['Protein'],
                'Carbs': meal['Carbs'],
                'Fat': meal['Fat']
            })

    return {
        'meals': all_meals,
        'totals': totals,
        'used_foods': all_used_today
    }


def build_week(filtered_df: pd.DataFrame, user_targets: Dict[str, float]) -> Dict[str, Any]:

    """
    Build a 7-day meal plan with variety constraints.

    Args:
        filtered_df: Filtered nutrition dataframe
        user_targets: User targets dict

    Returns:
        Dict with week_plan, weekly_totals, notes
    """
    week_plan = {}
    used_history = []  # Track foods used across days
    prev_day_items = []
    # Track all protein shakes used in the week to avoid overuse
    weekly_protein_shake_count = 0

    for day_idx in range(7):
        # Build day with variety constraints
        day_result = build_day(filtered_df, user_targets, [], prev_day_items, day_index=day_idx)
        week_plan[f'day_{day_idx + 1}'] = day_result['meals']

        # Count protein shakes in this day
        day_shakes = sum(1 for meal in day_result['meals'] if _is_protein_shake(meal['Food']))
        weekly_protein_shake_count += day_shakes

        # Update history
        prev_day_items = [item['Food'] for item in day_result['meals']]
        used_history.extend(prev_day_items)

        # Enforce max repeats across week
        used_history = enforce_max_repeats(used_history)

    # Calculate weekly totals
    weekly_totals = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0}
    for day_meals in week_plan.values():
        for meal in day_meals:
            weekly_totals['calories'] += meal['Calories']
            weekly_totals['protein'] += meal['Protein']
            weekly_totals['carbs'] += meal['Carbs']
            weekly_totals['fat'] += meal['Fat']

    # Generate notes about swaps/variety
    notes = []
    if len(set(used_history)) < len(used_history) * 0.7:
        notes.append("Some food repetition detected - consider expanding food preferences")

    return {
        'week_plan': week_plan,
        'weekly_totals': weekly_totals,
        'notes': notes
    }

def adjust_portion_to_hit_calories(food_row: pd.Series, target_kcal: float) -> float:
    """
    Adjust portion size to hit target calories.

    Args:
        food_row: Food data row
        target_kcal: Target calories

    Returns:
        Portion in grams
    """
    calories_per_100g = food_row['kcal']
    if calories_per_100g <= 0:
        return 100.0  # Default portion

    portion_g = (target_kcal / calories_per_100g) * 100

    # Reasonable bounds - cap at 250g for realism
    # For low-calorie foods like veggies, allow up to 300g
    if calories_per_100g < 50:
        portion_g = max(20, min(portion_g, 300))
    else:
        portion_g = max(20, min(portion_g, 250))

    return portion_g

def enforce_max_repeats(food_history: List[str], max_repeats: int = 2) -> List[str]:
    """
    Enforce maximum repeats in food history.

    Args:
        food_history: List of foods used
        max_repeats: Maximum allowed repeats

    Returns:
        Filtered history with repeats limited
    """
    from collections import Counter

    counts = Counter(food_history)
    filtered_history = []

    for food in food_history:
        if counts[food] <= max_repeats:
            filtered_history.append(food)
        # If over limit, we don't add but count remains for other instances

    return filtered_history

def calculate_bmr_tdee(age, weight, height, gender, activity_level):
    """Legacy function for compatibility."""
    user = {
        'age': age, 'sex': gender, 'weight': weight, 'height': height,
        'activity_level': activity_level, 'goal': 'maintain'
    }
    daily_calories, _ = calculate_targets(user)
    bmr, tdee = daily_calories - GOAL_ADJUSTMENTS['maintain'], daily_calories
    return bmr, tdee

def calculate_macros(calories, goal):
    """Legacy function for compatibility."""
    user = {'goal': goal}
    _, macro_targets = calculate_targets({**user, 'age': 25, 'sex': 'male', 'weight': 70, 'height': 170, 'activity_level': 'moderately active'})
    protein_pct = macro_targets['protein'] * 4 / calories
    carbs_pct = macro_targets['carbs'] * 4 / calories
    fat_pct = macro_targets['fat'] * 9 / calories
    return protein_pct, carbs_pct, fat_pct, macro_targets['protein'], macro_targets['carbs'], macro_targets['fat']

def filter_foods_by_preferences(nutrition_df, food_preference, allergies, cuisine_preference=None):
    """
    Wrapper for filter_meals to match app.py usage.
    """
    preferences = {
        'veg_flag': food_preference.lower() if food_preference != "None" else 'none',
        'allergens': [a.strip().lower() for a in allergies.split(',') if a.strip()],
    }
    return filter_meals(nutrition_df, preferences)

def generate_smart_swaps(original_meal, nutrition_df, veg_flag='none'):
    """
    Generate smart food swap with calculated quantity to match original macros.
    Respects dietary preferences (veg_flag) to avoid suggesting banned foods.

    Args:
        original_meal: Dict with 'Food', 'Calories', 'Protein', etc. (or food name string)
        nutrition_df: Nutrition dataframe
        veg_flag: 'none', 'vegetarian', or 'vegan' - restricts swap candidates

    Returns:
        List of dicts with 'food', 'amount', 'calories', 'protein', 'carbs', 'fat' for best swaps
    """
    if isinstance(original_meal, str):
        # Handle string input for backward compatibility
        food = original_meal
        if food not in nutrition_df.index:
            return []
        target_calories = nutrition_df.loc[food, 'kcal']
        target_protein = nutrition_df.loc[food, 'protein']
    else:
        # Handle dict input
        food = original_meal.get('Food', '')
        target_calories = original_meal.get('Calories', 0)
        target_protein = original_meal.get('Protein', 0)

    if food not in nutrition_df.index:
        return []

    # Find candidates with similar calories and protein (±10%)
    candidates = nutrition_df[
        (nutrition_df['kcal'] >= target_calories * 0.9) &
        (nutrition_df['kcal'] <= target_calories * 1.1) &
        (nutrition_df['protein'] >= target_protein * 0.9) &
        (nutrition_df['protein'] <= target_protein * 1.1) &
        (nutrition_df.index != food)
    ]

    if candidates.empty:
        # Relax criteria if no matches
        candidates = nutrition_df[
            (nutrition_df['kcal'] >= target_calories * 0.8) &
            (nutrition_df['kcal'] <= target_calories * 1.2) &
            (nutrition_df.index != food)
        ]

    if candidates.empty:
        return []

    # Filter candidates based on dietary preference
    if veg_flag in ('vegetarian', 'vegan'):
        idx_lower = candidates.index.astype(str).str.lower()
        drop_mask = np.zeros(len(candidates), dtype=bool)
        if veg_flag == 'vegetarian':
            veg_exclude_keywords = ['chicken', 'meat', 'fish', 'beef', 'pork', 'lamb', 'mutton',
                                    'tuna', 'salmon', 'shrimp', 'prawn', 'crab', 'lobster',
                                    'egg', 'boiled egg', 'omelette', 'egg white']
        else:  # vegan
            veg_exclude_keywords = [
                'chicken', 'meat', 'fish', 'beef', 'pork', 'lamb', 'mutton',
                'tuna', 'salmon', 'shrimp', 'prawn', 'crab', 'lobster',
                'egg', 'boiled egg', 'omelette', 'egg white',
                'milk', 'curd', 'yogurt', 'greek yogurt', 'paneer', 'cheese',
                'butter', 'buttermilk', 'lassi', 'whey', 'cottage cheese',
                'paneer butter masala', 'palak paneer', 'matar paneer',
                'kadai paneer', 'panner', 'mozzarella',
                'dahi', 'yogurt drink', 'protein smoothie',
            ]
        for kw in veg_exclude_keywords:
            pattern = _word_boundary_pattern(kw)
            drop_mask |= idx_lower.str.contains(pattern, na=False, regex=True)
        candidates = candidates[~drop_mask]

    if candidates.empty:
        return []

    # Pick the best candidates (highest protein density) - return up to 5 for variety
    candidates = candidates.copy()
    candidates['protein_density'] = candidates['protein'] / candidates['kcal']
    candidates = candidates.sort_values('protein_density', ascending=False).head(5)  # Top 5 for more swap variety

    swaps = []
    for _, best_swap in candidates.iterrows():
        # Calculate quantity to match original calories
        swap_calories_per_100g = best_swap['kcal']
        if swap_calories_per_100g <= 0:
            quantity_g = 100.0
        else:
            quantity_g = (target_calories / swap_calories_per_100g) * 100
            quantity_g = max(20, min(quantity_g, 250))  # Reasonable bounds

        # Calculate macros for this quantity
        scale_factor = quantity_g / 100
        display_amount, display_unit = get_display_amount_and_unit(best_swap.name, quantity_g, nutrition_df)

        swaps.append({
            'food': best_swap.name,
            'amount': f"{display_amount} {display_unit}",
            'calories': round(scale_factor * best_swap['kcal'], 1),
            'protein': round(scale_factor * best_swap['protein'], 1),
            'carbs': round(scale_factor * best_swap['carbs'], 1),
            'fat': round(scale_factor * best_swap['fat'], 1)
        })

    return swaps