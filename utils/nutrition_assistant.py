import re
from typing import Dict, Any, List

import numpy as np
import pandas as pd

try:
    import streamlit as st
except Exception:  # pragma: no cover
    st = None

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def _safe_get_row_text(row: pd.Series) -> str:
    """Create a text representation for retrieval from a dataset row."""
    parts: List[str] = []
    for col in ["category", "cuisine", "meal_types", "health_score", "tags"]:
        if col in row.index and row[col] is not None and str(row[col]).strip() != "":
            parts.append(str(row[col]))
    return " ".join(parts)


def _normalize_query(q: str) -> str:
    q = str(q or "").lower().strip()
    q = re.sub(r"\s+", " ", q)
    return q


def build_nutrition_retriever(nutrition_df: pd.DataFrame) -> Dict[str, Any]:
    """Build a TF-IDF retriever index."""
    foods = list(nutrition_df.index.astype(str))
    corpus: List[str] = []

    for food in foods:
        row = nutrition_df.loc[food]
        corpus.append(f"{food} {_safe_get_row_text(row)}".strip())

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        min_df=2,
        max_features=5000,
    )
    matrix = vectorizer.fit_transform(corpus)

    return {
        "vectorizer": vectorizer,
        "matrix": matrix,
        "foods": foods,
        "corpus": corpus,
    }


def _apply_diet_filter(nutrition_df: pd.DataFrame, veg_pref: str, allergies_csv: str = "") -> pd.DataFrame:
    """Conservative dataset-category filtering for the Assistant tab."""
    df = nutrition_df

    if veg_pref and veg_pref.lower() in {"vegetarian", "vegan"} and "category" in df.columns:
        cat = df["category"].astype(str).str.lower()
        if veg_pref.lower() == "vegan":
            df = df[~cat.isin(["dairy", "non-veg"])]
        else:
            df = df[~cat.isin(["non-veg"])]

    if allergies_csv and "category" in df.columns:
        allergies: List[str] = [a.strip().lower() for a in str(allergies_csv).split(",") if a.strip()]
        if allergies:
            cat = df["category"].astype(str).str.lower()
            mask_keep = np.ones(len(df), dtype=bool)
            for a in allergies:
                mask_keep &= ~cat.str.contains(re.escape(a), na=False)
            df = df[mask_keep]

    return df


def retrieve_relevant_foods(
    query: str,
    nutrition_df: pd.DataFrame,
    retriever: Dict[str, Any],
    top_k: int = 12,
    veg_pref: str = "none",
    allergies: str = "",
) -> pd.DataFrame:
    """Retrieve top-k foods using TF-IDF cosine similarity."""
    if nutrition_df is None or nutrition_df.empty:
        return pd.DataFrame()

    q = _normalize_query(query)

    try:
        vectorizer = retriever["vectorizer"]
        matrix = retriever["matrix"]
    except Exception:
        return pd.DataFrame()

    q_vec = vectorizer.transform([q])
    scores = cosine_similarity(q_vec, matrix)[0]

    top_idx = np.argsort(scores)[::-1][: max(top_k * 3, top_k)]

    candidates = nutrition_df.iloc[top_idx].copy()
    candidates["_retrieval_score"] = scores[top_idx]

    candidates = _apply_diet_filter(candidates, veg_pref=veg_pref, allergies_csv=allergies)
    candidates = candidates.sort_values("_retrieval_score", ascending=False)

    if len(candidates) > top_k:
        candidates = candidates.head(top_k)

    return candidates


