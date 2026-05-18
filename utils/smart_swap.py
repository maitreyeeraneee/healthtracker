import re
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd

try:
    import streamlit as st
except Exception:  # pragma: no cover
    st = None

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def _normalize_food(s: str) -> str:
    return re.sub(r"\s+", " ", str(s or "").strip().lower())


def build_swap_index(nutrition_df: pd.DataFrame):
    foods = list(nutrition_df.index.astype(str))
    corpus = []
    for food in foods:
        row = nutrition_df.loc[food]
        extra = []
        for col in ["category", "cuisine"]:
            if col in row.index and row[col] is not None and str(row[col]).strip():
                extra.append(str(row[col]))
        corpus.append(f"{food} {' '.join(extra)}".strip())

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        min_df=2,
        max_features=4000,
    )
    mat = vectorizer.fit_transform(corpus)
    return {"vectorizer": vectorizer, "matrix": mat, "foods": foods}


def _apply_diet_filter(df: pd.DataFrame, veg_pref: str, allergies_csv: str = "") -> pd.DataFrame:
    """Conservative filtering for Smart Swap.

    Requirements:
    - respect veg preference using dataset category
    - avoid foods matching user allergies using BOTH:
        1) category substring match
        2) food-name keyword match (e.g., dairy -> milk/curd/paneer/whey/cheese...)
    """
    if df is None or df.empty:
        return df

    v = (veg_pref or "none").lower()
    if v not in {"vegetarian", "vegan"}:
        v = "none"

    out = df

    # Veg filtering
    if v in {"vegetarian", "vegan"} and "category" in out.columns:
        cat = out["category"].astype(str).str.lower()
        if v == "vegan":
            out = out[~cat.isin(["dairy", "non-veg"])]
        else:
            out = out[~cat.isin(["non-veg"])]

    # Allergy keyword mapping (extendable). Kept conservative.
    allergy_keywords_map = {
        # dairy
        "dairy": [
            "milk", "curd", "dahi", "yogurt", "greek yogurt", "buttermilk", "lassi",
            "paneer", "cheese", "whey", "cottage cheese", "whey protein",
        ],
        "lactose": ["milk", "curd", "dahi", "yogurt", "lassi", "buttermilk", "whey"],
        # nuts
        "nut": [
            "almond", "almonds", "walnut", "walnuts", "peanut", "peanuts",
            "cashew", "cashews", "pistachio", "pistachios", "hazelnut", "hazelnuts",
            "nut", "nut butter", "peanut butter", "mixed nuts",
        ],
        "nuts": [
            "almond", "almonds", "walnut", "walnuts", "peanut", "peanuts",
            "cashew", "cashews", "pistachio", "pistachios", "hazelnut", "hazelnuts",
            "nut", "nut butter", "peanut butter", "mixed nuts",
        ],
        # eggs
        "egg": ["egg", "boiled egg", "omelette", "egg white"],
        "eggs": ["egg", "boiled egg", "omelette", "egg white"],
        # gluten / wheat (if present in dataset)
        "gluten": ["wheat", "atta", "maida", "bread", "flour"],
        "wheat": ["wheat", "atta", "maida"],
        # soy
        "soy": ["soy", "soybeans", "tofu", "tempeh", "edamame"],
        "sesame": ["sesame", "til"],
    }

    allergies_list = [a.strip().lower() for a in str(allergies_csv or "").split(",") if a.strip()]
    if allergies_list:
        # 1) category-based conservative filtering
        if "category" in out.columns:
            cat = out["category"].astype(str).str.lower()
            mask = np.ones(len(out), dtype=bool)
            for a in allergies_list:
                # Use substring match on category
                mask &= ~cat.str.contains(re.escape(a), na=False)
            out = out[mask]

        # 2) food-name keyword filtering
        idx_lower = out.index.astype(str).str.lower()
        name_mask = np.ones(len(out), dtype=bool)

        # build patterns
        for a in allergies_list:
            # normalize to map keys by substring
            key_matched = None
            for k in allergy_keywords_map.keys():
                if k in a or a in k:
                    key_matched = k
                    break
            keywords = allergy_keywords_map.get(key_matched, [])
            # If allergy term itself is like "dairy" or "nuts" but not matched, still attempt direct containment
            if not keywords:
                keywords = [a]

            for kw in keywords:
                if not kw:
                    continue
                # word boundary for single tokens; substring for multi-word phrases
                pattern = _word_boundary_pattern(kw) if " " not in kw else kw.lower()
                name_mask &= ~idx_lower.str.contains(pattern, na=False, regex=True)

        out = out[name_mask]

    return out




