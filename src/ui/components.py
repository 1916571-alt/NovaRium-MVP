import streamlit as st

# =========================================================
# NovaRium UI Components - Cosmic Glass Theme v2.0
# STITCH Design System Integration
# =========================================================

def apply_custom_css():
    """
    Apply global Cosmic Glass CSS styling to the Streamlit app.
    Based on STITCH Design System v2.0
    """
    st.markdown("""
<style>
    /* ============================================
       1. FONTS & GLOBAL RESET
       ============================================ */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;900&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* ============================================
       2. COSMIC BACKGROUND
       ============================================ */
    .stApp {
        background-color: #141121 !important;
        background-image:
            radial-gradient(circle at 15% 50%, rgba(59, 25, 230, 0.08), transparent 25%),
            radial-gradient(circle at 85% 30%, rgba(120, 50, 255, 0.05), transparent 25%);
        color: #ffffff !important;
    }

    /* Hide Streamlit default header/footer */
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* ============================================
       3. GLASS PANEL EFFECT
       ============================================ */
    .glass-panel {
        background: rgba(30, 27, 46, 0.6) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 1rem !important;
    }

    /* Streamlit containers with glass effect */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(30, 27, 46, 0.6);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 1.5rem;
        padding: 1.5rem;
        transition: all 0.3s ease;
    }

    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: rgba(255, 255, 255, 0.15);
        box-shadow: 0 0 30px rgba(59, 25, 230, 0.1);
    }

    /* ============================================
       4. TYPOGRAPHY
       ============================================ */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
    }

    h1 { font-size: 2.5rem !important; font-weight: 900 !important; }
    h2 { font-size: 1.75rem !important; }
    h3 { font-size: 1.25rem !important; }

    p, li, label, span, .stMarkdown {
        color: rgba(255, 255, 255, 0.7) !important;
    }

    /* ============================================
       5. NAVBAR STYLES
       ============================================ */
    .navbar-container {
        background: rgba(30, 27, 46, 0.6);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 1rem;
        padding: 0.75rem 1.5rem;
        margin-bottom: 2rem;
    }

    .navbar-brand {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .navbar-logo {
        width: 2.5rem;
        height: 2.5rem;
        background: linear-gradient(135deg, #3b19e6 0%, #7c3aed 100%);
        border-radius: 0.75rem;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 0 15px rgba(59, 25, 230, 0.4);
    }

    .navbar-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #ffffff !important;
        letter-spacing: -0.02em;
    }

    /* ============================================
       6. BUTTON STYLES
       ============================================ */
    /* Secondary/Ghost Button */
    .stButton > button {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border-radius: 0.75rem !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 500 !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.3s ease !important;
    }

    .stButton > button:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
        transform: translateY(-2px);
    }

    .stButton > button:active {
        transform: translateY(0) scale(0.98);
    }

    /* Primary Button */
    div[data-testid="stButton"] button[kind="primary"],
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #3b19e6 0%, #7c3aed 100%) !important;
        border: none !important;
        box-shadow: 0 0 20px rgba(59, 25, 230, 0.5) !important;
        color: white !important;
    }

    div[data-testid="stButton"] button[kind="primary"]:hover,
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 0 30px rgba(59, 25, 230, 0.7) !important;
        transform: translateY(-2px);
    }

    /* Nav button active state */
    .nav-btn-active {
        background: linear-gradient(135deg, #3b19e6 0%, #7c3aed 100%) !important;
        border: none !important;
        box-shadow: 0 0 15px rgba(59, 25, 230, 0.4) !important;
    }

    /* ============================================
       7. INPUT FIELDS
       ============================================ */
    .stTextInput > div > div,
    .stNumberInput > div > div,
    .stSelectbox > div > div,
    .stTextArea > div > div,
    .stMultiSelect > div > div {
        background-color: rgba(18, 17, 24, 0.5) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 0.75rem !important;
    }

    .stTextInput > div > div:focus-within,
    .stSelectbox > div > div:focus-within {
        border-color: #3b19e6 !important;
        box-shadow: 0 0 0 2px rgba(59, 25, 230, 0.2) !important;
        background-color: rgba(18, 17, 24, 0.8) !important;
    }

    /* Input text color */
    .stTextInput input, .stTextArea textarea {
        color: white !important;
    }

    /* Placeholder */
    .stTextInput input::placeholder {
        color: rgba(255, 255, 255, 0.4) !important;
    }

    /* ============================================
       8. SIDEBAR
       ============================================ */
    section[data-testid="stSidebar"] {
        background: rgba(20, 17, 33, 0.95) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }

    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: rgba(255, 255, 255, 0.9) !important;
        font-size: 0.9rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.1em !important;
        margin-bottom: 1rem !important;
    }

    /* ============================================
       9. METRICS & STATS
       ============================================ */
    div[data-testid="stMetric"] {
        background: rgba(30, 27, 46, 0.6);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 1rem;
        padding: 1.25rem;
    }

    div[data-testid="stMetric"] label {
        color: rgba(255, 255, 255, 0.6) !important;
        font-size: 0.85rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }

    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 2rem !important;
        font-weight: 900 !important;
    }

    /* Positive delta */
    div[data-testid="stMetric"] div[data-testid="stMetricDelta"] svg {
        color: #22c55e !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricDelta"] div {
        color: #22c55e !important;
    }

    /* ============================================
       10. TABS
       ============================================ */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(30, 27, 46, 0.4);
        border-radius: 0.75rem;
        padding: 0.25rem;
        gap: 0.25rem;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: rgba(255, 255, 255, 0.6) !important;
        border-radius: 0.5rem !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 500 !important;
    }

    .stTabs [aria-selected="true"] {
        background: rgba(59, 25, 230, 0.2) !important;
        color: #a78bfa !important;
    }

    /* ============================================
       11. EXPANDER
       ============================================ */
    .streamlit-expanderHeader {
        background: rgba(30, 27, 46, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 0.75rem !important;
        color: white !important;
    }

    .streamlit-expanderContent {
        background: rgba(30, 27, 46, 0.4) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-top: none !important;
        border-radius: 0 0 0.75rem 0.75rem !important;
    }

    /* ============================================
       12. DATA TABLES
       ============================================ */
    .stDataFrame {
        background: rgba(30, 27, 46, 0.6) !important;
        border-radius: 1rem !important;
        overflow: hidden;
    }

    .stDataFrame [data-testid="stDataFrameResizable"] {
        background: transparent !important;
    }

    /* ============================================
       13. PROGRESS BAR
       ============================================ */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #3b19e6, #ec4899) !important;
        border-radius: 9999px !important;
    }

    .stProgress > div > div > div {
        background: rgba(255, 255, 255, 0.1) !important;
    }

    /* ============================================
       14. CODE BLOCKS
       ============================================ */
    code, pre, .stCode, .stCodeBlock {
        background-color: #1a1a2e !important;
        color: #e2e8f0 !important;
        font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
    }

    pre {
        background-color: #1a1a2e !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 0.75rem !important;
        padding: 1rem !important;
    }

    /* Syntax highlighting */
    .hljs-keyword { color: #c792ea !important; }
    .hljs-string { color: #c3e88d !important; }
    .hljs-number { color: #f78c6c !important; }
    .hljs-function { color: #82aaff !important; }
    .hljs-comment { color: #676e95 !important; }

    /* ============================================
       15. ALERTS & TOASTS
       ============================================ */
    .stSuccess, .stInfo, .stWarning, .stError {
        background: rgba(30, 27, 46, 0.8) !important;
        border-radius: 0.75rem !important;
        backdrop-filter: blur(12px) !important;
    }

    .stSuccess {
        border-left: 4px solid #22c55e !important;
    }

    .stWarning {
        border-left: 4px solid #f59e0b !important;
    }

    .stError {
        border-left: 4px solid #ef4444 !important;
    }

    .stInfo {
        border-left: 4px solid #3b19e6 !important;
    }

    /* ============================================
       16. RADIO BUTTONS & CHECKBOXES
       ============================================ */
    .stRadio > div {
        background: transparent !important;
    }

    .stRadio label, .stCheckbox label {
        color: rgba(255, 255, 255, 0.8) !important;
    }

    /* ============================================
       17. SCROLLBAR
       ============================================ */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.3);
    }

    /* ============================================
       18. CUSTOM COMPONENTS
       ============================================ */
    /* Educational Guide Box */
    .edu-guide {
        background: linear-gradient(90deg, rgba(59, 25, 230, 0.1) 0%, rgba(124, 58, 237, 0.05) 100%);
        border-left: 4px solid #7c3aed;
        padding: 1.25rem 1.5rem;
        border-radius: 0 0.75rem 0.75rem 0;
        margin-bottom: 1.5rem;
    }

    .edu-title {
        color: #a78bfa !important;
        font-weight: 700;
        font-size: 0.85rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .edu-content {
        color: rgba(255, 255, 255, 0.85) !important;
        font-size: 0.95rem;
        line-height: 1.6;
    }

    /* Stat Card */
    .stat-card {
        background: rgba(30, 27, 46, 0.6);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 1rem;
        padding: 1.5rem;
        transition: all 0.3s ease;
    }

    .stat-card:hover {
        border-color: rgba(255, 255, 255, 0.15);
        box-shadow: 0 0 30px rgba(59, 25, 230, 0.15);
    }

    .stat-label {
        color: rgba(255, 255, 255, 0.5) !important;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.5rem;
    }

    .stat-value {
        font-size: 2.5rem;
        font-weight: 900;
        color: #ffffff;
        line-height: 1;
    }

    .stat-delta {
        font-size: 0.875rem;
        font-weight: 500;
        margin-top: 0.5rem;
    }

    .stat-delta.positive {
        color: #22c55e;
    }

    .stat-delta.negative {
        color: #ef4444;
    }

    /* Alert Card */
    .alert-card {
        background: rgba(30, 27, 46, 0.6);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 1rem;
        padding: 1.25rem;
        position: relative;
        overflow: hidden;
    }

    .alert-card.success {
        border-left: 4px solid #22c55e;
    }

    .alert-card.warning {
        border-left: 4px solid #f59e0b;
    }

    .alert-card.error {
        border-left: 4px solid #ef4444;
    }

    .alert-card .alert-title {
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }

    .alert-card.success .alert-title { color: #22c55e; }
    .alert-card.warning .alert-title { color: #f59e0b; }
    .alert-card.error .alert-title { color: #ef4444; }

    .alert-card .alert-content {
        color: rgba(255, 255, 255, 0.7);
        font-size: 0.9rem;
        line-height: 1.5;
    }

    /* Badge */
    .badge {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .badge.primary {
        background: rgba(59, 25, 230, 0.2);
        color: #a78bfa;
        border: 1px solid rgba(59, 25, 230, 0.3);
    }

    .badge.success {
        background: rgba(34, 197, 94, 0.2);
        color: #22c55e;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }

    .badge.warning {
        background: rgba(245, 158, 11, 0.2);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }

    .badge.error {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }

    /* Password Strength Indicator */
    .password-strength {
        display: flex;
        gap: 0.25rem;
        margin-top: 0.5rem;
    }

    .password-strength .bar {
        flex: 1;
        height: 4px;
        border-radius: 9999px;
        background: rgba(255, 255, 255, 0.1);
    }

    .password-strength .bar.active.weak { background: #ef4444; }
    .password-strength .bar.active.medium { background: #f59e0b; }
    .password-strength .bar.active.strong { background: #22c55e; }

    /* Section Divider */
    .section-divider {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin: 2rem 0;
        color: rgba(255, 255, 255, 0.3);
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }

    .section-divider::before,
    .section-divider::after {
        content: "";
        flex: 1;
        height: 1px;
        background: rgba(255, 255, 255, 0.1);
    }
</style>
""", unsafe_allow_html=True)


