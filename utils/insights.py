from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None or (isinstance(x, float) and np.isnan(x)):
            return default
        return float(x)
    except Exception:
        return default


def _build_daily_frame(daily_log: Dict[str, List[Dict[str, Any]]]) -> pd.DataFrame:
    if not daily_log:
        return pd.DataFrame()

    rows = []
    for date_str, meals in daily_log.items():
        d = pd.to_datetime(date_str, errors="coerce")
        if pd.isna(d):
            continue
        total = {"Date": d}
        for k in ["Calories", "Protein", "Carbs", "Fat"]:
            total[k] = 0.0
        # meal timing (late-night) is not available in current app, but we keep placeholder.
        for m in meals or []:
            total["Calories"] += _safe_float(m.get("Calories"))
            total["Protein"] += _safe_float(m.get("Protein"))
            total["Carbs"] += _safe_float(m.get("Carbs"))
            total["Fat"] += _safe_float(m.get("Fat"))
        rows.append(total)

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df.sort_values("Date")
    df["weekday"] = df["Date"].dt.day_name()
    df["is_weekend"] = df["Date"].dt.weekday >= 5
    df["day_index"] = np.arange(len(df))
    return df


def _linear_trend_slope(y: np.ndarray) -> float:
    if len(y) < 2:
        return 0.0
    x = np.arange(len(y))
    # least squares slope
    slope = np.cov(x, y, bias=True)[0, 1] / (np.var(x) + 1e-9)
    return float(slope)


def build_insights(
    daily_log: Dict[str, List[Dict[str, Any]]],
    targets: Optional[Dict[str, float]] = None,
    weight_log: Optional[Dict[str, float]] = None,
    workout_log: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Generate clean, AI-style insight cards.

    Only uses available data; if activity/workout timestamps are missing,
    we output a safe degraded insight.
    """
    df = _build_daily_frame(daily_log)
    if df.empty:
        return []

    insights: List[Dict[str, Any]] = []

    # Trend: calories slope
    for macro in ["Calories", "Protein", "Carbs", "Fat"]:
        slope = _linear_trend_slope(df[macro].values)
        if abs(slope) > 1e-6:
            direction = "increasing" if slope > 0 else "decreasing"
            insights.append(
                {
                    "title": f"{macro} trend is {direction}",
                    "detail": f"Over your logged period, {macro.lower()} shows a consistent {direction} pattern (slope ≈ {slope:.2f}).",
                    "kind": "trend",
                }
            )

    # Weekday vs weekend comparisons for protein/fiber-ish proxies
    weekday_mean_pro = df.loc[~df["is_weekend"], "Protein"].mean() if (~df["is_weekend"]).any() else 0.0
    weekend_mean_pro = df.loc[df["is_weekend"], "Protein"].mean() if (df["is_weekend"]).any() else 0.0
    if weekday_mean_pro > 0 and weekend_mean_pro > 0:
        diff = weekend_mean_pro - weekday_mean_pro
        if abs(diff) > 1e-3:
            if diff >= 0:
                insights.append(
                    {
                        "title": "Protein intake is higher on weekends",
                        "detail": f"Average protein: {weekend_mean_pro:.0f}g (weekend) vs {weekday_mean_pro:.0f}g (weekdays).",
                        "kind": "comparison",
                    }
                )
            else:
                insights.append(
                    {
                        "title": "Protein intake improves on weekdays",
                        "detail": f"Average protein: {weekday_mean_pro:.0f}g (weekdays) vs {weekend_mean_pro:.0f}g (weekend).",
                        "kind": "comparison",
                    }
                )

    # Weekend calories surplus
    weekday_mean_cal = df.loc[~df["is_weekend"], "Calories"].mean() if (~df["is_weekend"]).any() else 0.0
    weekend_mean_cal = df.loc[df["is_weekend"], "Calories"].mean() if (df["is_weekend"]).any() else 0.0
    if weekday_mean_cal > 0 and weekend_mean_cal > 0:
        cal_diff = weekend_mean_cal - weekday_mean_cal
        if abs(cal_diff) > 1e-3:
            if cal_diff > 0:
                insights.append(
                    {
                        "title": "Weekend calorie intake runs higher",
                        "detail": f"Average calories: {weekend_mean_cal:.0f} (weekend) vs {weekday_mean_cal:.0f} (weekdays).",
                        "kind": "comparison",
                    }
                )

    # Weight correlation (if provided)
    if weight_log:
        try:
            wdf = pd.DataFrame([{ "Date": pd.to_datetime(k, errors="coerce"), "Weight": v } for k, v in weight_log.items()])
            wdf = wdf.dropna(subset=["Date"]).sort_values("Date")
            if not wdf.empty:
                merged = pd.merge_asof(wdf, df.sort_values("Date"), on="Date", direction="backward", tolerance=pd.Timedelta(days=2))
                if not merged.empty and "Calories" in merged.columns:
                    corr = np.corrcoef(merged["Calories"].values, merged["Weight"].values)[0, 1]
                    if np.isfinite(corr):
                        insights.append(
                            {
                                "title": "Calories & weight move together (weak signal)",
                                "detail": f"Correlation between logged calories and weight is r ≈ {corr:.2f}.",
                                "kind": "correlation",
                            }
                        )
        except Exception:
            pass

    # Late-night eating correlation - not possible without timestamps
    # Current app logs only date, so we provide an explicit safe insight.
    insights.append(
        {
            "title": "Late-night eating insight needs timestamps",
            "detail": "Meal times aren’t logged in this version (only dates), so we can’t accurately correlate late-night meals with calorie surplus.",
            "kind": "limitation",
        }
    )

    # Limit cards for clean UI
    # Prefer comparison/correlation/trend variety
    kind_priority = {"comparison": 0, "correlation": 1, "trend": 2, "limitation": 3}
    insights_sorted = sorted(insights, key=lambda x: kind_priority.get(x.get("kind"), 9))
    return insights_sorted[:8]

