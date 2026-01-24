"""
Dossier Page - Deep dive into a single tort candidate
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from components.stage_badge import render_stage_badge
from components.score_display import render_score


def show():
    """Render the Dossier page."""

    # Check if a candidate is selected
    if not st.session_state.get('selected_candidate_id'):
        st.warning("No candidate selected. Please select a candidate from the Watchlist.")
        if st.button("← Back to Watchlist"):
            st.session_state.current_page = 'watchlist'
            st.rerun()
        return

    # Back button
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("← Back to Watchlist"):
            st.session_state.current_page = 'watchlist'
            st.rerun()

    # Load dossier data
    try:
        from db_helpers import get_dossier

        # Debug: Show what candidate_id we're loading
        print(f"Loading dossier for candidate_id: {st.session_state.selected_candidate_id}")

        dossier_data = get_dossier(st.session_state.selected_candidate_id)

        if not dossier_data:
            st.error("Candidate not found.")
            print(f"Candidate not found: {st.session_state.selected_candidate_id}")
            return

        render_dossier(dossier_data)

    except Exception as e:
        st.error(f"Error loading dossier: {str(e)}")
        print(f"Error loading dossier: {e}")
        import traceback
        traceback.print_exc()
        st.info("Showing sample data for demo purposes")
        dossier_data = get_sample_dossier()
        render_dossier(dossier_data)


def render_dossier(data: dict):
    """Render the full dossier for a candidate."""

    candidate = data['candidate']

    # Header
    st.markdown(f"""
    <div class='main-header'>
        <h1>{candidate['defendant_text']} × {candidate['product_text']} × {candidate['injury_text']}</h1>
        <p>
            Category: <strong>{candidate['category'].title()}</strong> │
            Score: <strong>{candidate['score_total']}</strong> │
            Stage: <strong>{candidate['stage'].replace('_', ' ').title()}</strong>
        </p>
        <p style='font-size: 0.85rem; margin-top: 0.5rem;'>
            First Seen: {candidate['first_seen']} │ Last Updated: {candidate['last_updated']}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Actions
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("✓ Mark Reviewed"):
            st.success("Marked as reviewed")
    with col2:
        if st.button("✗ Reject (False Positive)"):
            st.warning("Marked as rejected")
    with col3:
        if st.button("📁 Export to PDF"):
            st.info("PDF export coming soon")
    with col4:
        if st.button("📌 Pin to Dashboard"):
            st.success("Pinned to dashboard")

    st.markdown("---")

    # Why Now box
    st.markdown("### 🎯 Why Now")
    st.info(candidate.get('why_now', 'No explanation available'))

    st.markdown("---")

    # Metrics row
    st.markdown("### 📊 Metrics")
    metrics = data.get('metrics', {})
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Velocity (7d)", f"{metrics.get('velocity_7d', 0)} filings")
    with col2:
        st.metric("Velocity (28d)", f"{metrics.get('velocity_28d', 0)} filings")
    with col3:
        st.metric("Breadth", f"{metrics.get('breadth_states', 0)} states, {metrics.get('breadth_firms', 0)} firms")
    with col4:
        st.metric("Accel Ratio", f"{metrics.get('accel_ratio', 0):.1f}x")

    st.markdown("---")

    # Timeline
    st.markdown("### 📅 Timeline")
    render_timeline(data.get('timeline', []))

    st.markdown("---")

    # Evidence Ledger
    st.markdown("### 📋 Evidence Ledger")
    render_evidence(data.get('evidence', []))

    st.markdown("---")

    # Split view: Injury Distribution + Score Breakdown
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🩺 Injury Distribution")
        render_injury_chart(data.get('injuries', []))

    with col2:
        st.markdown("### 🎯 Score Breakdown")
        render_score_breakdown(candidate.get('score_components', {}), candidate.get('category', 'pharma'))


