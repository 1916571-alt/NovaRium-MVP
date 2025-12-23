import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import streamlit.components.v1 as components

# Import modularized logic
import analytics as al
import components as ui

# Page Config
st.set_page_config(
    page_title="NovaRium Edu",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize Session State
if 'page' not in st.session_state: st.session_state['page'] = 'monitor'
if 'step' not in st.session_state: st.session_state['step'] = 1
if 'custom_metrics' not in st.session_state: st.session_state['custom_metrics'] = []

# --- APPLY STYLES & HEADER ---
ui.apply_custom_css()
ui.render_navbar()

st.write("") # Spacer

con = al.get_connection()

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

    # Check if history data exists
    check_history = al.run_query("SELECT COUNT(*) as cnt FROM assignments WHERE user_id LIKE 'user_hist_%'", con)
    has_history = not check_history.empty and check_history.iloc[0, 0] > 0
    
    if not has_history:
        st.warning("데이터가 없습니다. 30일치 히스토리를 생성하세요.")
        if st.button("🔄 데이터 생성하기 (30일치)", type="primary"):
            st.info("터미널에서 `python scripts/generate_history.py`를 실행하세요.")
    else:
        # Data exists - show regenerate option with warning
        with st.expander("⚙️ 데이터 관리"):
            st.warning("⚠️ 기존 30일치 히스토리 데이터가 존재합니다.")
            if st.button("🔄 데이터 재생성 (기존 데이터 삭제)", type="secondary"):
                if st.button("✅ 예, 재생성"):
                     st.info("터미널에서 `python scripts/generate_history.py`를 실행하세요.")

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
    df_trend = al.run_query(sql_kpi, con)
    
    if not df_trend.empty:
        # 30-Day Average Stats (instead of latest day)
        avg_users = df_trend['users'].mean()
        avg_ctr = df_trend['ctr'].mean()
        avg_cvr = df_trend['cvr'].mean()
        avg_orders = df_trend['orders'].mean()
        
        # Latest vs Previous for delta
        latest = df_trend.iloc[-1]
        prev = df_trend.iloc[-2] if len(df_trend) > 1 else latest
        
        # KPI Cards (30-day average)
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.metric("Daily Active Users (30d Avg)", f"{int(avg_users):,}", f"{int(latest['users']-prev['users'])}")
        with k2:
            st.metric("Banner Click Rate (CTR)", f"{avg_ctr*100:.2f}%", f"{(latest['ctr']-prev['ctr'])*100:.2f}%")
        with k3:
            st.metric("Conversion Rate (CVR)", f"{avg_cvr*100:.2f}%", f"{(latest['cvr']-prev['cvr'])*100:.2f}%")
        with k4:
             st.metric("Orders (30d Avg)", f"{int(avg_orders):,}", f"{int(latest['orders']-prev['orders'])}")
        
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
            
# =========================================================
# PAGE: STUDY (WIZARD)
# =========================================================
elif st.session_state['page'] == 'study':
    
    # --- Progress Indicators (Nebula Style) ---
    steps = ["1. Hypothesis", "2. Design", "3. Collection", "4. Analysis"]
    ui.render_step_progress(steps, st.session_state['step'])
    
    curr = st.session_state['step']

    # --- STEP 1: HYPOTHESIS ---
    if curr == 1:
        st.markdown(f"<h2>Step 1. 목표 정의 (Define Your Vision)</h2>", unsafe_allow_html=True)
        ui.edu_guide("가설(Hypothesis)", "데이터 분석은 막연한 시도가 아닙니다. **'무엇을(X) 바꾸면 어떤 지표(Y)가 좋아질 것이다'**라는 명확한 믿음을 정의하세요.")

        col_mock, col_form = st.columns([1.5, 1], gap="large")
        
        # 1. Real Target App (Iframe)
        with col_mock:
            with st.container(border=True):
                st.markdown("#### 📱 NovaEats (Live Target)")
                st.caption("실제 구동 중인 웹 서버(FastAPI) 화면입니다. 에이전트들이 이곳을 방문하게 됩니다.")
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
                    t_ctx = st.session_state.get('target', '')
                    def_what = "메인 배너 문구를 '마감 임박'으로 변경하면"
                    def_why = "클릭률(CTR)이 15%까지 회복될 것이다"
                    
                    h_who = st.selectbox("대상(Who)", ["모든 유저에게", "신규 유저에게", "재구매 유저에게"])
                    h_what = st.text_input("무엇을(Changes)", def_what)
                    h_why = st.text_input("기대 효과(Impact)", def_why)
                    
                    if st.button("템플릿 적용"):
                        st.session_state['temp_hypo'] = f"{h_who}, {h_what}, {h_why}."
                        st.rerun()
                
                default_hypo = st.session_state.get('temp_hypo', "")
                hypo = st.text_area("가설을 작성하세요", value=default_hypo, placeholder="예: 메인 배너 문구를 '마감 임박'으로 변경하면, 클릭률(CTR)이 상승할 것이다.", height=120)
                
                st.write("")
                # Metrics Setup
                st.markdown("#### 🎯 지표 설정 (Metrics)")
                metrics_db = {
                    "CTR (클릭률)": {"desc": "노출 대비 클릭한 비율", "formula": "Clicks / Impressions", "type": "Conversion"},
                    "CVR (전환율)": {"desc": "방문자 중 실제 구매 비율", "formula": "Orders / Visitors", "type": "Conversion"},
                    "AOV (평균 주문액)": {"desc": "구매 고객 1인당 평균 결제 금액", "formula": "Revenue / Orders", "type": "Revenue"},
                    "Bounce Rate (이탈률)": {"desc": "첫 페이지만 보고 나가는 비율", "formula": "One-page / Total", "type": "Retention"},
                }
                
                m_sel = st.selectbox("Key Metric (OEC)", list(metrics_db.keys()), label_visibility="collapsed")
                st.caption(f"🧮 {metrics_db[m_sel]['desc']}")

                # Guardrail Metrics
                st.markdown("**2. 가드레일 지표 (Guardrail Metrics)**")
                default_gr = ["AOV (평균 주문액)"] if m_sel != "AOV (평균 주문액)" else ["CVR (전환율)"]
                g_sel = st.multiselect("보조 지표 선택", [k for k in metrics_db.keys() if k != m_sel], default=default_gr)
                
                if g_sel:
                    guard_threshold = st.number_input("허용 임계치 (%)", min_value=0.0, max_value=20.0, value=5.0, step=0.5)
                    st.info(f"💡 **{g_sel[0]}**이(가) **{guard_threshold}%**를 넘으면 조기 종료 경고가 표시됩니다.")
                    guard_metric_name = g_sel[0]
                else:
                    guard_threshold = 5.0
                    guard_metric_name = "Refund Rate"

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
                        st.session_state['guard_threshold'] = guard_threshold
                        st.session_state['guard_metric'] = guard_metric_name
                        st.session_state['step'] = 2
                        st.rerun()

    # --- STEP 2: EXPERIMENT DESIGN ---
    elif curr == 2:
        st.markdown(f"<h2>Step 2. 실험 설계 (Experiment Design)</h2>", unsafe_allow_html=True)
        ui.edu_guide("실험 설계의 3요소", "트래픽 비율 → 목표 설정 → 필요 표본 계산 순서로 진행합니다.")
        
        col_ratio = st.columns([1, 1], gap="large")
        with col_ratio[0]:
            with st.container(border=True):
                st.markdown("#### 🎛️ 비율 선택")
                split = st.slider("테스트(B) 그룹 비율", 10, 90, 50, format="%d%%")
                st.caption(f"Control(A): {100-split}% | Test(B): {split}%")
        
        with col_ratio[1]:
            with st.container(border=True):
                st.markdown("#### 🔍 Hash 검증")
                uid = st.text_input("User ID", "user_cosmic_99", key="hash_uid")
                b = al.get_bucket(uid)
                threshold = 100 - split
                grp = "B" if b >= threshold else "A"
                st.markdown(f"**Hash: {b}** → Group **{grp}**")
        
        st.divider()
        st.markdown("### 2️⃣ 목표 설정 및 표본 계산")

        c1, c2 = st.columns(2, gap="large")
        with c1:
            with st.container(border=True):
                st.markdown("#### ⚙️ Parameters")
                selected_metric = st.session_state.get('metric', 'CTR (클릭률)')
                
                # Fetch baseline
                sql_baseline = """
                SELECT 
                    (COUNT(DISTINCT CASE WHEN e.event_name = 'click_banner' THEN e.user_id END)::FLOAT / 
                     NULLIF(COUNT(DISTINCT a.user_id), 0)) as metric_value
                FROM assignments a
                LEFT JOIN events e ON a.user_id = e.user_id
                WHERE a.user_id LIKE 'user_hist_%'
                """
                if "CVR" in selected_metric:
                     sql_baseline = sql_baseline.replace("'click_banner'", "'purchase'")

                df_baseline = al.run_query(sql_baseline, con)
                auto_baseline = df_baseline.iloc[0, 0] if not df_baseline.empty and df_baseline.iloc[0, 0] else 0.10
                
                st.markdown(f"**현재 {selected_metric}** (자동 감지)")
                st.markdown(f"<div style='font-size:1.5rem; font-weight:bold; color:#ef4444;'>{auto_baseline*100:.2f}%</div>", unsafe_allow_html=True)
                
                st.write("")
                target_metric = st.number_input(f"**목표 {selected_metric}**", min_value=0.0, max_value=1.0, value=0.15, step=0.01)
                
                mde = (target_metric - auto_baseline) / auto_baseline if auto_baseline > 0 else 0
                st.caption(f"💡 상승폭: +{mde*100:.1f}%")
        
        with c2:
            with st.container(border=True):
                st.markdown("#### 🧮 필요 표본 수 (Required Sample)")
                n = al.calculate_sample_size(auto_baseline, mde)
                
                total_needed = n * 2
                st.markdown(f"<div class='big-stat'>{total_needed:,}</div>", unsafe_allow_html=True)
                st.markdown("**명 (총 필요 유저 수)**")
                st.progress(min(1.0, 0.3 + (mde * 2)))

        st.write("")
        if st.button("다음: 데이터 수집 시작 (Simulation) ➡️", type="primary", use_container_width=True):
            st.session_state['n'] = n
            st.session_state['split'] = split
            st.session_state['step'] = 3
            st.rerun()

    # --- STEP 3: COLLECTION (SIMULATION) ---
    elif curr == 3:
        st.markdown(f"<h2>Step 3. 데이터 모으기 (Collection)</h2>", unsafe_allow_html=True)
        ui.edu_guide("실시간 시뮬레이션", "Agent System이 가상의 유저가 되어 앱을 방문합니다.")
        
        # Agent Persona Settings
        with st.expander("🤖 에이전트 성향 설정 (Advanced)", expanded=False):
            st.caption("다양한 성향의 유저 비율을 조정해보세요.")
            c_p1, c_p2, c_p3, c_p4, c_p5 = st.columns(5)
            # Default distribution
            p_impulsive = c_p1.slider("충동형", 0, 100, 20)
            p_rational = c_p2.slider("계산형", 0, 100, 20)
            p_window = c_p3.slider("아이쇼핑", 0, 100, 40)
            p_mission = c_p4.slider("목적형", 0, 100, 10)
            p_cautious = c_p5.slider("신중형", 0, 100, 10)
            
            total_p = p_impulsive + p_rational + p_window + p_mission + p_cautious
            if total_p != 100:
                st.warning(f"합계가 100%가 되어야 합니다. (현재: {total_p}%)")

        col_sim, col_chart = st.columns([1, 1], gap="large")
        
        with col_sim:
            with st.container(border=True):
                st.markdown("#### 🚀 시뮬레이션 제어")
                st.info(f"Target: {st.session_state['n'] * 2:,}명 방문 예정")
                
                if st.button("▶️ Agent Swarm 투입 (Start)", type="primary", use_container_width=True):
                    with st.spinner("에이전트들이 쇼핑몰을 방문 중입니다..."):
                        # In a real scenario, this would trigger external scripts
                        # For now, we use synthetic data injection (same logic as before)
                        import scripts.generating_data as gen # Re-use generation logic
                        
                        # Simplified injection for demo speed
                        # Ideally, this calls agent_swarm/runner.py
                        # Here we simulate the OUTPUT of that runner
                        
                        # Generate dummy traffic around the target sample size
                        needed = st.session_state['n'] * 2
                        
                        # Use SQL to check if we already ran needed amount
                        curr_cnt = al.run_query("SELECT COUNT(*) FROM assignments WHERE user_id LIKE 'sim_%' OR user_id LIKE 'agent_%'", con).iloc[0,0]
                        
                        if curr_cnt < needed:
                            # Verify target App is running
                            try:
                                import requests
                                r = requests.get("http://localhost:8000")
                                if r.status_code != 200: raise Exception("Server/8000 down")
                            except:
                                st.error("Target App(Port 8000)에 연결할 수 없습니다. 터미널에서 `python target_app/main.py`를 실행해주세요.")
                                st.stop()

                            # Call runner (subprocess)
                            import subprocess
                            import sys
                            try:
                                # Construct weights string
                                weights = f"{p_impulsive},{p_rational},{p_window},{p_mission},{p_cautious}"
                                cmd = [sys.executable, "agent_swarm/runner.py", "--count", str(needed), "--weights", weights]
                                subprocess.run(cmd, check=True)
                            except Exception as e:
                                st.error(f"Simulation Failed: {e}")
                            
                            st.toast("시뮬레이션 완료! 데이터가 수집되었습니다.")
                            st.rerun()

        with col_chart:
            # Live counts
            df_live = al.run_query("""
                SELECT 
                    variant, 
                    COUNT(DISTINCT user_id) as visitors 
                FROM assignments 
                WHERE user_id LIKE 'sim_%' OR user_id LIKE 'agent_%'
                GROUP BY 1
            """, con)
            
            if not df_live.empty:
                st.bar_chart(df_live, x="variant", y="visitors", color="variant", horizontal=True)
            else:
                st.info("데이터 대기 중...")
        
        st.write("")
        if st.button("다음: 결과 분석 (Analysis) ➡️", type="primary", use_container_width=True):
             st.session_state['step'] = 4
             st.rerun()

    # --- STEP 4: ANALYSIS ---
    elif curr == 4:
        st.markdown(f"<h2>Step 4. 결론 내리기 (Analysis)</h2>", unsafe_allow_html=True)
        ui.edu_guide("P-value 검정", "우연히 이런 결과가 나올 확률을 계산합니다. 0.05(5%) 미만이어야 '통계적으로 유의미'하다고 봅니다.")
        
        primary_metric = st.session_state.get('metric', 'CTR (클릭률)')
        
        # Determine event name for query
        metric_event_map = {
            "CTR (클릭률)": "click_banner",
            "CVR (전환율)": "purchase",
            "AOV (평균 주문액)": "purchase"
        }
        event_name = metric_event_map.get(primary_metric, "click_banner")
        
        # Get Stats
        sql = f"""
        SELECT 
            a.variant,
            COUNT(DISTINCT a.user_id) as users,
            COUNT(DISTINCT e.user_id) as conversions
        FROM assignments a
        LEFT JOIN events e ON a.user_id = e.user_id AND e.event_name = '{event_name}'
        WHERE a.user_id LIKE 'sim_%' OR a.user_id LIKE 'agent_%'
        GROUP BY 1 ORDER BY 1
        """
        
        df = al.run_query(sql, con)
        
        # Calculate P-value and Stats using analytics module
        if len(df) == 2:
            res = al.calculate_statistics(
                df.iloc[0]['users'], df.iloc[0]['conversions'],
                df.iloc[1]['users'], df.iloc[1]['conversions']
            )
        else:
            res = {"lift": 0, "p_value": 1.0}

        c1, c2 = st.columns([1.5, 1], gap="large")
        with c1:
            with st.container(border=True):
                st.markdown("#### 📊 데이터 집계 (Data)")
                st.dataframe(df, use_container_width=True, hide_index=True)
        
        with c2:
            with st.container(border=True):
                st.markdown("#### 🏁 최종 성적표")
                
                if len(df) == 2:
                    st.metric("Lift (개선율)", al.format_delta(res['lift']), delta=None)
                    st.caption(f"📊 P-value: **{res['p_value']:.4f}**")
                    
                    if res['p_value'] < 0.05:
                        st.success(f"**WINNER** (실험 성공!)")
                        decision = "Significant"
                    else:
                        st.warning(f"**TIE** (차이 없음)")
                        decision = "Inconclusive"
                else:
                    st.info("데이터 부족")
                    decision = "No Data"
                
                # Report Saving
                st.divider()
                note = st.text_area("배운 점 (Learning Note)")
                if st.button("💾 실험 회고록에 저장", type="primary"):
                    con.execute(f"""
                        INSERT INTO experiments (
                            target, hypothesis, primary_metric, created_at, p_value, decision, learning_note
                        ) VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?)
                    """, [
                        st.session_state.get('target', '-'), 
                        st.session_state.get('hypothesis', '-'),
                        st.session_state.get('metric', '-'),
                        res['p_value'], decision, note
                    ])
                    # Cleanup Sim Data
                    con.execute("DELETE FROM assignments WHERE user_id LIKE 'sim_%' OR user_id LIKE 'agent_%'")
                    con.execute("DELETE FROM events WHERE user_id LIKE 'sim_%' OR user_id LIKE 'agent_%'")
                    
                    st.toast("저장 완료!")
                    st.session_state['page'] = 'portfolio'
                    st.session_state['step'] = 1
                    st.rerun()

# =========================================================
# PAGE: PORTFOLIO
# =========================================================
elif st.session_state['page'] == 'portfolio':
    st.title("📚 실험 회고록 (Experiment Retrospective)")
    
    df_history = al.run_query("SELECT * FROM experiments ORDER BY created_at DESC", con)
    
    if df_history.empty:
        st.info("실험 기록이 없습니다.")
    else:
        for _, row in df_history.iterrows():
            with st.container(border=True):
                st.markdown(f"**{row['hypothesis']}**")
                st.caption(f"{row['created_at']} | Result: {row['decision']}")