def _extract_intents(food_query: str) -> Dict[str, bool]:
    q = str(food_query or "").lower()
    intents = {
        "prefer_lower_calories": True,  # always suggest healthier/lower-cal where possible
        "prefer_higher_protein": False,
        "prefer_more_fiber": False,
    }
    if "protein" in q or "high protein" in q:
        intents["prefer_higher_protein"] = True
    if "fiber" in q or "high fiber" in q:
        intents["prefer_more_fiber"] = True
    if "low calorie" in q or "under" in q or "calorie" in q:
        intents["prefer_lower_calories"] = True
    if "weight loss" in q or "lose weight" in q:
        intents["prefer_lower_calories"] = True
    return intents


def _reasons_for_recommendation(src: pd.Series, tgt: pd.Series) -> List[str]:
    """Create human-friendly reasons for why tgt is a better swap than src."""
    reasons: List[str] = []

    def gv(x):
        try:
            return float(x)
        except Exception:
            return 0.0

    src_kcal = gv(src.get("kcal", 0))
    tgt_kcal = gv(tgt.get("kcal", 0))
    src_pro = gv(src.get("protein", 0))
    tgt_pro = gv(tgt.get("protein", 0))
    src_fat = gv(src.get("fat", 0))
    tgt_fat = gv(tgt.get("fat", 0))
    src_carb = gv(src.get("carbs", 0))
    tgt_carb = gv(tgt.get("carbs", 0))

    src_fiber = gv(src.get("fiber", 0)) if "fiber" in src.index else 0.0
    tgt_fiber = gv(tgt.get("fiber", 0)) if "fiber" in tgt.index else 0.0


    # Lower calories
    if tgt_kcal < src_kcal:
        pct = ((src_kcal - tgt_kcal) / src_kcal * 100) if src_kcal > 0 else 0
        reasons.append(f"Lower calories ({tgt_kcal:.0f} vs {src_kcal:.0f} kcal/100g, ~{pct:.0f}% less)")

    # Higher protein
    if tgt_pro > src_pro:
        pct = ((tgt_pro - src_pro) / src_pro * 100) if src_pro > 0 else 0
        reasons.append(f"Higher protein ({tgt_pro:.1f} vs {src_pro:.1f} g/100g, ~{pct:.0f}% more)")

    # More fiber
    if tgt_fiber > src_fiber:
        reasons.append(f"More fiber ({tgt_fiber:.1f} vs {src_fiber:.1f} g/100g)")

    # Lower fat
    if tgt_fat < src_fat:
        pct = ((src_fat - tgt_fat) / src_fat * 100) if src_fat > 0 else 0
        reasons.append(f"Lower fat ({tgt_fat:.1f} vs {src_fat:.1f} g/100g, ~{pct:.0f}% less)")

    # Better macro balance heuristic (closer carbs/protein/fat proportions)
    total_src = src_pro + src_carb + src_fat
    total_tgt = tgt_pro + tgt_carb + tgt_fat
    if total_src > 0 and total_tgt > 0:
        src_rat = np.array([src_pro, src_carb, src_fat]) / total_src
        tgt_rat = np.array([tgt_pro, tgt_carb, tgt_fat]) / total_tgt
        # target: more protein, moderate carbs, lower fat for swaps
        target = np.array([0.35, 0.45, 0.20])
        src_dist = float(np.linalg.norm(src_rat - target))
        tgt_dist = float(np.linalg.norm(tgt_rat - target))
        if tgt_dist < src_dist:
            reasons.append("More macro-balanced for protein-forward goals")

    # De-dup + limit
    dedup = []
    seen = set()
    for r in reasons:
        if r not in seen:
            dedup.append(r)
            seen.add(r)
    return dedup[:4]





