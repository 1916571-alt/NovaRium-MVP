"""
Experiment Wizard Module.

This module provides a step-by-step experiment wizard for A/B testing.
Each step is implemented in a separate module for maintainability.

Steps:
    1. Hypothesis (step1_hypothesis): Define target and variables
    2. Design (step2_design): Traffic split and sample size calculation
    3. Collection (step3_collection): Run agent swarm simulation
    4. Analysis (step4_analysis): Statistical analysis and decision making
"""
import streamlit as st

from src.ui import components as ui
from src.ui.pages.experiment import step1_hypothesis
from src.ui.pages.experiment import step2_design
from src.ui.pages.experiment import step3_collection
from src.ui.pages.experiment import step4_analysis
from src.ui.pages.experiment.constants import PAGE_MAP, METRICS_DB

# Step labels for progress indicator
STEP_LABELS = ["1. Hypothesis", "2. Design", "3. Collection", "4. Analysis"]


__all__ = [
    'render',
    'PAGE_MAP',
    'METRICS_DB',
    'step1_hypothesis',
    'step2_design',
    'step3_collection',
    'step4_analysis',
]


def render():
    """
    Render the experiment wizard based on current step.

    Routes to the appropriate step module based on session state.
    Defaults to step 1 if no step is set.
    """
    # Initialize step if not set
    if 'step' not in st.session_state:
        st.session_state['step'] = 1

    current_step = st.session_state.get('step', 1)

    # Render progress indicator
    ui.render_step_progress(STEP_LABELS, current_step)

    # Route to appropriate step
    if current_step == 1:
        step1_hypothesis.render()
    elif current_step == 2:
        step2_design.render()
    elif current_step == 3:
        step3_collection.render()
    elif current_step == 4:
        step4_analysis.render()
    else:
        # Fallback to step 1
        st.session_state['step'] = 1
        step1_hypothesis.render()


def get_current_step() -> int:
    """Get the current wizard step."""
    return st.session_state.get('step', 1)


def set_step(step: int) -> None:
    """Set the wizard step (1-4)."""
    if 1 <= step <= 4:
        st.session_state['step'] = step


def reset_wizard() -> None:
    """Reset the wizard to step 1 and clear experiment state."""
    keys_to_clear = [
        'step', 'hypothesis', 'metric', 'guardrails', 'min_effect',
        'guard_metric', 'exp_config', 'n', 'total_needed', 'split',
        'current_run_id', 'current_weight', 'p_dist', 'target',
        'builder_page', 'builder_comp', 'exp_variant_data',
        'session_guard_threshold', 'temp_hypo', 'last_live_chart',
        'last_loop_count', 'sim_process', 'sim_stop_requested',
        'show_segment_sql'
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

    st.session_state['step'] = 1
