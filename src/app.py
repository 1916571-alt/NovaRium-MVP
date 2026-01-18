"""
NovaRium Edu - Main Application
A/B Testing Simulator for Data Analysts

This is the main entry point that handles routing between pages.
Each page is implemented in src/ui/pages/ for better maintainability.
"""
import streamlit as st

import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import UI components and pages
from src.ui import components as ui
from src.ui.pages import intro, data_lab, dashboard, experiment, portfolio


def main():
    """Main application entry point."""
    # Page Config
    st.set_page_config(
        page_title="NovaRium Edu",
        page_icon="🌌",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Initialize Session State
    _init_session_state()

    # Apply Styles & Header
    ui.apply_custom_css()
    ui.render_navbar()

    st.write("")  # Spacer

    # Route to appropriate page
    _route_page()


def _init_session_state():
    """Initialize session state variables."""
    if 'page' not in st.session_state:
        st.session_state['page'] = 'data_lab'  # Default to Data Lab
    if 'step' not in st.session_state:
        st.session_state['step'] = 1
    if 'custom_metrics' not in st.session_state:
        st.session_state['custom_metrics'] = []


def _route_page():
    """Route to the appropriate page based on session state."""
    page = st.session_state['page']

    if page == 'intro':
        intro.render()
    elif page == 'data_lab':
        data_lab.render()
    elif page == 'monitor':
        dashboard.render()
    elif page == 'study':
        experiment.render()
    elif page == 'portfolio':
        portfolio.render()
    else:
        # Default fallback
        data_lab.render()


if __name__ == "__main__":
    main()