def render_navbar():
    """
    Render top navigation bar with Cosmic Glass styling.
    모든 텍스트는 한국어로 유지합니다.
    """
    # Custom navbar HTML
    st.markdown("""
    <div class="navbar-container" style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem;">
        <div class="navbar-brand">
            <div class="navbar-logo">
                <span style="font-size: 1.25rem;">🚀</span>
            </div>
            <span class="navbar-title">NovaRium</span>
            <span class="badge primary" style="margin-left: 0.5rem;">v2.0</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Navigation buttons using Streamlit columns
    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    cols = st.columns([1.2, 1, 1, 1, 1])

    with cols[0]:
        if st.button("🌌 NovaRium",
                     type="primary" if st.session_state.get('page') == 'intro' else "secondary",
                     use_container_width=True):
            st.session_state['page'] = 'intro'
            st.rerun()

    with cols[1]:
        if st.button("🛠️ 데이터 랩",
                     type="primary" if st.session_state.get('page') == 'data_lab' else "secondary",
                     use_container_width=True):
            st.session_state['page'] = 'data_lab'
            st.rerun()

    with cols[2]:
        if st.button("📊 모니터",
                     type="primary" if st.session_state.get('page') == 'monitor' else "secondary",
                     use_container_width=True):
            st.session_state['page'] = 'monitor'
            st.rerun()

    with cols[3]:
        if st.button("🚀 실험 위저드",
                     type="primary" if st.session_state.get('page') == 'study' else "secondary",
                     use_container_width=True):
            st.session_state['page'] = 'study'
            st.rerun()

    with cols[4]:
        if st.button("📚 회고록",
                     type="primary" if st.session_state.get('page') == 'portfolio' else "secondary",
                     use_container_width=True):
            st.session_state['page'] = 'portfolio'
            st.rerun()

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)


def edu_guide(title: str, content: str):
    """
    Render an educational guide box with Cosmic Glass styling.
    """
    st.markdown(f"""
    <div class="edu-guide">
        <div class="edu-title">
            <span style="font-size: 1.1em;">💡</span> {title}
        </div>
        <div class="edu-content">{content}</div>
    </div>
    """, unsafe_allow_html=True)


def render_step_progress(steps: list, current_step: int):
    """
    Render wizard progress steps with Cosmic Glass styling.
    """
    cols = st.columns(len(steps))

    for i, step_name in enumerate(steps):
        step_num = i + 1
        is_active = step_num == current_step
        is_completed = step_num < current_step

        if is_active:
            bar_color = "linear-gradient(90deg, #3b19e6, #7c3aed)"
            text_color = "#ffffff"
            weight = "700"
            glow = "0 0 15px rgba(59, 25, 230, 0.5)"
        elif is_completed:
            bar_color = "#22c55e"
            text_color = "#22c55e"
            weight = "500"
            glow = "none"
        else:
            bar_color = "rgba(255, 255, 255, 0.1)"
            text_color = "rgba(255, 255, 255, 0.4)"
            weight = "400"
            glow = "none"

        cols[i].markdown(f"""
        <div style="text-align: center;">
            <div style="
                height: 4px;
                width: 100%;
                background: {bar_color};
                border-radius: 9999px;
                margin-bottom: 0.75rem;
                box-shadow: {glow};
            "></div>
            <div style="
                color: {text_color};
                font-weight: {weight};
                font-size: 0.85rem;
                letter-spacing: -0.01em;
            ">{step_name}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)


def stat_card(label: str, value: str, delta: str = None, delta_type: str = "positive"):
    """
    Render a stat card with Cosmic Glass styling.

    Args:
        label: 지표 라벨
        value: 지표 값
        delta: 변화량 (optional)
        delta_type: "positive" or "negative"
    """
    delta_html = ""
    if delta:
        delta_class = "positive" if delta_type == "positive" else "negative"
        delta_icon = "↑" if delta_type == "positive" else "↓"
        delta_html = f'<div class="stat-delta {delta_class}">{delta_icon} {delta}</div>'

    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">{label}</div>
        <div class="stat-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def alert_card(title: str, content: str, alert_type: str = "success"):
    """
    Render an alert card with Cosmic Glass styling.

    Args:
        title: 알림 제목
        content: 알림 내용
        alert_type: "success", "warning", or "error"
    """
    icon_map = {
        "success": "✓",
        "warning": "⚠",
        "error": "✕"
    }
    icon = icon_map.get(alert_type, "ℹ")

    st.markdown(f"""
    <div class="alert-card {alert_type}">
        <div class="alert-title">{icon} {title}</div>
        <div class="alert-content">{content}</div>
    </div>
    """, unsafe_allow_html=True)


def section_divider(text: str = ""):
    """
    Render a section divider.
    """
    if text:
        st.markdown(f'<div class="section-divider">{text}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<hr style="border: none; border-top: 1px solid rgba(255,255,255,0.1); margin: 2rem 0;">', unsafe_allow_html=True)


def badge(text: str, badge_type: str = "primary"):
    """
    Return badge HTML string.

    Args:
        text: 배지 텍스트
        badge_type: "primary", "success", "warning", or "error"
    """
    return f'<span class="badge {badge_type}">{text}</span>'


def glass_container_start():
    """
    Start a glass container div. Must be paired with glass_container_end().
    """
    st.markdown("""
    <div style="
        background: rgba(30, 27, 46, 0.6);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 1.5rem;
        padding: 1.5rem;
        margin-bottom: 1rem;
    ">
    """, unsafe_allow_html=True)


def glass_container_end():
    """
    End a glass container div.
    """
    st.markdown("</div>", unsafe_allow_html=True)
