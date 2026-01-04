"""
DMO Web UI - Streamlit Application

A simple web interface for tracking Daily Methods of Operation.
"""

from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

from dmo_web import api_client

# Page configuration
st.set_page_config(
    page_title="DMO Tracker",
    page_icon="✓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .dmo-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f0f2f6;
        margin-bottom: 1rem;
    }
    .activity-item {
        margin-left: 2rem;
        color: #666;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =============================================================================
# Sidebar Navigation
# =============================================================================

st.sidebar.title("DMO Tracker")
page = st.sidebar.radio(
    "Navigation",
    ["📅 Today", "📋 Manage DMOs", "📊 Reports"],
    label_visibility="collapsed",
)

st.sidebar.markdown("---")
st.sidebar.caption("Daily Methods of Operation")


# =============================================================================
# Page: Today's Dashboard
# =============================================================================

def show_today_page() -> None:
    """Display today's dashboard with completion toggles."""
    st.markdown('<div class="main-header">📅 Today\'s DMOs</div>', unsafe_allow_html=True)
    st.markdown(f"**{date.today().strftime('%A, %B %d, %Y')}**")
    st.markdown("---")

    try:
        # Fetch today's report
        today = date.today()
        month_report = api_client.get_monthly_report(year=today.year, month=today.month)
        report = api_client.get_today_report()
        dmos_status = report.get("dmos", [])

        if not dmos_status:
            st.info("No active DMOs found. Create one in the 'Manage DMOs' page!")
            return

        # Display each DMO with completion toggle
        for dmo_status in dmos_status:
            dmo = dmo_status["dmo"]
            completed = dmo_status["completed"]
            activities = dmo_status.get("activities", [])
            note = dmo_status.get("note")

            # Create a card for each DMO
            with st.container():
                col1, col2 = st.columns([1, 4])

                with col1:
                    # Completion checkbox
                    new_completed = st.checkbox(
                        "Done",
                        value=completed,
                        key=f"checkbox_{dmo['id']}",
                    )

                    # If checkbox changed, update completion
                    if new_completed != completed:
                        try:
                            if new_completed:
                                api_client.mark_complete(dmo["id"], date.today())
                                st.success(f"✓ Marked '{dmo['name']}' as complete!")
                            else:
                                api_client.mark_incomplete(dmo["id"], date.today())
                                st.info(f"Marked '{dmo['name']}' as incomplete")
                            st.rerun()
                        except api_client.APIError as e:
                            st.error(f"Error updating completion: {e.message}")

                with col2:
                    # DMO name and activities
                    status_icon = "✅" if completed else "⬜"
                    st.markdown(f"### {status_icon} {dmo['name']}")

                    if dmo.get("description"):
                        st.caption(dmo["description"])

                    if activities:
                        with st.expander("Activities", expanded=False):
                            for activity in activities:
                                st.markdown(f"- {activity}")

                    if note:
                        st.markdown(f"*Note: {note}*")

                dmo_report = [d for d in month_report if d["dmo"]["id"] == dmo["id"]][0]
                # Normalize days
                days_report = [d["completed"] for d in dmo_report["days"]]
                print(days_report)
                cols = st.columns([1] * len(dmo_report["days"]))
                for i, col in enumerate(cols):
                    with col:
                        rep = dmo_report["days"][i]
                        status_icon = "✅" if rep["completed"] else (
                            "⬜" if i >= today.day else "❌"
                        )
                        st.markdown(status_icon)

                st.markdown("---")

    except api_client.APIError as e:
        st.error(f"Failed to load today's DMOs: {e.message}")
        st.info("Make sure the API server is running at http://localhost:8000")


# =============================================================================
# Page: Manage DMOs
# =============================================================================

def show_manage_page() -> None:
    """Display DMO management page."""
    st.markdown('<div class="main-header">📋 Manage DMOs</div>', unsafe_allow_html=True)

    # Create two tabs: List and Create
    tab1, tab2 = st.tabs(["📃 All DMOs", "➕ Create New"])

    with tab1:
        show_dmo_list()

    with tab2:
        show_create_dmo_form()


def show_dmo_list() -> None:
    """Display list of all DMOs with edit/delete options."""
    try:
        include_inactive = st.checkbox("Show inactive DMOs", value=False)
        dmos = api_client.list_dmos(include_inactive=include_inactive)

        if not dmos:
            st.info("No DMOs found. Create your first one in the 'Create New' tab!")
            return

        for dmo in dmos:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])

                with col1:
                    status = "🟢 Active" if dmo["active"] else "🔴 Inactive"
                    st.markdown(f"**{dmo['name']}** - {status}")
                    if dmo.get("description"):
                        st.caption(dmo["description"])

                with col2:
                    # Show activities count
                    try:
                        activities = api_client.list_activities(dmo["id"])
                        st.caption(f"📝 {len(activities)} activities")
                    except api_client.APIError:
                        pass

                with col3:
                    # Toggle active status
                    if dmo["active"]:
                        if st.button("Deactivate", key=f"deact_{dmo['id']}"):
                            try:
                                api_client.deactivate_dmo(dmo["id"])
                                st.success("DMO deactivated")
                                st.rerun()
                            except api_client.APIError as e:
                                st.error(f"Error: {e.message}")
                    else:
                        if st.button("Activate", key=f"act_{dmo['id']}"):
                            try:
                                api_client.activate_dmo(dmo["id"])
                                st.success("DMO activated")
                                st.rerun()
                            except api_client.APIError as e:
                                st.error(f"Error: {e.message}")

                with col4:
                    # Delete button
                    if st.button("🗑️ Delete", key=f"del_{dmo['id']}"):
                        try:
                            api_client.delete_dmo(dmo["id"])
                            st.success(f"Deleted '{dmo['name']}'")
                            st.rerun()
                        except api_client.APIError as e:
                            st.error(f"Error: {e.message}")

                # Show and manage activities
                with st.expander(f"Activities for {dmo['name']}"):
                    show_activities_section(dmo["id"])

                st.markdown("---")

    except api_client.APIError as e:
        st.error(f"Failed to load DMOs: {e.message}")


