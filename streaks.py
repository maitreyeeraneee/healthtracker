import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar


def streaks_tab():
    # Modern header with icon
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 24px;">
        <div style="background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%); 
                    width: 48px; height: 48px; border-radius: 12px; 
                    display: flex; align-items: center; justify-content: center;">
            <span style="font-size: 24px;">🔥</span>
        </div>
        <div>
            <h2 style="margin: 0; color: #1f2937;">Streaks & Consistency</h2>
            <p style="margin: 0; color: #6b7280; font-size: 0.9rem;">Track your meal logging consistency</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.daily_log:
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px; color: #6b7280;">
            <div style="font-size: 64px; margin-bottom: 16px;">🔥</div>
            <p style="font-size: 1.2rem; margin-bottom: 8px;">Start logging meals to build your streaks!</p>
            <p style="font-size: 0.95rem;">Consistency is key to achieving your health goals.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Calculate streaks
    current_streak, longest_streak, streak_data = calculate_streaks()

    # Display streak metrics with modern cards
    st.markdown("""
    <div class="card-container">
        <h4 style="margin-top: 0; color: #1f2937;">Your Streak Stats</h4>
    </div>
    """, unsafe_allow_html=True)
    
    metric_cols = st.columns(3)
    with metric_cols[0]:
        color = '#10b981' if current_streak >= 7 else '#f59e0b' if current_streak >= 3 else '#6b7280'
        st.markdown(f"""
        <div class="stat-item" style="border-top: 3px solid {color};">
            <div style="font-size: 48px; margin-bottom: 8px;">🔥</div>
            <div class="stat-value" style="color: {color};">{current_streak}</div>
            <div class="stat-label">Current Streak</div>
        </div>
        """, unsafe_allow_html=True)
    with metric_cols[1]:
        st.markdown(f"""
        <div class="stat-item" style="border-top: 3px solid #3b82f6;">
            <div style="font-size: 48px; margin-bottom: 8px;">🏆</div>
            <div class="stat-value" style="color: #3b82f6;">{longest_streak}</div>
            <div class="stat-label">Longest Streak</div>
        </div>
        """, unsafe_allow_html=True)
    with metric_cols[2]:
        total_logged_days = sum(1 for v in streak_data.values() if v)
        st.markdown(f"""
        <div class="stat-item" style="border-top: 3px solid #8b5cf6;">
            <div style="font-size: 48px; margin-bottom: 8px;">📝</div>
            <div class="stat-value" style="color: #8b5cf6;">{total_logged_days}</div>
            <div class="stat-label">Total Logged Days</div>
        </div>
        """, unsafe_allow_html=True)

    # Streak heatmap
    st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div class="card-container">
        <h4 style="margin-top: 0; color: #1f2937;">📊 Meal Logging Activity</h4>
    </div>
    """, unsafe_allow_html=True)
    
    heatmap_fig = create_streak_heatmap(streak_data)
    if heatmap_fig:
        st.plotly_chart(heatmap_fig, use_container_width=True)
    else:
        st.info("Not enough data to render the heatmap. Keep logging meals!")

    # Streak history - last 30 days with improved layout
    st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div class="card-container">
        <h4 style="margin-top: 0; color: #1f2937;">📅 Recent Activity (Last 30 Days)</h4>
    </div>
    """, unsafe_allow_html=True)
    
    if streak_data:
        # Sort by date descending
        sorted_dates = sorted(streak_data.items(), key=lambda x: x[0], reverse=True)
        recent = sorted_dates[:30]

        # Display as a clean grid with modern styling
        st.markdown("<div style='margin: 16px 0;'></div>", unsafe_allow_html=True)
        cols = st.columns(6)
        for idx, (date_str, logged) in enumerate(recent):
            col_idx = idx % 6
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            day_name = date_obj.strftime('%a')
            display = date_obj.strftime('%b %d')
            
            if logged:
                status_icon = "✅"
                bg_color = "#f0fdf4"
                border_color = "#10b981"
                text_color = "#10b981"
            else:
                status_icon = "⬜"
                bg_color = "#f9fafb"
                border_color = "#e5e7eb"
                text_color = "#9ca3af"
            
            with cols[col_idx]:
                st.markdown(f"""
                <div style="text-align: center; padding: 12px 8px; margin: 4px 0; 
                            background-color: {bg_color}; border-radius: 10px;
                            border: 2px solid {border_color}; transition: all 0.2s ease;">
                    <div style="font-size: 0.75rem; color: {text_color}; font-weight: 500;">{day_name}</div>
                    <div style="font-size: 0.85rem; color: #1f2937; font-weight: 600; margin: 4px 0;">{display}</div>
                    <div style="font-size: 1.5rem;">{status_icon}</div>
                </div>
                """, unsafe_allow_html=True)

        # Summary stats with modern cards
        st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
        streak_summary_col1, streak_summary_col2, streak_summary_col3 = st.columns(3)
        with streak_summary_col1:
            logged_30 = sum(1 for d, v in sorted_dates[:30] if v)
            rate = f"{logged_30/30*100:.0f}%"
            st.markdown(f"""
            <div class="stat-item" style="border-top: 3px solid #10b981;">
                <div class="stat-value" style="color: #10b981;">{logged_30}/30</div>
                <div class="stat-label">Days Logged</div>
                <div style="font-size: 0.8rem; color: #6b7280; margin-top: 4px;">{rate} success rate</div>
            </div>
            """, unsafe_allow_html=True)
        with streak_summary_col2:
            missed_30 = 30 - logged_30
            st.markdown(f"""
            <div class="stat-item" style="border-top: 3px solid #f59e0b;">
                <div class="stat-value" style="color: #f59e0b;">{missed_30}</div>
                <div class="stat-label">Days Missed</div>
                <div style="font-size: 0.8rem; color: #6b7280; margin-top: 4px;">Keep going!</div>
            </div>
            """, unsafe_allow_html=True)
        with streak_summary_col3:
            consistency_rate = f"{logged_30/30*100:.0f}%" if logged_30 > 0 else "0%"
            st.markdown(f"""
            <div class="stat-item" style="border-top: 3px solid #3b82f6;">
                <div class="stat-value" style="color: #3b82f6;">{consistency_rate}</div>
                <div class="stat-label">Consistency</div>
                <div style="font-size: 0.8rem; color: #6b7280; margin-top: 4px;">30-day average</div>
            </div>
            """, unsafe_allow_html=True)


