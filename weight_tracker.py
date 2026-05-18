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


def _get_tdee():
    """Get the user's TDEE from session state."""
    return st.session_state.get('tdee', 2000)


def _get_adjusted_calories():
    """Get the user's adjusted daily calories from session state."""
    return st.session_state.get('adjusted_calories', 2000)


def predict_weight_trend():
    """Generate weight predictions using simple calorie balance model.

    Returns:
        dict with 'optimistic' and 'pessimistic' DataFrames (Date, PredictedWeight)
        plus time-to-target estimates
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

    future_dates = []
    optimistic_weights = []
    pessimistic_weights = []
    follow_plan_weights = []
    ideal_body_weight = st.session_state.get('ideal_weight', current_weight)
    target_weight = st.session_state.get('target_weight', ideal_body_weight)

    # Scale factors based on adherence and consistency
    # Following plan: assumes user sticks to plan (adherence + consistency improve)
    follow_plan_factor = 0.3 + 0.7 * (macro_adherence * 0.6 + consistency * 0.4)
    optimistic_factor = 0.5 + 0.5 * (macro_adherence * 0.7 + consistency * 0.3)
    pessimistic_factor = 1.5 - 0.5 * (macro_adherence * 0.7 + consistency * 0.3)

    # Ensure factors are reasonable
    follow_plan_factor = max(0.3, min(follow_plan_factor, 1.0))
    optimistic_factor = max(0.3, min(optimistic_factor, 1.0))
    pessimistic_factor = max(1.0, min(pessimistic_factor, 2.5))

    follow_plan_balance = calorie_balance * follow_plan_factor
    optimistic_balance = calorie_balance * optimistic_factor
    pessimistic_balance = calorie_balance * pessimistic_factor

    # Daily weight change in kg (3500 kcal ≈ 0.45 kg)
    daily_change_follow = (follow_plan_balance / 3500.0) * 0.45
    daily_change_optimistic = (optimistic_balance / 3500.0) * 0.45
    daily_change_pessimistic = (pessimistic_balance / 3500.0) * 0.45

    # Estimate TDEE and adjusted calories for maintenance prediction
    tdee = _get_tdee()
    adjusted_cal = _get_adjusted_calories()
    # If at goal weight, maintenance calories = TDEE
    maintenance_calories = tdee

    # Project 90 days into future (approx 3 months)
    start_date = datetime.now().date()
    
    # Track when target weight is reached
    days_to_target_follow = None
    days_to_target_optimistic = None
    days_to_target_pessimistic = None
    
    # Maintenance weight after reaching target
    maintenance_weight = target_weight  # Once at target, stay at target with maintenance
    
    for day_offset in range(0, 91, 7):  # Weekly data points
        date = start_date + timedelta(days=day_offset)
        future_dates.append(date)

        # Follow plan weight
        fp_weight = current_weight + daily_change_follow * day_offset
        # Apply realistic bounds
        fp_weight = max(25.0, min(fp_weight, 250.0))
        follow_plan_weights.append(round(fp_weight, 1))

        # Optimistic weight
        opt_weight = current_weight + daily_change_optimistic * day_offset
        opt_weight = max(25.0, min(opt_weight, 250.0))
        optimistic_weights.append(round(opt_weight, 1))

        # Pessimistic weight
        pess_weight = current_weight + daily_change_pessimistic * day_offset
        pess_weight = max(25.0, min(pess_weight, 250.0))
        pessimistic_weights.append(round(pess_weight, 1))

        # Calculate days to reach target weight
        if days_to_target_follow is None and daily_change_follow != 0:
            needed_change = target_weight - current_weight
            days_needed = needed_change / daily_change_follow
            if days_needed > 0 and day_offset >= days_needed:
                days_to_target_follow = int(days_needed)
        if days_to_target_optimistic is None and daily_change_optimistic != 0:
            needed_change = target_weight - current_weight
            days_needed = needed_change / daily_change_optimistic
            if days_needed > 0 and day_offset >= days_needed:
                days_to_target_optimistic = int(days_needed)

    # If target wasn't reached within 90 days, estimate linearly
    if days_to_target_follow is None and daily_change_follow != 0:
        needed_change = target_weight - current_weight
        if needed_change != 0 and abs(daily_change_follow) > 0.001:
            days_to_target_follow = int(abs(needed_change / daily_change_follow))
        else:
            days_to_target_follow = 999  # Already at target or no change
    if days_to_target_optimistic is None and daily_change_optimistic != 0:
        needed_change = target_weight - current_weight
        if needed_change != 0 and abs(daily_change_optimistic) > 0.001:
            days_to_target_optimistic = int(abs(needed_change / daily_change_optimistic))
        else:
            days_to_target_optimistic = 999

    # For pessimistic, just cap at >365
    if daily_change_pessimistic != 0:
        needed_change = target_weight - current_weight
        if needed_change != 0 and abs(daily_change_pessimistic) > 0.001:
            days_to_target_pessimistic = int(abs(needed_change / daily_change_pessimistic))
        else:
            days_to_target_pessimistic = 999
    days_to_target_pessimistic = min(days_to_target_pessimistic or 999, 999)

    follow_df = pd.DataFrame({
        'Date': future_dates,
        'PredictedWeight': follow_plan_weights,
        'Scenario': 'Consistent Plan'
    })
    opt_df = pd.DataFrame({
        'Date': future_dates,
        'PredictedWeight': optimistic_weights,
        'Scenario': 'Optimal Plan'
    })
    pess_df = pd.DataFrame({
        'Date': future_dates,
        'PredictedWeight': pessimistic_weights,
        'Scenario': 'Inconsistent Plan'
    })

    return {
        'follow_plan': follow_df,
        'optimistic': opt_df,
        'pessimistic': pess_df,
        'current_weight': current_weight,
        'target_weight': target_weight,
        'ideal_body_weight': ideal_body_weight,
        'calorie_balance': calorie_balance,
        'macro_adherence': macro_adherence,
        'consistency': consistency,
        'daily_change_follow': daily_change_follow,
        'daily_change_opt': daily_change_optimistic,
        'daily_change_pess': daily_change_pessimistic,
        'days_to_target_follow': min(days_to_target_follow or 999, 999),
        'days_to_target_optimistic': min(days_to_target_optimistic or 999, 999),
        'days_to_target_pessimistic': days_to_target_pessimistic,
        'maintenance_calories': maintenance_calories,
        'adjusted_calories': adjusted_cal,
        'tdee': tdee,
    }


def create_weight_prediction_chart(prediction):
    """Create an enhanced dual-line chart showing weight projections with confidence bands."""
    if not prediction:
        return None

    combined = pd.concat([prediction['follow_plan'], prediction['optimistic'], prediction['pessimistic']])
    target_weight = prediction['target_weight']
    ideal_weight = prediction['ideal_body_weight']

    fig = go.Figure()

    # Follow Plan trace (main trace - thickest)
    fp = prediction['follow_plan']
    fig.add_trace(go.Scatter(
        x=fp['Date'], y=fp['PredictedWeight'],
        mode='lines+markers',
        name='✅ Following Plan',
        line=dict(color='#10b981', width=3.5, dash='solid'),
        marker=dict(size=6, color='#10b981', symbol='circle'),
    ))

    # Optimistic trace
    opt = prediction['optimistic']
    fig.add_trace(go.Scatter(
        x=opt['Date'], y=opt['PredictedWeight'],
        mode='lines+markers',
        name='⚡ Optimal Adherence',
        line=dict(color='#34d399', width=2, dash='dot'),
        marker=dict(size=5, color='#34d399', symbol='diamond'),
    ))

    # Pessimistic trace
    pess = prediction['pessimistic']
    fig.add_trace(go.Scatter(
        x=pess['Date'], y=pess['PredictedWeight'],
        mode='lines+markers',
        name='⚠️ Off Plan',
        line=dict(color='#ef4444', width=2.5, dash='dash'),
        marker=dict(size=5, color='#ef4444', symbol='x'),
    ))

    # Target weight horizontal line
    fig.add_hline(
        y=target_weight,
        line_dash="dot", line_color="#3b82f6",
        annotation_text=f"🎯 Target: {target_weight:.0f} kg",
        annotation_position="right",
        annotation_font=dict(color="#3b82f6", size=11),
        line_width=2,
    )

    # Ideal weight horizontal line
    if abs(ideal_weight - target_weight) > 0.5:
        fig.add_hline(
            y=ideal_weight,
            line_dash="dashdot", line_color="#8b5cf6",
            annotation_text=f"⭐ Ideal: {ideal_weight:.0f} kg",
            annotation_position="left",
            annotation_font=dict(color="#8b5cf6", size=10),
            line_width=1.5,
        )

    # Add actual weight history if available
    hist_df = _get_weight_data()
    if hist_df is not None and len(hist_df) > 0:
        fig.add_trace(go.Scatter(
            x=hist_df['Date'], y=hist_df['Weight'],
            mode='lines+markers',
            name='📊 Actual Weight',
            line=dict(color='#f59e0b', width=2.5, dash='solid'),
            marker=dict(size=7, color='#f59e0b', symbol='star'),
            hovertemplate='%{x|%b %d, %Y}<br>Weight: %{y:.1f} kg<extra></extra>',
        ))

    # Add confidence band between follow_plan and pessimistic
    fig.add_trace(go.Scatter(
        x=list(pess['Date']) + list(fp['Date'][::-1]),
        y=list(pess['PredictedWeight']) + list(fp['PredictedWeight'][::-1]),
        fill='toself',
        fillcolor='rgba(16, 185, 129, 0.08)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo='skip',
        showlegend=True,
        name='📊 Confidence Range',
    ))

    fig.update_layout(
        title=dict(
            text="📈 AI Weight Prediction (90-Day Outlook)",
            font=dict(size=16, color='#1f2937'),
        ),
        xaxis_title="Date",
        yaxis_title="Weight (kg)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10),
        ),
        hovermode="x unified",
        template="plotly_white",
        height=500,
        margin=dict(l=40, r=40, t=60, b=40),
        xaxis=dict(
            showgrid=True,
            gridcolor='#f1f5f9',
            gridwidth=1,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#f1f5f9',
            gridwidth=1,
            zeroline=False,
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
    )

    # Add a vertical line marking "today"
    fig.add_vline(
        x=datetime.now().timestamp() * 1000,
        line_dash="dash",
        line_color="#94a3b8",
        annotation_text="Today",
        annotation_position="top",
        line_width=1.5,
        opacity=0.6,
    )

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

            # Enhanced line chart with target line
            fig = go.Figure()
            
            # Main weight trace
            fig.add_trace(go.Scatter(
                x=df['Date'], y=df['Weight'],
                mode='lines+markers',
                name='Weight',
                line=dict(color='#10b981', width=2.5),
                marker=dict(size=8, color='#10b981'),
                hovertemplate='%{x|%b %d, %Y}<br>Weight: %{y:.1f} kg<extra></extra>',
            ))
            
            # Target weight line
            target = st.session_state.get('target_weight', st.session_state.ideal_weight)
            fig.add_hline(
                y=target,
                line_dash="dash",
                line_color="#ef4444",
                annotation_text=f"Target: {target:.1f} kg",
                annotation_position="right",
                line_width=2,
            )
            
            # Ideal weight line
            ideal = st.session_state.ideal_weight
            if abs(ideal - target) > 0.5:
                fig.add_hline(
                    y=ideal,
                    line_dash="dot",
                    line_color="#8b5cf6",
                    annotation_text=f"Ideal: {ideal:.1f} kg",
                    annotation_position="left",
                    line_width=1.5,
                )

            # Fit polynomial trendline
            if len(df) >= 3:
                x_numeric = (df['Date'] - df['Date'].min()).dt.total_seconds() / (3600 * 24)
                z = np.polyfit(x_numeric, df['Weight'], min(2, len(df) - 1))
                p = np.poly1d(z)
                trend_y = p(x_numeric)
                fig.add_trace(go.Scatter(
                    x=df['Date'], y=trend_y,
                    mode='lines',
                    name='Trend',
                    line=dict(color='#f59e0b', width=2, dash='dot'),
                    opacity=0.7,
                    hovertemplate='%{x|%b %d, %Y}<br>Trend: %{y:.1f} kg<extra></extra>',
                ))

            fig.update_layout(
                title=dict(
                    text="Weight Change Over Time",
                    font=dict(size=14, color='#1f2937'),
                ),
                xaxis_title="Date",
                yaxis_title="Weight (kg)",
                hovermode="x unified",
                template="plotly_white",
                height=400,
                margin=dict(l=40, r=40, t=50, b=40),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                ),
            )
            st.plotly_chart(fig, use_container_width=True)

            # Weight change stats in a clean row
            stats_cols = st.columns(4)
            if len(df) > 1:
                initial_weight = float(df['Weight'].iloc[0])
                current_weight_val = float(df['Weight'].iloc[-1])
                change = current_weight_val - initial_weight
                stats_cols[0].metric("Total Change", f"{change:+.1f} kg", f"From {initial_weight:.1f} kg")

                # Weekly trend
                df['week'] = df['Date'].dt.to_period('W')
                weekly_avg = df.groupby('week')['Weight'].mean().reset_index()
                weekly_avg['week'] = weekly_avg['week'].astype(str)
                if len(weekly_avg) > 1:
                    weekly_change = weekly_avg['Weight'].iloc[-1] - weekly_avg['Weight'].iloc[-2]
                    stats_cols[1].metric("Weekly Trend", f"{weekly_change:+.2f} kg/week")
                else:
                    stats_cols[1].metric("Weekly Trend", "N/A")

                # Monthly trend
                df['month'] = df['Date'].dt.to_period('M')
                monthly_avg = df.groupby('month')['Weight'].mean().reset_index()
                monthly_avg['month'] = monthly_avg['month'].astype(str)
                if len(monthly_avg) > 1:
                    monthly_change = monthly_avg['Weight'].iloc[-1] - monthly_avg['Weight'].iloc[-2]
                    stats_cols[2].metric("Monthly Trend", f"{monthly_change:+.2f} kg/month")
                else:
                    stats_cols[2].metric("Monthly Trend", "N/A")

                # Rate of change
                days_elapsed = (df['Date'].iloc[-1] - df['Date'].iloc[0]).days
                if days_elapsed > 0:
                    daily_rate = change / days_elapsed
                    stats_cols[3].metric("Daily Rate", f"{daily_rate:+.3f} kg/day")
                else:
                    stats_cols[3].metric("Daily Rate", "N/A")
        else:
            st.info("No weight data logged yet. Start logging your weight to see charts!")

    # --- Enhanced AI Weight Prediction Section ---
    st.markdown("---")
    st.subheader("🤖 AI Weight Prediction")

    with st.spinner("Analyzing your data for weight predictions..."):
        prediction = predict_weight_trend()

    if prediction:
        current_w = prediction['current_weight']
        target_w = prediction['target_weight']
        ideal_w = prediction['ideal_body_weight']
        weight_diff = target_w - current_w
        is_losing = weight_diff < 0
        
        # Determine direction emoji
        direction_emoji = "📉" if is_losing else "📈"
        
        # Show prediction insights
        insight_col1, insight_col2, insight_col3, insight_col4 = st.columns(4)
        with insight_col1:
            cal_balance = prediction['calorie_balance']
            balance_label = "Surplus" if cal_balance > 0 else "Deficit"
            st.metric(
                "Est. Calorie Balance",
                f"{abs(cal_balance):.0f} kcal",
                balance_label,
            )

        with insight_col2:
            adh = prediction['macro_adherence'] * 100
            st.metric("Macro Adherence", f"{adh:.0f}%", "Protein target")

        with insight_col3:
            cons = prediction['consistency'] * 100
            st.metric("Logging Consistency", f"{cons:.0f}%", "14-day streak")

        with insight_col4:
            follow_change = prediction['daily_change_follow'] * 90
            st.metric("90-Day Projection (Plan)", f"{follow_change:+.1f} kg", direction_emoji)

        # --- New: Time to Target Weight ---
        time_cols = st.columns(3)
        with time_cols[0]:
            days_follow = prediction['days_to_target_follow']
            if days_follow and days_follow < 999:
                weeks = days_follow // 7
                extra_days = days_follow % 7
                time_str = f"{weeks}w {extra_days}d" if weeks > 0 else f"{extra_days}d"
                st.metric(
                    "⏱️ Time to Target (Following Plan)",
                    time_str,
                    f"{days_follow} days",
                )
            else:
                st.metric("⏱️ Time to Target (Plan)", "At target ✓", "Maintain current weight")

        with time_cols[1]:
            days_opt = prediction['days_to_target_optimistic']
            if days_opt and days_opt < 999:
                weeks = days_opt // 7
                extra_days = days_opt % 7
                time_str = f"{weeks}w {extra_days}d" if weeks > 0 else f"{extra_days}d"
                st.metric(
                    "⚡ With Optimal Adherence",
                    time_str,
                    f"{days_opt} days",
                )
            else:
                st.metric("⚡ Optimal Time", "At target ✓")

        with time_cols[2]:
            days_pess = prediction['days_to_target_pessimistic']
            if days_pess and days_pess < 999:
                weeks = days_pess // 7
                extra_days = days_pess % 7
                time_str = f"{weeks}w {extra_days}d" if weeks > 0 else f"{extra_days}d"
                st.metric(
                    "⚠️ If Off Plan",
                    time_str,
                    f"or never reach target",
                )
            else:
                st.metric("⚠️ If Off Plan", "Not projected", "Inconsistent")

        # Prediction chart
        chart = create_weight_prediction_chart(prediction)
        if chart:
            st.plotly_chart(chart, use_container_width=True)

        # --- New: Ideal Weight Maintenance Prediction ---
        st.subheader("🎯 Ideal Weight Maintenance")
        maint_cols = st.columns(3)
        
        with maint_cols[0]:
            tdee_val = prediction['tdee']
            st.metric(
                "Maintenance Calories (TDEE)",
                f"{tdee_val:.0f} kcal/day",
                "Eat this to maintain weight",
            )
        
        with maint_cols[1]:
            adjusted_cal = prediction['adjusted_calories']
            if is_losing:
                st.metric(
                    "Current Deficit Calories",
                    f"{adjusted_cal:.0f} kcal/day",
                    f"Deficit: {tdee_val - adjusted_cal:.0f} kcal",
                )
            else:
                st.metric(
                    "Current Surplus Calories",
                    f"{adjusted_cal:.0f} kcal/day",
                    f"Surplus: {adjusted_cal - tdee_val:.0f} kcal",
                )
        
        with maint_cols[2]:
            # Estimate weight at maintenance
            maintenance_weight_pred = target_w  # Once at target, maintain with TDEE
            lbm = st.session_state.get('lean_body_mass', current_w * 0.7)
            bfp = st.session_state.get('body_fat_pct', 20)
            st.metric(
                "Predicted Maintenance Weight",
                f"{maintenance_weight_pred:.1f} kg",
                f"Body Fat: {bfp:.1f}%",
            )

        # --- New: Detailed Prediction Breakdown ---
        with st.expander("📊 View Detailed Prediction Data"):
            fp = prediction['follow_plan']
            opt = prediction['optimistic']
            pess = prediction['pessimistic']

            detail_df = pd.DataFrame({
                'Date': pd.to_datetime(fp['Date']),
                'Following Plan (kg)': fp['PredictedWeight'],
                'Optimal (kg)': opt['PredictedWeight'],
                'Off Plan (kg)': pess['PredictedWeight'],
                'Δ Plan vs Off (kg)': [
                    round(f - p, 1) for f, p in zip(fp['PredictedWeight'], pess['PredictedWeight'])
                ]
            })
            detail_df['Date_str'] = detail_df['Date'].dt.strftime('%b %d, %Y')
            display_df = detail_df.drop(columns=['Date']).rename(columns={'Date_str': 'Date'})
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            # Key metrics summary
            st.markdown("### 📋 Prediction Summary")
            sum_cols = st.columns(2)
            with sum_cols[0]:
                st.markdown(f"""
                **Current Stats:**
                - Current Weight: **{current_w:.1f} kg**
                - Target Weight: **{target_w:.1f} kg**
                - To Go: **{abs(weight_diff):.1f} kg** {'↓' if is_losing else '↑'}
                - Daily Calorie Balance: **{cal_balance:+.0f} kcal**
                - Macro Adherence: **{adh:.0f}%**
                - Logging Consistency: **{cons:.0f}%**
                """)
            with sum_cols[1]:
                st.markdown(f"""
                **Projections:**
                - Following Plan: **{prediction['daily_change_follow'] * 90:+.1f} kg** in 90 days
                - Optimal: **{prediction['daily_change_opt'] * 90:+.1f} kg** in 90 days
                - Off Plan: **{prediction['daily_change_pess'] * 90:+.1f} kg** in 90 days
                - Maintenance Calories: **{tdee_val:.0f} kcal/day**
                """)

            st.markdown("""
            <div style='background: #f0fdf4; padding: 15px; border-radius: 8px; border-left: 4px solid #10b981;'>
            <strong>How this works:</strong><br>
            • Based on the <strong>3500 kcal ≈ 0.45 kg (1 lb)</strong> body fat rule<br>
            • Your estimated daily calorie balance is calculated from tracked meals vs targets<br>
            • Macro adherence (protein target %) and logging consistency improve the optimistic projection<br>
            • <strong>Following Plan</strong>: Assumes you maintain adherence (deficit/surplus scales accordingly)<br>
            • <strong>Off Plan</strong>: Assumes reduced adherence (50-150% of current balance)<br>
            • Weight changes are linear estimates; actual results vary with metabolism, exercise, and water weight
            </div>
            """, unsafe_allow_html=True)

    else:
        st.info("Not enough data for predictions yet. Log meals and weight regularly to enable AI-powered predictions.")


def log_weight(weight, date):
    date_str = date.strftime('%Y-%m-%d')
    st.session_state.weight_log[date_str] = weight
    st.session_state.current_weight = float(weight)
    st.success(f"Weight logged: {weight} kg for {date.strftime('%B %d, %Y')}")
    st.rerun()