def suggest_swaps(
    food_query: str,
    nutrition_df: pd.DataFrame,
    veg_pref: str = "none",
    allergies: str = "",
    max_results: int = 5,
) -> List[Dict[str, Any]]:
    """Suggest healthier swap foods for a given input food.

    Uses TF-IDF cosine similarity over food names/categories, then ranks by
    nutrient comparisons (calories/protein/fiber/fat).
    """
    if nutrition_df is None or nutrition_df.empty:
        return []

    retriever = build_swap_index(nutrition_df)

    q = str(food_query or "").strip()
    if not q:
        return []

    # Choose source row: exact match if possible else pseudo-row via top similar.
    q_norm = q.lower()
    source_row = None
    for f in nutrition_df.index.astype(str):
        if f.lower() == q_norm:
            source_row = nutrition_df.loc[f]
            source_name = f
            break

    if source_row is None:
        # Use retrieval to pick a likely source.
        q_vec = retriever["vectorizer"].transform([q_norm])
        scores = cosine_similarity(q_vec, retriever["matrix"])[0]
        idx = int(np.argmax(scores))
        source_name = retriever["foods"][idx]
        source_row = nutrition_df.loc[source_name]

    # retrieval candidates
    vectorizer = retriever["vectorizer"]
    matrix = retriever["matrix"]
    foods = retriever["foods"]
    q_vec = vectorizer.transform([q_norm])
    scores = cosine_similarity(q_vec, matrix)[0]
    top_idx = np.argsort(scores)[::-1]

    candidates = []
    for i in top_idx:
        cand_name = foods[i]
        if cand_name.lower() == source_name.lower():
            continue
        row = nutrition_df.loc[cand_name]
        candidates.append((cand_name, row, float(scores[i])))
        if len(candidates) >= max_results * 15:
            break

    # apply diet filter
    cand_df = pd.DataFrame([
        {"food": n, **{k: row.get(k, np.nan) for k in ["kcal", "protein", "carbs", "fat", "fiber"] if k in row.index}, "_sim": sim}
        for n, row, sim in candidates
    ])

    # build df with index as food for nutrient comparisons
    # (We rely on nutrition_df for accurate values)
    cand_names = cand_df["food"].tolist() if not cand_df.empty else []
    cand_nut = nutrition_df.loc[cand_names] if cand_names else pd.DataFrame()

    cand_nut = cand_nut.copy()
    cand_nut["_sim"] = cand_df.set_index("food")["_sim"].reindex(cand_nut.index).values if not cand_df.empty else 0

    cand_nut = _apply_diet_filter(cand_nut, veg_pref=veg_pref, allergies_csv=allergies)

    # allergies: conservative category substring removal
    if allergies:
        allergies_list = [a.strip().lower() for a in str(allergies).split(",") if a.strip()]
        if "category" in cand_nut.columns and allergies_list:
            cat = cand_nut["category"].astype(str).str.lower()
            mask = np.ones(len(cand_nut), dtype=bool)
            for a in allergies_list:
                mask &= ~cat.str.contains(re.escape(a), na=False)
            cand_nut = cand_nut[mask]

    if cand_nut is None or cand_nut.empty:
        return []

    # Rank candidates
    src_kcal = float(source_row.get("kcal", 0) or 0)
    src_pro = float(source_row.get("protein", 0) or 0)
    src_fat = float(source_row.get("fat", 0) or 0)
    src_fiber = float(source_row.get("fiber", 0) or 0) if "fiber" in source_row.index else 0.0

    # Optional micronutrient ranking if dataset provides them.
    # We keep it robust: if columns are missing we fall back to macros only.
    mic_cols = ["iron", "calcium", "vitamin_c", "vitamin_a", "vitamin_d", "folate"]
    mic_cols = [c for c in mic_cols if c in nutrition_df.columns]

    def score(tgt_name: str, tgt_row: pd.Series, sim: float) -> float:
        tgt_kcal = float(tgt_row.get("kcal", 0) or 0)
        tgt_pro = float(tgt_row.get("protein", 0) or 0)
        tgt_fat = float(tgt_row.get("fat", 0) or 0)
        tgt_fiber = float(tgt_row.get("fiber", 0) or 0) if "fiber" in tgt_row.index else 0.0

        cal_gain = (src_kcal - tgt_kcal)
        pro_gain = (tgt_pro - src_pro)
        fat_gain = (src_fat - tgt_fat)
        fiber_gain = (tgt_fiber - src_fiber)

        # micronutrient uplift (higher is better), scaled down to keep macros dominant
        mic_gain = 0.0
        if mic_cols:
            for c in mic_cols:
                src_v = float(source_row.get(c, 0) or 0)
                tgt_v = float(tgt_row.get(c, 0) or 0)
                if tgt_v > src_v:
                    mic_gain += (tgt_v - src_v)

        # Encourage lower calories and higher protein; similarity provides relevance.
        return (sim * 50) + cal_gain * 0.4 + pro_gain * 2.0 + fat_gain * 0.8 + fiber_gain * 1.2 + mic_gain * 0.01



    scored = []
    for name, row in cand_nut.iterrows():
        sim = float(row.get("_sim", 0) or 0)
        scored.append((name, row, sim, score(name, row, sim)))

    scored.sort(key=lambda x: x[3], reverse=True)

    results: List[Dict[str, Any]] = []
    for name, row, sim, _ in scored[:max_results]:
        reasons = _reasons_for_recommendation(source_row, row)
        results.append({
            "from": source_name,
            "to": name,
            "_sim": sim,
            "kcal": float(row.get("kcal", 0) or 0),
            "protein": float(row.get("protein", 0) or 0),
            "carbs": float(row.get("carbs", 0) or 0),
            "fat": float(row.get("fat", 0) or 0),
            "fiber": float(row.get("fiber", 0) or 0) if "fiber" in row.index else None,
            "reasons": reasons,
        })

    return results


