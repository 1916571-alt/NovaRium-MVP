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
if 'page' not in st.session_state: st.session_state['page'] = 'study'
if 'step' not in st.session_state: st.session_state['step'] = 1
if 'custom_metrics' not in st.session_state: st.session_state['custom_metrics'] = []

con = duckdb.connect(DB_PATH) # Re-connect per run safely

# --- HEADER NAVIGATION ---
# Top bar with Logo and Tabs
c_logo, c_nav = st.columns([1, 4])
with c_logo:
    st.markdown("### 🌌 NovaRium")
with c_nav:
    # Use standard buttons acting as tabs, styled as pills
    c1, c2, c3 = st.columns([1, 1, 4])
    with c1:
        if st.button("🚀 Master Class", type="primary" if st.session_state['page']=='study' else "secondary", use_container_width=True):
            st.session_state['page'] = 'study'
            st.rerun()
    with c2:
        if st.button("🗄️ Portfolio", type="primary" if st.session_state['page']=='portfolio' else "secondary", use_container_width=True):
            st.session_state['page'] = 'portfolio'
            st.rerun()

st.write("") # Spacer

# =========================================================
# PAGE: STUDY (WIZARD)
# =========================================================
if st.session_state['page'] == 'study':
    
    # --- Progress Indicators (Nebula Style) ---
    steps = ["Hypothesis", "Design", "Sampling", "Collection", "Analysis"]
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
            <span style="color:{text_color}; font-weight:{weight}; font-size:0.9rem;">{i+1}. {s}</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

    # --- STEP 1: HYPOTHESIS ---
    if curr == 1:
        st.markdown(f"<h2>Step 1. 목표 정의 (Define Your Vision)</h2>", unsafe_allow_html=True)
        edu_guide("가설(Hypothesis)", "데이터 분석은 막연한 시도가 아닙니다. **'무엇을(X) 바꾸면 어떤 지표(Y)가 좋아질 것이다'**라는 명확한 믿음을 정의하세요.")

        col_mock, col_form = st.columns([1.5, 1], gap="large")
        
        # 1. Mock App (Inside Glass Card)
        with col_mock:
            with st.container(border=True):
                st.markdown("#### 📱 NovaEats 앱 (실험 대상)")
                st.caption("실제 앱 화면이라고 가정하고 개선할 부분을 선택해주세요.")
                
                # App Header
                m1, m2 = st.columns([3, 1])
                with m1: 
                    st.text_input("검색어를 입력하세요...", disabled=True, label_visibility="collapsed")
                with m2: 
                    st.markdown("🔔 👤")
                
                # Category Icons (New Feature)
                st.write("")
                st.markdown("**카테고리 (Category)**")
                cat_cols = st.columns(4)
                categories = ["치킨", "피자", "버거", "한식"]
                for i, cat in enumerate(categories):
                    with cat_cols[i]:
                        if st.button(f"{cat}", key=f"cat_{i}", use_container_width=True):
                            st.session_state['target'] = f"카테고리 아이콘 ({cat})"
                
                st.write("")
                
                # Main Banner
                st.info("🎁 **[첫 주문 이벤트]** 3,000원 할인 쿠폰 받기")
                if st.button("👉 배너 선택 (클릭)", use_container_width=True):
                    st.session_state['target'] = "메인 배너 (할인 문구)"
                
                st.write("")
                st.markdown("**🔥 인기 맛집 (Featured)**")
                r1, r2 = st.columns(2)
                with r1:
                    st.image("https://placehold.co/200x120/1e1e2d/FFF?text=Burger", use_container_width=True)
                    st.markdown("**버거킹덤 강남점** (⭐ 4.8)")
                    if st.button("주문하기 A", use_container_width=True):
                        st.session_state['target'] = "주문 버튼 A (Text/Color)"
                with r2:
                    st.image("https://placehold.co/200x120/1e1e2d/FFF?text=Sushi", use_container_width=True)
                    st.markdown("**갓스시 역삼점** (⭐ 4.9)")
                    if st.button("주문하기 B", use_container_width=True):
                        st.session_state['target'] = "주문 버튼 B (Layout)"

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
                    h_who = st.selectbox("대상(Who)", ["모든 유저에게", "신규 유저에게", "재구매 유저에게"])
                    h_what = st.text_input("무엇을(Changes)", "메인 배너 색상을 빨강으로 변경하면")
                    h_why = st.text_input("기대 효과(Impact)", "클릭률이 5% 상승할 것이다")
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

    # --- STEP 2: DESIGN ---
    elif curr == 2:
        st.markdown(f"<h2>Step 2. 실험 설계 (Power Analysis)</h2>", unsafe_allow_html=True)
        edu_guide("Sample Size (표본 크기)", "실험 인원이 너무 적으면 결과를 신뢰할 수 없습니다. 통계적 유의성(Alpha)과 검정력(Power)을 고려해 <strong>최소 몇 명이 필요한지</strong> 계산합니다.")

        c1, c2 = st.columns(2, gap="large")
        with c1:
            with st.container(border=True):
                st.markdown("#### ⚙️ Parameters")
                base_cvr = st.number_input("기존 전환율 (Baseline CVR)", 0.01, 1.0, 0.10, step=0.01)
                mde = st.slider("최소 감지 효과 (MDE)", 1, 50, 10, format="+%d%%")
                st.caption(f"목표: 전환율이 {base_cvr*100:.0f}%에서 {base_cvr*(1+mde/100)*100:.1f}%로 오르는 것을 감지")
        
        with c2:
            with st.container(border=True):
                st.markdown("#### 🧮 필요 표본 수 (Required Sample)")
                n = calculate_sample_size(base_cvr, mde/100)
                
                st.markdown(f"<div class='big-stat'>{n:,}</div>", unsafe_allow_html=True)
                st.markdown("**명 (그룹 당)**")
                
                st.progress(0.7)
                st.caption(f"총 필요 유저 수: {n*2:,} 명")
                
                st.write("")
                if st.button("다음: 트래픽 분배 ➡️", type="primary", use_container_width=True):
                    st.session_state['n'] = n
                    st.session_state['step'] = 3
                    st.rerun()

    # --- STEP 3: SAMPLING ---
    elif curr == 3:
        st.markdown(f"<h2>Step 3. 트래픽 분배 (Sampling)</h2>", unsafe_allow_html=True)
        edu_guide("Hashing (해시 할당)", "유저를 A/B 그룹으로 나눌 때 가장 공평한 방법은 Random입니다. 우리는 유저 ID를 <strong>Hash 함수</strong>에 넣어 고정된 그룹을 부여합니다.")

        c1, c2 = st.columns([1, 1], gap="large")
        with c1:
            with st.container(border=True):
                st.markdown("#### 🔍 해시 시뮬레이터 (Hash Simulator)")
                uid = st.text_input("테스트 User ID 입력", "user_cosmic_99")
                b = get_bucket(uid)
                grp = "B (Test)" if b >= 50 else "A (Control)" # Default 50/50 visual
                color = "#8B5CF6" if grp.startswith("B") else "#64748B"
                
                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.05); padding:20px; border-radius:15px; text-align:center;">
                    <div style="font-family:monospace; color:rgba(255,255,255,0.5);">MD5("{uid}") % 100</div>
                    <div style="font-size:3rem; font-weight:bold; color:white;">{b}</div>
                    <div style="color:{color}; font-weight:bold; font-size:1.2rem;">➜ Group {grp}</div>
                </div>
                """, unsafe_allow_html=True)

        with c2:
            with st.container(border=True):
                st.markdown("#### 🎛️ 트래픽 비율 설정")
                split = st.slider("테스트(B) 그룹 비율", 10, 90, 50, format="%d%%")
                st.caption(f"Control(A): {100-split}% | Test(B): {split}%")
                
                st.write("")
                if st.button("다음: 데이터 수집 ➡️", type="primary", use_container_width=True):
                    st.session_state['split'] = split
                    st.session_state['step'] = 4
                    st.rerun()

    # --- STEP 4: COLLECTION ---
    elif curr == 4:
        st.markdown(f"<h2>Step 4. 데이터 수집 (Collection)</h2>", unsafe_allow_html=True)
        edu_guide("Event Logging (로그 적재)", "유저가 들어오면 <strong>Assignments</strong>(그룹 할당) 테이블에 남고, 행동을 하면 <strong>Events</strong>(클릭/구매) 테이블에 기록됩니다.")

        if st.button("⚡ 가상 유저 1,000명 주입 (Simulate)", type="primary"):
            req_n = st.session_state.get('n', 1000)
            split = st.session_state.get('split', 50)/100
            base = 0.1
            lift = base * 1.15
            
            # Generate Logic
            current_count = run_query("SELECT COUNT(*) FROM assignments", con).iloc[0,0]
            new_users = []
            new_events = []
            
            for i in range(1000):
                uid = f"u_{current_count + i}"
                is_test = get_bucket(uid) >= (100 * (1 - split))
                variant = 'B' if is_test else 'A'
                
                new_users.append((uid, 'exp_1', variant, datetime.now()))
                
                rate = lift if variant == 'B' else base
                if np.random.random() < rate:
                    new_events.append((f"evt_{uid}", uid, 'purchase', datetime.now()))
            
            # Insert
            if new_users: 
                df_users = pd.DataFrame(new_users, columns=['uid','eid','var','ts'])
                con.execute("INSERT INTO assignments SELECT * FROM df_users")
            
            if new_events: 
                df_events = pd.DataFrame(new_events, columns=['eid','uid','name','ts'])
                con.execute("INSERT INTO events SELECT * FROM df_events")
            
            st.toast(f"유저 1,000명 데이터 생성 완료!")

        # Stats
        total_n = run_query("SELECT COUNT(DISTINCT user_id) FROM assignments", con).iloc[0,0]
        st.write("")
        col_main, col_db = st.columns([1, 2], gap="large")
        
        with col_main:
            with st.container(border=True):
                st.markdown("#### 수집 현황 (Status)")
                st.metric("누적 유저 수", f"{total_n:,}")
                st.progress(min(total_n / (st.session_state.get('n', 1000)*2), 1.0))
                
                if total_n > 0:
                    if st.button("다음: 결과 분석 ➡️", type="primary", use_container_width=True):
                        st.session_state['step'] = 5
                        st.rerun()
        
        with col_db:
            with st.container(border=True):
                st.markdown("#### 💾 실시간 DB (DuckDB)")
                tab1, tab2 = st.tabs(["Assignments (할당)", "Events (행동)"])
                with tab1:
                    df_a = run_query("SELECT * FROM assignments ORDER BY assigned_at DESC LIMIT 5", con)
                    st.dataframe(df_a, use_container_width=True, hide_index=True)
                with tab2:
                    df_e = run_query("SELECT * FROM events ORDER BY timestamp DESC LIMIT 5", con)
                    st.dataframe(df_e, use_container_width=True, hide_index=True)

    # --- STEP 5: ANALYSIS ---
    elif curr == 5:
        st.markdown(f"<h2>Step 5. 최종 분석 (Final Analysis)</h2>", unsafe_allow_html=True)
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
                
                if st.button("💾 포트폴리오에 저장", type="primary", use_container_width=True):
                    con.execute(f"INSERT INTO experiments (hypothesis, primary_metric, p_value, decision, learning_note, created_at) VALUES ('{st.session_state.get('hypothesis','-')}', '{st.session_state.get('metric','-')}', {p_val}, '{decision}', '{note}', CURRENT_TIMESTAMP)")
                    
                    # Cleanup
                    con.execute("DELETE FROM assignments")
                    con.execute("DELETE FROM events")
                    
                    st.toast("저장되었습니다!")
                    st.session_state['page'] = 'portfolio'
                    st.session_state['step'] = 1
                    st.rerun()

# =========================================================
# PAGE: PORTFOLIO
# =========================================================
elif st.session_state['page'] == 'portfolio':
    st.title("🗄️ 나의 실험 포트폴리오 (Portfolio)")
    st.markdown("### 성장 기록 아카이브")
    
    df_history = run_query("SELECT * FROM experiments ORDER BY created_at DESC", con)
    
    if df_history.empty:
        st.info("아직 진행된 실험이 없습니다. 마스터 클래스에서 첫 실험을 시작해보세요!")
    else:
        for _, row in df_history.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"#### {row['hypothesis']}")
                    st.caption(f"날짜: {row['created_at']} | 지표: {row['primary_metric']}")
                    if row['learning_note']:
                        st.markdown(f"> *{row['learning_note']}*")
                with c2:
                    p = row['p_value']
                    color = "#4ade80" if row['decision'] == 'Significant' else "#94a3b8"
                    st.markdown(f"<div style='text-align:right; font-weight:bold; color:{color}; font-size:1.2rem;'>{row['decision']}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='text-align:right; font-size:0.9rem; color:rgba(255,255,255,0.5);'>P = {p:.4f}</div>", unsafe_allow_html=True)