def show_activities_section(dmo_id: int) -> None:
    """Display and manage activities for a DMO."""
    try:
        activities = api_client.list_activities(dmo_id)

        if activities:
            for activity in activities:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"• {activity['name']}")
                with col2:
                    if st.button("Delete", key=f"del_act_{activity['id']}"):
                        try:
                            api_client.delete_activity(activity["id"])
                            st.success("Activity deleted")
                            st.rerun()
                        except api_client.APIError as e:
                            st.error(f"Error: {e.message}")
        else:
            st.caption("No activities yet")

        # Add new activity
        st.markdown("**Add Activity:**")
        with st.form(key=f"add_activity_{dmo_id}"):
            activity_name = st.text_input("Activity name", key=f"act_name_{dmo_id}")
            submit = st.form_submit_button("Add")

            if submit and activity_name:
                try:
                    api_client.create_activity(dmo_id, activity_name)
                    st.success(f"Added activity: {activity_name}")
                    st.rerun()
                except api_client.APIError as e:
                    st.error(f"Error: {e.message}")

    except api_client.APIError as e:
        st.error(f"Failed to load activities: {e.message}")


def show_create_dmo_form() -> None:
    """Display form to create a new DMO."""
    st.markdown("### Create New DMO")

    with st.form("create_dmo_form"):
        name = st.text_input("Name *", placeholder="e.g., Morning Routine")
        description = st.text_area("Description (optional)", placeholder="What is this DMO about?")

        # Activities
        st.markdown("**Activities (optional):**")
        activities = []
        for i in range(3):
            activity = st.text_input(f"Activity {i+1}", key=f"activity_{i}")
            if activity:
                activities.append(activity)

        submitted = st.form_submit_button("Create DMO")

        if submitted:
            if not name:
                st.error("Name is required!")
            else:
                try:
                    # Create DMO
                    dmo = api_client.create_dmo(name, description or None)
                    st.success(f"✓ Created DMO: {dmo['name']}")

                    # Create activities
                    if activities:
                        for i, activity_name in enumerate(activities):
                            api_client.create_activity(dmo["id"], activity_name, i)
                        st.success(f"✓ Added {len(activities)} activities")

                    st.rerun()

                except api_client.APIError as e:
                    st.error(f"Failed to create DMO: {e.message}")


# =============================================================================
# Page: Reports
# =============================================================================

def show_reports_page() -> None:
    """Display reports and statistics."""
    st.markdown('<div class="main-header">📊 Reports & Statistics</div>', unsafe_allow_html=True)

    # Month selector
    today = date.today()
    years = [y for y in range(2025, 2300)]
    months = [m for m in range(1, 13)]

    # DMO selector
    dmos = api_client.list_dmos(include_inactive=False)

    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        selected_year = st.selectbox(
            "Selected Year",
            options=years,
            index=years.index(today.year)
        )

    with col2:
        selected_month = st.selectbox(
            "Selected Month",
            options=months,
            index=months.index(today.month)
        )

    with col3:
        selected_dmo = st.selectbox(
            "Selected DMO",
            options=[d["name"] for d in dmos]
        )

    try:
        # Get monthly report
        reports = api_client.get_monthly_report(
            year=selected_year,
            month=selected_month,
            dmo_id=[d["id"] for d in dmos if d["name"] == selected_dmo][0]
        )

        if not reports:
            st.info("No active DMOs found for this month.")
            return

        # Display report for each DMO
        for report in reports:
            dmo = report["dmo"]
            summary = report["summary"]
            days = report["days"]

            st.markdown(f"### {dmo['name']}")

            # Summary statistics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Days", summary["total_days"])

            with col2:
                st.metric(
                    "Completed Days",
                    summary["completed_days"],
                    f"{summary['completion_rate'] * 100:.1f}%",
                )

            with col3:
                st.metric("Current Streak", f"{summary['current_streak']} days")

            with col4:
                st.metric("Longest Streak", f"{summary['longest_streak']} days")

            # Completion calendar
            st.markdown("**Completion Calendar:**")

            # Create DataFrame for calendar view
            calendar_data = []
            for day in days:
                calendar_data.append({
                    "Date": day["date"],
                    "Completed": "✅" if day["completed"] else "❌",
                    "Note": day.get("note", ""),
                })

            df = pd.DataFrame(calendar_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Completion trend chart
            st.markdown("**Completion Trend:**")
            completion_values = [1 if day["completed"] else 0 for day in days]
            chart_data = pd.DataFrame({
                "Day": range(1, len(days) + 1),
                "Completed": completion_values,
            })
            st.bar_chart(chart_data.set_index("Day"))

            st.markdown("---")

    except api_client.APIError as e:
        st.error(f"Failed to load reports: {e.message}")


# =============================================================================
# Main App Router
# =============================================================================

def main() -> None:
    """Main application entry point."""
    if page == "📅 Today":
        show_today_page()
    elif page == "📋 Manage DMOs":
        show_manage_page()
    elif page == "📊 Reports":
        show_reports_page()


if __name__ == "__main__":
    main()
