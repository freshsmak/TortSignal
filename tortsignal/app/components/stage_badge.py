"""
Stage Badge Component - Color-coded stage indicators
"""


def render_stage_badge(stage: str) -> str:
    """
    Render a color-coded stage badge.

    Args:
        stage: Stage string (HIGH_CONVICTION, INVESTIGATE, AWARENESS, QUIET)

    Returns:
        HTML string for the badge
    """
    stage = stage.upper()

    badge_classes = {
        'HIGH_CONVICTION': 'badge-high',
        'INVESTIGATE': 'badge-investigate',
        'AWARENESS': 'badge-awareness',
        'QUIET': 'badge-quiet',
    }

    badge_labels = {
        'HIGH_CONVICTION': 'HIGH',
        'INVESTIGATE': 'INVEST',
        'AWARENESS': 'AWARE',
        'QUIET': 'QUIET',
    }

    css_class = badge_classes.get(stage, 'badge-quiet')
    label = badge_labels.get(stage, stage[:6])

    return f"""
    <span class='badge {css_class}' title='{stage.replace('_', ' ').title()}'>
        {label}
    </span>
    """


def get_stage_from_score(score: int) -> str:
    """
    Determine stage based on score.

    Args:
        score: Total score (0-100)

    Returns:
        Stage string
    """
    if score >= 70:
        return 'HIGH_CONVICTION'
    elif score >= 40:
        return 'INVESTIGATE'
    elif score >= 20:
        return 'AWARENESS'
    else:
        return 'QUIET'


def get_stage_color(stage: str) -> str:
    """
    Get hex color for a stage.

    Args:
        stage: Stage string

    Returns:
        Hex color string
    """
    colors = {
        'HIGH_CONVICTION': '#e53e3e',
        'INVESTIGATE': '#ed8936',
        'AWARENESS': '#ecc94b',
        'QUIET': '#718096',
    }
    return colors.get(stage.upper(), '#718096')
