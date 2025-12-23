import streamlit as st

def apply_custom_css():
    """
    Apply global Cosmic Glass CSS styling to the Streamlit app.
    """
    st.markdown("""
<style>
    /* 1. Fonts & Global Reset */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* 2. Background (Deep Cosmic Dark) */
    .stApp {
        background-color: #0d0d1a !important;
        color: #ffffff !important;
    }
    
    /* 3. Glass Cards (The 'Bento' feel) */
    div[data-testid="stContainer"] {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
    }
    div[data-testid="stContainer"]:hover {
        border-color: rgba(255, 255, 255, 0.2);
        box-shadow: 0 8px 32px 0 rgba(139, 92, 246, 0.1);
    }

    /* 4. Typography Override */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }
    p, li, label, .stMarkdown {
        color: rgba(255, 255, 255, 0.7) !important;
    }
    
    /* 5. Inputs & Widgets */
    .stTextInput>div>div, .stNumberInput>div>div, .stSelectbox>div>div, .stTextArea>div>div {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px;
    }
    .stTextInput>div>div:focus-within {
        border-color: #818CF8 !important;
        box-shadow: 0 0 0 2px rgba(129, 140, 248, 0.2);
    }
    
    /* 6. Buttons */
    .stButton>button {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: white;
        border-radius: 30px; /* Pill shape */
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background: rgba(255, 255, 255, 0.1);
        border-color: #818CF8;
        color: #818CF8;
        transform: translateY(-2px);
    }
    /* Primary Button Gradient */
    div[data-testid="stButton"] button[kind="primary"] {
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%); /* Indigo to Violet */
        border: none;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
    }
    div[data-testid="stButton"] button[kind="primary"]:hover {
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.6);
    }
    
    /* 7. Educational Guide Styling */
    .edu-guide {
        background: linear-gradient(90deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.05) 100%);
        border-left: 4px solid #8B5CF6;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        margin-bottom: 2rem;
    }
    .edu-title {
        color: #A78BFA; /* Light Purple */
        font-weight: 700;
        font-size: 0.95rem;
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 4px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .edu-content {
        color: rgba(255, 255, 255, 0.8) !important;
        font-size: 0.95rem;
        line-height: 1.5;
    }

    /* 8. Big Stats */
    .big-stat {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(to right, #ffffff, #94a3b8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* 9. Progress Bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #6366F1, #EC4899);
    }
</style>
""", unsafe_allow_html=True)

def edu_guide(title, content):
    """
    Render an educational guide box.
    """
    st.markdown(f"""
    <div class="edu-guide">
        <div class="edu-title"><span style="font-size:1.2em">💡</span> {title}</div>
        <div class="edu-content">{content}</div>
    </div>
    """, unsafe_allow_html=True)

def render_navbar():
    """
    Render top navigation bar (Header).
    Handles page switching via session state.
    """
    c_logo, c_nav = st.columns([1, 4])
    with c_logo:
        if st.button("🌌 NovaRium", type="secondary", use_container_width=True):
            st.session_state['page'] = 'intro'
            st.rerun()

    with c_nav:
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            if st.button("🔍 모니터링 (Monitor)", type="primary" if st.session_state['page']=='monitor' else "secondary", use_container_width=True):
                st.session_state['page'] = 'monitor'
                st.rerun()
        with c2:
            if st.button("🚀 마스터 클래스 (Lab)", type="primary" if st.session_state['page']=='study' else "secondary", use_container_width=True):
                st.session_state['page'] = 'study'
                st.rerun()
        with c3:
            if st.button("📚 회고록 (Retro)", type="primary" if st.session_state['page']=='portfolio' else "secondary", use_container_width=True):
                st.session_state['page'] = 'portfolio'
                st.rerun()

def render_step_progress(steps, current_step):
    """
    Render wizard progress steps (Nebula Style).
    """
    cols = st.columns(len(steps))
    for i, s in enumerate(steps):
        is_active = (i + 1 == current_step)
        color = "#8B5CF6" if is_active else "rgba(255,255,255,0.2)"
        text_color = "white" if is_active else "rgba(255,255,255,0.4)"
        weight = "700" if is_active else "400"
        shadow = '0 0 10px #8B5CF6' if is_active else 'none'
        
        cols[i].markdown(f"""
        <div style="text-align:center;">
            <div style="height:4px; width:100%; background:{color}; border-radius:2px; margin-bottom:8px; box-shadow:{shadow}"></div>
            <span style="color:{text_color}; font-weight:{weight}; font-size:0.9rem;">{s}</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
