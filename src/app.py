"""
NovaRium Edu - Main Application Entry Point

A data analysis education platform for A/B testing and experimentation.
This module handles app configuration, routing, and global state management.
"""
import streamlit as st
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Kill old Streamlit instances on different ports (Windows only)
if os.name == 'nt':
    import subprocess
    try:
        for port in [8501, 8502, 8503]:
            result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    pid = parts[-1]
                    current_pid = os.getpid()
                    if pid.isdigit() and int(pid) != current_pid:
                        subprocess.run(['taskkill', '//F', '//PID', pid], capture_output=True)
    except Exception:
        pass

# Import core modules
from src.core import stats as al
from src.ui import components as ui

# Import page modules
from src.ui.pages import intro
from src.ui.pages import data_lab
from src.ui.pages import dashboard
from src.ui.pages import experiment
from src.ui.pages import portfolio


# =========================================================
# Environment Configuration
# =========================================================

def _get_env(key: str, default: str = '') -> str:
    """
    Get environment variable with Streamlit secrets priority.
    1. Check st.secrets first (Streamlit Cloud)
    2. Fall back to os.getenv (local/Render)
    """
    try:
        if hasattr(st, 'secrets') and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.getenv(key, default)


TARGET_APP_URL = _get_env('TARGET_APP_URL', 'http://localhost:8000')


# =========================================================
# Page Configuration
# =========================================================

st.set_page_config(
    page_title="NovaRium Edu",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# =========================================================
# Session State Initialization
# =========================================================

def _init_session_state():
    """Initialize session state with default values."""
    defaults = {
        'page': 'intro',
        'step': 1,
        'custom_metrics': [],
        'use_db_coordination': True,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


_init_session_state()


# =========================================================
# Apply Styles & Header
# =========================================================

ui.apply_custom_css()
ui.render_navbar()
st.write("")  # Spacer


# =========================================================
# Global Sidebar: System Settings
# =========================================================

def _render_system_sidebar():
    """Render system settings in sidebar."""
    with st.sidebar:
        st.markdown("---")
        st.markdown("### ⚙️ 시스템 설정")

        use_coordination = st.checkbox(
            "🔄 DB 협조 모드",
            value=st.session_state.get('use_db_coordination', True),
            help="Target App과 DB 연결을 조율합니다."
        )
        st.session_state['use_db_coordination'] = use_coordination

        if use_coordination:
            st.caption("✅ 권장: Target App과 DB 조율")
        else:
            st.warning("⚠️ 레거시 모드")
            st.caption("Target App 미실행 시만 사용")


_render_system_sidebar()


# =========================================================
# Page Router
# =========================================================

PAGE_REGISTRY = {
    'intro': intro.render,
    'data_lab': data_lab.render,
    'monitor': dashboard.render,
    'study': experiment.render,
    'portfolio': portfolio.render,
}


def _route_page():
    """Route to the appropriate page based on session state."""
    current_page = st.session_state.get('page', 'intro')

    if current_page in PAGE_REGISTRY:
        PAGE_REGISTRY[current_page]()
    else:
        # Fallback to intro
        st.session_state['page'] = 'intro'
        intro.render()


# =========================================================
# Main Entry Point
# =========================================================

if __name__ == "__main__":
    _route_page()
else:
    # When imported by Streamlit
    _route_page()