def render_timeline(events: list):
    """Render the chronological timeline of events."""
    if not events:
        st.info("No timeline events available")
        return

    for event in events:
        event_type = event.get('event_type', 'UNKNOWN')
        icon = get_event_icon(event_type)
        date = event.get('detected_at', '')
        snippet = event.get('snippet', '')

        st.markdown(f"""
        <div style='padding: 0.75rem; margin-bottom: 0.5rem; border-left: 3px solid #4299e1; background: #f7fafc;'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <span style='font-size: 1.2rem;'>{icon}</span>
                    <strong style='margin-left: 0.5rem;'>{event_type.replace('_', ' ').title()}</strong>
                </div>
                <span style='color: #718096; font-size: 0.875rem; font-family: monospace;'>{date}</span>
            </div>
            <p style='margin: 0.5rem 0 0 2rem; color: #2d3748;'>{snippet}</p>
        </div>
        """, unsafe_allow_html=True)


def render_evidence(documents: list):
    """Render the evidence ledger table."""
    if not documents:
        st.info("No evidence documents available")
        return

    df = pd.DataFrame(documents)
    df = df[['source_type', 'title', 'filed_date', 'external_url']].head(20)

    # Display as expandable rows
    for idx, row in df.iterrows():
        with st.expander(f"{row['source_type']} - {row['title']} ({row['filed_date']})"):
            st.markdown(f"**Source**: {row['source_type']}")
            st.markdown(f"**Date**: {row['filed_date']}")
            st.markdown(f"**Link**: [{row['title']}]({row['external_url']})")
            if 'snippet' in row:
                st.markdown(f"**Snippet**: {row.get('snippet', 'N/A')}")


def render_injury_chart(injuries: list):
    """Render horizontal bar chart of injury distribution."""
    if not injuries:
        st.info("No injury data available")
        return

    df = pd.DataFrame(injuries)

    fig = go.Figure(go.Bar(
        x=df['count'],
        y=df['injury'],
        orientation='h',
        marker=dict(
            color=df['count'],
            colorscale='Blues',
            showscale=False
        ),
        text=[f"{int(p*100)}%" for p in df['pct']],
        textposition='auto',
    ))

    fig.update_layout(
        xaxis_title="Count",
        yaxis_title="",
        height=300,
        margin=dict(l=0, r=0, t=0, b=0),
        yaxis=dict(autorange="reversed")
    )

    st.plotly_chart(fig, use_container_width=True)


def render_score_breakdown(components: dict, category: str):
    """Render score component breakdown with weights."""
    if not components:
        st.info("No score breakdown available")
        return

    # Get weights for this category
    weights = get_category_weights(category)

    # Create dataframe
    data = []
    for component, score in components.items():
        weight = weights.get(component, 0)
        weighted_score = score * (weight / 100)
        data.append({
            'component': component.replace('_', ' ').title(),
            'weight': f"{int(weight*100)}%",
            'score': score,
            'weighted': weighted_score
        })

    df = pd.DataFrame(data)

    # Render as horizontal bars
    for _, row in df.iterrows():
        st.markdown(f"**{row['component']}** ({row['weight']})")
        st.progress(row['score'] / 100)
        st.caption(f"Score: {row['score']:.0f} / 100")

    total = sum([r['weighted'] for r in data])
    st.markdown("---")
    st.markdown(f"### Total Score: {total:.0f}")


def get_event_icon(event_type: str) -> str:
    """Get icon for event type."""
    icons = {
        'FILING_SPIKE': '⚖️',
        'FILING_NEW': '📄',
        'ADVERSE_TREND': '💊',
        'META_ANALYSIS': '📚',
        'PAPER_PUBLISHED': '📄',
        'SEC_LANGUAGE_DELTA': '🏢',
        'FDA_COMMUNICATION': '🏛️',
        'IARC_2A': '⚠️',
        'IARC_2B': '⚠️',
    }
    return icons.get(event_type, '●')


