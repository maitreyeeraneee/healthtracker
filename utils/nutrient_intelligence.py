from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


# ---- Heuristic thresholds (best-effort; dataset-dependent) ----
# If nutrient column exists, we compare intake-per-day to these.
# Values are intentionally conservative because dataset nutrition columns
# may represent nutrient density per 100g, while the logged meal estimates
# will be scaled by grams.


@dataclass
class NutrientIssue:
    nutrient: str
    severity: str  # "low" / "high" / "missing"
    consumed: float
    suggested_target: Optional[float]
    message: str


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None or (isinstance(x, float) and np.isnan(x)):
            return default
        return float(x)
    except Exception:
        return default


def _find_first_col(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _nutrients_from_dataset(nutrition_df: pd.DataFrame) -> Dict[str, str]:
    """Map our conceptual nutrient names to dataset column names if available."""
    return {
        "iron": _find_first_col(nutrition_df, ["iron", "Iron"]),
        "calcium": _find_first_col(nutrition_df, ["calcium", "Calcium"]),
        "fiber": _find_first_col(nutrition_df, ["fiber", "Fiber"]),
        # macro-ish nutrients; dataset likely uses these exact names for swap
        "kcal": _find_first_col(nutrition_df, ["kcal", "kcal_100g", "Calories"]),
        "fat": _find_first_col(nutrition_df, ["fat", "Fat"]),
        "protein": _find_first_col(nutrition_df, ["protein", "Protein"]),
        "carbs": _find_first_col(nutrition_df, ["carbs", "Carbs"]),
    }


def _estimate_nutrient_intake_for_meals(
    meals: List[Dict[str, Any]],
    nutrition_df: pd.DataFrame,
    dataset_cols: Dict[str, Optional[str]],
) -> Tuple[float, Dict[str, float]]:
    """Estimate intake per logged day from dataset per-100g values.

    The meal entry amounts contain a display unit (e.g. "1.0 cup").
    We DO NOT have reliable grams in the log.

    Current app uses calculate_nutrition_per_serving during logging to compute
    Calories/Protein/Carbs/Fat per the user's chosen unit.

    For micronutrients, we approximate grams by reusing the same serving-size
    logic if unit/amount are available. However, the logged meal does not store
    raw grams or unit; only display string.

    Therefore, we do the following:
      - For macros (Calories/Protein/Carbs/Fat) use already logged values.
      - For other nutrients (iron/calcium/fiber) estimate using a proportional
        approach: treat kcal-per-100g as a scaling basis when we can.

    This is best-effort and prevents crashes when dataset columns are missing.
    """
    totals: Dict[str, float] = {}

    # Macros are already present in the day totals from app.get_meal_totals.
    # This helper returns micronutrients only; app can use macros separately.
    micronutrient_cols = {k: v for k, v in dataset_cols.items() if v and k not in {"kcal", "fat", "protein", "carbs"}}

    # Attempt proportional estimation using grams-from-calories.
    # If dataset has kcal and the logged calories correspond to chosen quantity,
    # then grams = (logged_calories / kcal_per_100g) * 100.
    kcal_col = dataset_cols.get("kcal")
    if not kcal_col:
        return 0.0, {k: 0.0 for k in micronutrient_cols.keys()}

    overall_kcal = 0.0

    for meal in meals:
        food = meal.get("Food")
        if not food or food not in nutrition_df.index:
            continue

        logged_kcal = _safe_float(meal.get("Calories"), 0.0)
        if logged_kcal <= 0:
            continue

        kcal_per_100g = _safe_float(nutrition_df.loc[food].get(kcal_col), 0.0)
        if kcal_per_100g <= 0:
            continue

        grams = (logged_kcal / kcal_per_100g) * 100.0
        overall_kcal += logged_kcal

        for concept, col in micronutrient_cols.items():
            v_per_100g = _safe_float(nutrition_df.loc[food].get(col), 0.0)
            totals[concept] = totals.get(concept, 0.0) + (grams / 100.0) * v_per_100g

    # Ensure all keys exist
    for concept in micronutrient_cols.keys():
        totals.setdefault(concept, 0.0)

    return overall_kcal, totals


def analyze_meal_day(
    meals: List[Dict[str, Any]],
    nutrition_df: pd.DataFrame,
    calorie_target: Optional[float] = None,
    protein_target: Optional[float] = None,
    fiber_target: Optional[float] = None,
    iron_target: Optional[float] = None,
    calcium_target: Optional[float] = None,
) -> Dict[str, Any]:
    """Return short insights + auto-correct suggestions.

    This function is intentionally deterministic and safe.
    """
    if nutrition_df is None or nutrition_df.empty or not meals:
        return {"issues": [], "smart_insights": [], "recommendations": []}

    dataset_cols = _nutrients_from_dataset(nutrition_df)

    # Severity checks for macros using logged totals (already computed in app).
    # We rely on app-provided targets when present.
    # Compute macro totals from meal entries.
    macro_totals = {
        "kcal": float(np.sum([_safe_float(m.get("Calories"), 0.0) for m in meals])),
        "protein": float(np.sum([_safe_float(m.get("Protein"), 0.0) for m in meals])),
        "fat": float(np.sum([_safe_float(m.get("Fat"), 0.0) for m in meals])),
        "carbs": float(np.sum([_safe_float(m.get("Carbs"), 0.0) for m in meals])),
    }

    # Default targets if not provided
    if protein_target is None:
        protein_target = 0
    if fiber_target is None:
        fiber_target = 25.0
    if iron_target is None:
        iron_target = 18.0
    if calcium_target is None:
        calcium_target = 1000.0

    issues: List[NutrientIssue] = []

    # Low protein
    if protein_target and macro_totals["protein"] < 0.8 * protein_target:
        issues.append(
            NutrientIssue(
                nutrient="protein",
                severity="low",
                consumed=macro_totals["protein"],
                suggested_target=protein_target,
                message=f"Protein looks low today ({macro_totals['protein']:.0f}g vs target {protein_target:.0f}g).",
            )
        )

    # High fat (heuristic: >30% calories from fat)
    if macro_totals["kcal"] > 0:
        fat_cal = macro_totals["fat"] * 9.0
        fat_ratio = fat_cal / macro_totals["kcal"] if macro_totals["kcal"] else 0.0
        if fat_ratio > 0.33:
            issues.append(
                NutrientIssue(
                    nutrient="fat",
                    severity="high",
                    consumed=macro_totals["fat"],
                    suggested_target=None,
                    message=f"Fat may be high today (~{fat_ratio*100:.0f}% of calories).",
                )
            )

    # Low fiber / low iron / low calcium based on dataset columns (if present)
    _, micronutrient_totals = _estimate_nutrient_intake_for_meals(meals, nutrition_df, dataset_cols)

    for concept, target in [("fiber", fiber_target), ("iron", iron_target), ("calcium", calcium_target)]:
        if concept in micronutrient_totals:
            consumed = micronutrient_totals.get(concept, 0.0)
            # Only raise issue if dataset provided a non-zero value somewhere.
            if consumed > 0 and consumed < 0.8 * target:
                issues.append(
                    NutrientIssue(
                        nutrient=concept,
                        severity="low",
                        consumed=consumed,
                        suggested_target=target,
                        message=f"Your {concept} intake seems low ({consumed:.1f} vs target {target:.0f}).",
                    )
                )

    # Build short smart insights
    smart_insights: List[str] = []
    for iss in issues[:4]:
        smart_insights.append(iss.message)

    # Auto-correct recommendations: propose likely swaps from current meal foods
    # using Smart Swap suggester but only if available.
    recommendations: List[Dict[str, Any]] = []
    try:
        from .smart_swap import suggest_swaps

        # Use first low nutrient issue as driver
        driver = None
        if any(i.nutrient == "protein" and i.severity == "low" for i in issues):
            driver = "protein"
        elif any(i.nutrient == "fiber" and i.severity == "low" for i in issues):
            driver = "fiber"
        elif any(i.nutrient == "iron" and i.severity == "low" for i in issues):
            driver = "iron"
        elif any(i.nutrient == "calcium" and i.severity == "low" for i in issues):
            driver = "calcium"

        if driver:
            # Recommend swaps for the most calorie-dense logged item
            def sort_key(m):
                return _safe_float(m.get("Calories"), 0.0)

            meals_sorted = sorted(meals, key=sort_key, reverse=True)
            src_food = None
            for m in meals_sorted:
                f = m.get("Food")
                if f in nutrition_df.index:
                    src_food = f
                    break

            if src_food:
                swaps = suggest_swaps(src_food, nutrition_df, veg_pref="none", allergies="", max_results=6)
                # Attach a reason label based on driver
                for s in swaps[:3]:
                    reasons = s.get("reasons") or []
                    recommendations.append(
                        {
                            "source": s.get("from"),
                            "target": s.get("to"),
                            "driver": driver,
                            "kcal": s.get("kcal"),
                            "protein": s.get("protein"),
                            "fiber": s.get("fiber"),
                            "reasons": reasons,
                        }
                    )
    except Exception:
        # Keep it non-breaking
        recommendations = []

    return {
        "issues": [i.__dict__ for i in issues],
        "smart_insights": smart_insights,
        "recommendations": recommendations,
    }

