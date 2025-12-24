import streamlit as st
import pandas as pd
import numpy as np
import duckdb
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import streamlit.components.v1 as components

import sys
import os
# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import modularized logic
from src.core import stats as al
from src.ui import components as ui
from src.core import mart_builder as mb  # New Module

# Page Config
st.set_page_config(
    page_title="NovaRium Edu",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize Session State
if 'page' not in st.session_state: st.session_state['page'] = 'data_lab' # Default to Data Lab
if 'step' not in st.session_state: st.session_state['step'] = 1
if 'custom_metrics' not in st.session_state: st.session_state['custom_metrics'] = []

# --- APPLY STYLES & HEADER ---
ui.apply_custom_css()
ui.render_navbar()

st.write("") # Spacer

# con = al.get_connection() # [REMOVED] Global connection causes locking issues
# DB_PATH will be used for specific query connections
DB_PATH = al.DB_PATH

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
# PAGE: DATA ENGINEERING LAB (NEW)
# =========================================================
elif st.session_state['page'] == 'data_lab':
    st.markdown("## 🛠️ 데이터 엔지니어링 랩 (Data Mart Builder)")
    st.caption("비즈니스 대시보드를 구축하기 위해 먼저 Raw Data를 분석 가능한 'Data Mart'로 가공해야 합니다.")
    
    col_setup, col_code = st.columns([1, 1.2], gap="large")
    
    with col_setup:
        with st.container(border=True):
            st.markdown("### 1. 마트 설계 (Schema Design)")
            st.info("💡 분석가님, 대시보드에서 어떤 지표를 보고 싶으신가요?")
            
            # Default metrics
            metrics = st.multiselect(
                "포함할 핵심 지표 (Metrics)",
                options=['total_users (DAU)', 'revenue (매출)', 'ctr (클릭률)', 'cvr (전환율)', 'aov (객단가)', 'arpu (인당 매출)', 'session_depth (인당 활동량)'],
                default=['total_users (DAU)', 'revenue (매출)', 'ctr (클릭률)', 'cvr (전환율)', 'aov (객단가)']
            )
            
            # Helper logic to parse selection to clean keys
            clean_metrics = []
            if any('revenue' in m for m in metrics): clean_metrics.append('revenue')
            if any('ctr' in m for m in metrics): clean_metrics.append('ctr')
            if any('cvr' in m for m in metrics): clean_metrics.append('cvr')
            if any('aov' in m for m in metrics): clean_metrics.append('aov')
            if any('arpu' in m for m in metrics): clean_metrics.append('arpu')
            if any('session_depth' in m for m in metrics): clean_metrics.append('session_depth')
            
            st.write("")
            if st.button("🚀 데이터 마트 구축 (Build & Run)", type="primary", use_container_width=True):
                # Execute ETL
                with st.spinner("ETL 파이프라인 가동 중... (Airflow Task #101)"):
                    try:
                        # 1. Generate SQL
                        sql = mb.generate_mart_sql(clean_metrics)
                        
                        # 2. Execute
                        import duckdb
                        with duckdb.connect(DB_PATH) as txn_con:
                            txn_con.execute("BEGIN TRANSACTION")
                            txn_con.execute(sql)
                            txn_con.execute("COMMIT")
                            
                            # 3. Validation
                            row_count = txn_con.execute("SELECT COUNT(*) FROM dm_daily_kpi").fetchone()[0]
                            st.success(f"구축 완료! 총 {row_count:,}개의 일별 데이터가 적재되었습니다.")
                        
                        # Move to dashboard
                        import time
                        time.sleep(1)
                        st.session_state['page'] = 'monitor'
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"ETL 실패: {e}")

            st.divider()
            st.markdown("**🔍 데이터 흐름 (Data Lineage)**")
            # Fixed scale to 1.1 for optimal visibility
            st.graphviz_chart(mb.generate_mart_diagram(clean_metrics, scale=1.1), use_container_width=True)

    with col_code:
        st.markdown("### 2. SQL 쿼리 생성기 (Query Generator)")
        st.caption("선택하신 설계에 따라 자동으로 생성된 ETL 쿼리입니다. 현업에서는 이 코드가 Airflow에서 매일 새벽에 실행됩니다.")
        
        # Real-time SQL Generation
        generated_sql = mb.generate_mart_sql(clean_metrics)
        st.code(generated_sql, language="sql")
        
        st.markdown("""
        > [!NOTE]
        > **왜 SQL을 직접 짜지 않고 생성하나요?**  
        > 데이터 엔지니어링에서는 휴먼 에러를 줄이기 위해, 메타데이터(설계)를 기반으로 쿼리를 자동 생성(Templating)하는 방식을 자주 사용합니다.
        """)

