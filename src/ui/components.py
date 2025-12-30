import streamlit as st

# =========================================================
# NovaRium UI Components - Cosmic Glass Theme v2.0
# STITCH Design System Integration
# =========================================================

def apply_custom_css():
    """
    Apply global Cosmic Glass CSS styling to the Streamlit app.
    Based on STITCH Design System v2.0 + v3.0
    """
    st.markdown("""
<style>
    /* ============================================
       1. FONTS & GLOBAL RESET (강화된 버전)
       ============================================ */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;900&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');

    /* 모든 요소에 폰트 강제 적용 */
    *, *::before, *::after {
        font-family: 'Inter', 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    html, body, [class*="css"], .stApp, .main, section[data-testid="stSidebar"] {
        font-family: 'Inter', 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* ============================================
       2. COSMIC BACKGROUND (강화된 버전)
       ============================================ */
    /* 최상위 앱 컨테이너 */
    .stApp, .stApp > header, .stApp > section {
        background-color: #0B0E14 !important;
        background-image:
            radial-gradient(at 0% 0%, rgba(90, 137, 246, 0.15) 0px, transparent 50%),
            radial-gradient(at 100% 100%, rgba(124, 58, 237, 0.1) 0px, transparent 50%) !important;
        color: #ffffff !important;
    }

    /* Main 컨테이너 - STITCH 레이아웃을 위해 여백 제거 */
    .main .block-container {
        background: transparent !important;
        padding: 0 !important;
        max-width: 100% !important;
    }

    /* Streamlit 기본 여백 완전 제거 */
    .stApp > header + div {
        padding: 0 !important;
    }

    div[data-testid="stAppViewBlockContainer"] {
        padding: 0 !important;
        max-width: 100% !important;
    }

    /* STITCH 레이아웃 컨테이너 */
    .stitch-layout {
        display: flex;
        min-height: 100vh;
        width: 100%;
    }

    /* STITCH 사이드바 - 고정 너비 288px (w-72) */
    .stitch-sidebar {
        width: 288px;
        min-width: 288px;
        background: rgba(17, 20, 28, 0.75);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
        padding: 1.5rem;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        position: fixed;
        left: 0;
        top: 0;
        height: 100vh;
        z-index: 100;
    }

    /* STITCH 메인 콘텐츠 영역 */
    .stitch-main {
        flex: 1;
        margin-left: 288px;
        display: flex;
        flex-direction: column;
        min-height: 100vh;
        overflow: hidden;
    }

    /* STITCH 상단 헤더 - rounded-full glass */
    .stitch-header {
        background: rgba(20, 25, 34, 0.4);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 9999px;
        margin: 1rem 1.5rem 0.5rem 1.5rem;
        padding: 0.75rem 1.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        position: sticky;
        top: 0;
        z-index: 50;
    }

    /* STITCH 스크롤 콘텐츠 */
    .stitch-content {
        flex: 1;
        overflow-y: auto;
        padding: 1.5rem;
    }

    .stitch-content-inner {
        max-width: 1280px;
        margin: 0 auto;
    }

    /* STITCH 그리드 시스템 */
    .stitch-grid-3 {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1.5rem;
        margin-bottom: 2rem;
    }

    .stitch-grid-2 {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1.5rem;
        margin-bottom: 2rem;
    }

    @media (max-width: 1024px) {
        .stitch-grid-3 { grid-template-columns: repeat(2, 1fr); }
    }

    @media (max-width: 768px) {
        .stitch-grid-3, .stitch-grid-2 { grid-template-columns: 1fr; }
        .stitch-sidebar { display: none; }
        .stitch-main { margin-left: 0; }
    }

    /* STITCH 카드 - rounded-3xl (1.5rem) */
    .stitch-card {
        background: rgba(20, 25, 34, 0.4);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 1.5rem;
        padding: 1.5rem;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
    }

    .stitch-card:hover {
        background: rgba(255, 255, 255, 0.05);
        border-color: rgba(255, 255, 255, 0.15);
    }

    /* STITCH 네비게이션 링크 */
    .stitch-nav-link {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.75rem 1rem;
        border-radius: 9999px;
        color: rgba(255, 255, 255, 0.6);
        font-size: 0.875rem;
        font-weight: 600;
        text-decoration: none;
        transition: all 0.2s ease;
        cursor: pointer;
        border: 1px solid transparent;
    }

    .stitch-nav-link:hover {
        background: rgba(255, 255, 255, 0.05);
        color: white;
    }

    .stitch-nav-link.active {
        background: linear-gradient(90deg, rgba(90, 137, 246, 0.2) 0%, rgba(90, 137, 246, 0.05) 100%);
        border: 1px solid rgba(90, 137, 246, 0.3);
        box-shadow: 0 0 15px rgba(90, 137, 246, 0.15);
        color: white;
    }

    /* STITCH 페이지 타이틀 */
    .stitch-page-title {
        margin-bottom: 2rem;
    }

    .stitch-page-title h1 {
        font-size: 1.875rem !important;
        font-weight: 700 !important;
        color: white !important;
        margin-bottom: 0.5rem !important;
    }

    .stitch-page-title p {
        color: rgba(255, 255, 255, 0.6) !important;
        font-size: 1rem !important;
    }

    /* 모든 section 요소 */
    section[data-testid="stMain"],
    div[data-testid="stAppViewContainer"],
    .stApp > div:first-child {
        background-color: #0B0E14 !important;
        background-image:
            radial-gradient(at 0% 0%, rgba(90, 137, 246, 0.15) 0px, transparent 50%),
            radial-gradient(at 100% 100%, rgba(124, 58, 237, 0.1) 0px, transparent 50%) !important;
    }

    /* Hide Streamlit default header/footer */
    header[data-testid="stHeader"] {
        background: transparent !important;
        backdrop-filter: none !important;
    }
    #MainMenu {visibility: hidden !important; display: none !important;}
    footer {visibility: hidden !important; display: none !important;}
    .stDeployButton {display: none !important;}

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
       6. BUTTON STYLES (STITCH v3 강화)
       ============================================ */
    /* 모든 버튼 기본 스타일 */
    button, .stButton > button, [data-testid="baseButton-secondary"] {
        background: rgba(20, 25, 34, 0.4) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        color: white !important;
        border-radius: 9999px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        font-family: 'Inter', 'Plus Jakarta Sans', sans-serif !important;
        transition: all 0.3s ease !important;
        cursor: pointer !important;
    }

    .stButton > button:hover, [data-testid="baseButton-secondary"]:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
    }

    .stButton > button:active {
        transform: translateY(0) scale(0.98) !important;
    }

    /* Primary Button - 보라색 그라데이션 + 글로우 */
    [data-testid="baseButton-primary"],
    div[data-testid="stButton"] button[kind="primary"],
    .stButton > button[kind="primary"],
    button[kind="primary"] {
        background: linear-gradient(135deg, #5a89f6 0%, #7c3aed 100%) !important;
        border: none !important;
        box-shadow: 0 0 20px rgba(90, 137, 246, 0.4) !important;
        color: white !important;
    }

    [data-testid="baseButton-primary"]:hover,
    div[data-testid="stButton"] button[kind="primary"]:hover,
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 0 30px rgba(90, 137, 246, 0.6) !important;
        transform: translateY(-2px) scale(1.02) !important;
    }

    /* Nav button active state - Cosmic Glow */
    .nav-active {
        background: linear-gradient(90deg, rgba(90, 137, 246, 0.2) 0%, rgba(90, 137, 246, 0.05) 100%) !important;
        border: 1px solid rgba(90, 137, 246, 0.3) !important;
        box-shadow: 0 0 15px rgba(90, 137, 246, 0.15) !important;
    }

    /* STITCH 버튼 클래스 - Primary (그라데이션 + 글로우) */
    .stitch-btn-primary {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        padding: 0.75rem 1.5rem;
        background: linear-gradient(135deg, #3b19e6 0%, #6d4aff 100%);
        border: none;
        border-radius: 9999px;
        color: white;
        font-size: 0.875rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
    }

    .stitch-btn-primary:hover {
        background: linear-gradient(135deg, #4c2af5 0%, #7e5bff 100%);
        box-shadow: 0 0 20px rgba(59, 25, 230, 0.5);
        transform: translateY(-2px);
    }

    .stitch-btn-primary:active {
        background: linear-gradient(135deg, #2a0ab6 0%, #5230e5 100%);
        transform: scale(0.98);
    }

    /* STITCH 버튼 클래스 - Secondary (Ghost 스타일) */
    .stitch-btn-secondary {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        padding: 0.75rem 1.5rem;
        background: transparent;
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 9999px;
        color: white;
        font-size: 0.875rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
    }

    .stitch-btn-secondary:hover {
        background: rgba(59, 25, 230, 0.1);
        border-color: #6d4aff;
        box-shadow: 0 0 15px rgba(59, 25, 230, 0.15);
    }

    .stitch-btn-secondary:active {
        background: rgba(59, 25, 230, 0.2);
        border-color: #3b19e6;
        transform: scale(0.98);
    }

    /* STITCH 버튼 클래스 - Tertiary (텍스트 링크) */
    .stitch-btn-tertiary {
        background: none;
        border: none;
        color: rgba(255, 255, 255, 0.7);
        font-size: 0.875rem;
        font-weight: 500;
        cursor: pointer;
        transition: color 0.2s ease;
    }

    .stitch-btn-tertiary:hover {
        color: white;
        text-decoration: underline;
        text-decoration-color: #6d4aff;
        text-underline-offset: 4px;
    }

    /* STITCH 아이콘 버튼 */
    .stitch-btn-icon {
        width: 2.5rem;
        height: 2.5rem;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 9999px;
        color: white;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .stitch-btn-icon:hover {
        background: #3b19e6;
        border-color: transparent;
        box-shadow: 0 0 15px rgba(59, 25, 230, 0.4);
        transform: scale(1.1);
    }

    /* STITCH 스탯 카드 추가 스타일 */
    .stitch-stat-card {
        background: rgba(20, 25, 34, 0.4);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 1.5rem;
        padding: 1.5rem;
        transition: all 0.3s ease;
    }

    .stitch-stat-card:hover {
        background: rgba(255, 255, 255, 0.05);
        border-color: rgba(255, 255, 255, 0.15);
    }

    .stitch-stat-card .icon-container {
        width: 3rem;
        height: 3rem;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 0.75rem;
        margin-bottom: 1rem;
    }

    .stitch-stat-card .icon-container.primary {
        background: linear-gradient(135deg, rgba(90, 137, 246, 0.2), rgba(90, 137, 246, 0.05));
    }

    .stitch-stat-card .icon-container.success {
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(34, 197, 94, 0.05));
    }

    .stitch-stat-card .icon-container.warning {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(245, 158, 11, 0.05));
    }

    .stitch-stat-card .icon-container.error {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(239, 68, 68, 0.05));
    }

    .stitch-stat-card .value {
        font-size: 1.875rem;
        font-weight: 700;
        color: white;
        margin-bottom: 0.25rem;
    }

    .stitch-stat-card .label {
        font-size: 0.875rem;
        color: rgba(255, 255, 255, 0.6);
    }

    .stitch-stat-card .delta {
        font-size: 0.75rem;
        font-weight: 500;
        margin-top: 0.5rem;
    }

    .stitch-stat-card .delta.positive {
        color: #22c55e;
    }

    .stitch-stat-card .delta.negative {
        color: #ef4444;
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


# =========================================================
# STITCH Global Layout Components
# =========================================================

def render_stitch_sidebar():
    """
    STITCH 스타일 사이드바 렌더링.
    고정 너비 288px, glass-panel-heavy 스타일.
    """
    current_page = st.session_state.get('page', 'intro')

    # 네비게이션 아이템 정의
    nav_items = [
        {'id': 'intro', 'icon': 'rocket_launch', 'label': 'NovaRium', 'filled': True},
        {'id': 'data_lab', 'icon': 'science', 'label': '데이터 랩', 'filled': False},
        {'id': 'monitor', 'icon': 'monitoring', 'label': '모니터', 'filled': False},
        {'id': 'study', 'icon': 'school', 'label': '실험 위저드', 'filled': False},
        {'id': 'portfolio', 'icon': 'folder_open', 'label': '회고록', 'filled': False},
    ]

    # 사이드바 HTML 생성
    nav_links_html = ""
    for item in nav_items:
        is_active = current_page == item['id']
        active_class = "active" if is_active else ""
        fill_style = "font-variation-settings: 'FILL' 1;" if (is_active or item['filled']) else ""
        icon_color = "#5a89f6" if is_active else "inherit"

        nav_links_html += f'''
        <div class="stitch-nav-link {active_class}" data-page="{item['id']}" style="margin-bottom: 0.5rem;">
            <span class="material-symbols-outlined" style="font-size: 20px; color: {icon_color}; {fill_style}">{item['icon']}</span>
            <span>{item['label']}</span>
        </div>
        '''

    sidebar_html = f'''
    <div class="stitch-sidebar">
        <div style="display: flex; flex-direction: column; gap: 2rem;">
            <!-- 브랜딩 -->
            <div style="display: flex; align-items: center; gap: 1rem; padding: 0 0.5rem;">
                <div style="width: 40px; height: 40px; background: linear-gradient(135deg, #5a89f6 0%, #7c3aed 100%); border-radius: 0.75rem; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 20px rgba(90, 137, 246, 0.4);">
                    <span class="material-symbols-outlined" style="color: white; font-size: 24px;">rocket_launch</span>
                </div>
                <div>
                    <h1 style="margin: 0; font-size: 1.125rem; font-weight: 700; color: white;">NovaRium</h1>
                    <p style="margin: 0; font-size: 0.75rem; color: rgba(255,255,255,0.5);">Analyst Platform</p>
                </div>
            </div>
            <!-- 네비게이션 -->
            <nav style="display: flex; flex-direction: column; gap: 0.25rem;">
                {nav_links_html}
            </nav>
        </div>
        <!-- 하단 시스템 상태 -->
        <div style="display: flex; flex-direction: column; gap: 1rem;">
            <div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%); border: 1px solid rgba(255,255,255,0.05); border-radius: 1rem; padding: 1rem;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.5rem;">
                    <span style="font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #93c5fd;">시스템 상태</span>
                    <div style="width: 8px; height: 8px; background: #22c55e; border-radius: 50%; box-shadow: 0 0 8px rgba(34, 197, 94, 0.6);"></div>
                </div>
                <p style="margin: 0; font-size: 0.75rem; color: rgba(255,255,255,0.5);">모든 시스템 정상 작동 중</p>
            </div>
        </div>
    </div>
    '''
    st.markdown(sidebar_html, unsafe_allow_html=True)


def render_stitch_header(breadcrumb: list = None, show_search: bool = True):
    """
    STITCH 스타일 상단 헤더 렌더링.
    rounded-full glass 스타일.

    Args:
        breadcrumb: 브레드크럼 리스트 예: ['Home', 'Data Lab']
        show_search: 검색창 표시 여부
    """
    if breadcrumb is None:
        breadcrumb = ['Home']

    # 브레드크럼 HTML
    breadcrumb_html = ""
    for i, item in enumerate(breadcrumb):
        if i < len(breadcrumb) - 1:
            breadcrumb_html += f'<span style="color: rgba(255,255,255,0.4);">{item}</span>'
            breadcrumb_html += '<span class="material-symbols-outlined" style="font-size: 16px; color: rgba(255,255,255,0.2);">chevron_right</span>'
        else:
            breadcrumb_html += f'<span style="color: white; font-weight: 600;">{item}</span>'

    search_html = ""
    if show_search:
        search_html = '''
        <div style="position: relative; display: none;" class="md-show">
            <span class="material-symbols-outlined" style="position: absolute; left: 12px; top: 50%; transform: translateY(-50%); font-size: 20px; color: rgba(255,255,255,0.4);">search</span>
            <input type="text" placeholder="실험 검색..." style="height: 40px; width: 200px; background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.1); border-radius: 9999px; padding-left: 40px; padding-right: 16px; color: white; font-size: 0.875rem; outline: none;" />
        </div>
        '''

    header_html = f'''
    <div class="stitch-header">
        <div style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.875rem;">
            {breadcrumb_html}
        </div>
        <div style="display: flex; align-items: center; gap: 1rem;">
            {search_html}
            <button style="width: 40px; height: 40px; background: rgba(255,255,255,0.05); border: none; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; position: relative;">
                <span class="material-symbols-outlined" style="font-size: 20px; color: rgba(255,255,255,0.7);">notifications</span>
                <span style="position: absolute; top: 10px; right: 10px; width: 8px; height: 8px; background: #ef4444; border-radius: 50%; border: 2px solid #0B0E14;"></span>
            </button>
            <button style="width: 40px; height: 40px; background: rgba(255,255,255,0.05); border: none; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer;">
                <span class="material-symbols-outlined" style="font-size: 20px; color: rgba(255,255,255,0.7);">settings</span>
            </button>
        </div>
    </div>
    '''
    st.markdown(header_html, unsafe_allow_html=True)


def render_stitch_page_title(title: str, subtitle: str = "", badge: str = None):
    """
    STITCH 스타일 페이지 타이틀 렌더링.

    Args:
        title: 페이지 제목
        subtitle: 부제목
        badge: 뱃지 텍스트 (예: "Live Dashboard")
    """
    badge_html = ""
    if badge:
        badge_html = f'''
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
            <div style="width: 8px; height: 8px; background: #5a89f6; border-radius: 50%; animation: pulse 2s infinite;"></div>
            <span style="font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #5a89f6;">{badge}</span>
        </div>
        '''

    subtitle_html = ""
    if subtitle:
        subtitle_html = f'<p style="margin: 0; color: rgba(255,255,255,0.5); font-size: 1.125rem;">{subtitle}</p>'

    title_html = f'''
    <div class="stitch-page-title">
        {badge_html}
        <h1 style="margin: 0 0 0.5rem 0; font-size: 2.5rem; font-weight: 700; color: white; letter-spacing: -0.02em;">{title}</h1>
        {subtitle_html}
    </div>
    '''
    st.markdown(title_html, unsafe_allow_html=True)


def render_stitch_stat_card(label: str, value: str, delta: str = None, delta_type: str = "positive", icon: str = "analytics", color: str = "primary"):
    """
    STITCH 스타일 KPI 스탯 카드.

    Args:
        label: 지표 라벨
        value: 지표 값
        delta: 변화량 (예: "+12%")
        delta_type: "positive" or "negative"
        icon: Material Symbols 아이콘명
        color: "primary", "success", "warning", "error"
    """
    color_map = {
        "primary": "#5a89f6",
        "success": "#22c55e",
        "warning": "#f59e0b",
        "error": "#ef4444",
        "purple": "#8b5cf6"
    }
    accent_color = color_map.get(color, "#5a89f6")

    delta_html = ""
    if delta:
        delta_bg = "rgba(34, 197, 94, 0.1)" if delta_type == "positive" else "rgba(239, 68, 68, 0.1)"
        delta_border = "rgba(34, 197, 94, 0.2)" if delta_type == "positive" else "rgba(239, 68, 68, 0.2)"
        delta_color = "#22c55e" if delta_type == "positive" else "#ef4444"
        delta_icon = "trending_up" if delta_type == "positive" else "trending_down"
        delta_html = f'''
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-top: 1rem;">
            <div style="display: flex; align-items: center; gap: 0.25rem; padding: 0.25rem 0.5rem; background: {delta_bg}; border: 1px solid {delta_border}; border-radius: 9999px;">
                <span class="material-symbols-outlined" style="font-size: 14px; color: {delta_color};">{delta_icon}</span>
                <span style="font-size: 0.75rem; font-weight: 700; color: {delta_color};">{delta}</span>
            </div>
            <span style="font-size: 0.75rem; color: rgba(255,255,255,0.4);">vs. 지난주</span>
        </div>
        '''

    card_html = f'''
    <div class="stitch-card" style="border-radius: 2rem;">
        <div style="position: absolute; top: 0; right: 0; padding: 1.5rem; opacity: 0.5;">
            <span class="material-symbols-outlined" style="font-size: 48px; color: rgba(255,255,255,0.1);">{icon}</span>
        </div>
        <div style="position: relative; z-index: 10;">
            <p style="margin: 0; font-size: 0.875rem; color: rgba(255,255,255,0.5);">{label}</p>
            <h3 style="margin: 0.25rem 0 0 0; font-size: 2rem; font-weight: 700; color: white;">{value}</h3>
            {delta_html}
        </div>
    </div>
    '''
    st.markdown(card_html, unsafe_allow_html=True)


def render_stitch_card(title: str = None, subtitle: str = None, content: str = "", padding: str = "1.5rem"):
    """
    STITCH 스타일 기본 카드.

    Args:
        title: 카드 제목
        subtitle: 부제목
        content: 내부 HTML 콘텐츠
        padding: 패딩 값
    """
    header_html = ""
    if title:
        subtitle_html = f'<p style="margin: 0; font-size: 0.875rem; color: rgba(255,255,255,0.5);">{subtitle}</p>' if subtitle else ""
        header_html = f'''
        <div style="margin-bottom: 1.5rem;">
            <h3 style="margin: 0; font-size: 1.125rem; font-weight: 700; color: white;">{title}</h3>
            {subtitle_html}
        </div>
        '''

    card_html = f'''
    <div class="stitch-card" style="padding: {padding}; border-radius: 2rem;">
        {header_html}
        {content}
    </div>
    '''
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
    """STITCH 메인 콘텐츠 영역 시작."""
    st.markdown('''
    <div class="stitch-main">
        <div class="stitch-content">
            <div class="stitch-content-inner">
    ''', unsafe_allow_html=True)


def stitch_content_end():
    """STITCH 메인 콘텐츠 영역 종료."""
    st.markdown('</div></div></div>', unsafe_allow_html=True)
