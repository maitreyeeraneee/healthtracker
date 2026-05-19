import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.supabase_client import insert_row

def water_tracker_tab():
    # Modern header with icon
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 24px;">
        <div style="background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%); 
                    width: 48px; height: 48px; border-radius: 12px; 
                    display: flex; align-items: center; justify-content: center;">
            <span style="font-size: 24px;">💧</span>
        </div>
        <div>
            <h2 style="margin: 0; color: #1f2937;">Water Tracking</h2>
            <p style="margin: 0; color: #6b7280; font-size: 0.9rem;">Stay hydrated throughout the day</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.metrics_calculated:
        st.info("Please calculate your needs in the sidebar to see water tracking.")
        return

    # Daily target in glasses (assuming 250ml per glass)
    glasses_target = int(st.session_state.water_intake / 250)
    
    # Display target card
    st.markdown(f"""
    <div class="metric-card" style="display: inline-flex; align-items: center; gap: 16px; padding: 20px 28px;">
        <div style="text-align: center;">
            <div class="metric-card-value" style="color: #3b82f6;">{glasses_target}</div>
            <div class="metric-card-label">Glasses/Day</div>
        </div>
        <div style="width: 1px; height: 40px; background: #e5e7eb;"></div>
        <div style="text-align: center;">
            <div class="metric-card-value" style="font-size: 1.5rem; color: #06b6d4;">{st.session_state.water_intake:.0f}</div>
            <div class="metric-card-label">ml/Day</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Initialize water log if not exists
    if 'water_log' not in st.session_state:
        st.session_state.water_log = {}

    col1, col2 = st.columns([1, 2])

    with col1:
        # Log intake card
        st.markdown("""
        <div class="card-container">
            <h4 style="margin-top: 0; color: #1f2937;">Log Water Intake</h4>
        </div>
        """, unsafe_allow_html=True)

        # Quick add buttons with modern styling
        st.markdown("**Quick Add:**")
        glass_sizes = [1, 2, 3]  # glasses
        cols = st.columns(3)
        for i, size in enumerate(glass_sizes):
            with cols[i]:
                # Custom styled buttons using HTML
                if st.button(f"+{size}", key=f"water_{size}", 
                            help=f"Add {size} glass{'es' if size > 1 else ''} (250ml each)"):
                    add_water_intake(size * 250)  # 250ml per glass

        st.markdown("<div style='margin: 16px 0;'></div>", unsafe_allow_html=True)
        
        # Custom amount
        custom_amount = st.number_input(
            "Custom Amount (ml)", 
            min_value=50, 
            max_value=1000, 
            value=250, 
            step=50,
            help="Enter a custom amount of water to log"
        )
        if st.button("Add Custom Amount", use_container_width=True):
            add_water_intake(custom_amount)

    with col2:
        # Today's progress card
        st.markdown("""
        <div class="card-container">
            <h4 style="margin-top: 0; color: #1f2937;">Today's Progress</h4>
        </div>
        """, unsafe_allow_html=True)
        
        today = datetime.now().date()
        today_str = today.strftime('%Y-%m-%d')

        if today_str in st.session_state.water_log:
            total_ml = sum(entry['amount'] for entry in st.session_state.water_log[today_str])
            glasses_consumed = int(total_ml / 250)
            progress = min(total_ml / st.session_state.water_intake, 1.0)

            # Enhanced progress ring with modern colors
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=glasses_consumed,
                delta={'reference': glasses_target, 'increasing': {'color': '#10b981'}},
                title={'text': f"Glasses Today", 'font': {'size': 16, 'color': '#374151'}},
                number={'font': {'size': 40, 'color': '#1f2937'}},
                gauge={
                    'axis': {'range': [0, glasses_target], 'tickwidth': 0},
                    'bar': {'color': "#3b82f6"},
                    'bgcolor': "#eff6ff",
                    'borderwidth': 2,
                    'bordercolor': "#bfdbfe",
                    'steps': [
                        {'range': [0, glasses_target * 0.3], 'color': '#fee2e2'},
                        {'range': [glasses_target * 0.3, glasses_target * 0.6], 'color': '#fef3c7'},
                        {'range': [glasses_target * 0.6, glasses_target], 'color': '#d1fae5'}
                    ],
                    'threshold': {
                        'line': {'color': "#10b981", 'width': 4},
                        'thickness': 0.75,
                        'value': glasses_target
                    }
                }
            ))
            fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig, use_container_width=True)

            # Progress metrics
            metric_cols = st.columns(3)
            with metric_cols[0]:
                st.markdown(f"""
                <div class="stat-item">
                    <div class="stat-value" style="color: #3b82f6;">{glasses_consumed}</div>
                    <div class="stat-label">Glasses</div>
                </div>
                """, unsafe_allow_html=True)
            with metric_cols[1]:
                st.markdown(f"""
                <div class="stat-item">
                    <div class="stat-value" style="color: #06b6d4;">{total_ml:.0f}</div>
                    <div class="stat-label">ml Consumed</div>
                </div>
                """, unsafe_allow_html=True)
            with metric_cols[2]:
                st.markdown(f"""
                <div class="stat-item">
                    <div class="stat-value" style="color: {'#10b981' if progress >= 0.8 else '#f59e0b'};">{progress*100:.0f}%</div>
                    <div class="stat-label">Of Target</div>
                </div>
                """, unsafe_allow_html=True)

            # Progress bar
            st.progress(progress)
            
            # Status message
            if progress >= 1.0:
                st.success("🎉 Congratulations! You've reached your daily water goal!")
            elif progress >= 0.8:
                st.info(f"💧 Almost there! {glasses_target - glasses_consumed} more glasses to go.")
            elif progress >= 0.5:
                st.info(f"💧 Good progress! Keep drinking water.")
            else:
                st.warning(f"💧 You're behind on your water intake. Drink up!")

            # Today's log with modern styling
            st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
            st.markdown("**Today's Log:**")
            
            log_entries = st.session_state.water_log[today_str]
            for i, entry in enumerate(log_entries[-6:]):  # Show last 6 entries
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 12px; 
                            padding: 8px 12px; margin: 4px 0; 
                            background: #f9fafb; border-radius: 8px;
                            border-left: 3px solid #3b82f6;">
                    <span style="color: #6b7280; font-size: 0.9rem;">🕒 {entry['time']}</span>
                    <span style="color: #1f2937; font-weight: 500;">{entry['amount']} ml</span>
                </div>
                """, unsafe_allow_html=True)
            
            if len(log_entries) > 6:
                st.caption(f"... and {len(log_entries) - 6} more entries")
        else:
            # Empty state
            st.markdown("""
            <div style="text-align: center; padding: 40px 20px; color: #6b7280;">
                <div style="font-size: 48px; margin-bottom: 16px;">💧</div>
                <p style="font-size: 1.1rem; margin-bottom: 8px;">No water logged today yet</p>
                <p style="font-size: 0.9rem;">Start tracking your hydration by adding water intake</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Empty state gauge
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=0,
                title={'text': f"Glasses Today (0/{glasses_target})"},
                gauge={
                    'axis': {'range': [0, glasses_target]},
                    'bar': {'color': "#d1d5db"},
                    'bgcolor': "#f9fafb",
                    'steps': [{'range': [0, glasses_target], 'color': "#e5e7eb"}]
                }
            ))
            fig.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)

    # Analytics section
    if st.session_state.water_log:
        st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div class="card-container">
            <h4 style="margin-top: 0; color: #1f2937;">📊 Hydration Analytics</h4>
        </div>
        """, unsafe_allow_html=True)

        # Prepare data
        data = []
        for date, entries in st.session_state.water_log.items():
            total = sum(entry['amount'] for entry in entries)
            data.append({'date': date, 'total_ml': total, 'glasses': int(total / 250)})

        if data:
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')

            # Create styled charts
            chart_cols = st.columns(3)
            
            # Daily bar chart with modern styling
            with chart_cols[0]:
                fig_daily = px.bar(
                    df.tail(14), 
                    x='date', 
                    y='glasses', 
                    title="Daily Intake (14 Days)",
                    color=['#3b82f6' if g >= glasses_target else '#f59e0b' for g in df.tail(14)['glasses']],
                    labels={'glasses': 'Glasses', 'date': 'Date'}
                )
                fig_daily.update_layout(
                    showlegend=False,
                    height=250,
                    margin=dict(l=40, r=20, t=40, b=40),
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    yaxis=dict(showgrid=True, gridcolor='#f3f4f6')
                )
                st.plotly_chart(fig_daily, use_container_width=True)

            # Weekly summary
            with chart_cols[1]:
                df['week'] = df['date'].dt.to_period('W').astype(str)
                weekly = df.groupby('week')['glasses'].sum().reset_index()
                fig_weekly = px.bar(
                    weekly.tail(8),
                    x='week', 
                    y='glasses', 
                    title="Weekly Total",
                    color='glasses',
                    color_continuous_scale='Blues',
                    labels={'glasses': 'Total Glasses', 'week': 'Week'}
                )
                fig_weekly.update_layout(
                    showlegend=False,
                    height=250,
                    margin=dict(l=40, r=20, t=40, b=40),
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    yaxis=dict(showgrid=True, gridcolor='#f3f4f6')
                )
                st.plotly_chart(fig_weekly, use_container_width=True)

            # Monthly summary
            with chart_cols[2]:
                df['month'] = df['date'].dt.to_period('M').astype(str)
                monthly = df.groupby('month')['glasses'].sum().reset_index()
                fig_monthly = px.bar(
                    monthly.tail(6),
                    x='month', 
                    y='glasses', 
                    title="Monthly Total",
                    color='glasses',
                    color_continuous_scale='Teal',
                    labels={'glasses': 'Total Glasses', 'month': 'Month'}
                )
                fig_monthly.update_layout(
                    showlegend=False,
                    height=250,
                    margin=dict(l=40, r=20, t=40, b=40),
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    yaxis=dict(showgrid=True, gridcolor='#f3f4f6')
                )
                st.plotly_chart(fig_monthly, use_container_width=True)

def add_water_intake(amount):
    now = datetime.now()
    today = now.date().strftime('%Y-%m-%d')
    if today not in st.session_state.water_log:
        st.session_state.water_log[today] = []
    st.session_state.water_log[today].append({
        'time': now.strftime('%H:%M'),
        'amount': amount
    })
    insert_row("water_logs", {
        "user_id": st.session_state.get("user_id"),
        "logged_at": now.isoformat(),
        "amount_ml": amount,
    })
    st.success(f"Added {amount} ml of water!")
    st.rerun()