def smart_swap_tab_ui(nutrition_df: pd.DataFrame, food_preference: str, allergies: str):
    """Streamlit UI for Smart Swap tab."""
    st.subheader("Smart Swap")
    st.caption("Enter a food. Get healthier replacements with dataset-grounded reasons.")

    if nutrition_df is None or nutrition_df.empty:
        st.warning("Nutrition dataset is unavailable.")
        return

    veg_pref = food_preference.lower() if food_preference in {"Vegetarian", "Vegan"} else "none"

    food_options = list(nutrition_df.index.astype(str))
    q = st.selectbox(
        "Food item",
        options=food_options,
        index=0 if food_options else 0,
        key="smart_swap_select",
        format_func=lambda x: str(x),
    )

    max_results = st.slider("Number of recommendations", 3, 10, 5, step=1, key="smart_swap_k")

    if st.button("Find swaps", key="smart_swap_btn"):
        swaps = suggest_swaps(q, nutrition_df, veg_pref=veg_pref, allergies=allergies, max_results=max_results)

        if not swaps:
            st.info("No swaps found for the given input with your filters.")
            return

        for s in swaps:
            header = f"{s['from']} → {s['to']}"
            st.markdown(f"### {header}")
            metrics_parts = [
                f"{s['kcal']:.0f} kcal/100g",
                f"{s['protein']:.1f}g protein",
                f"{s['carbs']:.1f}g carbs",
                f"{s['fat']:.1f}g fat",
            ]
            if s.get("fiber") is not None:
                metrics_parts.append(f"{s['fiber']:.1f}g fiber")
            st.caption(", ".join(metrics_parts))
            if s.get("reasons"):
                st.write("Reasons:")
                for r in s["reasons"]:
                    st.markdown(f"- {r}")
            st.divider()