def get_category_weights(category: str) -> dict:
    """Get scoring weights for a category."""
    weights_map = {
        'pharma': {
            'faers_trend': 0.40,
            'court_velocity': 0.30,
            'court_breadth': 0.10,
            'literature': 0.15,
            'sec_language': 0.05
        },
        'device': {
            'maude_trend': 0.40,
            'court_velocity': 0.30,
            'court_breadth': 0.10,
            'literature': 0.10,
            'sec_language': 0.10
        },
        'chemical': {
            'literature': 0.40,
            'court_velocity': 0.25,
            'court_breadth': 0.15,
            'sec_language': 0.05
        },
    }
    return weights_map.get(category, weights_map['pharma'])


def get_sample_dossier() -> dict:
    """Return sample dossier data for demo - EARLY SIGNAL, not formed MDL."""
    return {
        'candidate': {
            'candidate_id': '1',
            'defendant_text': 'L\'Oréal USA',
            'product_text': 'Dark & Lovely Hair Relaxer',
            'injury_text': 'Uterine Cancer',
            'score_total': 68,
            'score_components': {
                'literature': 75,
                'court_velocity': 58,
                'court_breadth': 42,
                'faers_trend': 0  # No FDA reports - consumer product
            },
            'stage': 'INVESTIGATE',
            'category': 'consumer',
            'first_seen': '2024-10-12',
            'last_updated': '2025-01-20 14:30',
            'why_now': '12 new filings in last 7 days across 4 states. Recent NIH study links chemical hair straighteners to uterine cancer. FDA has not issued safety communication yet.'
        },
        'metrics': {
            'velocity_7d': 12,
            'velocity_28d': 34,
            'accel_ratio': 1.8,
            'breadth_states': 4,
            'breadth_firms': 3
        },
        'timeline': [
            {
                'event_type': 'FILING_SPIKE',
                'detected_at': '2025-01-18',
                'snippet': '+12 cases filed in 7 days (300% increase vs baseline)'
            },
            {
                'event_type': 'PAPER_PUBLISHED',
                'detected_at': '2024-12-05',
                'snippet': 'NIH Sister Study: Hair straightener use associated with 2.6x uterine cancer risk'
            },
            {
                'event_type': 'FILING_NEW',
                'detected_at': '2024-10-12',
                'snippet': 'First product liability case filed in Illinois (Smith v. L\'Oréal USA)'
            },
        ],
        'evidence': [
            {
                'source_type': 'Court',
                'title': 'Johnson v. L\'Oréal USA Inc.',
                'filed_date': '2025-01-18',
                'external_url': 'https://example.com',
                'snippet': 'Plaintiff used Dark & Lovely relaxer for 15 years, diagnosed with uterine leiomyosarcoma age 38'
            },
            {
                'source_type': 'Court',
                'title': 'Williams v. Strength of Nature LLC',
                'filed_date': '2025-01-16',
                'external_url': 'https://example.com',
                'snippet': 'Alleges defendants failed to warn of endocrine-disrupting chemicals in hair straightening products'
            },
            {
                'source_type': 'PubMed',
                'title': 'Hair Product Use and Uterine Cancer - NIH Sister Study',
                'filed_date': '2024-12-05',
                'external_url': 'https://pubmed.com',
                'snippet': 'Permanent hair straightener use associated with 2.6-fold increased uterine cancer risk (HR: 2.59, 95% CI: 1.46-4.58)'
            },
            {
                'source_type': 'PubMed',
                'title': 'Phthalates and Parabens in Hair Products - Exposure Study',
                'filed_date': '2023-03-22',
                'external_url': 'https://pubmed.com',
                'snippet': 'Chemical hair straighteners contain high levels of endocrine disruptors including formaldehyde, phthalates, parabens'
            },
        ],
        'injuries': [
            {'injury': 'Uterine Leiomyosarcoma', 'count': 18, 'pct': 0.52},
            {'injury': 'Endometrial Cancer', 'count': 12, 'pct': 0.35},
            {'injury': 'Uterine Fibroids', 'count': 4, 'pct': 0.13},
        ]
    }