def calculate_streaks():
    if not st.session_state.daily_log:
        return 0, 0, {}

    # Get all dates with logging
    logged_dates = set()
    for date_str, meals in st.session_state.daily_log.items():
        if meals:  # Has meals logged
            logged_dates.add(date_str)

    # Create date range from first log to today
    if not logged_dates:
        return 0, 0, {}

    start_date = min(logged_dates)
    end_date = datetime.now().date()

    # Build streak data
    streak_data = {}
    current_date = datetime.strptime(start_date, '%Y-%m-%d').date()

    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        streak_data[date_str] = date_str in logged_dates
        current_date += timedelta(days=1)

    # Calculate current streak
    current_streak = 0
    check_date = end_date
    while check_date >= datetime.strptime(start_date, '%Y-%m-%d').date():
        date_str = check_date.strftime('%Y-%m-%d')
        if date_str in streak_data and streak_data[date_str]:
            current_streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    # Calculate longest streak
    longest_streak = 0
    temp_streak = 0
    for date_str in sorted(streak_data.keys()):
        if streak_data[date_str]:
            temp_streak += 1
            longest_streak = max(longest_streak, temp_streak)
        else:
            temp_streak = 0

    return current_streak, longest_streak, streak_data


def create_streak_heatmap(streak_data):
    if not streak_data:
        return None

    # Prepare data for heatmap with proper week/weekday layout
    # GitHub-style: weeks as columns, weekdays as rows
    data = []
    for date_str, logged in streak_data.items():
        date = datetime.strptime(date_str, '%Y-%m-%d')
        iso_year, iso_week, iso_weekday = date.isocalendar()
        # Monday=0, Sunday=6 for display
        weekday_display = date.weekday()  # 0=Monday
        data.append({
            'date': date,
            'year': date.year,
            'month': date.month,
            'day': date.day,
            'week_num': iso_week,
            'weekday': weekday_display,
            'logged': 1 if logged else 0,
            'label': date.strftime('%b %d, %Y')
        })

    df = pd.DataFrame(data)

    if df.empty:
        return None

    # Determine date range for nice display
    min_date = df['date'].min()
    max_date = df['date'].max()

    # Create pivot table: week as index, weekday as columns
    # Normalize week numbers to make them sequential for proper display
    df['week_label'] = df['week_num'].astype(str) + '-' + df['year'].astype(str)

    # For better display, create a numeric week index from the min week
    all_weeks = sorted(df['week_label'].unique())
    week_to_idx = {w: i for i, w in enumerate(all_weeks)}
    df['week_idx'] = df['week_label'].map(week_to_idx)

    # Pivot: weekday rows, week columns
    pivot = df.pivot_table(
        values='logged',
        index='weekday',
        columns='week_idx',
        aggfunc='max',
        fill_value=0
    )

    # Ensure all 7 weekdays are represented
    for wd in range(7):
        if wd not in pivot.index:
            pivot.loc[wd] = 0
    pivot = pivot.sort_index()

    # Weekday labels (Monday = 0)
    weekday_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    # Create heatmap with GitHub-like colors
    fig = go.Figure()

    fig.add_trace(go.Heatmap(
        z=pivot.values,
        x=list(range(len(pivot.columns))),
        y=weekday_labels,
        colorscale=[
            [0, '#ebedf0'],      # No activity (light gray)
            [0.25, '#9be9a8'],   # Low activity (light green)
            [0.5, '#40c463'],    # Medium activity (mid green)
            [0.75, '#30a14e'],   # High activity (dark green)
            [1, '#216e39'],      # Very high activity (deep green)
        ],
        showscale=True,
        hoverongaps=False,
        text=[[f"{date.strftime('%b %d, %Y')} - {'✅ Logged' if v else '❌ Missed'}"
               if not isinstance(v, (int, float)) else f"{'✅ Logged' if v else '❌ Missed'}"
               for v in row] for row in pivot.values],
        hoverinfo='text',
        zmin=0,
        zmax=1,
        xgap=3,
        ygap=3,
    ))

    # Number of weeks for adaptive height
    num_weeks = len(pivot.columns)

    fig.update_layout(
        title=dict(
            text=f"<b>Meal Logging Activity</b><br><span style='font-size:12px;color:gray;'>"
                 f"{min_date.strftime('%b %d, %Y')} - {max_date.strftime('%b %d, %Y')}</span>",
            font=dict(size=16),
        ),
        xaxis=dict(
            title="Week",
            showgrid=False,
            tickmode='array',
            tickvals=list(range(len(all_weeks))),
            ticktext=[f"W{w.split('-')[0]}" for w in all_weeks],
            tickfont=dict(size=9),
        ),
        yaxis=dict(
            title="Day",
            showgrid=False,
            tickfont=dict(size=11),
        ),
        height=max(180, 40 + len(weekday_labels) * 25),
        margin=dict(l=40, r=20, t=60, b=30),
        plot_bgcolor='white',
        paper_bgcolor='white',
    )

    return fig