import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np


def _get_weight_data():
    """Return sorted weight log as DataFrame, or None."""
    log = st.session_state.get('weight_log', {})
    if not log:
        return None
    df = pd.DataFrame(list(log.items()), columns=['Date', 'Weight'])
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    return df


def _estimate_daily_deficit_surplus():
    """Estimate daily calorie balance (deficit or surplus) based on tracked meals and targets.

    Uses weighted average of recent logged meal days to estimate habitual
    calorie surplus or deficit. Returns kcal/day (negative = deficit).
    """
    daily_log = st.session_state.get('daily_log', {})
    if not daily_log:
        return -300.0  # default modest deficit assumption

    adjusted_calories = st.session_state.get('adjusted_calories', 2000)

    deficits = []
    for date_str, meals in daily_log.items():
        if not meals:
            continue
        consumed = sum(m.get('Calories', 0) for m in meals)
        deficits.append(consumed - adjusted_calories)

    if not deficits:
        return -300.0

    # Weight recent days more heavily (last 7 days, 3x weight)
    weights = []
    for i, _ in enumerate(deficits):
        if i >= len(deficits) - 7:
            weights.append(3)
        else:
            weights.append(1)

    avg_deficit = np.average(deficits, weights=weights[:len(deficits)])
    return round(avg_deficit, 1)


def _estimate_macro_adherence():
    """Estimate macro adherence score 0.0-1.0 based on tracked meals."""
    daily_log = st.session_state.get('daily_log', {})
    if not daily_log:
        return 0.5  # neutral assumption

    protein_target = st.session_state.get('protein_g', 150)
    if protein_target <= 0:
        return 0.5

    adherence_scores = []
    for date_str, meals in daily_log.items():
        if not meals:
            continue
        protein_consumed = sum(m.get('Protein', 0) for m in meals)
        ratio = min(protein_consumed / protein_target, 1.5)
        adherence_scores.append(min(ratio, 1.0))

    return np.mean(adherence_scores) if adherence_scores else 0.5


