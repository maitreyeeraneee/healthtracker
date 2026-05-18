import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar


def streaks_tab():
    st.header("Streaks & Meal Logging")

    if not st.session_state.daily_log:
        st.info("Start logging meals to build your streaks!")
        return

    # Calculate streaks
    current_streak, longest_streak, streak_data = calculate_streaks()

    # Display streak metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Streak", f"{current_streak} days")
    with col2:
        st.metric("Longest Streak", f"{longest_streak} days")
    with col3:
        total_logged_days = sum(1 for v in streak_data.values() if v)
        st.metric("Total Logged Days", total_logged_days)

    # Streak heatmap
    st.subheader("Meal Logging Activity ")
    heatmap_fig = create_streak_heatmap(streak_data)
    if heatmap_fig:
        st.plotly_chart(heatmap_fig, use_container_width=True)
    else:
        st.info("Not enough data to render the heatmap. Keep logging meals!")

    # Streak history - last 30 days with improved layout
    st.subheader("Recent Activity (Last 30 Days)")
    if streak_data:
        # Sort by date descending
        sorted_dates = sorted(streak_data.items(), key=lambda x: x[0], reverse=True)
        recent = sorted_dates[:30]

        # Display as a clean table with columns
        cols = st.columns(5)
        for idx, (date_str, logged) in enumerate(recent):
            col_idx = idx % 5
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            day_name = date_obj.strftime('%a')
            display = date_obj.strftime('%b %d')
            status = "✅" if logged else "⬜"
            with cols[col_idx]:
                st.markdown(
                    f"<div style='padding:4px;margin:2px;border-radius:4px;font-size:0.85em;"
                    f"background-color:{'#d4edda' if logged else '#f8f9fa'};"
                    f"border:1px solid {'#c3e6cb' if logged else '#dee2e6'};'>"
                    f"<span style='font-weight:600;'>{day_name}</span> {display}<br>"
                    f"<span style='font-size:1.2em;'>{status}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        # Summary stats
        st.markdown("---")
        streak_summary_col1, streak_summary_col2, streak_summary_col3 = st.columns(3)
        with streak_summary_col1:
            logged_30 = sum(1 for d, v in sorted_dates[:30] if v)
            st.metric("Logged in Last 30 Days", f"{logged_30}/30", f"{logged_30/30*100:.0f}%")
        with streak_summary_col2:
            missed_30 = 30 - logged_30
            st.metric("Missed Days", f"{missed_30}")
        with streak_summary_col3:
            st.metric("Logging Rate", f"{logged_30/30*100:.0f}%" if logged_30 > 0 else "0%")


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