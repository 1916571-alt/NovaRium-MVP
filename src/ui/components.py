import streamlit as st
import streamlit.components.v1 as components

# =========================================================
# NovaRium UI Components - STITCH Design System v3.0
# Atomic Design 기반 Cosmic Glass Theme
# =========================================================

# =========================================================
# DESIGN TOKENS - STITCH v3 Color System (Navigation Update)
# =========================================================
STITCH_COLORS = {
    'primary': '#5a89f6',           # STITCH v3 navigation primary
    'primary_light': '#6d4aff',
    'primary_glow': '#5a89f6',
    'background_dark': '#0B0E14',   # Deep cosmic background
    'surface_dark': '#181C25',
    'glass_bg': 'rgba(20, 25, 34, 0.4)',
    'glass_bg_heavy': 'rgba(17, 20, 28, 0.75)',
    'glass_border': 'rgba(255, 255, 255, 0.08)',
    'success': '#10B981',           # Emerald-500
    'warning': '#F59E0B',
    'error': '#EF4444',
    'text_primary': '#ffffff',
    'text_secondary': 'rgba(255, 255, 255, 0.6)',
    'text_muted': 'rgba(148, 163, 184, 1)',  # slate-400
}

def apply_custom_css():
    """STITCH v3 전역 CSS 스타일 적용. Atomic Design 기반."""
    st.markdown("""
<style>
    /* ============================================
       STITCH v3 DESIGN SYSTEM - ATOMIC CSS
       ============================================ */

    /* 1. FONTS & GLOBAL RESET */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;900&display=swap');

    *, *::before, *::after {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        box-sizing: border-box;
    }

    html, body, [class*="css"], .stApp, .main {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* 2. GLOBAL SCALE */
    html { font-size: 15px !important; }
    .stApp { zoom: 0.95; }

    /* ============================================
       3. COSMIC BACKGROUND - STITCH v3 Navigation
       ============================================ */
    .stApp, .stApp > header, .stApp > section {
        background-color: #0B0E14 !important;
        background-image:
            radial-gradient(at 0% 0%, rgba(90, 137, 246, 0.15) 0px, transparent 50%),
            radial-gradient(at 100% 100%, rgba(124, 58, 237, 0.1) 0px, transparent 50%) !important;
        color: #ffffff !important;
    }

    /* Decorative Background Glows - STITCH v3 Cosmic */
    .stApp::before {
        content: "";
        position: fixed;
        top: -10%;
        left: 20%;
        width: 500px;
        height: 500px;
        background: rgba(90, 137, 246, 0.2);
        border-radius: 50%;
        filter: blur(120px);
        mix-blend-mode: screen;
        opacity: 0.4;
        pointer-events: none;
        z-index: 0;
    }

    .stApp::after {
        content: "";
        position: fixed;
        bottom: -10%;
        right: 10%;
        width: 400px;
        height: 400px;
        background: rgba(139, 92, 246, 0.2);
        border-radius: 50%;
        filter: blur(100px);
        mix-blend-mode: screen;
        opacity: 0.3;
        pointer-events: none;
        z-index: 0;
    }

    .main .block-container {
        background: transparent !important;
        padding: 1rem 2rem !important;
        max-width: 1200px !important;
        position: relative;
        z-index: 1;
    }

    div[data-testid="stAppViewBlockContainer"] {
        padding: 1rem 2rem !important;
        max-width: 1200px !important;
        margin: 0 auto;
    }

    section[data-testid="stMain"], div[data-testid="stAppViewContainer"] {
        background-color: #0B0E14 !important;
        background-image:
            radial-gradient(at 0% 0%, rgba(90, 137, 246, 0.15) 0px, transparent 50%),
            radial-gradient(at 100% 100%, rgba(124, 58, 237, 0.1) 0px, transparent 50%) !important;
    }

    /* Hide Streamlit defaults */
    header[data-testid="stHeader"] { background: transparent !important; }
    #MainMenu, footer, .stDeployButton { display: none !important; }

    /* ============================================
       4. GLASS PANEL - STITCH v3 (Blur 16px)
       ============================================ */
    .glass-panel {
        background: rgba(30, 28, 38, 0.4) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 1.25rem !important;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2) !important;
    }

    /* Interactive Glass Card with Hover Glow */
    .glass-card-interactive {
        background: rgba(30, 28, 38, 0.4);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 1.25rem;
        padding: 1.5rem;
        transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
        position: relative;
    }

    .glass-card-interactive:hover {
        box-shadow: 0 0 25px rgba(59, 25, 230, 0.15), 0 4px 30px rgba(0, 0, 0, 0.2);
        transform: translateY(-2px);
        border-color: rgba(93, 62, 255, 0.5);
    }

    /* Streamlit containers */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(30, 28, 38, 0.4);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 1.25rem;
        padding: 1.5rem;
        transition: all 0.3s ease;
    }

    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: rgba(93, 62, 255, 0.3);
        box-shadow: 0 0 20px rgba(59, 25, 230, 0.1);
    }

    /* ============================================
       5. TYPOGRAPHY - STITCH v3
       ============================================ */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
    }

    h1 { font-size: 3rem !important; font-weight: 900 !important; }
    h2 { font-size: 1.5rem !important; }
    h3 { font-size: 1.125rem !important; }

    p, li, label, span, .stMarkdown { color: rgba(255, 255, 255, 0.6) !important; }

    /* Gradient Text */
    .gradient-text {
        background: linear-gradient(135deg, #ffffff 0%, #a5a5ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    /* ============================================
       6. BUTTONS - STITCH v3 Button Kit
       ============================================ */

    /* 6.1 Primary Button - STITCH v3 Navigation Style */
    .stitch-btn-primary, [data-testid="baseButton-primary"], button[kind="primary"] {
        background: #5a89f6 !important;
        border: none !important;
        border-radius: 9999px !important;
        color: white !important;
        font-weight: 700 !important;
        padding: 0.75rem 1.5rem !important;
        transition: all 0.3s ease !important;
        cursor: pointer !important;
        box-shadow: 0 0 20px rgba(90, 137, 246, 0.4) !important;
    }

    .stitch-btn-primary:hover, [data-testid="baseButton-primary"]:hover, button[kind="primary"]:hover {
        background: #6b96f7 !important;
        box-shadow: 0 0 25px rgba(90, 137, 246, 0.6) !important;
        transform: scale(1.02) translateY(-2px) !important;
    }

    .stitch-btn-primary:active, [data-testid="baseButton-primary"]:active, button[kind="primary"]:active {
        background: #4a79e6 !important;
        transform: scale(0.98) !important;
    }

    /* 6.2 Secondary Button - Ghost Style STITCH v3 */
    .stitch-btn-secondary, [data-testid="baseButton-secondary"], button:not([kind="primary"]) {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 9999px !important;
        color: rgba(148, 163, 184, 1) !important;
        font-weight: 600 !important;
        padding: 0.75rem 1.5rem !important;
        transition: all 0.3s ease !important;
        cursor: pointer !important;
    }

    .stitch-btn-secondary:hover, [data-testid="baseButton-secondary"]:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
        color: white !important;
    }

    .stitch-btn-secondary:active, [data-testid="baseButton-secondary"]:active {
        background: rgba(90, 137, 246, 0.1) !important;
        border-color: rgba(90, 137, 246, 0.3) !important;
        transform: scale(0.98) !important;
    }

    /* 6.3 Tertiary Button - Text Link */
    .stitch-btn-tertiary {
        background: none !important;
        border: none !important;
        color: rgba(255, 255, 255, 0.7) !important;
        font-weight: 500 !important;
        cursor: pointer !important;
        transition: color 0.2s ease !important;
    }

    .stitch-btn-tertiary:hover {
        color: white !important;
        text-decoration: underline !important;
        text-decoration-color: #3b19e6 !important;
        text-underline-offset: 4px !important;
    }

    /* 6.4 Icon Button */
    .stitch-btn-icon {
        width: 3rem !important;
        height: 3rem !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 9999px !important;
        color: white !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
    }

    .stitch-btn-icon:hover {
        background: #3b19e6 !important;
        border-color: transparent !important;
        box-shadow: 0 0 15px rgba(59, 25, 230, 0.4) !important;
        transform: scale(1.1) !important;
    }

    /* ============================================
       7. CARDS - STITCH v3 Card Kit
       ============================================ */

    /* 7.1 Default Card */
    .stitch-card, .stitch-card-default {
        background: rgba(30, 28, 38, 0.4);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 1.25rem;
        padding: 1.5rem;
        transition: all 0.3s ease;
    }

    .stitch-card:hover, .stitch-card-default:hover {
        border-color: rgba(93, 62, 255, 0.5);
        box-shadow: 0 0 20px rgba(59, 25, 230, 0.15), 0 4px 30px rgba(0, 0, 0, 0.2);
        transform: translateY(-2px);
    }

    /* 7.2 Success Card - Left Border Accent */
    .stitch-card-success {
        background: rgba(30, 28, 38, 0.4);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 1.25rem;
        padding: 1.5rem;
        position: relative;
        overflow: hidden;
    }

    .stitch-card-success::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 6px;
        height: 100%;
        background: #4ADE80;
        box-shadow: 0 0 10px rgba(74, 222, 128, 0.4);
    }

    /* 7.3 Warning Card - Bottom Border Accent */
    .stitch-card-warning {
        background: rgba(30, 28, 38, 0.4);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-bottom: 3px solid rgba(245, 158, 11, 0.8);
        border-radius: 1.25rem;
        padding: 1.5rem;
    }

    /* 7.4 Error Card - Full Border + Tint */
    .stitch-card-error {
        background: rgba(239, 68, 68, 0.02);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: 1.25rem;
        padding: 1.5rem;
    }

    /* 7.5 Stat Card */
    .stitch-stat-card {
        background: rgba(30, 28, 38, 0.4);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 1.25rem;
        padding: 1.5rem;
        transition: all 0.3s ease;
    }

    .stitch-stat-card:hover {
        border-color: rgba(93, 62, 255, 0.3);
        box-shadow: 0 0 15px rgba(59, 25, 230, 0.1);
    }

    .stitch-stat-card .value {
        font-size: 2rem;
        font-weight: 700;
        color: white;
    }

    .stitch-stat-card .label {
        font-size: 0.875rem;
        color: rgba(255, 255, 255, 0.5);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .stitch-stat-card .delta {
        font-size: 0.75rem;
        font-weight: 600;
        margin-top: 0.5rem;
    }

    .stitch-stat-card .delta.positive { color: #4ADE80; }
    .stitch-stat-card .delta.negative { color: #EF4444; }

    /* ============================================
       8. FORM FIELDS - STITCH v3 Form Kit
       ============================================ */

    /* 8.1 Text Input */
    .stTextInput > div > div, .stNumberInput > div > div, .stTextArea > div > div {
        background-color: rgba(22, 21, 33, 0.5) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 0.75rem !important;
        color: white !important;
        transition: all 0.2s ease !important;
    }

    .stTextInput > div > div:focus-within, .stNumberInput > div > div:focus-within {
        border-color: #3b19e6 !important;
        box-shadow: 0 0 0 2px rgba(59, 25, 230, 0.2), 0 0 15px rgba(59, 25, 230, 0.1) !important;
        background-color: rgba(22, 21, 33, 0.8) !important;
    }

    .stTextInput input, .stTextArea textarea, .stNumberInput input {
        color: white !important;
    }

    .stTextInput input::placeholder { color: rgba(255, 255, 255, 0.4) !important; }

    /* 8.2 Select/Dropdown */
    .stSelectbox > div > div, .stMultiSelect > div > div {
        background-color: rgba(22, 21, 33, 0.5) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 0.75rem !important;
    }

    .stSelectbox > div > div:focus-within {
        border-color: #3b19e6 !important;
        box-shadow: 0 0 15px rgba(59, 25, 230, 0.2) !important;
    }

    /* 8.3 Validation States */
    .stitch-input-success { border-color: rgba(74, 222, 128, 0.5) !important; }
    .stitch-input-warning { border-color: rgba(245, 158, 11, 0.5) !important; }
    .stitch-input-error { border-color: rgba(239, 68, 68, 0.5) !important; background: rgba(239, 68, 68, 0.05) !important; }

    /* ============================================
       9. SIDEBAR - STITCH v3 (w-72 = 288px)
       ============================================ */
    section[data-testid="stSidebar"] {
        background: rgba(17, 20, 28, 0.75) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
        min-width: 288px !important;
        width: 288px !important;
    }

    /* STITCH v3 Nav Active Style - Cosmic Glow */
    .nav-active {
        background: linear-gradient(90deg, rgba(90, 137, 246, 0.2) 0%, rgba(90, 137, 246, 0.05) 100%) !important;
        border: 1px solid rgba(90, 137, 246, 0.3) !important;
        box-shadow: 0 0 15px rgba(90, 137, 246, 0.15) !important;
        border-radius: 9999px !important;
    }

    .nav-item {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.75rem 1rem;
        border-radius: 9999px;
        color: rgba(148, 163, 184, 1);
        font-weight: 600;
        font-size: 0.875rem;
        transition: all 0.2s ease;
    }

    .nav-item:hover {
        background: rgba(255, 255, 255, 0.05);
        color: white;
    }

    .nav-item.active {
        background: linear-gradient(90deg, rgba(90, 137, 246, 0.2) 0%, rgba(90, 137, 246, 0.05) 100%);
        border: 1px solid rgba(90, 137, 246, 0.3);
        box-shadow: 0 0 15px rgba(90, 137, 246, 0.15);
        color: white;
    }

    .nav-item .icon {
        font-size: 20px;
        transition: transform 0.2s ease;
    }

    .nav-item:hover .icon {
        transform: scale(1.1);
    }

    .nav-item.active .icon {
        color: #5a89f6;
    }

    section[data-testid="stSidebar"] > div {
        min-width: 260px !important;
        width: 100% !important;
    }

    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: rgba(255, 255, 255, 0.9) !important;
        font-size: 0.9rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.1em !important;
        margin-bottom: 1rem !important;
    }

    section[data-testid="stSidebar"] h1 {
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }

    section[data-testid="stSidebar"] button {
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }

    /* Sidebar collapse button - hide text, show icon only */
    button[data-testid="stSidebarCollapseButton"],
    button[data-testid="stSidebarExpandButton"],
    [data-testid="stSidebarCollapsedControl"] button {
        font-size: 0 !important;
        width: 32px !important;
        height: 32px !important;
        min-width: 32px !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
    }

    button[data-testid="stSidebarCollapseButton"]::before,
    button[data-testid="stSidebarExpandButton"]::before,
    [data-testid="stSidebarCollapsedControl"] button::before {
        content: "☰" !important;
        font-size: 16px !important;
        color: white !important;
    }

    button[data-testid="stSidebarCollapseButton"] span,
    button[data-testid="stSidebarExpandButton"] span,
    [data-testid="stSidebarCollapsedControl"] button span {
        display: none !important;
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
       11. EXPANDER (Updated for Streamlit 1.x)
       ============================================ */
    .streamlit-expanderHeader,
    [data-testid="stExpander"] summary {
        background: rgba(30, 27, 46, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 0.75rem !important;
        color: white !important;
    }

    .streamlit-expanderContent,
    [data-testid="stExpander"] > div[data-testid="stExpanderDetails"] {
        background: rgba(30, 27, 46, 0.4) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-top: none !important;
        border-radius: 0 0 0.75rem 0.75rem !important;
    }

    /* Hide Material Icon text in expander (keyboard_arrow_right 등) */
    [data-testid="stIconMaterial"] {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        height: 0 !important;
        overflow: hidden !important;
    }

    /* Expander summary arrow replacement */
    [data-testid="stExpander"] summary {
        list-style: none !important;
    }
    [data-testid="stExpander"] summary::-webkit-details-marker {
        display: none !important;
    }
    [data-testid="stExpander"] [data-testid="stExpanderToggleIcon"] {
        display: none !important;
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
       14. CODE BLOCKS - SQL Syntax Highlighting
       ============================================ */
    code, pre, .stCode, .stCodeBlock {
        background-color: #0d1117 !important;
        color: #e6edf3 !important;
        font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace !important;
        font-size: 0.875rem !important;
        line-height: 1.6 !important;
    }

    pre {
        background-color: #0d1117 !important;
        border: 1px solid rgba(90, 137, 246, 0.2) !important;
        border-radius: 0.75rem !important;
        padding: 1.25rem !important;
        overflow-x: auto !important;
    }

    /* Streamlit Code Block Container */
    [data-testid="stCodeBlock"] {
        background-color: #0d1117 !important;
        border-radius: 0.75rem !important;
    }

    [data-testid="stCodeBlock"] pre {
        background-color: #0d1117 !important;
    }

    /* SQL Syntax Highlighting - GitHub Dark Theme */
    .hljs-keyword, .token.keyword { color: #ff7b72 !important; font-weight: 600 !important; }
    .hljs-string, .token.string { color: #a5d6ff !important; }
    .hljs-number, .token.number { color: #79c0ff !important; }
    .hljs-function, .token.function { color: #d2a8ff !important; }
    .hljs-comment, .token.comment { color: #8b949e !important; font-style: italic !important; }
    .hljs-operator, .token.operator { color: #ff7b72 !important; }
    .hljs-punctuation, .token.punctuation { color: #c9d1d9 !important; }
    .hljs-builtin, .token.builtin { color: #79c0ff !important; }
    .hljs-variable, .token.variable { color: #ffa657 !important; }
    .hljs-type, .token.class-name { color: #7ee787 !important; }

    /* SQL specific keywords */
    .language-sql .hljs-keyword { color: #ff7b72 !important; text-transform: uppercase; }
    .language-sql .hljs-built_in { color: #d2a8ff !important; }
    .language-sql .hljs-title { color: #79c0ff !important; }

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

    /* ============================================
       19. MARKDOWN HTML RENDERING FIX
       ============================================ */
    .stMarkdown div[data-testid="stMarkdownContainer"] {
        overflow: visible !important;
    }
    .stMarkdown div[data-testid="stMarkdownContainer"] > div {
        display: block !important;
    }
    .stMarkdown div[data-testid="stMarkdownContainer"] p {
        margin: 0 !important;
    }

    /* Z-Index Hierarchy */
    section[data-testid="stSidebar"] {
        z-index: 100 !important;
    }
    .stitch-header {
        z-index: 50 !important;
    }
    .stitch-card, .glass-panel {
        z-index: 10 !important;
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


# =========================================================
# STITCH Global Layout Components
# =========================================================

def render_stitch_sidebar():
    """STITCH 스타일 사이드바 렌더링 (deprecated - use render_stitch_topnav instead)."""
    pass  # Now using top navigation


def render_stitch_topnav():
    """STITCH v3 스타일 상단 네비게이션 바 렌더링. 좌측 로고 없이 네비게이션 + 시스템 상태 + Login."""
    current_page = st.session_state.get('page', 'intro')

    # 상단 네비게이션 스타일 (CSS minified) + Login 버튼 스타일
    st.markdown('''<style>
    .stitch-status{display:flex;align-items:center;gap:0.5rem;justify-content:flex-end;}
    .stitch-status-dot{width:8px;height:8px;background:#10B981;border-radius:50%;box-shadow:0 0 8px rgba(16,185,129,0.6);animation:stitch-pulse 2s infinite;}
    @keyframes stitch-pulse{0%,100%{opacity:1;}50%{opacity:0.6;}}
    .topnav-login-btn button {
        background: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        color: white !important;
        font-size: 12px !important;
        padding: 0.35rem 0.8rem !important;
        border-radius: 6px !important;
        height: auto !important;
        min-height: auto !important;
        font-weight: 500 !important;
    }
    .topnav-login-btn button:hover {
        background: rgba(255,255,255,0.15) !important;
    }
    </style>''', unsafe_allow_html=True)

    # Navigation + Status + Login
    nav_col, status_col, login_col = st.columns([8, 1, 1])

    with nav_col:
        nav_items = [
            {'id': 'intro', 'icon': '🚀', 'label': 'NovaRium'},
            {'id': 'data_lab', 'icon': '🔬', 'label': '데이터 랩'},
            {'id': 'monitor', 'icon': '📊', 'label': '모니터'},
            {'id': 'study', 'icon': '🧪', 'label': '실험 위저드'},
            {'id': 'portfolio', 'icon': '📁', 'label': '회고록'},
        ]
        cols = st.columns(len(nav_items))
        for i, item in enumerate(nav_items):
            with cols[i]:
                is_active = current_page == item['id']
                btn_type = "primary" if is_active else "secondary"
                if st.button(f"{item['label']}", key=f"topnav_{item['id']}", use_container_width=True, type=btn_type):
                    st.session_state.page = item['id']
                    st.rerun()

    with status_col:
        st.markdown('<div class="stitch-status"><div class="stitch-status-dot"></div><span style="font-size:0.8125rem;color:rgba(148,163,184,1);font-weight:500;white-space:nowrap;">시스템 정상</span></div>', unsafe_allow_html=True)

    with login_col:
        st.markdown('<div class="topnav-login-btn">', unsafe_allow_html=True)
        if st.button("Login", key="topnav_login"):
            st.session_state['show_auth_modal'] = True
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


def render_stitch_header(breadcrumb: list = None, show_search: bool = True):
    """STITCH v3 스타일 상단 헤더 렌더링. rounded-full glass + 프로필 영역."""
    if breadcrumb is None:
        breadcrumb = ['홈']

    # Breadcrumb HTML 생성 (이모지 사용)
    breadcrumb_parts = []
    for i, item in enumerate(breadcrumb):
        if i < len(breadcrumb) - 1:
            breadcrumb_parts.append(f'<span style="color:rgba(148,163,184,1);font-weight:500;">{item}</span>')
            breadcrumb_parts.append('<span style="font-size:14px;color:rgba(100,116,139,1);margin:0 4px;">›</span>')
        else:
            breadcrumb_parts.append(f'<span style="color:white;font-weight:700;">{item}</span>')
    breadcrumb_html = ''.join(breadcrumb_parts)

    # Search bar HTML (optional) - 이모지 사용
    search_html = ''
    if show_search:
        search_html = '<div style="position:relative;"><div style="position:absolute;left:12px;top:50%;transform:translateY(-50%);font-size:16px;">🔍</div><input type="text" placeholder="실험 검색..." style="height:40px;width:200px;border-radius:9999px;border:1px solid rgba(255,255,255,0.1);background:rgba(0,0,0,0.2);padding-left:36px;padding-right:16px;font-size:0.875rem;color:white;outline:none;"></div><div style="height:24px;width:1px;background:rgba(255,255,255,0.1);margin:0 8px;"></div>'

    # 알림/설정 버튼 + 프로필 트리거 (이모지 사용)
    actions_html = '<button style="width:36px;height:36px;background:rgba(255,255,255,0.05);border:none;border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer;position:relative;font-size:16px;">🔔<span style="position:absolute;top:6px;right:6px;width:8px;height:8px;background:#ef4444;border-radius:50%;border:2px solid #0B0E14;"></span></button><button style="width:36px;height:36px;background:rgba(255,255,255,0.05);border:none;border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:16px;">⚙️</button><button style="margin-left:8px;display:flex;align-items:center;gap:8px;border-radius:9999px;border:1px solid rgba(255,255,255,0.1);background:rgba(255,255,255,0.05);padding:4px 12px 4px 4px;cursor:pointer;"><div style="width:28px;height:28px;border-radius:50%;background:linear-gradient(135deg,#5a89f6,#8b5cf6);display:flex;align-items:center;justify-content:center;"><span style="font-size:12px;color:white;font-weight:700;">SJ</span></div><div style="display:flex;flex-direction:column;align-items:flex-start;"><span style="font-size:0.7rem;font-weight:700;color:white;line-height:1.2;">사용자</span><span style="font-size:0.6rem;font-weight:500;color:rgba(148,163,184,1);line-height:1.2;">분석가</span></div><span style="font-size:12px;color:rgba(148,163,184,1);">▼</span></button>'

    header_html = f'<div style="background:rgba(20,25,34,0.4);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border:1px solid rgba(255,255,255,0.08);border-radius:9999px;margin:0 0 1.5rem 0;padding:0.5rem 1rem;display:flex;align-items:center;justify-content:space-between;box-shadow:0 4px 24px rgba(0,0,0,0.2);"><div style="display:flex;align-items:center;font-size:0.875rem;">{breadcrumb_html}</div><div style="display:flex;align-items:center;gap:8px;">{search_html}{actions_html}</div></div>'
    st.markdown(header_html, unsafe_allow_html=True)


def render_stitch_page_title(title: str, subtitle: str = "", badge: str = None):
    """STITCH 스타일 페이지 타이틀 렌더링."""
    badge_html = ""
    if badge:
        badge_html = f'<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.5rem;"><div style="width:8px;height:8px;background:#5a89f6;border-radius:50%;"></div><span style="font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:#5a89f6;">{badge}</span></div>'

    subtitle_html = ""
    if subtitle:
        subtitle_html = f'<p style="margin:0;color:rgba(255,255,255,0.5);font-size:1.125rem;">{subtitle}</p>'

    title_html = f'<div style="margin-bottom:2rem;">{badge_html}<h1 style="margin:0 0 0.5rem 0;font-size:2.5rem;font-weight:700;color:white;letter-spacing:-0.02em;">{title}</h1>{subtitle_html}</div>'
    st.markdown(title_html, unsafe_allow_html=True)


def render_stitch_stat_card(label: str, value: str, delta: str = None, delta_type: str = "positive", icon: str = "📊", color: str = "primary"):
    """STITCH v3 스타일 KPI 스탯 카드. 이모지 아이콘 지원."""
    # Color mapping for icon backgrounds
    color_map = {
        "primary": {"bg": "rgba(90,137,246,0.2)", "text": "#5a89f6"},
        "purple": {"bg": "rgba(139,92,246,0.2)", "text": "#a78bfa"},
        "success": {"bg": "rgba(16,185,129,0.2)", "text": "#10B981"},
        "warning": {"bg": "rgba(245,158,11,0.2)", "text": "#F59E0B"},
        "error": {"bg": "rgba(239,68,68,0.2)", "text": "#EF4444"},
    }
    icon_color = color_map.get(color, color_map["primary"])

    # Delta HTML (이모지 사용)
    delta_html = ""
    if delta:
        delta_arrow = "↑" if delta_type == "positive" else "↓"
        delta_color = "#10B981" if delta_type == "positive" else "#EF4444"
        delta_html = f'<div style="font-size:0.75rem;color:{delta_color};display:flex;align-items:center;gap:4px;"><span>{delta_arrow}</span><span>{delta}</span></div>'

    card_html = f'<div style="background:rgba(20,25,34,0.4);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border:1px solid rgba(255,255,255,0.08);border-radius:1.5rem;padding:1.5rem;position:relative;overflow:hidden;"><div style="position:absolute;top:0;right:0;padding:1rem;opacity:0.15;font-size:48px;">{icon}</div><div style="display:flex;align-items:center;gap:12px;margin-bottom:1rem;"><div style="padding:8px;border-radius:8px;background:{icon_color["bg"]};font-size:20px;">{icon}</div><span style="font-size:0.875rem;font-weight:500;color:rgba(203,213,225,1);">{label}</span></div><div style="font-size:2.25rem;font-weight:700;color:white;margin-bottom:4px;">{value}</div>{delta_html}</div>'
    st.markdown(card_html, unsafe_allow_html=True)


def render_stitch_card(title: str = None, subtitle: str = None, content: str = "", padding: str = "1.5rem"):
    """STITCH 스타일 기본 카드."""
    header_html = ""
    if title:
        subtitle_html = f'<p style="margin:0;font-size:0.875rem;color:rgba(255,255,255,0.5);">{subtitle}</p>' if subtitle else ""
        header_html = f'<div style="margin-bottom:1.5rem;"><h3 style="margin:0;font-size:1.125rem;font-weight:700;color:white;">{title}</h3>{subtitle_html}</div>'

    card_html = f'<div style="background:rgba(20,25,34,0.4);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border:1px solid rgba(255,255,255,0.08);border-radius:2rem;padding:{padding};position:relative;overflow:hidden;transition:all 0.3s ease;">{header_html}{content}</div>'
    st.markdown(card_html, unsafe_allow_html=True)


def stitch_grid_start(columns: int = 3):
    """
    STITCH 그리드 시작. stitch_grid_end()와 함께 사용.

    Args:
        columns: 컬럼 수 (2 또는 3)
    """
    grid_class = f"stitch-grid-{columns}"
    st.markdown(f'<div class="{grid_class}">', unsafe_allow_html=True)


def stitch_grid_end():
    """STITCH 그리드 종료."""
    st.markdown('</div>', unsafe_allow_html=True)


def stitch_content_start():
    """STITCH 메인 콘텐츠 영역 시작. Streamlit 사이드바와 함께 사용."""
    # Streamlit 기본 레이아웃 사용 - 추가 wrapper 불필요
    pass


def stitch_content_end():
    """STITCH 메인 콘텐츠 영역 종료."""
    pass


def render_isolated_html(html_content: str, height: int = 100):
    """Shadow DOM 격리 렌더링을 위한 st.components.v1.html wrapper."""
    full_html = f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>*{{margin:0;padding:0;box-sizing:border-box;font-family:'Inter',sans-serif;}}body{{background:transparent;}}</style></head><body>{html_content}</body></html>'''
    components.html(full_html, height=height, scrolling=False)
