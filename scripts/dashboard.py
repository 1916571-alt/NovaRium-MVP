import streamlit as st
import duckdb
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import hashlib
from scipy import stats
from datetime import datetime, timedelta
import streamlit.components.v1 as components

# Page Config
st.set_page_config(
    page_title="NovaRium Edu",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Constants
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'novarium_local.db')

@st.cache_resource
def get_connection():
    return duckdb.connect(DB_PATH)

def run_query(query, con):
    try:
        return con.execute(query).df()
    except Exception as e:
        return str(e)

# --- COSMIC GLASS CSS ---
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

# --- Helper Functions ---
def edu_guide(title, content):
    st.markdown(f"""
    <div class="edu-guide">
        <div class="edu-title"><span style="font-size:1.2em">💡</span> {title}</div>
        <div class="edu-content">{content}</div>
    </div>
    """, unsafe_allow_html=True)

def calculate_sample_size(baseline_cvr, mde, alpha=0.05, power=0.8):
    standard_norm = stats.norm()
    Z_alpha = standard_norm.ppf(1 - alpha/2)
    Z_beta = standard_norm.ppf(power)
    p1 = baseline_cvr
    p2 = baseline_cvr * (1 + mde)
    pooled_prob = (p1 + p2) / 2
    if p1 == p2: return 0
    n = (2 * pooled_prob * (1 - pooled_prob) * (Z_alpha + Z_beta)**2) / (p1 - p2)**2
    return int(n)

def get_bucket(user_id, num_buckets=100):
    hash_obj = hashlib.md5(str(user_id).encode())
    return int(hash_obj.hexdigest(), 16) % num_buckets

# --- Initialize State ---
# Change Default Page to 'monitor'
if 'page' not in st.session_state: st.session_state['page'] = 'monitor'
if 'step' not in st.session_state: st.session_state['step'] = 1
if 'custom_metrics' not in st.session_state: st.session_state['custom_metrics'] = []

con = duckdb.connect(DB_PATH) # Re-connect per run safely

# --- HEADER NAVIGATION ---
# Top bar with Logo and Tabs
c_logo, c_nav = st.columns([1, 4])
with c_logo:
    if st.button("🌌 NovaRium", type="secondary", use_container_width=True):
        st.session_state['page'] = 'intro'
        st.rerun()

with c_nav:
    # Use standard buttons acting as tabs, styled as pills
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

st.write("") # Spacer

