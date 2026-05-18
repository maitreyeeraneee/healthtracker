import os
import re
import json
import base64
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any, Dict, Optional, Tuple

import pandas as pd

try:
    import streamlit as st
    HAS_STREAMLIT = True
except Exception:
    HAS_STREAMLIT = False

import logging

logger = logging.getLogger(__name__)



@dataclass
class DetectedFoodResult:
    ok: bool
    food_name: Optional[str] = None
    category: Optional[str] = None
    calories: Optional[float] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None
    unit: Optional[str] = None
    quantity: Optional[float] = None
    matched_food_name: Optional[str] = None
    matched_unit: Optional[str] = None
    matched_display_amount: Optional[float] = None
    matched_display_unit: Optional[str] = None
    # grams used for final nutrition
    used_grams: Optional[float] = None
    raw_response_text: Optional[str] = None
    error: Optional[str] = None


def _get_env_gemini_key() -> Optional[str]:
    # Must use GEMINI_API_KEY from .env (Streamlit loads env vars).
    return os.getenv("GEMINI_API_KEY")


def _b64_from_bytes(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


def _normalize_food_name(name: str) -> str:
    if not name:
        return ""
    return re.sub(r"\s+", " ", name.strip())


def _similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    a = a.lower().strip()
    b = b.lower().strip()
    return SequenceMatcher(None, a, b).ratio()


def match_closest_food(detected_food_name: str, nutrition_df: pd.DataFrame) -> Tuple[Optional[str], float]:
    if nutrition_df is None or nutrition_df.empty:
        return None, 0.0

    if not detected_food_name:
        return None, 0.0

    # Exact match (case-insensitive)
    for food in nutrition_df.index:
        if str(food).lower() == str(detected_food_name).lower():
            return food, 1.0

    # Light fuzzy match over index (dataset usually manageable)
    best_food = None
    best_score = 0.0
    for food in nutrition_df.index:
        score = _similarity(detected_food_name, str(food))
        if score > best_score:
            best_score = score
            best_food = food

    return best_food, best_score


def _extract_first_number(text: str) -> Optional[float]:
    if not text:
        return None
    m = re.search(r"(\d+(?:\.\d+)?)", text)
    if not m:
        return None
    try:
        return float(m.group(1))
    except Exception:
        return None


def _infer_quantity_and_unit_from_gemini(
    quantity: Optional[float],
    unit: Optional[str],
    calories: Optional[float],
    calories_per_100g: Optional[float],
) -> Tuple[Optional[float], Optional[str], Optional[float]]:
    """Return (quantity, unit, used_grams).

    If Gemini provided unit+quantity, we still translate to grams using app's unit conversion later.
    If missing, infer grams from calories.
    """
    if calories is not None and calories_per_100g and calories_per_100g > 0:
        # grams that would match calories (using dataset kcal per 100g)
        used_grams = (calories / calories_per_100g) * 100.0
        # clamp reasonable bounds
        used_grams = max(10.0, min(600.0, used_grams))
    else:
        used_grams = None

    # If unit+quantity present, we keep them for UI display matching.
    # Final conversion to grams is done later with get_display_amount_and_unit + calculate_nutrition_per_serving.
    return quantity, unit, used_grams


def _parse_json_safely(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None

    # Try direct JSON block first
    try:
        return json.loads(text)
    except Exception:
        pass

    # Try to find {...} in text
    try:
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            return None
        return json.loads(m.group(0))
    except Exception:
        return None


def _clean_category(cat: Optional[str]) -> Optional[str]:
    if not cat:
        return None
    c = str(cat).strip()
    return c if c else None


def detect_food_from_image(
    image_bytes: bytes,
    mime_type: str,
    nutrition_df: pd.DataFrame,
    # Vision-capable model name (SDK model id)
    gemini_model: str = "gemini-2.0-flash",
) -> DetectedFoodResult:

    """Calls Gemini Vision API and then matches to the nutrition dataset.

    Note: final macro calories/protein/carbs/fat are computed from the dataset after matching.
    """

    api_key = _get_env_gemini_key()
    key_loaded_ok = bool(api_key)

    # Debug logging (never log the key itself)
    if HAS_STREAMLIT:
        try:
            st.write(
                {
                    "[gemini_food_recognition] key_loaded_ok": key_loaded_ok,
                    "[gemini_food_recognition] gemini_model": gemini_model,
                }
            )
        except Exception:
            pass

    logger.info("Gemini key loaded: %s; model: %s", key_loaded_ok, gemini_model)

    if not api_key:
        return DetectedFoodResult(ok=False, error="Missing GEMINI_API_KEY environment variable.")

    if not image_bytes:
        return DetectedFoodResult(ok=False, error="No image bytes provided.")

    # Prevent stale/cached SDK config issues: build per-call model instance
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name=gemini_model)

    b64 = _b64_from_bytes(image_bytes)


    prompt = (
        "You are a nutrition expert. Analyze the provided food image and return a STRICT JSON object with these keys:\n"
        "{\n"
        '  "food_name": string,\n'
        '  "category": string,\n'
        '  "serving": {"quantity": number, "unit": string},\n'
        '  "estimated_calories": number,\n'
        '  "estimated_protein_g": number,\n'
        '  "estimated_carbs_g": number,\n'
        '  "estimated_fat_g": number\n'
        "}\n"
        "Rules:\n"
        "- If you cannot determine serving quantity/unit, set serving.quantity to null and serving.unit to null.\n"
        "- estimated_* must be numbers (use null if truly unknown).\n"
        "- Keep food_name concise (e.g., 'Chicken Biryani', 'Apple', 'Vegetable Salad').\n"
        "- category can be like 'Rice/Grains', 'Protein', 'Vegetables', 'Fruit', 'Dairy', 'Snacks', 'Beverages'.\n"
        "Return ONLY JSON. No markdown." 
    )

    try:
        response = model.generate_content(
            [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": b64,
                    }
                },
            ],
            generation_config={"temperature": 0.2},
        )

        # Debug logging: attempt to log an HTTP status if SDK exposes it.
        status_code = getattr(getattr(response, "_response", None), "status_code", None)
        if HAS_STREAMLIT:
            try:
                st.write({"[gemini_food_recognition] api_response_status": status_code})
            except Exception:
                pass
        logger.info("Gemini response status_code: %s", status_code)

        text = getattr(response, "text", None)
        if not text:
            try:
                text = response.candidates[0].content.parts[0].text  # type: ignore[attr-defined]
            except Exception:
                text = None
    except Exception as e:
        msg = str(e)
        status_code = getattr(e, "status_code", None)
        if HAS_STREAMLIT:
            try:
                st.write(
                    {
                        "[gemini_food_recognition] api_response_status": status_code,
                        "[gemini_food_recognition] api_error": msg[:500],
                    }
                )
            except Exception:
                pass
        logger.exception("Gemini API call failed (status_code=%s): %s", status_code, msg)
        friendly = msg
        lowered = msg.lower()
        if "429" in lowered or "quota" in lowered or "rate limit" in lowered or "resource_exhausted" in lowered:
            friendly = "Gemini quota/rate limit reached. Please try again in a few minutes."
        elif "401" in lowered or "403" in lowered or "permission" in lowered:
            friendly = "Gemini API authentication failed. Check your GEMINI_API_KEY in the .env file."
        elif "network" in lowered or "timeout" in lowered or "temporarily" in lowered:
            friendly = "Network error while analyzing the image. Please try again."
        else:
            friendly = "Image analysis failed. Please try again."

        return DetectedFoodResult(ok=False, error=friendly)



    parsed = _parse_json_safely(text or "")
    if not parsed:
        return DetectedFoodResult(ok=False, error="Could not parse Gemini JSON response.", raw_response_text=text)

    food_name = _normalize_food_name(parsed.get("food_name")) or None
    category = _clean_category(parsed.get("category"))

    serving = parsed.get("serving") or {}
    quantity = serving.get("quantity")
    unit = serving.get("unit")

    # Normalize numbers
    def _to_float_or_none(v):
        if v is None:
            return None
        try:
            return float(v)
        except Exception:
            return None

    calories = _to_float_or_none(parsed.get("estimated_calories"))
    protein = _to_float_or_none(parsed.get("estimated_protein_g"))
    carbs = _to_float_or_none(parsed.get("estimated_carbs_g"))
    fat = _to_float_or_none(parsed.get("estimated_fat_g"))

    # Match to closest nutrition dataset item
    matched_food, match_score = match_closest_food(food_name or "", nutrition_df)

    # Compute final macros from dataset for the inferred grams.
    # We'll infer grams primarily from Gemini calories if available.
    used_grams = None
    matched_unit_for_display = None
    display_amount = None
    display_unit = None

    if matched_food is not None and matched_food in nutrition_df.index:
        calories_per_100g = float(nutrition_df.loc[matched_food, "kcal"]) if pd.notna(nutrition_df.loc[matched_food, "kcal"]) else None

        quantity, unit, used_grams = _infer_quantity_and_unit_from_gemini(
            quantity=quantity,
            unit=unit,
            calories=calories,
            calories_per_100g=calories_per_100g,
        )

        # If used_grams is inferred, convert to display unit for the app.
        # For macros, we will calculate nutrition using the dataset and a best-effort unit.
        # App utilities require (quantity, unit, grams via convert_units_to_grams).
        from .data_loader import (
            calculate_nutrition_per_serving,
            get_display_amount_and_unit,
            convert_units_to_grams,
        )

        if used_grams is not None:
            display_amount, display_unit = get_display_amount_and_unit(matched_food, used_grams, nutrition_df)


            # Determine an internal unit that can be used with calculate_nutrition_per_serving.
            # We'll choose the display_unit if it exists in unit_options, otherwise 'grams'.
            matched_unit_for_display = display_unit
            # convert display back to grams consistency: use internal calculate_nutrition_per_serving
            nutrition = calculate_nutrition_per_serving(matched_food, display_amount, matched_unit_for_display, nutrition_df)

            final_calories = nutrition.get("Calories")
            final_protein = nutrition.get("Protein")
            final_carbs = nutrition.get("Carbs")
            final_fat = nutrition.get("Fat")

            return DetectedFoodResult(
                ok=True,
                food_name=food_name,
                category=category,
                calories=float(final_calories) if final_calories is not None else calories,
                protein=float(final_protein) if final_protein is not None else protein,
                carbs=float(final_carbs) if final_carbs is not None else carbs,
                fat=float(final_fat) if final_fat is not None else fat,
                unit=unit,
                quantity=quantity,
                matched_food_name=str(matched_food),
                matched_unit=matched_unit_for_display,
                matched_display_amount=display_amount,
                matched_display_unit=display_unit,
                used_grams=used_grams,
                raw_response_text=text,
            )

    # If match failed or dataset missing, still return Gemini estimates.
    return DetectedFoodResult(
        ok=True,
        food_name=food_name,
        category=category,
        calories=calories,
        protein=protein,
        carbs=carbs,
        fat=fat,
        unit=unit,
        quantity=quantity,
        matched_food_name=str(matched_food) if matched_food is not None else None,
        raw_response_text=text,
    )

