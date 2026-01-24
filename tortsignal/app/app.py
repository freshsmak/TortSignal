"""
TortSignal Dashboard - The Bloomberg Terminal for Mass Torts

Main entry point for the Streamlit application.
"""

import streamlit as st

# Must be first Streamlit command
st.set_page_config(
    page_title="TortSignal",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Import pages
from pages import watchlist, dossier

# Custom CSS for terminal aesthetic
st.markdown("""
<style>
    /* Terminal-inspired color scheme */
    :root {
        --navy: #1e3a5f;
        --charcoal: #2d3748;
        --alert-red: #e53e3e;
        --warning: #ed8936;
        --caution: #ecc94b;
        --quiet: #718096;
    }

    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, var(--navy) 0%, var(--charcoal) 100%);
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 2rem;
    }

    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2rem;
        font-weight: 600;
    }

    .main-header p {
        color: #a0aec0;
        margin: 0.5rem 0 0 0;
        font-size: 0.95rem;
    }

    /* Stage badges */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .badge-high {
        background: var(--alert-red);
        color: white;
    }

    .badge-investigate {
        background: var(--warning);
        color: white;
    }

    .badge-awareness {
        background: var(--caution);
        color: #2d3748;
    }

    .badge-quiet {
        background: var(--quiet);
        color: white;
    }

    /* Score display */
    .score-large {
        font-size: 2.5rem;
        font-weight: 700;
        line-height: 1;
    }

    .score-high {
        color: var(--alert-red);
    }

    .score-med {
        color: var(--warning);
    }

    .score-low {
        color: var(--quiet);
    }

    /* Metric cards */
    .metric-card {
        background: #f7fafc;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid var(--navy);
    }

    .metric-card h4 {
        margin: 0 0 0.5rem 0;
        color: var(--charcoal);
        font-size: 0.875rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .metric-card p {
        margin: 0;
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--navy);
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Sidebar styling */
    .css-1d391kg {
        background: var(--charcoal);
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Main application entry point."""

    # Initialize session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'watchlist'

    if 'selected_candidate_id' not in st.session_state:
        st.session_state.selected_candidate_id = None

    # Sidebar navigation
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; padding: 1rem 0;'>
            <h1 style='margin: 0; color: white; font-size: 1.5rem;'>⚖️ TortSignal</h1>
            <p style='margin: 0.5rem 0 0 0; color: #a0aec0; font-size: 0.8rem;'>
                The Bloomberg Terminal for Mass Torts
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Navigation - sync radio with session state
        page_options = ["Watchlist", "Dossier"]
        page_map = {"Watchlist": 'watchlist', "Dossier": 'dossier'}
        reverse_map = {'watchlist': "Watchlist", 'dossier': "Dossier"}

        # Determine current index based on session state
        current_selection = reverse_map.get(st.session_state.current_page, "Watchlist")
        current_index = page_options.index(current_selection)

        def on_nav_change():
            """Callback when navigation changes."""
            selected = st.session_state.nav_radio
            st.session_state.current_page = page_map[selected]

        page = st.radio(
            "Navigation",
            page_options,
            index=current_index,
            key="nav_radio",
            on_change=on_nav_change
        )

        st.markdown("---")

        # Quick stats
        st.markdown("### Quick Stats")
        try:
            from db_helpers import get_quick_stats
            stats = get_quick_stats()
            st.metric("Active Candidates", stats.get('total', 0))
            st.metric("High Conviction", stats.get('high_conviction', 0))
            st.metric("New (7d)", stats.get('new_7d', 0))
        except Exception as e:
            st.info("Database not connected")

        st.markdown("---")

        # Settings
        with st.expander("⚙️ Settings"):
            st.checkbox("Auto-refresh (5min)", value=False)
            st.selectbox("Display density", ["Comfortable", "Compact"])
            if st.button("Clear Cache"):
                st.cache_data.clear()
                st.success("Cache cleared!")

    # Main content area
    if st.session_state.current_page == 'watchlist':
        watchlist.show()
    elif st.session_state.current_page == 'dossier':
        dossier.show()


if __name__ == "__main__":
    main()