# =========================================================
# PAGE: SITUATION ROOM (DASHBOARD)
# =========================================================
if st.session_state['page'] == 'monitor':
    # --- HEADER SECTION ---
    st.markdown("""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 20px;">
        <div>
            <h2 style="margin:0;">🛸 종합 상황실 (Operations Center)</h2>
            <p style="margin:0; opacity:0.7;">NovaEats 서비스의 실시간 매출 및 운영 현황을 모니터링합니다.</p>
        </div>
        <div style="text-align:right;">
            <span style="background:rgba(74, 222, 128, 0.1); color:#4ade80; padding:4px 12px; border-radius:15px; font-size:0.8rem; font-weight:bold;">● Live System Online</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    check_history = al.run_query("SELECT COUNT(*) as cnt FROM assignments WHERE user_id LIKE 'user_hist_%'")
    has_history = not check_history.empty and check_history.iloc[0, 0] > 0
    
    if not has_history:
        st.warning("경고: 과거 데이터가 없습니다. 원활한 상황실 운영을 위해 30일치 데이터를 생성하세요.")
        if st.button("🔄 데이터 초기화 (Reset)", type="primary"):
            st.info("터미널에서 `python scripts/generate_history.py`를 실행하세요.")
    else:
        # --- TIER 1: REAL-TIME PULSE (LIVE) ---
        st.markdown("### 🟢 실시간 운영 현황 (Real-time Pulse)")

        # Real-time Queries (No Random Simulation)
        # 1. Active Users (Last 30 mins)
        sql_live = """
            SELECT 
                COUNT(DISTINCT user_id) as active_users,
                (SELECT COUNT(*) FROM events 
                 WHERE event_name = 'purchase' 
                 AND timestamp >= CURRENT_DATE) as today_orders,
                 (SELECT COALESCE(SUM(value), 0) FROM events 
                 WHERE event_name = 'purchase' 
                 AND timestamp >= CURRENT_DATE) as today_revenue
            FROM events 
            WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 30 MINUTE
        """
        live_stats = al.run_query(sql_live)
        
        if not live_stats.empty:
            now_users = live_stats.iloc[0]['active_users']
            today_orders = live_stats.iloc[0]['today_orders']
            today_rev = live_stats.iloc[0]['today_revenue']
        else:
            now_users, today_orders, today_rev = 0, 0, 0

        # Server Latency Check (Real Ping)
        import time
        import requests
        start_time = time.time()
        latency_ms = 0
        server_status = "Offline"
        
        try:
             # Check localhost:8000
             requests.get("http://localhost:8000", timeout=1)
             latency_ms = int((time.time() - start_time) * 1000)
             server_status = "Online"
        except:
             latency_ms = 0
             server_status = "Down"

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("현재 접속자 (30min)", f"{now_users}명", "Real-time")
        with c2:
            st.metric("오늘 매출 (Values)", f"₩{int(today_rev):,}", f"{today_orders} Orders")
        with c3:
            st.metric("시스템 상태 (Health)", server_status, f"{latency_ms}ms")
        with c4:
             st.metric("데이터 마트 (ETL)", "Sync Active", "Daily Updated")
             
        # Recent Events (Real DB Fetch)
        st.caption("🔊 Recent Events Log (Real DB)")
        
        sql_log = """
            SELECT user_id, event_name, value, timestamp 
            FROM events 
            ORDER BY timestamp DESC LIMIT 3
        """
        df_log = al.run_query(sql_log)
        
        log_html_items = []
        for _, row in df_log.iterrows():
            ts = pd.to_datetime(row['timestamp']).strftime('%H:%M:%S')
            if row['event_name'] == 'purchase':
                 item = f"<span style='color:#4ADE80;'>[{ts}] 💰 Purchase (User_{row['user_id'][-4:]}: ₩{int(row['value']):,})</span>"
            else:
                 item = f"<span style='color:#A78BFA;'>[{ts}] Action: {row['event_name']}</span>"
            log_html_items.append(item)
            
        ticker_html = f"""
        <div style="background:rgba(255,255,255,0.05); padding:10px; border-radius:8px; display:flex; gap:20px; font-family:monospace; font-size:0.9rem; overflow:hidden;">
            {''.join(log_html_items) if log_html_items else '<span>대기 중... (No Events)</span>'}
        </div>
        """
        st.markdown(ticker_html, unsafe_allow_html=True)
        
        st.divider()

        # --- TIER 2: BUSINESS INTELLIGENCE (FROM MART) ---
        st.markdown("### 🔵 비즈니스 분석 (Business Intelligence)")
        
        # Fetch from Data Mart
        # Using simple SELECT from pre-aggregated table
        sql_mart = "SELECT * FROM dm_daily_kpi ORDER BY report_date ASC"
        df_trend = al.run_query(sql_mart)
        
        if not df_trend.empty:
            # Safe Access Helper
            def get_col_safe(df, col):
                return df[col] if col in df.columns else pd.Series([0]*len(df))

            # Revenue Logic
            has_rev = 'total_revenue' in df_trend.columns
            avg_rev = df_trend['total_revenue'].mean() if has_rev else 0
            
            # AOV Logic
            has_aov = 'aov' in df_trend.columns
            avg_aov = df_trend['aov'].mean() if has_aov else 0

            # CVR Logic
            has_cvr = 'cvr' in df_trend.columns
            
            latest = df_trend.iloc[-1]
            prev = df_trend.iloc[-2] if len(df_trend) > 1 else latest
            
            # Business Metrics
            b1, b2, b3, b4 = st.columns(4)
            with b1:
                if has_rev:
                    st.metric("일평균 매출 (Revenue)", f"₩{int(avg_rev):,}", f"{int(latest['total_revenue']-prev['total_revenue']):,}원")
                else:
                    st.metric("일평균 매출 (Revenue)", "-", "Not Selected", help="Data Lab에서 'Revenue' 지표를 추가하세요.")
            with b2:
                if has_aov:
                    st.metric("객단가 (AOV)", f"₩{int(avg_aov):,}", f"{int(latest['aov']-prev['aov']):,}원")
                else:
                     st.metric("객단가 (AOV)", "-", "Not Selected", help="Data Lab에서 'AOV' 지표를 추가하세요.")
            with b3:
                if has_cvr:
                    st.metric("구매 전환율 (CVR)", f"{latest['cvr']*100:.2f}%", f"{(latest['cvr']-prev['cvr'])*100:.2f}%")
                else:
                    st.metric("구매 전환율 (CVR)", "-", "Not Selected", help="Data Lab에서 'CVR' 지표를 추가하세요.")
            with b4:
                st.metric("재구매율 (Retention)", "28.4%", "예측치")

            # Chart Area
            tab_names = []
            if has_rev: tab_names.append("💰 매출 트렌드")
            if has_aov: tab_names.append("🛒 객단가(AOV)")
            tab_names.append("🔻 퍼널 분석") # Funnel is usually always possible if users/clicks exist
            
            tabs = st.tabs(tab_names)
            
            # Render Tabs dynamically
            idx = 0
            if has_rev:
                with tabs[idx]:
                    fig = px.area(df_trend, x='report_date', y='total_revenue', title='Daily Revenue Trend', template='plotly_dark')
                    fig.update_traces(line_color='#8B5CF6', fillcolor="rgba(139, 92, 246, 0.3)")
                    st.plotly_chart(fig, use_container_width=True)
                idx += 1
                
            if has_aov:
                with tabs[idx]:
                    fig2 = px.bar(df_trend, x='report_date', y='aov', title='Average Order Value (AOV)', template='plotly_dark')
                    fig2.update_traces(marker_color='#3B82F6')
                    st.plotly_chart(fig2, use_container_width=True)
                idx += 1
                
            with tabs[idx]:
                # Funnel logic needs specific cols too
                cols_present = df_trend.columns
                v_total = latest['total_users'] if 'total_users' in cols_present else 0
                v_click = latest['click_count'] if 'click_count' in cols_present else 0
                v_order = latest['total_orders'] if 'total_orders' in cols_present else 0
                
                funnel_data = dict(
                    number=[v_total, v_click, v_order], 
                    stage=["1. 방문 (Total Users)", "2. 클릭 (Active Clicks)", "3. 구매 (Orders)"]
                )
                fig3 = px.funnel(funnel_data, x='number', y='stage', title=f'Conversion Funnel ({latest["report_date"]})', template='plotly_dark')
                st.plotly_chart(fig3, use_container_width=True)

        st.divider()

        # --- TIER 3: SYSTEM & CRISIS MONITOR ---
        st.markdown("### 🟠 시스템 및 위기 감지 (System Integrity)")
        
        alerts = []
        
        if not df_trend.empty:
            # 1. CTR Alert (Content Fatigue)
            if 'ctr' in df_trend.columns and latest['ctr'] < 0.05:
                alerts.append({
                    "level": "Critical",
                    "title": "클릭률(CTR) 급락 경보",
                    "desc": f"현재 CTR이 **{latest['ctr']*100:.1f}%**입니다. (정상 범위: 15%~)",
                    "cause": "배너 소재 피로도 증가 또는 카피라이팅 매력도 저하",
                    "action": "메인 배너 교체 실험(A/B Test) 권장",
                    "target": "메인 배너 (할인 문구)",
                    "metric_key": "ctr",
                    "threshold": 0.05
                })

            # 2. Revenue Drop Alert (Business Risk)
            if 'total_revenue' in df_trend.columns and len(df_trend) > 1:
                prev_rev = prev['total_revenue']
                curr_rev = latest['total_revenue']
                # If revenue dropped by more than 30% compared to yesterday
                if prev_rev > 0 and (curr_rev / prev_rev) < 0.7:
                    drop_rate = (1 - (curr_rev / prev_rev)) * 100
                    alerts.append({
                        "level": "Warning",
                        "title": "매출(Revenue) 이상 하락",
                        "desc": f"전일 대비 매출이 **-{drop_rate:.1f}%** 감소했습니다.",
                        "cause": "구매 전환율(CVR) 저하 또는 결제 시스템 장애 가능성",
                        "action": "결제 프로세스 점검 및 할인율 조정 실험",
                        "target": "카테고리 아이콘 (치킨)", # Example fallback
                        "metric_key": "total_revenue",
                        "threshold": None
                    })

            # 3. CVR Alert (UX Friction)
            if 'cvr' in df_trend.columns and latest['cvr'] < 0.01: # Less than 1%
                 alerts.append({
                    "level": "Critical",
                    "title": "전환율(CVR) 위험 수준",
                    "desc": f"구매 전환율이 **{latest['cvr']*100:.1f}%**로 매우 낮습니다.",
                    "cause": "상세 페이지 UI 불편 또는 가격 저항선 도달",
                    "action": "상세 페이지 UI 개선 실험 필요",
                    "target": "카테고리 아이콘 (치킨)",
                    "metric_key": "cvr",
                    "threshold": 0.01
                })

        st.caption("ℹ️ **감지 로직(Detection Logic)**: CTR < 5% (소재 피로), 매출 하락 > 30% (이탈 위험), CVR < 1% (UX 마찰). 모든 데이터는 실제 DB(`dm_daily_kpi`)에서 실시간으로 연산됩니다.")

        # Render Alerts
        if alerts:
            for alert in alerts:
                with st.container(border=True):
                    # Layout: Text (Left) | Button (Right)
                    c_text, c_btn = st.columns([3.5, 1])
                    
                    with c_text:
                        st.markdown(f"#### 🚨 {alert['title']}")
                        st.markdown(f"**현상**: {alert['desc']}") 
                        st.info(f"**원인/조치**: {alert['cause']} → {alert['action']}")
                        
                    with c_btn:
                        st.write("") # Vertical spacer
                        st.write("") 
                        if st.button(f"⚡ 개선 실험 생성", key=f"btn_{alert['title']}", type="primary", use_container_width=True):
                            st.session_state['page'] = 'study'
                            st.session_state['step'] = 1
                            st.session_state['target'] = alert['target']
                            st.rerun()
                    
                    # Interactive Trend Chart
                    with st.expander("📉 상세 트렌드 분석 (Trend Analysis)", expanded=False):
                        metric = alert['metric_key']
                        if metric in df_trend.columns:
                            fig_alert = px.line(df_trend, x='report_date', y=metric, markers=True, title=f"{alert['title']} - Trend View", template="plotly_dark")
                            fig_alert.update_traces(line_color='#ef4444', line_width=3)
                            
                            # Add Threshold Line if exists
                            if alert.get('threshold'):
                                fig_alert.add_hline(y=alert['threshold'], line_dash="dash", line_color="yellow", annotation_text="Threshold (위험 기준)")
                                
                            st.plotly_chart(fig_alert, use_container_width=True)
                        else:
                            st.warning("해당 지표의 상세 데이터를 불러올 수 없습니다.")
        else:
            st.success("✅ 모든 시스템 및 비즈니스 지표가 정상 범위(Normal) 내에서 운영 중입니다.")
            st.caption(f"Based on real-time data from `dm_daily_kpi` (Updated: {datetime.now().strftime('%H:%M')})")
            
        with st.expander("⚙️ 데이터 관리 (Admin)"):
             if st.button("데이터 재생성 (Reset History)"):
                  st.warning("터미널에서 generate_history.py를 실행하세요.")
            
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

        # Component Mapping (Moved up for Iframe Logic)
        # Component Mapping (Moved up for Iframe Logic)
        # Component Mapping (Enhanced with Types for Robustness)
        PAGE_MAP = {
            "메인 홈 (/)": {
                "url": "/",
                "components": {
                    "메인 배너 (Hero Banner)": {"id": "hero-banner", "type": "BANNER"},
                    "카테고리 아이콘 (Category Icons)": {"id": "category-nav", "type": "ICON_SET"}
                }
            },
            "상세 페이지 (/detail)": {
                "url": "/detail",
                "components": {
                    "구매하기 버튼 (Primary CTA)": {"id": "add-to-cart-btn", "type": "BUTTON"},
                    "상품 가격 (Price Label)": {"id": "price-tag", "type": "TEXT"}
                }
            },
            "장바구니 (/cart)": {
                "url": "/cart",
                "components": {
                    "주문 결제 버튼 (Checkout CTA)": {"id": "checkout-btn", "type": "BUTTON"}
                }
            },
            "검색 결과 (/search)": {
                "url": "/search",
                "components": {
                    "검색 결과 카드 (Result Item)": {"id": "search-result-item", "type": "LAYOUT"}
                }
            },
            "주문 배달 현황 (/tracking)": {
                "url": "/tracking",
                "components": {
                    "도착 예정 시간 (ETA Header)": {"id": "arrival-time", "type": "TEXT"},
                    "라이더 마커 (Driver Icon)": {"id": "driver-marker", "type": "ICON"}
                }
            }
        }

        col_mock, col_form = st.columns([1.2, 1], gap="large")
        
        # Determine Current Selection
        default_page = list(PAGE_MAP.keys())[0]
        sel_page = st.session_state.get('builder_page', default_page)
        sel_comp_name = st.session_state.get('builder_comp', list(PAGE_MAP[sel_page]['components'].keys())[0])
        
        sel_url_path = PAGE_MAP[sel_page]['url']
        # Extract ID and Type
        sel_comp_data = PAGE_MAP[sel_page]['components'].get(sel_comp_name, {"id": "", "type": "TEXT"})
        sel_comp_id = sel_comp_data['id']
        comp_type = sel_comp_data['type']
        
        target_url = f"http://localhost:8000{sel_url_path}?highlight={sel_comp_id}"

        # 1. Real Target App (Iframe)
        with col_mock:
            with st.container(border=True):
                st.markdown("#### 📱 NovaEats (Live Target)")
                st.caption(f"실제 서버 화면: `{sel_url_path}` (Highlight: `{sel_comp_id}`)")
                try:
                    components.iframe(target_url, height=600, scrolling=True)
                except Exception:
                    st.error("서버 연결 실패: Target App이 실행 중인지 확인하세요.")

        # 2. Form (Glass Card) - Dynamic Builder
        with col_form:
            with st.container(border=True):
                st.markdown("#### 🧬 실험 설계 (Experiment Builder)")
                
                # Layout Strategy: Tabs to reduce vertical height
                tab_design, tab_strategy = st.tabs(["🎨 디자인 (Design)", "📊 전략 (Strategy)"])
                
                # --- TAB 1: DESIGN ---
                with tab_design:
                    st.caption("1. 실험 대상 & 변인 설정")
                    
                    # [A] Targeting
                    c1, c2 = st.columns(2)
                    with c1:
                        target_page = st.selectbox("페이지 (Page)", list(PAGE_MAP.keys()), key='builder_page')
                    with c2:
                        comp_options = list(PAGE_MAP[target_page]['components'].keys())
                        target_comp = st.selectbox("요소 (Component)", comp_options, key='builder_comp')
                    
                    current_target = f"{target_page} > {target_comp}"
                    st.session_state['target'] = current_target

                    # [B] Variables (Visual Simulator)
                    st.write("")
                    st.caption("2. 변인 시뮬레이션")

                    bg_map = {"Red (Urgent)": "#EF4444", "Blue (Trust)": "#3B82F6", "Black (Dark Mode)": "#111827", "#EF4444 (Red)": "#EF4444", "#3B82F6 (Blue)": "#3B82F6", "#10B981 (Green)": "#10B981", "#111827 (Black)": "#111827"}
                    
                    st.markdown(f"**Group B (Test)** <span style='background:#4B5563; padding:2px 6px; border-radius:4px; font-size:0.7em'>{comp_type}</span>", unsafe_allow_html=True)
                        
                    config_data = {}
                    variant_summary = ""
                    
                    # --- DYNAMIC FORM ---
                    if comp_type == 'BANNER':
                        config_data['title'] = st.text_input("타이틀", "첫 주문 50% 할인")
                        config_data['badge'] = st.text_input("뱃지", "선착순 마감")
                        config_data['theme'] = st.selectbox("테마", ["Red (Urgent)", "Blue (Trust)", "Black (Dark Mode)"])
                        variant_summary = f"{config_data['theme']} 테마, '{config_data['title']}'"
                        b_html = f"""<div style='background:{bg_map.get(config_data['theme'])}; border-radius:12px; padding:15px; color:white; box-shadow:0 4px 6px -1px rgba(0,0,0,0.1);'><span style='background:rgba(255,255,255,0.2); font-size:10px; padding:2px 6px; border-radius:4px;'>{config_data['badge']}</span><h3 style='margin:5px 0; font-size:16px;'>{config_data['title']}</h3><button style='background:white; color:{bg_map.get(config_data['theme'])}; border:none; padding:4px 12px; border-radius:20px; font-size:10px; font-weight:bold; cursor:pointer;'>Click</button></div>"""
                        
                    elif comp_type == 'BUTTON':
                        config_data['text'] = st.text_input("텍스트", "지금 주문하기")
                        config_data['color'] = st.selectbox("색상", ["#EF4444 (Red)", "#3B82F6 (Blue)", "#10B981 (Green)", "#111827 (Black)"])
                        variant_summary = f"{config_data['color']} 버튼"
                        color_code = bg_map.get(config_data['color'])
                        b_html = f"""<button style='background:{color_code}; color:white; border:none; padding:10px 20px; border-radius:8px; font-weight:bold; box-shadow:0 10px 15px -3px {color_code}66; width:100%;'>{config_data['text']}</button>"""
                        
                    elif comp_type == 'ICON_SET' or comp_type == 'ICON':
                        config_data['style'] = st.selectbox("스타일", ["3D Render (Playful)", "Flat Line (Clean)"])
                        variant_summary = f"{config_data['style']} 아이콘"
                        # Mock Images for demo
                        img_url = "https://cdn-icons-png.flaticon.com/512/3075/3075977.png" if "3D" in config_data['style'] else "https://cdn-icons-png.flaticon.com/512/709/709699.png"
                        b_html = f"""<div style='text-align:center;'><img src='{img_url}' style='width:64px; height:64px; drop-shadow:0 10px 10px rgba(0,0,0,0.2);'></div>"""

                    elif comp_type == 'TEXT':
                        config_data['content'] = st.text_input("내용", "수정된 텍스트")
                        config_data['size'] = st.slider("크기 (px)", 12, 32, 18)
                        config_data['color'] = st.color_picker("색상", "#EF4444")
                        variant_summary = f"텍스트 변경"
                        b_html = f"""<div style='font-size:{config_data['size']}px; color:{config_data['color']}; font-weight:bold; text-align:center;'>{config_data['content']}</div>"""
                    
                    else:
                        val = st.text_input("변경 내용", "Layout Change")
                        variant_summary = val
                        b_html = f"<div style='background:#374151; padding:10px; border-radius:8px; text-align:center; color:#9CA3AF;'>{val}</div>"

                    st.caption("👇 미리보기 (Preview)")
                    st.markdown(b_html, unsafe_allow_html=True)
                    
                    st.success("✅ 디자인 설정 완료! 상단의 **'📊 전략 (Strategy)'** 탭으로 이동하세요.", icon="👉")

                    st.session_state['exp_variant_data'] = config_data
                    variant_val = variant_summary
                    
                # --- TAB 2: STRATEGY ---
                with tab_strategy:
                    # [C] Hypothesis
                    st.caption("3. 가설 수립 (Hypothesis)")
                    default_hypo = st.session_state.get('temp_hypo', "")
                    if not default_hypo:
                         placeholder_text = f"만약 '{target_comp}'을(를) '{variant_summary[:20]}...'으로 변경한다면, [지표]가 상승할 것이다."
                    else:
                         placeholder_text = ""     
                    hypo = st.text_area("가설 구체화", value=default_hypo, placeholder=placeholder_text, height=80)
                    
                    if st.checkbox("💡 가설 템플릿 사용"):
                        def_why = "클릭률(CTR)이 15%까지 회복될 것이다"
                        h_who = st.selectbox("대상(Who)", ["모든 유저에게", "신규 유저에게", "재구매 유저에게"])
                        h_impact = st.text_input("기대 효과(Impact)", def_why)
                        if st.button("템플릿 적용"):
                            st.session_state['temp_hypo'] = f"{h_who}, {target_comp}을(를) {variant_summary}로 변경하면, {h_impact}."
                            st.rerun()

                    st.divider()

                    # [D] Advanced Metrics
                    st.markdown("#### 🎯 핵심 지표 (OEC)")
                    
                    # Auto Recommendation logic
                    rec_metric = "CTR (클릭률)"
                    if comp_type == 'BUTTON': rec_metric = "CVR (전환율)"
                    elif comp_type == 'TEXT' or comp_type == 'ICON': rec_metric = "Bounce Rate (이탈률)"
                    
                    st.success(f"🤖 AI 추천: **{rec_metric}** (요소 속성 '{comp_type}' 기반)")

                    metrics_db = {
                        "CTR (클릭률)": {"desc": "노출 대비 클릭한 비율", "formula": "Clicks / Impressions", "type": "Conversion"},
                        "CVR (전환율)": {"desc": "방문자 중 실제 구매 비율", "formula": "Orders / Visitors", "type": "Conversion"},
                        "AOV (평균 주문액)": {"desc": "구매 고객 1인당 평균 결제 금액", "formula": "Revenue / Orders", "type": "Revenue"},
                        "Bounce Rate (이탈률)": {"desc": "첫 페이지만 보고 나가는 비율", "formula": "One-page / Total", "type": "Retention"},
                    }
                    
                    c_m1, c_m2 = st.columns([1.2, 1], gap="medium")
                    with c_m1:
                        m_sel = st.selectbox("핵심 지표 (Primary Metric)", list(metrics_db.keys()), index=list(metrics_db.keys()).index(rec_metric))
                        st.caption(f"{metrics_db[m_sel]['desc']}")
                        
                        st.markdown("---")
                        st.caption(f"🚀 성공 판단 기준 (MDE)")
                        min_eff = st.slider("최소 목표 상승폭", 1, 30, 5, format="+%d%%", help=f"실험군(B)의 {m_sel}가 대조군(A)보다 최소 이만큼은 높아야 성공으로 간주합니다.")

                    with c_m2:
                        st.caption("🛡️ 안전 장치 (Guardrail Metrics)")
                        avail_gr = [k for k in metrics_db.keys() if k != m_sel]
                        g_sel = st.multiselect("보조 지표 (악영향 감지)", avail_gr, default=avail_gr[:1])
                        
                        if g_sel:
                            st.info(f"⚠️ **{g_sel[0]}** 등이 급락하지 않는지 감시합니다.")
                            guard_threshold = st.slider("최대 허용 하락폭 (Safety Margin)", 1.0, 20.0, 5.0, format="-%.1f%%", help="가드레일 지표가 이 기준 이상 떨어지면 경고가 발생합니다.")
                        else:
                            st.caption("설정된 가드레일 지표가 없습니다.")
                            guard_threshold = 5.0

                st.write("")
                if st.button("실험 설계 완료 및 다음 단계 ➡️", type="primary", use_container_width=True):
                    if not hypo:
                        st.toast("가설을 입력해야 진행할 수 있습니다!", icon="⚠️")
                    elif not variant_val:
                          st.toast("Group B의 변경 사항을 입력해주세요!", icon="⚠️")
                    else:
                        st.session_state['hypothesis'] = hypo
                        st.session_state['metric'] = m_sel
                        st.session_state['guardrails'] = g_sel
                        st.session_state['session_guard_threshold'] = guard_threshold  # Save dynamic input
                        st.session_state['min_effect'] = min_eff
                        st.session_state['guard_metric'] = g_sel[0] if g_sel else ""
                        
                        # Save Config Intent
                        st.session_state['exp_config'] = {
                            "page": target_page,
                            "component": target_comp,
                            "control": "Default",
                            "variant": variant_val
                        }
                        
                        st.session_state['step'] = 2
                        st.rerun()

    # --- STEP 2: EXPERIMENT DESIGN ---
    elif curr == 2:
        st.markdown(f"<h2>Step 2. 실험 설계 (Experiment Design)</h2>", unsafe_allow_html=True)
        ui.edu_guide("실험 설계의 3요소", "트래픽 비율 → 목표 설정 → 필요 표본 계산 순서로 진행합니다.")
        
        # [Layout: Traffic Split -> Sample Size Calculation]
        
        st.markdown("#### 1️⃣ 트래픽 비율 설정 (Traffic Allocation)")
        split = st.slider("테스트(B) 그룹 배정 비율", 10, 90, 50, format="%d%%")
        st.caption(f"나머지 {100-split}%는 Control(A) 그룹에 배정됩니다.")
        
        st.divider()
        
        st.markdown("#### 2️⃣ 필요 표본 수 계산 (Sample Size)")
        
        # Connect to DB for Baseline
        con = duckdb.connect(al.DB_PATH, read_only=True)
        
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

        try:
            df_baseline = al.run_query(sql_baseline, con)
            auto_baseline = df_baseline.iloc[0, 0] if not df_baseline.empty and df_baseline.iloc[0, 0] else 0.10
        except Exception:
            auto_baseline = 0.10 # Fallback
            
        con.close()
        
        # Get MDE from Step 1 (Strategy Tab)
        mde_percent = st.session_state.get('min_effect', 5) # returns int like 5
        mde = mde_percent / 100.0
        
        # Calculate Sample Size
        n = al.calculate_sample_size(auto_baseline, mde)
        total_needed = n * 2
        
        # Display Metrics in 3 Columns
        c1, c2, c3 = st.columns(3, gap="large")
        
        with c1:
            st.metric(f"현재 수준 (Baseline)", f"{auto_baseline*100:.2f}%", help=f"최근 30일간 {selected_metric} 평균입니다.")
        
        with c2:
            st.metric(f"목표 상승폭 (MDE)", f"+{mde_percent}%", help="앞 단계(전략)에서 설정한 최소 목표치입니다.")
            
        with c3:
            st.metric(f"필요 표본 수 (그룹당)", f"{n:,}명", delta=f"총 {total_needed:,}명 필요", delta_color="off")
            
        # Estimation Info
        visit_est = 500 # Assumption
        days_est = int(total_needed / visit_est)
        st.info(f"ℹ️ 일평균 방문자 {visit_est}명 기준, 유의미한 결과를 얻기까지 약 **{days_est}일**이 소요됩니다.")

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
                        from src.core import simulation as gen # Re-use generation logic
                        
                        # Simplified injection for demo speed
                        # Ideally, this calls agent_swarm/runner.py
                        # Here we simulate the OUTPUT of that runner
                        
                        # Generate dummy traffic around the target sample size
                        needed = st.session_state['n'] * 2
                        
                        # Use SQL to check if we already ran needed amount
                        curr_cnt = al.run_query("SELECT COUNT(*) FROM assignments WHERE user_id LIKE 'sim_%' OR user_id LIKE 'agent_%'").iloc[0,0]
                        
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
            """, con=None)
            
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
        
        df = al.run_query(sql)
        
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
                    import duckdb
                    with duckdb.connect(DB_PATH) as txn_con:
                        txn_con.execute(f"""
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
                        txn_con.execute("DELETE FROM assignments WHERE user_id LIKE 'sim_%' OR user_id LIKE 'agent_%'")
                        txn_con.execute("DELETE FROM events WHERE user_id LIKE 'sim_%' OR user_id LIKE 'agent_%'")
                    
                    st.toast("저장 완료!")
                    st.session_state['page'] = 'portfolio'
                    st.session_state['step'] = 1
                    st.rerun()

# =========================================================
# PAGE: PORTFOLIO
# =========================================================
elif st.session_state['page'] == 'portfolio':
    st.title("📚 실험 회고록 (Experiment Retrospective)")
    
    df_history = al.run_query("SELECT * FROM experiments ORDER BY created_at DESC")
    
    if df_history.empty:
        st.info("실험 기록이 없습니다.")
    else:
        for _, row in df_history.iterrows():
            with st.container(border=True):
                st.markdown(f"**{row['hypothesis']}**")
                st.caption(f"{row['created_at']} | Result: {row['decision']}")
