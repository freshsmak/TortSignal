"""
Score Display Component - Large, color-coded score numbers
"""


def render_score(score: int, max_score: int = 100, size: str = 'medium') -> str:
    """
    Render a color-coded score display.

    Args:
        score: The score value
        max_score: Maximum possible score (default 100)
        size: Display size - 'small', 'medium', 'large'

    Returns:
        HTML string for the score display
    """
    # Determine color based on score
    if score >= 70:
        css_class = 'score-high'
    elif score >= 40:
        css_class = 'score-med'
    else:
        css_class = 'score-low'

    # Determine font size
    size_map = {
        'small': '1.25rem',
        'medium': '1.75rem',
        'large': '2.5rem'
    }
    font_size = size_map.get(size, '1.75rem')

    return f"""
    <div style='display: inline-block;'>
        <span style='font-size: {font_size}; font-weight: 700;' class='{css_class}'>
            {score}
        </span>
        <span style='font-size: 0.875rem; color: #718096; margin-left: 0.25rem;'>
            / {max_score}
        </span>
    </div>
    """


def render_score_bar(score: int, max_score: int = 100, height: str = '8px') -> str:
    """
    Render a horizontal progress bar for the score.

    Args:
        score: The score value
        max_score: Maximum possible score (default 100)
        height: Bar height (CSS value)

    Returns:
        HTML string for the score bar
    """
    percentage = (score / max_score) * 100

    # Determine color
    if score >= 70:
        color = '#e53e3e'
    elif score >= 40:
        color = '#ed8936'
    else:
        color = '#718096'

    return f"""
    <div style='width: 100%; background: #e2e8f0; border-radius: 4px; overflow: hidden; height: {height};'>
        <div style='width: {percentage}%; height: 100%; background: {color}; transition: width 0.3s ease;'></div>
    </div>
    """


def render_score_with_bar(score: int, max_score: int = 100) -> str:
    """
    Render score number with progress bar below.

    Args:
        score: The score value
        max_score: Maximum possible score (default 100)

    Returns:
        HTML string combining score and bar
    """
    return f"""
    <div style='margin-bottom: 0.5rem;'>
        {render_score(score, max_score, size='medium')}
    </div>
    {render_score_bar(score, max_score)}
    """