def _estimate_consistency_streak_score():
    """Score 0.0-1.0 based on logging streak consistency."""
    daily_log = st.session_state.get('daily_log', {})
    if not daily_log:
        return 0.3

    dates = sorted(daily_log.keys())
    if len(dates) < 2:
        return 0.5

    # Count consecutive days logged in last 14 days
    now = datetime.now().date()
    check_dates = [(now - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(14)]
    logged_count = sum(1 for d in check_dates if d in daily_log and daily_log[d])
    return min(logged_count / 14.0, 1.0)


def predict_weight_trend():
    """Generate weight predictions using simple calorie balance model.

    Returns:
        dict with 'optimistic' and 'pessimistic' DataFrames (Date, PredictedWeight)
    """
    weight_df = _get_weight_data()
    current_weight = st.session_state.get('current_weight', 70.0)
    if weight_df is not None and len(weight_df) > 0:
        current_weight = weight_df['Weight'].iloc[-1]
    else:
        current_weight = st.session_state.get('current_weight', 70.0)
        if not current_weight or current_weight <= 0:
            current_weight = st.session_state.get('weight', 70.0)

    # Estimate current calorie balance
    calorie_balance = _estimate_daily_deficit_surplus()
    macro_adherence = _estimate_macro_adherence()
    consistency = _estimate_consistency_streak_score()

    # 3500 kcal ≈ 0.45 kg (1 lb) of body fat
    # Daily weight change = calorie_balance / 3500 * 0.45 (in kg)
    # For optimistic: assume user follows plan (50% better deficit/surplus adherence)
    # For pessimistic: assume user backslides (50% worse)

    future_dates = []
    optimistic_weights = []
    pessimistic_weights = []

    # Scale factors based on adherence and consistency
    optimistic_factor = 0.5 + 0.5 * (macro_adherence * 0.7 + consistency * 0.3)
    pessimistic_factor = 1.5 - 0.5 * (macro_adherence * 0.7 + consistency * 0.3)

    # Ensure factors are reasonable
    optimistic_factor = max(0.3, min(optimistic_factor, 1.0))
    pessimistic_factor = max(1.0, min(pessimistic_factor, 2.5))

    optimistic_balance = calorie_balance * optimistic_factor
    pessimistic_balance = calorie_balance * pessimistic_factor

    # Daily weight change in kg (3500 kcal ≈ 0.45 kg)
    daily_change_optimistic = (optimistic_balance / 3500.0) * 0.45
    daily_change_pessimistic = (pessimistic_balance / 3500.0) * 0.45

    # Project 90 days into future (approx 3 months)
    start_date = datetime.now().date()
    for day_offset in range(0, 91, 7):  # Weekly data points
        date = start_date + timedelta(days=day_offset)
        future_dates.append(date)

        opt_weight = current_weight + daily_change_optimistic * day_offset
        pess_weight = current_weight + daily_change_pessimistic * day_offset

        # Apply realistic bounds (don't go below 30 or above 250)
        opt_weight = max(30.0, min(opt_weight, 250.0))
        pess_weight = max(30.0, min(pess_weight, 250.0))

        optimistic_weights.append(round(opt_weight, 1))
        pessimistic_weights.append(round(pess_weight, 1))

    opt_df = pd.DataFrame({
        'Date': future_dates,
        'PredictedWeight': optimistic_weights,
        'Scenario': 'Consistent Plan'
    })
    pess_df = pd.DataFrame({
        'Date': future_dates,
        'PredictedWeight': pessimistic_weights,
        'Scenario': 'Inconsistent Plan'
    })

    return {
        'optimistic': opt_df,
        'pessimistic': pess_df,
        'current_weight': current_weight,
        'calorie_balance': calorie_balance,
        'macro_adherence': macro_adherence,
        'consistency': consistency,
        'daily_change_opt': daily_change_optimistic,
        'daily_change_pess': daily_change_pessimistic,
    }


def create_weight_prediction_chart(prediction):
    """Create a dual-line chart showing optimistic vs pessimistic weight projections."""
    if not prediction:
        return None

    combined = pd.concat([prediction['optimistic'], prediction['pessimistic']])

    # Target weight line
    target_weight = st.session_state.get('target_weight',
                                          st.session_state.get('ideal_weight', 70.0))

    fig = go.Figure()

    # Optimistic trace
    opt = prediction['optimistic']
    fig.add_trace(go.Scatter(
        x=opt['Date'], y=opt['PredictedWeight'],
        mode='lines+markers',
        name='✅ Following Plan',
        line=dict(color='#10b981', width=3, dash='solid'),
        marker=dict(size=6, color='#10b981'),
    ))

    # Pessimistic trace
    pess = prediction['pessimistic']
    fig.add_trace(go.Scatter(
        x=pess['Date'], y=pess['PredictedWeight'],
        mode='lines+markers',
        name='⚠️ Off Plan',
        line=dict(color='#ef4444', width=3, dash='dash'),
        marker=dict(size=6, color='#ef4444'),
    ))

    # Target weight line
    fig.add_hline(
        y=target_weight,
        line_dash="dot", line_color="#3b82f6",
        annotation_text=f"Target: {target_weight:.0f} kg",
        annotation_position="right",
        annotation_font=dict(color="#3b82f6", size=12),
    )

    # Add current weight marker if available
    hist_df = _get_weight_data()
    if hist_df is not None and len(hist_df) > 0:
        fig.add_trace(go.Scatter(
            x=hist_df['Date'], y=hist_df['Weight'],
            mode='lines+markers',
            name='📊 Actual Weight',
            line=dict(color='#f59e0b', width=2, dash='dot'),
            marker=dict(size=5, color='#f59e0b'),
        ))

    fig.update_layout(
        title="📈 Weight Prediction (90-Day Outlook)",
        xaxis_title="Date",
        yaxis_title="Weight (kg)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        hovermode="x unified",
        template="plotly_white",
        height=450,
    )

    # Add shaded confidence region between optimistic and pessimistic
    fig.add_trace(go.Scatter(
        x=list(pess['Date']) + list(opt['Date'][::-1]),
        y=list(pess['PredictedWeight']) + list(opt['PredictedWeight'][::-1]),
        fill='toself',
        fillcolor='rgba(16, 185, 129, 0.1)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo='skip',
        showlegend=True,
        name='📊 Projection Range',
    ))

    return fig


def weight_tracker_tab():
    st.header("⚖️ Weight Tracking")

    if not st.session_state.metrics_calculated:
        st.info("Please calculate your needs in the sidebar to see weight tracking.")
        return

    # Current metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Weight", f"{st.session_state.get('current_weight', 'N/A')} kg")
    with col2:
        st.metric("Ideal Body Weight", f"{st.session_state.ideal_weight:.1f} kg")
    with col3:
        st.metric("Target Weight", f"{st.session_state.get('target_weight', st.session_state.ideal_weight):.1f} kg")

    # Initialize weight log if not exists
    if 'weight_log' not in st.session_state:
        st.session_state.weight_log = {}

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Log Weight")

        # Weight input
        weight_default = st.session_state.get('current_weight', 70.0)
        if not weight_default or weight_default <= 0:
            weight_default = 70.0
        weight = st.number_input(
            "Weight (kg)",
            min_value=30.0,
            max_value=200.0,
            value=float(weight_default),
            key="weight_input_tracker",
        )
        date = st.date_input("Date", datetime.now().date(), key="weight_date_tracker")

        if st.button("Log Weight"):
            log_weight(weight, date)

        # Set target weight
        st.subheader("Set Target Weight")
        target_default = st.session_state.get('target_weight', st.session_state.ideal_weight)
        target_weight = st.number_input(
            "Target Weight (kg)",
            min_value=30.0,
            max_value=200.0,
            value=float(target_default),
            key="target_weight_input_tracker",
        )

        if st.button("Set Target"):
            st.session_state.target_weight = target_weight
            st.success(f"Target weight set to {target_weight} kg")

    with col2:
        # Weight history chart
        if st.session_state.weight_log:
            df = pd.DataFrame(list(st.session_state.weight_log.items()), columns=['Date', 'Weight'])
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date')

            # Update current weight
            st.session_state.current_weight = float(df['Weight'].iloc[-1])

            # Line chart with target line
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['Date'], y=df['Weight'], mode='lines+markers',
                                     name='Weight', line=dict(color='#4CAF50')))
            fig.add_hline(y=st.session_state.get('target_weight', st.session_state.ideal_weight),
                          line_dash="dash", line_color="red", annotation_text="Target Weight")
            fig.add_hline(y=st.session_state.ideal_weight,
                          line_dash="dot", line_color="blue", annotation_text="Ideal Weight")

            fig.update_layout(title="Weight Change Over Time",
                              xaxis_title="Date", yaxis_title="Weight (kg)")
            st.plotly_chart(fig, use_container_width=True)

            # Weight change stats
            if len(df) > 1:
                initial_weight = float(df['Weight'].iloc[0])
                current_weight = float(df['Weight'].iloc[-1])
                change = current_weight - initial_weight
                st.metric("Total Change", f"{change:+.1f} kg", f"From {initial_weight:.1f} kg")

                # Weekly trend
                df['week'] = df['Date'].dt.to_period('W')
                weekly_avg = df.groupby('week')['Weight'].mean().reset_index()
                weekly_avg['week'] = weekly_avg['week'].astype(str)
                if len(weekly_avg) > 1:
                    weekly_change = weekly_avg['Weight'].iloc[-1] - weekly_avg['Weight'].iloc[-2]
                    st.metric("Weekly Trend", f"{weekly_change:+.2f} kg")

                # Monthly trend
                df['month'] = df['Date'].dt.to_period('M')
                monthly_avg = df.groupby('month')['Weight'].mean().reset_index()
                monthly_avg['month'] = monthly_avg['month'].astype(str)
                if len(monthly_avg) > 1:
                    monthly_change = monthly_avg['Weight'].iloc[-1] - monthly_avg['Weight'].iloc[-2]
                    st.metric("Monthly Trend", f"{monthly_change:+.2f} kg")
        else:
            st.info("No weight data logged yet. Start logging your weight to see charts!")

    # --- Weight Prediction Section ---
    st.markdown("---")
    st.subheader("🤖 AI Weight Prediction")

    with st.spinner("Analyzing your data for weight predictions..."):
        prediction = predict_weight_trend()

    if prediction:
        # Show prediction insights
        insight_col1, insight_col2, insight_col3, insight_col4 = st.columns(4)
        with insight_col1:
            cal_balance = prediction['calorie_balance']
            balance_label = "Surplus" if cal_balance > 0 else "Deficit"
            st.metric("Est. Calorie Balance", f"{abs(cal_balance):.0f} kcal", balance_label)

        with insight_col2:
            adh = prediction['macro_adherence'] * 100
            st.metric("Macro Adherence", f"{adh:.0f}%")

        with insight_col3:
            cons = prediction['consistency'] * 100
            st.metric("Logging Consistency", f"{cons:.0f}%")

        with insight_col4:
            # Projected 90-day weight change for optimistic
            opt_change = prediction['daily_change_opt'] * 90
            st.metric("90-Day Projection (Plan)", f"{opt_change:+.1f} kg")

        # Prediction chart
        chart = create_weight_prediction_chart(prediction)
        if chart:
            st.plotly_chart(chart, use_container_width=True)

        # Detailed prediction breakdown
        with st.expander("📊 View Prediction Details"):
            opt = prediction['optimistic']
            pess = prediction['pessimistic']

            detail_df = pd.DataFrame({
                'Date': pd.to_datetime(opt['Date']),
                'Following Plan (kg)': opt['PredictedWeight'],
                'Off Plan (kg)': pess['PredictedWeight'],
                'Difference (kg)': [
                    round(o - p, 1) for o, p in zip(opt['PredictedWeight'], pess['PredictedWeight'])
                ]
            })
            detail_df['Date_str'] = detail_df['Date'].dt.strftime('%b %d, %Y')
            display_df = detail_df.drop(columns=['Date']).rename(columns={'Date_str': 'Date'})
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            st.markdown("""
            **How this works:**
            - Based on the **3500 kcal ≈ 0.45 kg** body fat rule
            - Your estimated daily calorie balance is calculated from tracked meals vs targets
            - Macro adherence (protein target %) and logging consistency improve the optimistic projection
            - **Following Plan**: Assumes you maintain adherence (deficit/surplus scales accordingly)
            - **Off Plan**: Assumes reduced adherence (50-150% of current balance)
            - Weight changes are linear estimates; actual results vary with metabolism, exercise, and water weight
            """)

    else:
        st.info("Not enough data for predictions yet. Log meals and weight regularly to enable AI-powered predictions.")


def log_weight(weight, date):
    date_str = date.strftime('%Y-%m-%d')
    st.session_state.weight_log[date_str] = weight
    st.session_state.current_weight = float(weight)
    st.success(f"Weight logged: {weight} kg for {date.strftime('%B %d, %Y')}")
    st.rerun()