def assistant_answer(
    query: str,
    nutrition_df: pd.DataFrame,
    retriever: Dict[str, Any],
    veg_pref: str = "none",
    allergies: str = "",
    max_results: int = 6,
) -> str:
    """Dataset-grounded answers for the Assistant tab (no external LLM calls)."""
    if nutrition_df is None or nutrition_df.empty:
        return "Nutrition dataset is unavailable."

    # Lightweight intent parsing
    ql = str(query or "").lower()
    effective_pref = veg_pref
    if "vegan" in ql:
        effective_pref = "vegan"
    elif "vegetarian" in ql:
        effective_pref = "vegetarian"

    retrieved = retrieve_relevant_foods(
        query=query,
        nutrition_df=nutrition_df,
        retriever=retriever,
        top_k=max_results * 2,
        veg_pref=effective_pref or "none",
        allergies=allergies,
    )

    if retrieved is None or retrieved.empty:
        return "I couldn’t find foods matching your query with your dietary preferences."

    def _fiber_val(row: pd.Series) -> float:
        try:
            return float(row.get("fiber", 0) or 0)
        except Exception:
            return 0.0

    def _protein_val(row: pd.Series) -> float:
        try:
            return float(row.get("protein", 0) or 0)
        except Exception:
            return 0.0

    ranked = retrieved.copy()
    ranked["_final_score"] = ranked["_retrieval_score"] + 0.5 * ranked.apply(_protein_val, axis=1) + 0.2 * ranked.apply(_fiber_val, axis=1)
    ranked = ranked.sort_values("_final_score", ascending=False)

    picks = ranked.head(max_results)

    lines: List[str] = ["Here are dataset-matched options based on your query and diet filters:"]

    for food, row in picks.iterrows():
        kcal = float(row.get("kcal", 0) or 0)
        protein = float(row.get("protein", 0) or 0)
        carbs = float(row.get("carbs", 0) or 0)
        fat = float(row.get("fat", 0) or 0)
        fiber = float(row.get("fiber", 0) or 0) if "fiber" in row.index else None

        if fiber is not None:
            lines.append(f"• {food} — {kcal:.0f} kcal/100g, {protein:.1f}g protein, {carbs:.1f}g carbs, {fat:.1f}g fat, {fiber:.1f}g fiber")
        else:
            lines.append(f"• {food} — {kcal:.0f} kcal/100g, {protein:.1f}g protein, {carbs:.1f}g carbs, {fat:.1f}g fat")

    # Keep response short; do NOT include the banned Smart Swap tip line.
    return "\n".join(lines)


def assistant_tab_ui(nutrition_df: pd.DataFrame, veg_pref: str, allergies: str):
    """Streamlit UI for the Assistant tab (imported by app.py)."""
    import streamlit as st

    if "assistant_messages" not in st.session_state:
        st.session_state.assistant_messages = []

    st.subheader("AI Nutrition Assistant")
    st.caption("Dataset-grounded answers using TF-IDF retrieval (no external LLM calls).")

    if nutrition_df is None or nutrition_df.empty:
        st.warning("Nutrition dataset is unavailable.")
        return

    if "assistant_retriever" not in st.session_state:
        st.session_state.assistant_retriever = build_nutrition_retriever(nutrition_df)

    chat_box = st.container()
    with chat_box:
        for msg in st.session_state.assistant_messages:
            role = msg.get("role")
            content = msg.get("content")
            if role == "user":
                st.markdown(
                    f"<div style='background:#eef2ff;border-radius:12px;padding:10px 14px;margin:8px 0;'><b>You:</b> {content}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<div style='background:#f8fafc;border-radius:12px;padding:10px 14px;margin:8px 0;border:1px solid #e5e7eb;'><b>Assistant:</b><br/>{str(content).replace(chr(10), '<br/>')}</div>",
                    unsafe_allow_html=True,
                )

    with st.form("assistant_form", clear_on_submit=True):
        user_query = st.text_input(
            "Ask a nutrition question",
            placeholder="Best vegetarian protein sources under 300 calories?",
            key="assistant_query",
        )
        submitted = st.form_submit_button("Ask")

    if submitted and user_query.strip():
        st.session_state.assistant_messages.append({"role": "user", "content": user_query.strip()})
        answer = assistant_answer(
            query=user_query,
            nutrition_df=nutrition_df,
            retriever=st.session_state.assistant_retriever,
            veg_pref=veg_pref,
            allergies=allergies,
            max_results=6,
        )
        st.session_state.assistant_messages.append({"role": "assistant", "content": answer})
        st.rerun()

    st.caption("You can ask: protein sources, vegan/vegetarian options, weight-loss friendly snacks, and macro-focused suggestions.")

