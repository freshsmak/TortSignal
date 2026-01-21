"""
Watchlist Page - Ranked list of emerging tort candidates
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from components.stage_badge import render_stage_badge
from components.score_display import render_score


def show():
    """Render the Watchlist page."""

    # Header
    st.markdown("""
    <div class='main-header'>
        <h1>Watchlist</h1>
        <p>Ranked emerging mass tort candidates</p>
    </div>
    """, unsafe_allow_html=True)

    # Last updated timestamp
    col1, col2 = st.columns([3, 1])
    with col2:
        st.caption(f"Last updated: {datetime.now().strftime('%I:%M %p')}")

    # Filters section
    st.markdown("### Filters")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        category_filter = st.multiselect(
            "Category",
            ["Pharma", "Device", "Chemical", "Gov Contractor", "Consumer"],
            default=[]
        )

    with col2:
        stage_filter = st.multiselect(
            "Stage",
            ["High Conviction", "Investigate", "Awareness", "Quiet"],
            default=[]
        )

    with col3:
        date_range = st.selectbox(
            "Date Range",
            ["Last 7 days", "Last 30 days", "Last 90 days", "All time"],
            index=1
        )

    with col4:
        min_score = st.slider(
            "Min Score",
            min_value=0,
            max_value=100,
            value=0,
            step=5
        )

    # Sort options
    col1, col2 = st.columns([1, 3])
    with col1:
        sort_by = st.selectbox(
            "Sort by",
            ["Score (High→Low)", "Score (Low→High)", "Recency", "Velocity", "Breadth"],
            index=0
        )

    st.markdown("---")

    # Load data
    try:
        from db_helpers import get_watchlist

        # Apply filters
        filters = {
            'categories': [c.lower() for c in category_filter] if category_filter else None,
            'stages': [s.upper().replace(' ', '_') for s in stage_filter] if stage_filter else None,
            'min_score': min_score,
            'days': parse_date_range(date_range),
        }

        df = get_watchlist(filters)

        # Apply sorting
        df = apply_sorting(df, sort_by)

        # Display count
        st.markdown(f"**{len(df)} candidates** matching filters")

        if len(df) == 0:
            st.info("No candidates match the selected filters. Try adjusting your criteria.")
            return

        # Render table
        render_watchlist_table(df)

        # Bulk actions
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            if st.button("📥 Export CSV"):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download",
                    data=csv,
                    file_name=f"tortsignal_watchlist_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        with col2:
            if st.button("🔄 Refresh Data"):
                st.cache_data.clear()
                st.rerun()

    except Exception as e:
        st.error(f"Error loading watchlist: {str(e)}")
        st.info("Make sure the database is configured and accessible.")

        # Show sample data for demo
        st.markdown("### Sample Data (Demo)")
        df = get_sample_data()
        render_watchlist_table(df)


def render_watchlist_table(df: pd.DataFrame):
    """Render the main watchlist table."""

    # Format the dataframe for display
    for idx, row in df.iterrows():
        col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 2, 2, 1, 1.5, 1, 1])

        with col1:
            st.markdown(f"**{row['defendant_text']}**")

        with col2:
            st.markdown(f"{row['product_text']}")

        with col3:
            injury = row['injury_text']
            if len(injury) > 25:
                injury = injury[:25] + "..."
            st.markdown(f"_{injury}_")

        with col4:
            st.markdown(render_score(row['score_total']), unsafe_allow_html=True)

        with col5:
            st.markdown(render_stage_badge(row['stage']), unsafe_allow_html=True)

        with col6:
            updated = row.get('last_updated', '')
            if isinstance(updated, str):
                st.caption(updated)
            else:
                st.caption(updated.strftime('%m/%d/%y') if pd.notna(updated) else 'N/A')

        with col7:
            if st.button("View", key=f"view_{idx}"):
                st.session_state.selected_candidate_id = row['cluster_id']
                st.session_state.current_page = 'dossier'
                st.rerun()

        st.markdown("---")


def parse_date_range(date_range: str) -> int:
    """Convert date range string to number of days."""
    mapping = {
        "Last 7 days": 7,
        "Last 30 days": 30,
        "Last 90 days": 90,
        "All time": 9999
    }
    return mapping.get(date_range, 30)


def apply_sorting(df: pd.DataFrame, sort_by: str) -> pd.DataFrame:
    """Apply sorting to the dataframe."""
    if sort_by == "Score (High→Low)":
        return df.sort_values('score_total', ascending=False)
    elif sort_by == "Score (Low→High)":
        return df.sort_values('score_total', ascending=True)
    elif sort_by == "Recency":
        return df.sort_values('last_updated', ascending=False)
    elif sort_by == "Velocity":
        if 'velocity_7d' in df.columns:
            return df.sort_values('velocity_7d', ascending=False)
        return df
    elif sort_by == "Breadth":
        if 'breadth_states' in df.columns:
            return df.sort_values('breadth_states', ascending=False)
        return df
    return df


def get_sample_data() -> pd.DataFrame:
    """Return sample data for demo purposes."""
    return pd.DataFrame([
        {
            'cluster_id': '1',
            'defendant_text': 'Bayer AG',
            'product_text': 'Roundup',
            'injury_text': 'Non-Hodgkin Lymphoma',
            'score_total': 92,
            'stage': 'HIGH_CONVICTION',
            'category': 'chemical',
            'last_updated': '2h ago',
            'velocity_7d': 47,
            'breadth_states': 12
        },
        {
            'cluster_id': '2',
            'defendant_text': 'Johnson & Johnson',
            'product_text': 'Talcum Powder',
            'injury_text': 'Ovarian Cancer',
            'score_total': 78,
            'stage': 'HIGH_CONVICTION',
            'category': 'consumer',
            'last_updated': '1d ago',
            'velocity_7d': 32,
            'breadth_states': 9
        },
        {
            'cluster_id': '3',
            'defendant_text': 'Novo Nordisk',
            'product_text': 'Ozempic',
            'injury_text': 'Gastroparesis',
            'score_total': 64,
            'stage': 'INVESTIGATE',
            'category': 'pharma',
            'last_updated': '3h ago',
            'velocity_7d': 28,
            'breadth_states': 7
        },
        {
            'cluster_id': '4',
            'defendant_text': '3M Company',
            'product_text': 'AFFF Foam',
            'injury_text': 'Various Cancers',
            'score_total': 56,
            'stage': 'INVESTIGATE',
            'category': 'chemical',
            'last_updated': '5h ago',
            'velocity_7d': 18,
            'breadth_states': 11
        },
        {
            'cluster_id': '5',
            'defendant_text': 'Philips',
            'product_text': 'CPAP Machines',
            'injury_text': 'Respiratory Issues',
            'score_total': 42,
            'stage': 'INVESTIGATE',
            'category': 'device',
            'last_updated': '12h ago',
            'velocity_7d': 14,
            'breadth_states': 6
        },
    ])