# =========================================================
# PAGE: INTRO (BRAND IDENTITY)
# =========================================================
if st.session_state['page'] == 'intro':
    st.markdown("""
    <div style="text-align: center; padding: 50px 0;">
        <h1 style="font-size: 3.5rem; background: linear-gradient(to right, #818CF8, #C084FC); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 20px;">
            Where Data Analysts are Born.
        </h1>
        <p style="font-size: 1.2rem; margin-bottom: 40px; color: rgba(255,255,255,0.7);">
            "책으로만 배우는 A/B 테스트는 그만. 직접 경험하며 데이터 분석가로 다시 태어나세요."
        </p>
    </div>
    
    <div style="display: flex; gap: 20px; justify-content: center; margin-bottom: 50px;">
        <div style="background: rgba(255,255,255,0.05); padding: 30px; border-radius: 20px; width: 45%; border: 1px solid rgba(255,255,255,0.1);">
            <h3 style="color: #A78BFA; margin-bottom: 15px;">✨ Nova (New)</h3>
            <p style="font-size: 1.1rem; line-height: 1.6;">
                라틴어로 <strong>'새로운'</strong>이라는 뜻이자, 우주를 밝히는 <strong>초신성(Supernova)</strong>을 의미합니다.<br>
                데이터의 홍수 속에서 인사이트를 발견하고 비즈니스를 밝히는 여러분을 상징합니다.
            </p>
        </div>
        <div style="background: rgba(255,255,255,0.05); padding: 30px; border-radius: 20px; width: 45%; border: 1px solid rgba(255,255,255,0.1);">
            <h3 style="color: #A78BFA; margin-bottom: 15px;">🏛️ Arium (Place)</h3>
            <p style="font-size: 1.1rem; line-height: 1.6;">
                라틴어 접미사로 <strong>'~을 위한 공간'</strong> 또는 '생태계'를 뜻합니다.<br>
                예비 분석가들이 마음껏 가설을 세우고, 실패하고, 성장할 수 있는 안전한 훈련소입니다.
            </p>
        </div>
    </div>
    
    <div style="text-align: center;">
        <div style="background: linear-gradient(90deg, #6366F1, #8B5CF6); padding: 15px 30px; border-radius: 50px; display: inline-block; font-weight: bold; font-size: 1.2rem; box-shadow: 0 10px 30px rgba(99, 102, 241, 0.3);">
            🚀 Mission: "데이터로 비즈니스를 움직이는 초신성(Analyst)을 위한 실전 생태계"
        </div>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# PAGE: MONITORING DASHBOARD (HOME)
# =========================================================
if st.session_state['page'] == 'monitor':
    st.markdown("## 📊 종합 상황실 (Monitoring Dashboard)")
    st.caption("NovaEats 서비스의 핵심 지표를 실시간으로 모니터링합니다.")

    # 1. Fetch KPI Logic (Last 30 days)
    # Using 'user_hist_' IDs from history generator
    sql_kpi = """
    WITH daily_stats AS (
        SELECT 
            date_trunc('day', assigned_at) as day,
            COUNT(DISTINCT a.user_id) as users,
            COUNT(DISTINCT CASE WHEN e.event_name = 'click_banner' THEN e.user_id END) as clicks,
            COUNT(DISTINCT CASE WHEN e.event_name = 'purchase' THEN e.user_id END) as orders
        FROM assignments a
        LEFT JOIN events e ON a.user_id = e.user_id
        WHERE a.user_id LIKE 'user_hist_%'
        GROUP BY 1
    )
    SELECT *,
        (clicks::FLOAT / NULLIF(users,0)) as ctr,
        (orders::FLOAT / NULLIF(clicks,0)) as cvr
    FROM daily_stats
    ORDER BY day ASC
    """
    df_trend = run_query(sql_kpi, con)
    
    if not df_trend.empty:
        # Latest Stats (Last available day)
        latest = df_trend.iloc[-1]
        prev = df_trend.iloc[-2] if len(df_trend) > 1 else latest
        
        # KPI Cards
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.metric("Daily Active Users", f"{int(latest['users']):,}", f"{int(latest['users']-prev['users'])}")
        with k2:
            st.metric("Banner Click Rate (CTR)", f"{latest['ctr']*100:.2f}%", f"{(latest['ctr']-prev['ctr'])*100:.2f}%")
        with k3:
            st.metric("Conversion Rate (CVR)", f"{latest['cvr']*100:.2f}%", f"{(latest['cvr']-prev['cvr'])*100:.2f}%")
        with k4:
             st.metric("Orders", f"{int(latest['orders']):,}", f"{int(latest['orders']-prev['orders'])}")
        
        st.divider()
        
        # 2. Crisis Alert Logic
        # If CTR drops below 5% (simulated crisis is ~4%)
        if latest['ctr'] < 0.05:
            st.error(f"🚨 **[Critical Alert]** 메인 배너 클릭률(CTR)이 급격히 하락했습니다! (현재: {latest['ctr']*100:.1f}%)")
            
            c_alert, c_action = st.columns([3, 1])
            with c_alert:
                st.markdown("최근 3일간 지표가 정상 범위(15%)에서 위험 수준(4%)으로 떨어졌습니다. 원인을 파악하고 해결 실험을 진행하세요.")
            with c_action:
                if st.button("🛠️ 실험으로 해결하기 (Start Test)", type="primary", use_container_width=True):
                    st.session_state['page'] = 'study'
                    st.session_state['step'] = 1
                    st.session_state['target'] = "메인 배너 (할인 문구)" # Auto-context
                    st.rerun()
        else:
            st.success("✅ 모든 서비스 지표가 정상 범위입니다.")

        # 3. Trend Charts
        st.markdown("### 📈 30일 지표 트렌드 (Metric Trends)")
        
        tab_ctr, tab_cvr = st.tabs(["클릭률 (CTR)", "구매 전환율 (CVR)"])
        
        with tab_ctr:
            fig = px.line(df_trend, x='day', y='ctr', markers=True, 
                          title='Daily Banner CTR', template='plotly_dark')
            fig.update_traces(line_color='#ef4444' if latest['ctr'] < 0.05 else '#4ade80', line_width=4)
            fig.add_hrect(y0=0.14, y1=0.16, line_width=0, fillcolor="green", opacity=0.1, annotation_text="Target Range")
            st.plotly_chart(fig, use_container_width=True)
            
        with tab_cvr:
            fig2 = px.line(df_trend, x='day', y='cvr', markers=True, 
                           title='Daily Purchase CVR (Click to Order)', template='plotly_dark')
            fig2.update_traces(line_color='#8B5CF6', line_width=3)
            st.plotly_chart(fig2, use_container_width=True)

    else:
        st.warning("데이터가 없습니다. `generate_history.py`를 실행해주세요.")
        if st.button("데이터 생성하기"):
             # Call script via simple trigger? (Would need restart, but let's just guide user)
             st.info("터미널에서 `python scripts/generate_history.py`를 실행하세요.")

# =========================================================
# PAGE: STUDY (WIZARD)
# =========================================================
elif st.session_state['page'] == 'study':
    
    # --- Progress Indicators (Nebula Style) ---
    steps = ["1. Hypothesis", "2. Design", "3. Collection", "4. Analysis"]
    curr = st.session_state['step']
    
    cols = st.columns(len(steps))
    for i, s in enumerate(steps):
        is_active = (i + 1 == curr)
        color = "#8B5CF6" if is_active else "rgba(255,255,255,0.2)"
        text_color = "white" if is_active else "rgba(255,255,255,0.4)"
        weight = "700" if is_active else "400"
        
        cols[i].markdown(f"""
        <div style="text-align:center;">
            <div style="height:4px; width:100%; background:{color}; border-radius:2px; margin-bottom:8px; box-shadow:{'0 0 10px #8B5CF6' if is_active else 'none'}"></div>
            <span style="color:{text_color}; font-weight:{weight}; font-size:0.9rem;">{s}</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

    # --- STEP 1: HYPOTHESIS ---
    if curr == 1:
        st.markdown(f"<h2>Step 1. 목표 정의 (Define Your Vision)</h2>", unsafe_allow_html=True)
        edu_guide("가설(Hypothesis)", "데이터 분석은 막연한 시도가 아닙니다. **'무엇을(X) 바꾸면 어떤 지표(Y)가 좋아질 것이다'**라는 명확한 믿음을 정의하세요.")

        col_mock, col_form = st.columns([1.5, 1], gap="large")
        
        # 1. Real Target App (Iframe)
        with col_mock:
            with st.container(border=True):
                st.markdown("#### 📱 NovaEats (Live Target)")
                st.caption("실제 구동 중인 웹 서버(FastAPI) 화면입니다. 에이전트들이 이곳을 방문하게 됩니다.")
                
                # Embedding the FastAPI app
                try:
                    components.iframe("http://localhost:8000", height=600, scrolling=True)
                except Exception:
                    st.error("서버 연결 실패: Target App이 실행 중인지 확인하세요.")
                
                # Target Selection (Manual Override for Education)
                st.divider()
                st.caption("실험 타겟 설정 (Manual Setup)")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("👉 메인 배너 실험", use_container_width=True):
                        st.session_state['target'] = "메인 배너 (할인 문구)"
                with c2:
                    if st.button("👉 카테고리 아이콘 실험", use_container_width=True):
                        st.session_state['target'] = "카테고리 아이콘 (치킨)"

        # 2. Form (Glass Card)
        with col_form:
            with st.container(border=True):
                st.markdown("#### ✍️ 실험 설계 (Setup)")
                
                # Target Check
                tgt = st.session_state.get('target', '👈 왼쪽 앱에서 요소를 선택하세요')
                st.markdown(f"""
                <div style='padding:12px; background:rgba(139, 92, 246, 0.1); border:1px solid rgba(139, 92, 246, 0.3); border-radius:10px; color:#A78BFA; font-weight:bold; margin-bottom:1.5rem; text-align:center;'>
                    선택된 타겟: {tgt}
                </div>
                """, unsafe_allow_html=True)
                
                # Hypothesis Builder
                st.markdown("**가설 설정 (Hypothesis)**")
                with st.expander("💡 가설 템플릿 사용하기"):
                    # Context-Aware Logic
                    t_ctx = st.session_state.get('target', '')
                    def_what = "메인 배너 색상을 빨강으로 변경하면"
                    def_why = "클릭률이 5% 상승할 것이다"
                    
                    if "메인 배너" in t_ctx:
                        def_what = "메인 배너 문구를 '마감 임박'으로 변경하면"
                        def_why = "클릭률(CTR)이 15%까지 회복될 것이다"
                    elif "카테고리" in t_ctx:
                        def_what = "카테고리 아이콘을 3D 스타일로 변경하면"
                        def_why = "카테고리 탭 클릭 수가 20% 증가할 것이다"

                    h_who = st.selectbox("대상(Who)", ["모든 유저에게", "신규 유저에게", "재구매 유저에게"])
                    h_what = st.text_input("무엇을(Changes)", def_what)
                    h_why = st.text_input("기대 효과(Impact)", def_why)
                    
                    if st.button("템플릿 적용"):
                        st.session_state['temp_hypo'] = f"{h_who}, {h_what}, {h_why}."
                        st.rerun()
                
                default_hypo = st.session_state.get('temp_hypo', "")
                hypo = st.text_area("가설을 작성하세요", value=default_hypo, placeholder="예: 메인 배너 문구를 '마감 임박'으로 변경하면, 클릭률(CTR)이 상승할 것이다.", height=120)
                
                st.write("")
                # Metrics Setup (Advanced)
                st.markdown("#### 🎯 지표 설정 (Metrics)")
                
                # Metric Library (Educational)
                metrics_db = {
                    "CTR (클릭률)": {
                        "desc": "노출 대비 클릭한 비율 (Click Through Rate)", 
                        "formula": "Clicks / Impressions * 100",
                        "type": "Conversion"
                    },
                    "CVR (전환율)": {
                        "desc": "방문자 중 실제 구매(목표)로 이어진 비율 (Conversion Rate)", 
                        "formula": "Orders / Visitors * 100",
                        "type": "Conversion"
                    },
                    "AOV (평균 주문액)": {
                        "desc": "구매 고객 1인당 평균 결제 금액 (Average Order Value)", 
                        "formula": "Total Revenue / Total Orders",
                        "type": "Revenue"
                    },
                    "Bounce Rate (이탈률)": {
                        "desc": "첫 페이지만 보고 나가는 비율. (낮을수록 좋음)", 
                        "formula": "One-page Sessions / Total Sessions * 100",
                        "type": "Retention"
                    },
                    "Purchase Logic (결제 시간)": {
                        "desc": "상품 클릭 후 결제 완료까지 걸리는 시간 (Time to Purchase)",
                        "formula": "Purchase Time - Click Time (Avg)",
                        "type": "UX"
                    }
                }
                
                # 1. Primary Metric (OEC)
                st.markdown("**1. 핵심 성공 지표 (Primary Metric)**")
                st.caption("실험의 성공/실패를 판가름하는 단 하나의 지표 (OEC)")
                m_sel = st.selectbox("Key Metric (OEC)", list(metrics_db.keys()), label_visibility="collapsed")
                
                # Info Card for Primary
                sel_info = metrics_db[m_sel]
                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.05); border-left:4px solid #8B5CF6; padding:10px 15px; border-radius:4px; margin-bottom:15px;">
                    <div style="color:#A78BFA; font-weight:bold;">{m_sel}</div>
                    <div style="font-size:0.9rem; margin-top:4px;">{sel_info['desc']}</div>
                    <div style="font-size:0.8rem; color:rgba(255,255,255,0.5); margin-top:4px;">🧮 산식: {sel_info['formula']}</div>
                </div>
                """, unsafe_allow_html=True)

                # 2. Guardrail Metrics
                st.markdown("**2. 가드레일 지표 (Guardrail Metrics)**")
                st.caption("실험군에서 **절대 망가지면 안 되는** 보조 지표들입니다. (부작용 감시)")
                default_gr = ["AOV (평균 주문액)"] if m_sel != "AOV (평균 주문액)" else ["CVR (전환율)"]
                g_sel = st.multiselect("보조 지표 선택", [k for k in metrics_db.keys() if k != m_sel], default=default_gr)
                
                if g_sel:
                    for g in g_sel:
                        info = metrics_db[g]
                        st.caption(f"🛡️ **{g}**: {info['desc']}")

                # Custom Metric
                with st.expander("➕ 지표 직접 만들기 (Custom)"):
                    nm = st.text_input("지표 이름")
                    desc = st.text_input("설명 (예: 회원가입 버튼 클릭 수)")
                    if st.button("추가"): 
                        st.session_state['custom_metrics'].append(nm)
                        st.rerun()
                
                st.write("")
                if st.button("다음: 실험 설계 단계로 ➡️", type="primary", use_container_width=True):
                    if not hypo:
                        st.toast("가설을 입력해야 진행할 수 있습니다!", icon="⚠️")
                    elif tgt.startswith('👈'):
                        st.toast("왼쪽 앱 화면에서 개선할 타겟을 선택해주세요!", icon="point_left")
                    else:
                        st.session_state['hypothesis'] = hypo
                        st.session_state['metric'] = m_sel
                        st.session_state['guardrails'] = g_sel
                        st.session_state['step'] = 2
                        st.rerun()

    # --- STEP 2: EXPERIMENT DESIGN (Unified: Traffic + Power Analysis) ---
    elif curr == 2:
        st.markdown(f"<h2>Step 2. 실험 설계 (Experiment Design)</h2>", unsafe_allow_html=True)
        edu_guide("실험 설계의 3요소", "트래픽 비율 → 목표 설정 → 필요 표본 계산 순서로 진행합니다. <strong>트래픽 비율이 표본 크기에 영향</strong>을 주므로 먼저 결정해야 합니다.")
        
        # === PART 1: Traffic Ratio Selection ===
        st.markdown("### 1️⃣ 트래픽 비율 설정")
        
        col_ratio = st.columns([1, 1], gap="large")
        with col_ratio[0]:
            with st.container(border=True):
                st.markdown("#### 🎛️ 비율 선택")
                with st.expander("💡 비율 선택 가이드"):
                    st.markdown("""
                    | 비율 | 상황 | 예시 |
                    |------|------|------|
                    | **50/50** | 표준 실험 | UI 색상, 문구 변경 |
                    | **90/10** | 고위험 실험 | 결제 플로우, 핵심 기능 |
                    | **10/90** | 저위험 + 확신 | 명백한 개선사항 빠른 적용 |
                    
                    **현재 상황:** 배너 문구 변경 → 추천 **50/50**
                    """)
                split = st.slider("테스트(B) 그룹 비율", 10, 90, 50, format="%d%%")
                st.caption(f"Control(A): {100-split}% | Test(B): {split}%")
        
        with col_ratio[1]:
            with st.container(border=True):
                st.markdown("#### 🔍 Hash 검증")
                uid = st.text_input("User ID", "user_cosmic_99", key="hash_uid")
                b = get_bucket(uid)
                threshold = 100 - split
                grp = "B" if b >= threshold else "A"
                st.markdown(f"**Hash: {b}** → Group **{grp}**")
        
        st.divider()
        st.markdown("### 2️⃣ 목표 설정 및 표본 계산")

        c1, c2 = st.columns(2, gap="large")
        with c1:
            with st.container(border=True):
                st.markdown("#### ⚙️ Parameters")
                
                # Context-Aware Baseline (Fetch from DB)
                selected_metric = st.session_state.get('metric', 'CTR (클릭률)')
                
                # Query latest metric value
                if "CTR" in selected_metric:
                    sql_baseline = """
                    SELECT 
                        (COUNT(DISTINCT CASE WHEN e.event_name = 'click_banner' THEN e.user_id END)::FLOAT / 
                         NULLIF(COUNT(DISTINCT a.user_id), 0)) as metric_value
                    FROM assignments a
                    LEFT JOIN events e ON a.user_id = e.user_id
                    WHERE a.user_id LIKE 'user_hist_%'
                    AND a.assigned_at >= CURRENT_DATE - INTERVAL '3 days'
                    """
                    metric_label = "클릭률 (CTR)"
                    normal_target = 0.15  # Normal CTR is 15%
                else:  # CVR or other
                    sql_baseline = """
                    SELECT 
                        (COUNT(DISTINCT CASE WHEN e.event_name = 'purchase' THEN e.user_id END)::FLOAT / 
                         NULLIF(COUNT(DISTINCT a.user_id), 0)) as metric_value
                    FROM assignments a
                    LEFT JOIN events e ON a.user_id = e.user_id
                    WHERE a.user_id LIKE 'user_hist_%'
                    AND a.assigned_at >= CURRENT_DATE - INTERVAL '3 days'
                    """
                    metric_label = "전환율 (CVR)"
                    normal_target = 0.20  # Normal CVR is 20%
                
                df_baseline = run_query(sql_baseline, con)
                auto_baseline = df_baseline.iloc[0, 0] if not df_baseline.empty and df_baseline.iloc[0, 0] else 0.10
                
                # Display Current (Read-only style)
                st.markdown(f"**현재 {metric_label}** (자동 감지)")
                st.markdown(f"""
                <div style='padding:15px; background:rgba(239, 68, 68, 0.1); border:2px solid #ef4444; border-radius:10px; text-align:center;'>
                    <div style='font-size:2rem; font-weight:bold; color:#ef4444;'>{auto_baseline*100:.2f}%</div>
                    <div style='font-size:0.9rem; color:rgba(255,255,255,0.6); margin-top:5px;'>최근 3일 평균</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.write("")
                
                # Target Input (User sets goal)
                target_metric = st.number_input(f"**목표 {metric_label}** (실험 성공 시 도달할 목표)", 
                                               min_value=float(auto_baseline), 
                                               max_value=1.0, 
                                               value=float(normal_target), 
                                               step=0.01,
                                               format="%.2f",
                                               help=f"정상 범위: {normal_target*100:.0f}%")
                
                # Calculate MDE internally
                mde = (target_metric - auto_baseline) / auto_baseline if auto_baseline > 0 else 0
                
                st.caption(f"💡 목표: {auto_baseline*100:.2f}% → {target_metric*100:.2f}% (상승폭: +{mde*100:.1f}%)")
                
                base_cvr = auto_baseline  # Use detected baseline for calculation
        
        with c2:
            with st.container(border=True):
                st.markdown("#### 🧮 필요 표본 수 (Required Sample)")
                n = calculate_sample_size(base_cvr, mde)
                
                # Adjust for traffic ratio
                if split == 50:
                    n_control = n
                    n_test = n
                    total_needed = n * 2
                else:
                    # For unequal splits, adjust proportionally
                    control_pct = (100 - split) / 100
                    test_pct = split / 100
                    # Keep total sample size but distribute by ratio
                    total_needed = int(n * 2 * max(1/control_pct, 1/test_pct))
                    n_control = int(total_needed * control_pct)
                    n_test = int(total_needed * test_pct)
                
                st.markdown(f"<div class='big-stat'>{total_needed:,}</div>", unsafe_allow_html=True)
                st.markdown("**명 (총 필요 유저 수)**")
                
                st.progress(min(1.0, 0.3 + (mde * 2)))
                st.caption(f"• Control (A): **{n_control:,}명** ({100-split}%)")
                st.caption(f"• Test (B): **{n_test:,}명** ({split}%)")
                st.caption(f"💡 트래픽 비율에 따라 각 그룹의 필요 인원이 조정됩니다.")
                
                # Educational Explainer
                with st.expander("📐 계산 로직 보기 (How is this calculated?)"):
                    st.markdown("""
                    ### 표본 크기 계산 공식 (Sample Size Formula)
                    
                    A/B 테스트에서 필요한 샘플 수는 다음 공식으로 계산됩니다:
                    
                    ```
                    n = 2 × p̄(1-p̄) × (Z_α/2 + Z_β)² / (p₁ - p₂)²
                    ```
                    
                    **각 요소 설명:**
                    
                    1. **p₁, p₂**: 대조군(A)과 실험군(B)의 전환율
                       - p₁ = 현재 클릭률 (예: 6.93%)
                       - p₂ = 목표 클릭률 (예: 15%)
                    
                    2. **p̄ (Pooled Probability)**: 두 그룹의 평균 전환율
                       - p̄ = (p₁ + p₂) / 2
                       - 분산 계산에 사용
                    
                    3. **Z_α/2**: 유의수준(α)에 대한 Z-score
                       - α = 0.05 (95% 신뢰도) → Z = 1.96
                       - "5% 확률로 오판할 수 있음"을 의미
                    
                    4. **Z_β**: 검정력(Power)에 대한 Z-score
                       - Power = 0.80 (80%) → Z = 0.84
                       - "실제 차이가 있을 때 80% 확률로 감지"
                    
                    5. **(p₁ - p₂)²**: 효과 크기의 제곱
                       - 차이가 클수록 적은 샘플로 감지 가능
                       - 차이가 작을수록 더 많은 샘플 필요
                    
                    **직관적 이해:**
                    - 🔍 작은 차이를 찾으려면 → 많은 샘플 필요
                    - 🎯 큰 차이를 찾으려면 → 적은 샘플로도 충분
                    - 📊 신뢰도를 높이려면 → 더 많은 샘플 필요
                    
                    **현재 계산값:**
                    - 현재: {:.2%} → 목표: {:.2%}
                    - 효과 크기: {:.2%}
                    - 필요 샘플: {:,}명 (그룹당)
                    """.format(base_cvr, target_metric, abs(target_metric - base_cvr), n))
                
                
                st.write("")
                if st.button("다음: 데이터 수집 ➡️", type="primary", use_container_width=True):
                    st.session_state['split'] = split
                    st.session_state['total_needed'] = total_needed
                    st.session_state['n_control'] = n_control
                    st.session_state['n_test'] = n_test
                    st.session_state['baseline_metric'] = base_cvr
                    st.session_state['target_metric'] = target_metric
                    st.session_state['step'] = 3
                    st.rerun()

    # --- STEP 3: COLLECTION (formerly Step 4) ---
    elif curr == 3:
        st.markdown(f"<h2>Step 3. 데이터 수집 (Collection)</h2>", unsafe_allow_html=True)
        edu_guide("Event Logging (로그 적재)", "유저가 들어오면 <strong>Assignments</strong>(그룹 할당) 테이블에 남고, 행동을 하면 <strong>Events</strong>(클릭/구매) 테이블에 기록됩니다.")

        # Get target sample size from Step 2
        # If not available, recalculate based on current session state
        if 'total_needed' in st.session_state and st.session_state['total_needed'] < 5000:
            target_total = st.session_state['total_needed']
            n_control = st.session_state.get('n_control', 235)
            n_test = st.session_state.get('n_test', 235)
        else:
            # Fallback: recalculate from baseline metrics
            base_cvr = st.session_state.get('baseline_metric', 0.0693)
            target_metric = st.session_state.get('target_metric', 0.15)
            mde = abs(target_metric - base_cvr) / base_cvr
            
            # Recalculate sample size
            from scipy import stats
            alpha = 0.05
            power = 0.80
            p1 = base_cvr
            p2 = target_metric
            p_avg = (p1 + p2) / 2
            z_alpha = stats.norm.ppf(1 - alpha/2)
            z_beta = stats.norm.ppf(power)
            n = int(2 * p_avg * (1 - p_avg) * ((z_alpha + z_beta) / (p2 - p1))**2) + 1
            
            split = st.session_state.get('split', 50)
            if split == 50:
                n_control = n
                n_test = n
                target_total = n * 2
            else:
                control_pct = (100 - split) / 100
                test_pct = split / 100
                target_total = int(n * 2 * max(1/control_pct, 1/test_pct))
                n_control = int(target_total * control_pct)
                n_test = int(target_total * test_pct)
        
        
        # Check current data count (only count THIS experiment's users)
        # Use experiment_id to track current session, or timestamp-based filtering
        experiment_id = st.session_state.get('experiment_id', 'exp_current')
        
        # For now, let's count users created AFTER entering Step 3
        # Store a timestamp when first entering Step 3
        if 'step3_start_time' not in st.session_state:
            st.session_state['step3_start_time'] = datetime.now()
        
        start_time = st.session_state['step3_start_time']
        
        # Count only users created after Step 3 started
        current_n = run_query(f"""
            SELECT COUNT(DISTINCT user_id) 
            FROM assignments 
            WHERE (user_id LIKE 'sim_%' OR user_id LIKE 'agent_%')
            AND timestamp >= '{start_time.strftime('%Y-%m-%d %H:%M:%S')}'
        """, con).iloc[0,0]
        
        remaining = max(0, target_total - current_n)
        progress_pct = min(100, (current_n / target_total * 100) if target_total > 0 else 0)
        
        # Centered container
        col_center = st.columns([1, 2, 1])
        with col_center[1]:
            with st.container(border=True):
                st.markdown("### 📊 데이터 생성 방식 선택")
                
                # Progress Display
                st.markdown(f"""
                <div style='background:rgba(255,255,255,0.05); padding:15px; border-radius:10px; margin-bottom:20px;'>
                    <div style='display:flex; justify-content:space-between; margin-bottom:10px;'>
                        <span style='color:rgba(255,255,255,0.7);'>현재 진행률</span>
                        <span style='font-weight:bold; color:#8B5CF6;'>{current_n:,}명 / {target_total:,}명</span>
                    </div>
                    <div style='background:rgba(255,255,255,0.1); height:10px; border-radius:5px; overflow:hidden;'>
                        <div style='background:linear-gradient(90deg, #8B5CF6, #C084FC); height:100%; width:{progress_pct}%;'></div>
                    </div>
                    <div style='text-align:center; margin-top:10px; color:rgba(255,255,255,0.6); font-size:0.9rem;'>
                        {progress_pct:.1f}% 완료 | 남은 인원: {remaining:,}명
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.write("")
                
                # Button 1: Quick Simulation
                with st.expander("ℹ️ ⚡ 빠른 시뮬레이션 (1초, 교육용)"):
                    st.markdown(f"""
                    **Python 코드로 확률 계산하여 즉시 생성**
                    
                    1. 남은 인원({remaining:,}명)만큼 가상 User ID 생성
                    2. Hash 함수로 A/B 그룹 할당 ({100-split_ratio}/{split_ratio})
                    3. 확률로 클릭/구매 결정
                    4. DB에 직접 입력
                    
                    **장점:** 1초 이내 완료  
                    **단점:** 현실성 낮음
                    """)
                
                if st.button(f"⚡ 빠른 시뮬레이션 ({remaining:,}명 생성)", type="primary", use_container_width=True, disabled=(remaining==0)):
                    with st.spinner(f"데이터 생성 중... ({remaining:,}명)"):
                        split = split_ratio / 100
                        base = st.session_state.get('baseline_metric', 0.10)
                        target = st.session_state.get('target_metric', 0.15)
                        
                        current_count = run_query("SELECT COUNT(*) FROM assignments", con).iloc[0,0]
                        new_users = []
                        new_events = []
                        
                        for i in range(remaining):
                            uid = f"sim_{current_count + i}"
                            is_test = get_bucket(uid) >= (100 * (1 - split))
                            variant = 'B' if is_test else 'A'
                            
                            new_users.append((uid, 'exp_1', variant, datetime.now()))
                            
                            # Use actual target metrics from Step 2
                            rate = target if variant == 'B' else base
                            if np.random.random() < rate:
                                new_events.append((f"evt_{uid}", uid, 'purchase', datetime.now()))
                        
                        if new_users:
                            df_users = pd.DataFrame(new_users, columns=['uid','eid','var','ts'])
                            con.execute("INSERT INTO assignments SELECT * FROM df_users")
                        
                        if new_events:
                            df_events = pd.DataFrame(new_events, columns=['eid','uid','name','ts'])
                            con.execute("INSERT INTO events SELECT * FROM df_events")
                        
                        st.toast(f"✅ {remaining:,}명 데이터 생성 완료!")
                        st.rerun()
                
                st.write("")
                
                # Button 2: Agent Swarm
                with st.expander("ℹ️ 🤖 에이전트 투입 (실전)"):
                    st.markdown(f"""
                    **실제 HTTP 요청으로 앱 방문 후 판단**
                    
                    1. 남은 인원({remaining:,}명)만큼 에이전트 생성
                    2. 5가지 행동 유형으로 분산 (충동/계산/윈도우쇼핑/목적/신중)
                    3. `localhost:8000` 실제 접속하여 판단
                    4. DB 자동 기록
                    
                    **장점:** 현실적, 실전 시뮬레이션  
                    **단점:** 시간 소요, Target App 필요
                    """)
                
                if st.button(f"🤖 에이전트 투입 ({remaining:,}명)", type="secondary", use_container_width=True, disabled=(remaining==0)):
                    # Calculate agent distribution based on remaining
                    agent_config = {
                        "impulsive": int(remaining * 0.2),
                        "calculator": int(remaining * 0.25),
                        "browser": int(remaining * 0.25),
                        "mission": int(remaining * 0.2),
                        "cautious": int(remaining * 0.1)
                    }
                    
                    with st.spinner(f"🤖 에이전트 투입 중... ({remaining:,}명)"):
                        try:
                            import sys
                            import os
                            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                            if project_root not in sys.path:
                                sys.path.insert(0, project_root)
                            
                            from agent_swarm.runner import run_agent_swarm
                            
                            progress_placeholder = st.empty()
                            def update_progress(current, total, msg):
                                progress_placeholder.progress(current / total, text=f"{msg} ({current}/{total})")
                            
                            results = run_agent_swarm(agent_config, update_progress)
                            
                            st.success(f"✅ 에이전트 {results['total']}명 투입 완료!")
                            st.info(f"📊 클릭: {results['clicked']}명 | 구매: {results['purchased']}명")
                            
                            st.rerun()
                        
                        except Exception as e:
                            st.error(f"❌ 에이전트 실행 실패: {str(e)}")
                            st.info("💡 Tip: Target App (localhost:8000)이 실행 중인지 확인하세요.")
                
                st.write("")
                st.divider()
                
                # Next button
                if current_n >= target_total:
                    st.success(f"✅ 목표 달성! ({current_n:,}/{target_total:,}명)")
                    if st.button("다음: 결과 분석 ➡️", type="primary", use_container_width=True):
                        st.session_state['step'] = 4
                        st.rerun()
                else:
                    st.info(f"💡 위 버튼 중 하나를 선택하여 데이터를 생성하세요. (남은 인원: {remaining:,}명)")
    


    # --- STEP 4: ANALYSIS (formerly Step 5) ---
    elif curr == 4:
        st.markdown(f"<h2>Step 4. 최종 분석 (Final Analysis)</h2>", unsafe_allow_html=True)
        edu_guide("P-value (유의 확률)", "결과가 우연히 나왔을 확률입니다. 보통 <strong>0.05 (5%)</strong>보다 낮으면 '통계적으로 유의미하다'고 판단하여 Test 안을 채택합니다.")

        # SQL
        sql = """
        SELECT 
            a.variant as 'Variant',
            COUNT(DISTINCT a.user_id) as 'Users',
            COUNT(DISTINCT e.user_id) as 'Conversions'
        FROM assignments a
        LEFT JOIN events e ON a.user_id = e.user_id 
        GROUP BY 1 ORDER BY 1
        """
        df = run_query(sql, con)
        
        # Calc Stats
        p_val = 1.0
        decision = "Inconclusive"
        if len(df) == 2:
            c_users, c_conv = df.iloc[0,1], df.iloc[0,2]
            t_users, t_conv = df.iloc[1,1], df.iloc[1,2]
            
            c_rate = c_conv/c_users
            t_rate = t_conv/t_users
            lift = (t_rate - c_rate) / c_rate
            
            pooled_p = (c_conv + t_conv) / (c_users + t_users)
            se = np.sqrt(pooled_p * (1 - pooled_p) * (1/c_users + 1/t_users))
            if se > 0:
                z = (t_rate - c_rate) / se
                p_val = stats.norm.sf(abs(z))*2
                if p_val < 0.05: decision = "Significant"

        c1, c2 = st.columns([1.5, 1], gap="large")
        with c1:
            with st.container(border=True):
                st.markdown("#### 📊 데이터 집계 (Data)")
                st.code(sql, language="sql")
                st.dataframe(df, use_container_width=True, hide_index=True)
        
        with c2:
            with st.container(border=True):
                st.markdown("#### 🏁 최종 성적표")
                
                if len(df) == 2:
                    st.metric("Lift (개선율)", f"{lift*100:.2f}%", f"P-value: {p_val:.4f}")
                    
                    if decision == "Significant":
                        st.success(f"**WINNER** (실험 성공!)")
                    else:
                        st.warning(f"**TIE** (차이 없음)")
                
                st.divider()
                note = st.text_area("배운 점 (Learning Note)", placeholder="이번 실험을 통해 무엇을 알게 되었나요?")
                
                if st.button("💾 실험 회고록에 저장 (Save Report)", type="primary", use_container_width=True):
                    # Prepare Data
                    h = st.session_state.get('hypothesis', '-')
                    t = st.session_state.get('target', '-')
                    pm = st.session_state.get('metric', '-')
                    gr = str(st.session_state.get('guardrails', []))
                    n = st.session_state.get('n', 0)
                    split = st.session_state.get('split', 50)
                    
                    # Safe Insert
                    con.execute(f"""
                        INSERT INTO experiments (
                            target, hypothesis, primary_metric, guardrails, sample_size, 
                            traffic_split, p_value, decision, learning_note, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, [t, h, pm, gr, n, split, p_val, decision, note])
                    
                    # Cleanup
                    con.execute("DELETE FROM assignments")
                    con.execute("DELETE FROM events")
                    
                    st.toast("회고록에 저장되었습니다! 📝")
                    st.session_state['page'] = 'portfolio'
                    st.session_state['step'] = 1
                    st.rerun()

# =========================================================
# PAGE: EXPERIMENT RETROSPECTIVE (PORTFOLIO)
# =========================================================
elif st.session_state['page'] == 'portfolio':
    st.title("📚 실험 회고록 (Experiment Retrospective)")
    st.markdown("### 내가 진행한 실험들의 성장 기록")
    
    df_history = run_query("SELECT * FROM experiments ORDER BY created_at DESC", con)
    
    if df_history.empty:
        st.info("아직 진행된 실험이 없습니다. 마스터 클래스에서 첫 실험을 시작해보세요!")
    else:
        # 1. Filter Context
        all_targets = ["All"] + list(df_history['target'].unique()) if 'target' in df_history.columns else ["All"]
        all_targets = [t for t in all_targets if t is not None]
        
        selected_target = st.selectbox("📂 카테고리 필터 (Category)", all_targets, index=0)
        
        if selected_target != "All":
            df_history = df_history[df_history['target'] == selected_target]
            
        st.divider()

        # 2. Experiment Cards
        for _, row in df_history.iterrows():
            with st.container(border=True):
                # Summary Row
                c1, c2, c3 = st.columns([0.5, 3, 1.5])
                with c1:
                    st.markdown("🧪")
                with c2:
                    st.markdown(f"**{row['hypothesis']}**")
                    tgt_badge = f"<span style='background:rgba(255,255,255,0.1); padding:2px 6px; border-radius:4px; font-size:0.8rem;'>{row.get('target', 'General')}</span>"
                    st.markdown(f"{tgt_badge} | {row['created_at'].strftime('%Y-%m-%d %H:%M')}", unsafe_allow_html=True)
                with c3:
                    decision = row['decision']
                    color = "#4ade80" if decision == 'Significant' else "#94a3b8"
                    st.markdown(f"<div style='text-align:right; color:{color}; font-weight:bold;'>{decision}</div>", unsafe_allow_html=True)

                # Detail Report (Expander)
                with st.expander("📄 상세 보고서 보기 (View Report)"):
                    st.markdown("#### 1. 실험 설계 (Design)")
                    d1, d2, d3 = st.columns(3)
                    d1.metric("Target", row.get('target', '-'))
                    d2.metric("Primary Metric", row['primary_metric'])
                    d3.metric("Guardrails", row.get('guardrails', 'None'))
                    
                    st.markdown("#### 2. 실험 결과 (Results)")
                    r1, r2, r3 = st.columns(3)
                    r1.metric("Sample Size", f"{row.get('sample_size', 0):,}명")
                    r2.metric("P-value", f"{row['p_value']:.4f}")
                    r3.metric("Traffic Split", f"{row.get('traffic_split', 0)}%")
                    
                    if row['learning_note']:
                        st.markdown(f"""
                        <div style="background:rgba(139, 92, 246, 0.1); padding:15px; border-radius:8px; margin-top:10px;">
                            <strong>💡 Learning Note:</strong><br>
                            {row['learning_note']}
                        </div>
                        """, unsafe_allow_html=True)
