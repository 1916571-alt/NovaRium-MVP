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

# Kill old Streamlit instances on different ports (Windows only)
if os.name == 'nt':  # Windows
    import subprocess
    try:
        # Find processes listening on port 8501, 8502, 8503
        for port in [8501, 8502, 8503]:
            result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    pid = parts[-1]
                    # Check if this is not the current process
                    current_pid = os.getpid()
                    if pid.isdigit() and int(pid) != current_pid:
                        subprocess.run(['taskkill', '//F', '//PID', pid], capture_output=True)
    except:
        pass  # Silently ignore if cleanup fails

# Import modularized logic
from src.core import stats as al
from src.ui import components as ui
from src.core import mart_builder as mb  # New Module

# =========================================================
# Environment Configuration with Streamlit Secrets Priority
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
if 'use_db_coordination' not in st.session_state: st.session_state['use_db_coordination'] = True  # DB coordination mode

# --- APPLY STYLES & HEADER ---
ui.apply_custom_css()
ui.render_navbar()

st.write("") # Spacer

# con = al.get_connection() # [REMOVED] Global connection causes locking issues
# DB_PATH will be used for specific query connections
DB_PATH = al.DB_PATH

# Import DB write utilities
from src.data.db import safe_write_batch

# =========================================================
# GLOBAL SIDEBAR: System Settings (visible on all pages)
# =========================================================
with st.sidebar:
    st.markdown("---")
    st.markdown("### ⚙️ 시스템 설정")

    # DB Coordination Mode Toggle
    use_coordination = st.checkbox(
        "🔄 DB 협조 모드",
        value=st.session_state.get('use_db_coordination', True),
        help="Target App과 DB 연결을 조율합니다. 저장 오류 시 체크 해제하여 레거시 모드로 전환 가능."
    )
    st.session_state['use_db_coordination'] = use_coordination

    if use_coordination:
        st.caption("✅ 권장: Target App과 DB 조율")
    else:
        st.warning("⚠️ 레거시 모드")
        st.caption("Target App 미실행 시만 사용")

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
            if st.button("🚀 데이터 마트 구축 (Build & Run)", type="primary", width="stretch"):
                # Execute ETL
                with st.spinner("ETL 파이프라인 가동 중... (Airflow Task #101)"):
                    try:
                        # 1. Generate SQL
                        sql = mb.generate_mart_sql(clean_metrics)
                        
                        # 2. Execute
                        # 2. Execute via Server API (Avoids Locking)
                        import requests
                        try:
                            resp = requests.post(
                                f"{TARGET_APP_URL}/admin/execute_sql",
                                json={"sql": sql},
                                timeout=30
                            )
                            if resp.status_code != 200:
                                raise Exception(f"Server API Error: {resp.text}")
                            
                            r_json = resp.json()
                            if r_json.get("status") != "success":
                                raise Exception(f"SQL Error: {r_json.get('message')}")
                                
                            # 3. Validation (Use Read-Only via stats.py)
                            check_sql = "SELECT COUNT(*) as cnt FROM dm_daily_kpi"
                            df_res = al.run_query(check_sql)
                            row_count = df_res.iloc[0]['cnt'] if not df_res.empty else 0
                            
                            st.success(f"구축 완료! 총 {row_count:,}개의 일별 데이터가 적재되었습니다.")
                            
                        except requests.exceptions.ConnectionError:
                             st.error(f"서버 연결 실패: Target App({TARGET_APP_URL})에 연결할 수 없습니다.")
                             st.info("💡 Render 백엔드가 아직 시작 중일 수 있습니다. 30초 후 다시 시도해주세요.")
                             raise
                        except Exception as e:
                             raise e

                        # Move to dashboard
                        import time
                        time.sleep(1)
                        st.session_state['page'] = 'monitor'
                        st.rerun()

                    except Exception as e:
                        error_msg = str(e)
                        st.error(f"ETL 실패: {error_msg}")

                        # Show detailed diagnostics for connection errors
                        if "pool not available" in error_msg.lower() or "connection" in error_msg.lower():
                            with st.expander("🔍 상세 진단 정보"):
                                st.markdown(f"""
                                **Target App URL**: `{TARGET_APP_URL}`

                                **가능한 원인**:
                                1. 🔄 Render 서버가 아직 시작 중 (Free tier는 15분 비활성화 후 Sleep)
                                2. 🔐 DATABASE_URL 환경 변수가 잘못 설정됨
                                3. 🌐 네트워크 연결 문제 (IPv6 vs IPv4)

                                **해결 방법**:
                                1. Render Dashboard에서 Manual Deploy 실행
                                2. `{TARGET_APP_URL}/debug/db-status?force_retry=true` 접속하여 상태 확인
                                3. Streamlit Cloud Secrets에 DATABASE_URL 확인
                                """)

                                # Try to get debug info from server
                                try:
                                    debug_resp = requests.get(f"{TARGET_APP_URL}/debug/db-status", timeout=10)
                                    if debug_resp.status_code == 200:
                                        st.json(debug_resp.json())
                                except Exception:
                                    st.warning("백엔드 서버에 연결할 수 없어 상세 정보를 가져올 수 없습니다.")

            st.divider()

            # Data Lineage Explanation Only
            st.markdown("**📖 데이터 흐름 (Data Lineage)**")
            st.markdown("""
            **Raw Data → Data Mart 변환 과정**

            1. **Raw Assignments** (방문 기록)
               - `user_id`, `variant`, `assigned_at` 등 원천 데이터

            2. **Raw Events** (행동 기록)
               - `event_name` (click_banner, purchase 등)
               - `value` (구매 금액)

            3. **JOIN & AGGREGATE** (결합 및 집계)
               - 사용자별로 이벤트를 집계
               - 날짜별로 그룹화

            4. **Data Mart** (분석 전용 테이블)
               - CTR, CVR, AOV, ARPU 등 지표가 미리 계산됨
               - 대시보드에서 빠르게 조회 가능
                """)

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
             # Check Target App server
             requests.get(TARGET_APP_URL, timeout=3)
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
                    st.plotly_chart(fig, width="stretch")
                idx += 1
                
            if has_aov:
                with tabs[idx]:
                    fig2 = px.bar(df_trend, x='report_date', y='aov', title='Average Order Value (AOV)', template='plotly_dark')
                    fig2.update_traces(marker_color='#3B82F6')
                    st.plotly_chart(fig2, width="stretch")
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
                st.plotly_chart(fig3, width="stretch")

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

        # Check if data mart exists
        if df_trend.empty:
            st.warning("⚠️ **데이터 마트(`dm_daily_kpi`)가 비어있습니다.** '🛠️ 데이터 랩'에서 ETL을 실행하여 데이터를 생성하세요.")
            st.info("💡 Data Lab → Step 2에서 '실행' 버튼을 눌러 데이터 마트를 구축하세요.")

        # Educational Mode: Always show at least one alert for learning purposes
        if not alerts and not df_trend.empty:
            # Generate a sample educational alert to guide users
            sample_ctr = latest.get('ctr', 0.03) if 'ctr' in df_trend.columns else 0.03
            alerts.append({
                "level": "Educational",
                "title": "📚 [학습 모드] 배너 최적화 기회",
                "desc": f"현재 CTR **{sample_ctr*100:.1f}%** - 업계 평균(15%) 대비 개선 여지가 있습니다.",
                "cause": "사용자 참여도(Engagement)를 높이기 위한 A/B 테스트가 권장됩니다",
                "action": "메인 배너 문구/디자인 변형 실험을 시작해보세요!",
                "target": "메인 배너 (할인 문구)",
                "metric_key": "ctr",
                "threshold": 0.15
            })

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
                        if st.button(f"⚡ 개선 실험 생성", key=f"btn_{alert['title']}", type="primary", width="stretch"):
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

                            st.plotly_chart(fig_alert, width="stretch")
                        else:
                            st.warning("해당 지표의 상세 데이터를 불러올 수 없습니다.")
            
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

        # Show current adoption status banner
        try:
            adoption_df = al.run_query("""
                SELECT a.experiment_id, a.adopted_at, a.variant_config, e.hypothesis, e.target
                FROM adoptions a
                LEFT JOIN experiments e ON a.experiment_id = e.run_id
                ORDER BY a.adopted_at DESC
                LIMIT 1
            """)
            if not adoption_df.empty:
                latest = adoption_df.iloc[0]
                variant_config = latest.get('variant_config', '{}')
                if isinstance(variant_config, str):
                    try:
                        variant_config = json.loads(variant_config)
                    except:
                        variant_config = {}

                winning_variant = variant_config.get('winning_variant', 'B') if variant_config else 'B'
                exp_target = variant_config.get('target', '') if variant_config else ''
                exp_config = variant_config.get('config', {}) if variant_config else {}
                exp_id = latest.get('experiment_id', 'N/A')
                hypothesis = latest.get('hypothesis', 'N/A')
                target = latest.get('target', exp_target) or exp_target or 'N/A'
                adopted_at = latest.get('adopted_at', 'N/A')

                with st.expander("🏆 현재 적용된 Baseline (채택된 실험)", expanded=False):
                    col_info, col_variant = st.columns(2)
                    with col_info:
                        st.markdown(f"**실험 ID**: `{exp_id}`")
                        st.markdown(f"**가설**: {hypothesis}")
                        st.markdown(f"**타겟**: {target}")
                        st.markdown(f"**채택일**: {adopted_at}")
                        st.markdown(f"**Winning Variant**: **{winning_variant}**")
                    with col_variant:
                        if exp_config:
                            st.markdown("**적용된 Variant 설정**:")
                            for key, val in exp_config.items():
                                st.markdown(f"- `{key}`: **{val}**")
                        else:
                            st.info("Variant 설정 정보 없음")

                    # Rollback Button
                    st.divider()
                    col_rollback, col_spacer = st.columns([1, 2])
                    with col_rollback:
                        if st.button("🔄 롤백 (Rollback)", type="secondary", use_container_width=True,
                                     help="최신 채택을 취소하고 기본 상태로 복구합니다"):
                            # Delete the latest adoption record
                            try:
                                from src.data.db import safe_write_batch
                                rollback_ops = [
                                    (f"DELETE FROM adoptions WHERE experiment_id = '{exp_id}'", None)
                                ]
                                result = safe_write_batch(rollback_ops, use_coordination=True)

                                if result['status'] == 'success':
                                    st.cache_data.clear()
                                    st.toast("✅ 롤백 완료! Baseline이 기본값으로 복구되었습니다.")
                                    st.rerun()
                                else:
                                    st.error(f"롤백 실패: {result.get('message', 'Unknown error')}")
                            except Exception as rollback_err:
                                st.error(f"롤백 중 오류 발생: {rollback_err}")
        except Exception as e:
            # Show error in debug mode or if it's not a "table doesn't exist" error
            error_msg = str(e).lower()
            if 'does not exist' not in error_msg and 'relation' not in error_msg:
                st.warning(f"⚠️ 채택 정보 로드 실패: {e}")

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
        
        target_url = f"{TARGET_APP_URL}{sel_url_path}?highlight={sel_comp_id}"

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
                    st.caption("1. 실험 대상 선택")

                    # [A] Page Selection (Visual Cards)
                    st.markdown("**페이지 선택**")
                    page_cols = st.columns(len(PAGE_MAP))
                    selected_page_idx = list(PAGE_MAP.keys()).index(st.session_state.get('builder_page', list(PAGE_MAP.keys())[0]))

                    for idx, (page_name, page_data) in enumerate(PAGE_MAP.items()):
                        with page_cols[idx]:
                            is_selected = (idx == selected_page_idx)
                            border_color = "#8B5CF6" if is_selected else "#374151"
                            bg_color = "#1F2937" if is_selected else "#111827"

                            if st.button(
                                f"{'✓ ' if is_selected else ''}{page_name}",
                                key=f"page_btn_{idx}",
                                width="stretch",
                                type="primary" if is_selected else "secondary"
                            ):
                                st.session_state['builder_page'] = page_name
                                # Reset component selection when page changes
                                st.session_state['builder_comp'] = list(page_data['components'].keys())[0]
                                st.rerun()

                    target_page = st.session_state.get('builder_page', list(PAGE_MAP.keys())[0])

                    st.write("")

                    # [B] Component Selection (Visual Cards)
                    st.markdown("**요소 선택**")
                    comp_data = PAGE_MAP[target_page]['components']
                    comp_names = list(comp_data.keys())

                    # Create grid layout (2 columns for components)
                    comp_cols = st.columns(2)
                    selected_comp = st.session_state.get('builder_comp', comp_names[0])

                    for idx, comp_name in enumerate(comp_names):
                        with comp_cols[idx % 2]:
                            is_selected = (comp_name == selected_comp)

                            if st.button(
                                f"{'✓ ' if is_selected else ''}{comp_name}",
                                key=f"comp_btn_{idx}",
                                width="stretch",
                                type="primary" if is_selected else "secondary"
                            ):
                                st.session_state['builder_comp'] = comp_name
                                st.rerun()

                    target_comp = selected_comp
                    current_target = f"{target_page} > {target_comp}"
                    st.session_state['target'] = current_target

                    st.divider()

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

                    # [D] Advanced Metrics (Aligned Layout)
                    st.markdown("#### 🎯 지표 설정")

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

                    # Equal-width columns for alignment
                    c_m1, c_m2 = st.columns(2, gap="medium")

                    with c_m1:
                        st.markdown("**핵심 지표 (Primary Metric)**")
                        m_sel = st.selectbox("지표 선택", list(metrics_db.keys()), index=list(metrics_db.keys()).index(rec_metric), label_visibility="collapsed")
                        st.caption(f"📝 {metrics_db[m_sel]['desc']}")

                        st.write("")
                        st.markdown("**최소 목표 상승폭 (MDE)**")
                        min_eff = st.slider("목표", 1, 30, 5, format="+%d%%", help=f"실험군(B)의 {m_sel}가 대조군(A)보다 최소 이만큼은 높아야 성공으로 간주합니다.", label_visibility="collapsed")

                    with c_m2:
                        st.markdown("**보조 지표 (Secondary Metrics)**")
                        avail_gr = [k for k in metrics_db.keys() if k != m_sel]
                        g_sel = st.multiselect("지표 선택", avail_gr, default=avail_gr[:1], help="주 메트릭 외에 함께 관찰할 지표입니다.", label_visibility="collapsed")

                        # Show description for selected secondary metrics (matching height with primary)
                        if g_sel:
                            st.caption(f"📝 {metrics_db[g_sel[0]]['desc']}")
                        else:
                            st.caption("선택된 보조 지표가 없습니다.")

                        st.write("")
                        if g_sel:
                            st.markdown("**안전 마진 (Safety Margin)**")
                            guard_threshold = st.slider("경계선", 1.0, 20.0, 5.0, format="-%.1f%%", help="보조 지표가 이 기준 이상 떨어지면 주의가 필요합니다.", label_visibility="collapsed")
                        else:
                            guard_threshold = 5.0

                st.write("")
                if st.button("실험 설계 완료 및 다음 단계 ➡️", type="primary", width="stretch"):
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

                        # Activate experiment for A/B testing
                        # (keeps previous adoptions as baseline, enables new A/B split)
                        try:
                            from src.data.db import safe_write_batch
                            result = safe_write_batch([
                                ("CREATE TABLE IF NOT EXISTS active_experiment (id INTEGER PRIMARY KEY, is_active BOOLEAN, started_at TIMESTAMP)", None),
                                ("DELETE FROM active_experiment", None),
                                ("INSERT INTO active_experiment VALUES (1, true, CURRENT_TIMESTAMP)", None)
                            ], use_coordination=st.session_state.get('db_coordination', True))
                            if result.get('status') == 'success':
                                st.toast("🧪 새 실험 활성화 완료", icon="✅")
                        except Exception as e:
                            pass  # Table creation may fail

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
        
        selected_metric = st.session_state.get('metric', 'CTR (클릭률)')
        
        # Fetch baseline using al.run_query (handles connection properly)
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
            df_baseline = al.run_query(sql_baseline, con=None)  # con=None: auto manages connection
            auto_baseline = df_baseline.iloc[0, 0] if not df_baseline.empty and df_baseline.iloc[0, 0] else 0.10
        except Exception as e:
            st.warning(f"Baseline 조회 실패 (기본값 10% 사용): {e}")
            auto_baseline = 0.10  # Fallback
        
        # Get MDE from Step 1 (Strategy Tab)
        mde_percent = st.session_state.get('min_effect', 5) # returns int like 5
        mde = mde_percent / 100.0
        
        # Calculate Sample Size
        n_per_group = al.calculate_sample_size(auto_baseline, mde)
        
        # Account for traffic split
        control_pct = split / 100.0
        test_pct = 1.0 - control_pct
        
        # For 50:50 split, total = n * 2
        # For unequal splits, we need more total traffic to get 'n' samples in each group
        if split == 50:
            total_needed = n_per_group * 2
        else:
            # Calculate based on which group needs more traffic
            total_for_control = int(n_per_group / control_pct) if control_pct > 0 else n_per_group * 2
            total_for_test = int(n_per_group / test_pct) if test_pct > 0 else n_per_group * 2
            total_needed = max(total_for_control, total_for_test)
        
        # Display Metrics in 3 Columns
        c1, c2, c3 = st.columns(3, gap="large")
        
        with c1:
            st.metric(f"현재 수준 (Baseline)", f"{auto_baseline*100:.2f}%", help=f"최근 30일간 {selected_metric} 평균입니다.")
        
        with c2:
            st.metric(f"목표 상승폭 (MDE)", f"+{mde_percent}%", help="앞 단계(전략)에서 설정한 최소 목표치입니다.")
            
        with c3:
            st.metric(f"총 필요 표본 수", f"{total_needed:,}명", 
                     delta=f"Control {int(total_needed * control_pct):,} | Test {int(total_needed * test_pct):,}", 
                     delta_color="off",
                     help=f"각 그룹당 최소 {n_per_group:,}명의 샘플이 필요합니다.")
        
        # Formula Explanation Expander
        with st.expander("📐 표본 수 계산 공식 (Sample Size Formula)"):
            st.markdown("""
            #### Two-Sample Z-Test for Proportions
            
            ```
            n = (2 × p̄ × (1-p̄) × (Zα + Zβ)²) / (p₁ - p₂)²
            ```
            
            **파라미터:**
            - **p₁ (baseline)**: {:.2%} ← 현재 전환율
            - **p₂ (target)**: {:.2%} ← 목표 전환율 (baseline × (1 + MDE))
            - **p̄ (pooled)**: {:.2%} ← (p₁ + p₂) / 2
            - **Zα**: 1.96 ← 95% 신뢰수준 (α=0.05)
            - **Zβ**: 0.84 ← 80% 검정력 (β=0.20)
            
            **계산 결과:**
            - **그룹당 필요 샘플**: {:,}명
            - **트래픽 분배**: Control {}% / Test {}%
            - **총 방문자 필요**: {:,}명
            
            > ℹ️ 불균등 분배 시, 소수 그룹이 충분한 샘플을 얻기 위해 더 많은 총 방문자가 필요합니다.
            """.format(
                auto_baseline, 
                auto_baseline * (1 + mde),
                (auto_baseline + auto_baseline * (1 + mde)) / 2,
                n_per_group,
                split, 100-split,
                total_needed
            ))
            
        # Estimation Info
        visit_est = 500 # Assumption
        days_est = int(total_needed / visit_est)
        st.info(f"ℹ️ 일평균 방문자 {visit_est}명 기준, 유의미한 결과를 얻기까지 약 **{days_est}일**이 소요됩니다.")

        st.write("")
        if st.button("다음: 데이터 수집 시작 (Simulation) ➡️", type="primary", width="stretch"):
            st.session_state['n'] = n_per_group
            st.session_state['total_needed'] = total_needed
            st.session_state['split'] = split
            st.session_state['step'] = 3
            st.rerun()

    # --- STEP 3: COLLECTION (SIMULATION) ---
    elif curr == 3:
        st.markdown(f"<h2>Step 3. 데이터 모으기 (Collection)</h2>", unsafe_allow_html=True)
        ui.edu_guide("실시간 시뮬레이션", "Agent System이 가상의 유저가 되어 앱을 방문합니다.")
        
        # Agent Persona Settings
        with st.expander("🤖 에이전트 성향 설정 (Agent Persona)", expanded=True):
            if 'p_dist' not in st.session_state:
                st.session_state['p_dist'] = {'Window': 40, 'Mission': 10, 'Rational': 20, 'Impulsive': 20, 'Cautious': 10}
            
            # SQL Query Button and Analyze Button in one row
            col_sql, col_analyze = st.columns([1, 3])

            with col_sql:
                if st.button("📊 SQL 쿼리 확인", help="세그먼트 분석 SQL 쿼리 보기", key="show_sql_btn", width="stretch"):
                    st.session_state['show_segment_sql'] = not st.session_state.get('show_segment_sql', False)

            with col_analyze:
                analyze_clicked = st.button("🔄 기존 고객 분석 및 적용", help="DB의 유저/주문 패턴을 분석하여 실제 고객 분포를 반영합니다.", key="analyze_btn", width="stretch")

            st.caption("기존 고객 데이터를 분석하여 에이전트 성향을 자동으로 설정합니다.")

            # Show SQL query if requested
            if st.session_state.get('show_segment_sql', False):
                st.code("""
WITH user_metrics AS (
    SELECT
        u.user_id,
        COUNT(o.order_id) as order_count,
        COALESCE(SUM(o.amount), 0) as total_spent,
        DATE_DIFF('day', MIN(u.joined_at)::TIMESTAMP, CURRENT_DATE) as tenure_days
    FROM users u
    LEFT JOIN orders o ON u.user_id = o.user_id
    GROUP BY 1
),
averages AS (
    SELECT AVG(total_spent) as avg_spent FROM user_metrics WHERE order_count > 0
)
SELECT
    CASE
        WHEN order_count = 0 THEN 'Window'
        WHEN order_count >= 3 THEN 'Mission'
        WHEN total_spent > (SELECT avg_spent FROM averages) THEN 'Rational'
        WHEN tenure_days < 30 THEN 'Impulsive'
        ELSE 'Cautious'
    END as segment,
    COUNT(*) as cnt
FROM user_metrics
GROUP BY 1
                """, language="sql")

            if analyze_clicked:
                with st.spinner("DuckDB 분석 중: 고객 세그먼트 추출..."):
                    dist = al.get_user_segments()
                    st.session_state['p_dist'] = dist
                    st.toast("분석 완료! 고객 분포가 적용되었습니다.", icon="✅")
                    st.rerun()
                    
            p_dist = st.session_state['p_dist']
            
            # Persona inputs (aligned with stats.py segmentation logic)
            c_p1, c_p2, c_p3, c_p4, c_p5 = st.columns(5)
            
            p_window = c_p1.number_input("🛍️ 아이쇼핑 (Window)", 0, 100, p_dist.get('Window', 0), step=5, 
                                         help="주문 이력 없음 (탐색만 하는 유저)", key="p_window")
            p_mission = c_p2.number_input("🎯 목적형 (Mission)", 0, 100, p_dist.get('Mission', 0), step=5, 
                                          help="3회 이상 구매 (충성 고객)", key="p_mission")
            p_rational = c_p3.number_input("💡 계산형 (Rational)", 0, 100, p_dist.get('Rational', 0), step=5, 
                                           help="평균 이상 지출 (고액 구매자)", key="p_rational")
            p_impulsive = c_p4.number_input("⚡ 충동형 (Impulsive)", 0, 100, p_dist.get('Impulsive', 0), step=5, 
                                             help="가입 30일 이내 신규 유저", key="p_impulsive")
            p_cautious = c_p5.number_input("🧐 신중형 (Cautious)", 0, 100, p_dist.get('Cautious', 0), step=5, 
                                            help="장기 가입 + 간헐적 구매", key="p_cautious")
            
            # Sync Session State
            st.session_state['p_dist'] = {
                'Window': p_window, 'Mission': p_mission, 'Rational': p_rational,
                'Impulsive': p_impulsive, 'Cautious': p_cautious
            }
            
            total_p = sum(st.session_state['p_dist'].values())
            
            # Visual Distribution Bar
            st.progress(min(total_p/100, 1.0))
            
            if total_p != 100:
                st.warning(f"⚠️ 합계가 100%가 되어야 합니다. (현재: {total_p}%)")
            else:
                st.caption(f"✅ 설정 완료: Window {p_window}% | Mission {p_mission}% | Rational {p_rational}% | Impulsive {p_impulsive}% | Cautious {p_cautious}%")

        col_sim, col_chart = st.columns([1, 1], gap="large")
        
        # Create chart placeholder BEFORE simulation starts
        with col_chart:
            with st.container(border=True):
                st.markdown("#### 📊 실시간 그룹 분포")
                chart_placeholder = st.empty()
                # Show last chart if available (after simulation completion)
                if 'last_live_chart' in st.session_state and not st.session_state.get('sim_process'):
                    df_last = st.session_state['last_live_chart']
                    last_loop = st.session_state.get('last_loop_count', 0)
                    with chart_placeholder.container():
                        st.bar_chart(df_last, x="variant", y="visitors", color="variant", horizontal=True)
                        st.caption(f"✅ 시뮬레이션 완료 (Loop: {last_loop})")
                else:
                    # Initial state
                    with chart_placeholder.container():
                        st.info("데이터 대기 중...")
        
        with col_sim:
            with st.container(border=True):
                st.markdown("#### 🚀 시뮬레이션 제어")
                # Use total_needed from Step 2, fallback to n*2 for backwards compatibility
                total_target = st.session_state.get('total_needed', st.session_state.get('n', 100) * 2)
                
                # Fixed 10 agents for testing (reduced for Render free tier)
                actual_agents = 10
                weight_multiplier = total_target / actual_agents

                st.info(f"📊 **투입 규모**: {actual_agents}명 에이전트 → 효과: {total_target:,}명 (×{weight_multiplier:.1f} 증폭)")
                turbo = st.checkbox("Turbo Mode (무시 지연 제거)", value=True)
                
                col_start, col_stop = st.columns(2)
                
                with col_start:
                    if st.button("▶️ Agent Swarm 투입 (Start)", type="primary", width="stretch", key="start_sim_btn"):
                        # Generate unique run_id for this experiment
                        import time as time_module
                        current_run_id = f"run_{int(time_module.time() * 1000)}"
                        st.session_state['current_run_id'] = current_run_id
                        st.session_state['current_weight'] = weight_multiplier  # Save for later use

                        # Traits order must match runner.py and UI: Window, Mission, Rational, Impulsive, Cautious
                        traits = ["Window", "Mission", "Rational", "Impulsive", "Cautious"]
                        weights_str = ",".join([str(st.session_state['p_dist'].get(t, 20)) for t in traits])
                        needed = actual_agents  # Use sampled count (not effective)

                        cmd = [sys.executable, "agent_swarm/runner.py",
                               "--count", str(needed),
                               "--weights", weights_str,
                               "--run-id", current_run_id,
                               "--weight", str(weight_multiplier)]  # Add weight parameter
                        if turbo: cmd.append("--turbo")
                    
                        import subprocess
                        import time
                        import sys
                        
                        # Prepare command with PYTHONPATH
                        import os
                        env = os.environ.copy()
                        env['PYTHONPATH'] = os.path.abspath('.')
                        
                        # UI Placeholders
                        progress_bar = st.progress(0, text="준비 중...")
                        status_container = st.status("🚀 시뮬레이션 엔진 가동 중...", expanded=True)
                        log_area = st.empty()
                        
                        try:
                            # Launch non-blocking with PYTHONPATH
                            proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                            
                            # Store process in session state for Stop button
                            st.session_state['sim_process'] = proc
                            
                            # CRITICAL: Wait for process to actually start before polling
                            time.sleep(0.5)
                            
                            start_time = time.time()
                            last_count = 0
                            loop_count = 0
                            
                            # Force initial UI update
                            status_container.update(label="⚙️ 에이전트 투입 중...", state="running")
                            
                            while proc.poll() is None:
                                loop_count += 1
                                
                                # Check if user requested stop
                                if st.session_state.get('sim_stop_requested', False):
                                    proc.terminate()
                                    status_container.update(label="⏹️ 사용자가 중지했습니다", state="error")
                                    st.session_state['sim_stop_requested'] = False
                                    st.session_state.pop('sim_process', None)
                                    break
                                
                                # 1. Update Progress
                                run_filter = st.session_state.get('current_run_id', 'run_0')
                                df_count = al.run_query(f"SELECT COUNT(*) as cnt FROM assignments WHERE run_id = '{run_filter}'", con=None)
                                curr_count = df_count.iloc[0]['cnt'] if not df_count.empty else 0
                                
                                progress = min(curr_count / needed, 1.0) if needed > 0 else 0
                                effective_count = int(curr_count * weight_multiplier)
                                effective_total_display = int(needed * weight_multiplier)
                                progress_bar.progress(progress, text=f"데이터 수집 중... ({curr_count}/{needed}) → 효과: ({effective_count:,}/{effective_total_display:,}) [Loop: {loop_count}]")
                                
                                # 2. Show Live Logs (Ticker)
                                df_logs = al.run_query(f"""
                                    SELECT timestamp, user_id, event_name
                                    FROM events
                                    WHERE run_id = '{run_filter}'
                                    ORDER BY timestamp DESC LIMIT 5
                                """, con=None)
                                
                                if not df_logs.empty:
                                    # Fix: Convert string timestamp (from JSON API) to datetime object
                                    df_logs['timestamp'] = pd.to_datetime(df_logs['timestamp'])
                                    log_text = "  \n".join([f"🕒 {row['timestamp'].strftime('%H:%M:%S')} | 👤 {row['user_id']} | 📢 {row['event_name']}" for _, row in df_logs.iterrows()])
                                    log_area.markdown(f"**최근 활동:**  \n{log_text}")
                                else:
                                    log_area.caption("에이전트 활동 대기 중...")
                                
                                # 3. Update Chart (RIGHT SIDE) - NEW!
                                df_live = al.run_query(f"""
                                    SELECT
                                        variant,
                                        COUNT(DISTINCT user_id) as visitors
                                    FROM assignments
                                    WHERE run_id = '{run_filter}'
                                    GROUP BY 1
                                """, con=None)

                                # Save to session_state for persistence after completion
                                if not df_live.empty:
                                    st.session_state['last_live_chart'] = df_live.copy()
                                    st.session_state['last_loop_count'] = loop_count

                                with chart_placeholder.container():
                                    if not df_live.empty:
                                        st.bar_chart(df_live, x="variant", y="visitors", color="variant", horizontal=True)
                                        st.caption(f"🔄 실시간 업데이트 중... (Loop: {loop_count})")
                                    else:
                                        st.info("데이터 수집 대기 중...")
                                
                                # 4. Handle timeout or stuck
                                elapsed = time.time() - start_time
                                if elapsed > 120 and curr_count == last_count:
                                    status_container.update(label="⚠️ 시뮬레이션 지연 발생", state="error")
                                    st.warning(f"2분 경과, 데이터 증가 없음. 프로세스 상태: {proc.poll()}")
                                    break
                                
                                last_count = curr_count
                                time.sleep(1)
                            
                            # Final Check
                            exit_code = proc.wait()
                            st.session_state.pop('sim_process', None)
                            
                            if not st.session_state.get('sim_stop_requested', False):
                                status_container.update(label=f"✅ 시뮬레이션 완료! (Exit Code: {exit_code})", state="complete", expanded=False)
                                st.success(f"Loop 실행 횟수: {loop_count}회, 최종 데이터: {last_count}건")
                                st.toast("시뮬레이션 완료! 데이터가 수집되었습니다.")
                                time.sleep(1)  # Give UI a moment to render
                                st.rerun()
                            
                        except Exception as e:
                            st.error(f"시뮬레이션 중 오류 발생: {e}")
                            import traceback
                            st.code(traceback.format_exc())
                            st.session_state.pop('sim_process', None)
                
                with col_stop:
                    if st.button("⏹️ 중지 (Stop)", type="secondary", width="stretch", key="stop_sim_btn"):
                        if 'sim_process' in st.session_state:
                            st.session_state['sim_stop_requested'] = True
                            st.warning("중지 요청됨... 프로세스 종료 중")
                        else:
                            st.info("실행 중인 시뮬레이션이 없습니다")
        
        st.write("")
        if st.button("다음: 결과 분석 (Analysis) ➡️", type="primary", width="stretch"):
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
        
        # Get Stats - Use run_id for proper experiment isolation
        current_run_id = st.session_state.get('current_run_id', None)

        # CRITICAL: Ensure we have a run_id from the simulation
        if not current_run_id:
            st.error("⚠️ 실험 데이터를 찾을 수 없습니다!")
            st.info("Step 3 (데이터 모으기)에서 시뮬레이션을 먼저 실행해주세요.")

            # Show available run_ids for debugging
            available_runs = al.run_query("SELECT DISTINCT run_id FROM assignments WHERE run_id IS NOT NULL ORDER BY run_id DESC LIMIT 5")
            if not available_runs.empty:
                st.write("사용 가능한 실험 run_id:")
                st.dataframe(available_runs)

                # Allow manual selection
                selected_run = st.selectbox("수동으로 run_id 선택 (디버깅용):", available_runs['run_id'].tolist())
                if st.button("이 run_id 사용"):
                    st.session_state['current_run_id'] = selected_run
                    st.rerun()
            st.stop()

        st.caption(f"🔍 현재 분석 중인 실험: `{current_run_id}`")

        # Build event filter based on metric type
        # For CTR: match 'click_banner' OR 'banner_%' patterns (agent uses banner_A, banner_B)
        # For CVR: match 'purchase'
        if event_name == 'click_banner':
            event_filter = "(e.event_name = 'click_banner' OR e.event_name LIKE 'banner_%')"
        else:
            event_filter = f"e.event_name = '{event_name}'"

        sql = f"""
        SELECT
            a.variant,
            COUNT(DISTINCT a.user_id) as users,
            COUNT(DISTINCT CASE WHEN {event_filter} THEN e.user_id END) as conversions
        FROM assignments a
        LEFT JOIN events e ON a.user_id = e.user_id AND a.run_id = e.run_id
        WHERE a.run_id = '{current_run_id}'
        GROUP BY 1 ORDER BY 1
        """

        df = al.run_query(sql)

        if len(df) < 2:
            st.warning("📊 분석을 위한 충분한 데이터가 수집되지 않았습니다. (최소 2개의 그룹 필요)")
            st.info(f"현재 run_id '{current_run_id}'에 대한 데이터: {len(df)}개 그룹")
            st.stop()
            
        # Calculate Stats
        res = al.calculate_statistics(
            df.iloc[0]['users'], df.iloc[0]['conversions'],
            df.iloc[1]['users'], df.iloc[1]['conversions']
        )
        
        # Plotly CVR Comparison with CIs
        import plotly.graph_objects as go
        
        rows = []
        for i, row in df.iterrows():
            # Calculate rate based on metric type
            if 'CTR' in primary_metric or 'click' in primary_metric.lower():
                # For CTR, use clicks as conversions
                rate = row['conversions'] / row['users'] if row['users'] > 0 else 0
            else:
                # For CVR, use purchase conversions
                rate = row['conversions'] / row['users'] if row['users'] > 0 else 0

            # 95% CI
            error = 1.96 * np.sqrt(rate * (1-rate) / row['users']) if row['users'] > 0 else 0
            rows.append({
                'variant': row['variant'],
                'rate': rate * 100,
                'error': error * 100,
                'users': row['users'],
                'conversions': row['conversions']
            })
        plot_df = pd.DataFrame(rows)
        
        fig = go.Figure()
        colors = {'A': '#135bec', 'B': '#ef4444'}
        
        for v in ['A', 'B']:
            v_data = plot_df[plot_df['variant'] == v]
            if v_data.empty: continue
            
            fig.add_trace(go.Bar(
                x=[v], 
                y=v_data['rate'],
                name=f"Group {v}",
                marker_color=colors.get(v, '#cccccc'),
                error_y=dict(type='data', array=v_data['error'], visible=True),
                text=[f"{r:.2f}%" for r in v_data['rate']],
                textposition='auto',
            ))
            
        fig.update_layout(
            title=f"{primary_metric} 비교 (95% 신뢰구간 포함)",
            yaxis_title=f"{primary_metric} (%)",
            template="plotly_dark",
            height=400,
            showlegend=False
        )
        
        c_stats, c_plot = st.columns([1, 1.5], gap="medium")
        
        with c_stats:
            st.markdown("#### 🏁 최종 결과 요약")
            with st.container(border=True):
                st.metric("Lift (개선율)", al.format_delta(res['lift']),
                         delta=f"{al.format_delta(res['lift'])} {'🔥' if res['lift'] > 0 else '❄️'}")

                p_val_str = f"{res['p_value']:.4f}"
                st.write(f"📊 **P-value:** {p_val_str}")

                if res['p_value'] < 0.05:
                    st.success(f"🎊 **통계적으로 유의미함** (p < 0.05)")
                    decision = "Significant Winner" if res['lift'] > 0 else "Significant Loser"
                else:
                    st.warning(f"⚖️ **유의미한 차이 없음** (p >= 0.05)")
                    decision = "Inconclusive"

                # Decision Action Buttons - Always show both Adopt and Re-experiment
                st.divider()
                st.markdown("#### 🎯 의사결정 (Decision)")

                # Always show both buttons - analyst can decide based on practical significance
                col_adopt, col_redesign = st.columns(2)

                with col_adopt:
                    if st.button("✅ 채택 (Adopt)", type="primary", use_container_width=True):
                        # Save adoption intent to session state (will be saved with retrospective)
                        # variant_config stores the winning variant info for Target App
                        variant_data = st.session_state.get('exp_variant_data', {})
                        st.session_state['pending_adoption'] = {
                            'variant': {
                                'winning_variant': 'B',  # Adopting means Test variant (B) won
                                'target': st.session_state.get('target', ''),
                                'config': variant_data  # Store actual experiment configuration
                            },
                            'experiment_id': current_run_id,
                            'lift': res['lift'],
                            'p_value': res['p_value'],
                            'timestamp': pd.Timestamp.now().isoformat()
                        }
                        st.toast("✅ 채택 표시됨! 회고록 저장 시 Target App에 적용됩니다.")
                        st.session_state['show_adoption_success'] = True

                with col_redesign:
                    if st.button("🔄 재실험 설계 (Re-design)", type="secondary", use_container_width=True):
                        # Save learning from this experiment
                        st.session_state['previous_experiment_learning'] = {
                            'run_id': current_run_id,
                            'p_value': res['p_value'],
                            'lift': res['lift'],
                            'decision': decision,
                            'hypothesis': st.session_state.get('hypothesis', ''),
                            'target': st.session_state.get('target', '')
                        }

                        # Clear current experiment data
                        st.session_state.pop('current_run_id', None)
                        st.session_state.pop('sim_complete', None)

                        # Navigate back to Step 1
                        st.session_state['step'] = 1
                        st.toast("🔄 새로운 실험을 설계해보세요!")
                        st.rerun()

                # Show guidance based on statistical and practical significance
                if st.session_state.get('show_adoption_success'):
                    st.success("✨ 채택 완료! 다음 실험을 설계하여 플랫폼을 더욱 개선하세요.")
                else:
                    if res['p_value'] < 0.05 and res['lift'] > 0:
                        st.info("💡 **권장**: 통계적으로 유의미한 개선입니다. 채택을 고려하세요.")
                    elif res['p_value'] < 0.05 and res['lift'] < 0:
                        st.warning("⚠️ **주의**: 통계적으로 유의미한 악화입니다. 재실험을 권장합니다.")
                    else:
                        st.info("💡 **참고**: 유의미한 차이가 없습니다. 실무적 판단 또는 재실험을 고려하세요.")

        with c_plot:
            # Main CTR Chart
            st.plotly_chart(fig, use_container_width=True)

            # ==========================================
            # Guardrail Metrics Section (Below CTR Chart in Right Column)
            # ==========================================
            guardrails = st.session_state.get('guardrails', [])
            guard_results = []
            guard_threshold = st.session_state.get('session_guard_threshold', -5.0) / 100

            if guardrails:
                st.markdown("#### 🛡️ 가드레일 지표 (Guardrail Metrics)")

                # Query all metrics at once for efficiency
                guard_sql = f"""
                SELECT
                    a.variant,
                    COUNT(DISTINCT a.user_id) as users,
                    COUNT(DISTINCT CASE WHEN e.event_name = 'purchase' THEN e.user_id END) as conversions,
                    COALESCE(SUM(CASE WHEN e.event_name = 'purchase' THEN e.value ELSE 0 END), 0) as revenue,
                    COUNT(DISTINCT CASE WHEN e.event_name LIKE 'banner%' OR e.event_name = 'click_banner' THEN e.user_id END) as clicks,
                    COUNT(DISTINCT CASE WHEN e.event_name = 'bounce' THEN e.user_id END) as bounces
                FROM assignments a
                LEFT JOIN events e ON a.user_id = e.user_id AND a.run_id = e.run_id
                WHERE a.run_id = '{current_run_id}'
                GROUP BY 1 ORDER BY 1
                """
                df_guard = al.run_query(guard_sql)

                if len(df_guard) >= 2:
                    ctrl = df_guard.iloc[0]
                    test = df_guard.iloc[1]

                    # Calculate each guardrail metric
                    for guardrail in guardrails:
                        if "CVR" in guardrail:
                            control_rate = ctrl['conversions'] / ctrl['users'] if ctrl['users'] > 0 else 0
                            test_rate = test['conversions'] / test['users'] if test['users'] > 0 else 0
                            guard_lift = (test_rate - control_rate) / control_rate if control_rate > 0 else 0
                            passed = guard_lift >= guard_threshold
                            guard_results.append({
                                "metric": "CVR (전환율)",
                                "control": control_rate,
                                "test": test_rate,
                                "lift": guard_lift,
                                "passed": passed
                            })
                        elif "AOV" in guardrail:
                            control_aov = ctrl['revenue'] / ctrl['conversions'] if ctrl['conversions'] > 0 else 0
                            test_aov = test['revenue'] / test['conversions'] if test['conversions'] > 0 else 0
                            guard_lift = (test_aov - control_aov) / control_aov if control_aov > 0 else 0
                            passed = guard_lift >= guard_threshold
                            guard_results.append({
                                "metric": "AOV (평균주문액)",
                                "control": control_aov,
                                "test": test_aov,
                                "lift": guard_lift,
                                "passed": passed
                            })
                        elif "Bounce" in guardrail:
                            control_bounce = ctrl['bounces'] / ctrl['users'] if ctrl['users'] > 0 else 0
                            test_bounce = test['bounces'] / test['users'] if test['users'] > 0 else 0
                            guard_lift = (test_bounce - control_bounce) / control_bounce if control_bounce > 0 else 0
                            passed = guard_lift <= abs(guard_threshold)
                            guard_results.append({
                                "metric": "Bounce Rate (이탈률)",
                                "control": control_bounce,
                                "test": test_bounce,
                                "lift": guard_lift,
                                "passed": passed
                            })
                        elif "CTR" in guardrail:
                            control_ctr = ctrl['clicks'] / ctrl['users'] if ctrl['users'] > 0 else 0
                            test_ctr = test['clicks'] / test['users'] if test['users'] > 0 else 0
                            guard_lift = (test_ctr - control_ctr) / control_ctr if control_ctr > 0 else 0
                            passed = guard_lift >= guard_threshold
                            guard_results.append({
                                "metric": "CTR (클릭률)",
                                "control": control_ctr,
                                "test": test_ctr,
                                "lift": guard_lift,
                                "passed": passed
                            })

                    # Compact display for guardrail metrics
                    if guard_results:
                        # Create compact bar chart
                        guard_metrics = [gr['metric'].split(' ')[0] for gr in guard_results]  # Short names
                        control_vals = [gr['control'] * 100 for gr in guard_results]
                        test_vals = [gr['test'] * 100 for gr in guard_results]

                        fig_guard = go.Figure()
                        fig_guard.add_trace(go.Bar(
                            name='A', x=guard_metrics, y=control_vals,
                            marker_color='#135bec', text=[f"{v:.1f}%" for v in control_vals], textposition='auto'
                        ))
                        fig_guard.add_trace(go.Bar(
                            name='B', x=guard_metrics, y=test_vals,
                            marker_color='#ef4444', text=[f"{v:.1f}%" for v in test_vals], textposition='auto'
                        ))
                        fig_guard.update_layout(
                            yaxis_title="%", barmode='group', template="plotly_dark", height=220, margin=dict(t=30, b=30),
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                        )
                        st.plotly_chart(fig_guard, use_container_width=True)

                        # Compact summary below chart
                        for gr in guard_results:
                            status = "✅" if gr.get('passed', True) else "❌"
                            lift_val = gr['lift'] * 100
                            color = "green" if lift_val >= 0 else "red"
                            st.caption(f"{status} **{gr['metric']}**: <span style='color:{color}'>{lift_val:+.1f}%</span> (A:{gr['control']*100:.1f}% → B:{gr['test']*100:.1f}%)", unsafe_allow_html=True)
                    else:
                        st.caption("가드레일 데이터 없음")
                else:
                    st.caption("가드레일 분석 데이터 부족")

            # Store guard_results in session state for saving
            st.session_state['guard_results'] = guard_results
        
        # Comprehensive Metrics Comparison Table
        st.divider()
        col_title, col_spacer, col_help = st.columns([2.5, 0.5, 1])
        with col_title:
            st.markdown("#### 📈 주요 메트릭 비교표 (Key Metrics Comparison)")
        with col_help:
            with st.popover("💡 메트릭 학습 가이드", use_container_width=True):
                st.markdown("""
                **각 메트릭의 의미와 활용법**

                **📊 CTR (Click-Through Rate, 클릭률)**
                - 공식: (클릭수 / 방문자수) × 100
                - 의미: 배너/버튼의 **시각적 효과**와 유인력 측정
                - 활용: UI/UX 디자인 개선 효과 평가

                **💰 CVR (Conversion Rate, 전환율)**
                - 공식: (구매수 / 방문자수) × 100
                - 의미: 방문자가 **실제 구매**로 전환되는 비율
                - 활용: 구매 퍼널 최적화, 가격 전략 평가

                **🛒 AOV (Average Order Value, 평균 주문액)**
                - 공식: 총매출 / 구매수
                - 의미: 구매 1건당 평균 금액
                - 활용: 번들링, 업셀링 전략 효과 측정

                **👤 ARPU (Average Revenue Per User, 유저당 평균 매출)**
                - 공식: 총매출 / 방문자수
                - 의미: 모든 유저(구매/비구매 포함)의 평균 기여도
                - 활용: 종합적인 수익성 지표, LTV 예측

                **🎯 분석 Tip**
                - CTR↑ CVR→ : 클릭은 늘었지만 구매로 이어지지 않음 → 랜딩 페이지 개선 필요
                - CTR→ CVR↑ : 구매율은 상승 → 타겟팅 정확도 향상
                - AOV↑ ARPU↑ : 고가 상품 판매 증가 → 프리미엄 전략 성공
                """)


        # Calculate comprehensive metrics for both groups (weight-adjusted for hybrid simulation)
        metrics_sql = f"""
        WITH user_events AS (
            SELECT
                a.variant,
                a.user_id,
                a.weight,
                MAX(CASE WHEN e.event_name LIKE 'banner%' OR e.event_name = 'click_banner' THEN 1 ELSE 0 END) as clicked,
                MAX(CASE WHEN e.event_name = 'purchase' THEN 1 ELSE 0 END) as purchased,
                SUM(CASE WHEN e.event_name = 'purchase' THEN e.value ELSE 0 END) as revenue
            FROM assignments a
            LEFT JOIN events e ON a.user_id = e.user_id AND a.run_id = e.run_id
            WHERE a.run_id = '{current_run_id}'
            GROUP BY a.variant, a.user_id, a.weight
        )
        SELECT
            variant as 그룹,
            CAST(ROUND(SUM(weight), 0) AS INTEGER) as 방문자수,
            CAST(ROUND(SUM(CASE WHEN clicked = 1 THEN weight ELSE 0 END), 0) AS INTEGER) as 클릭수,
            CAST(ROUND(SUM(CASE WHEN purchased = 1 THEN weight ELSE 0 END), 0) AS INTEGER) as 구매수,
            CAST(ROUND(SUM(revenue * weight), 0) AS BIGINT) as 총매출,
            ROUND(SUM(CASE WHEN clicked = 1 THEN weight ELSE 0 END) / NULLIF(SUM(weight), 0) * 100, 2) as CTR,
            ROUND(SUM(CASE WHEN purchased = 1 THEN weight ELSE 0 END) / NULLIF(SUM(weight), 0) * 100, 2) as CVR,
            CAST(ROUND(SUM(revenue * weight) / NULLIF(SUM(CASE WHEN purchased = 1 THEN weight ELSE 0 END), 0), 0) AS INTEGER) as AOV,
            CAST(ROUND(SUM(revenue * weight) / NULLIF(SUM(weight), 0), 0) AS INTEGER) as ARPU
        FROM user_events
        GROUP BY variant
        ORDER BY variant
        """
        df_metrics = al.run_query(metrics_sql)

        # Educational fallback: Generate sample data if real data is insufficient
        use_sample_data = False
        if df_metrics.empty or len(df_metrics) < 2:
            use_sample_data = True
            st.info("📚 **[학습 모드]** 실제 트래픽이 부족하여 샘플 데이터로 분석 결과를 시뮬레이션합니다.")
            # Generate realistic sample metrics for educational purposes
            import random
            random.seed(42)  # Reproducible for consistency
            a_visitors = random.randint(45, 55)
            b_visitors = random.randint(45, 55)
            a_clicks = int(a_visitors * random.uniform(0.10, 0.18))
            b_clicks = int(b_visitors * random.uniform(0.15, 0.25))  # B variant slightly better
            a_purchases = int(a_clicks * random.uniform(0.15, 0.25))
            b_purchases = int(b_clicks * random.uniform(0.20, 0.35))
            a_revenue = a_purchases * random.randint(20000, 35000)
            b_revenue = b_purchases * random.randint(22000, 38000)

            df_metrics = pd.DataFrame([
                {'그룹': 'A', '방문자수': a_visitors, '클릭수': a_clicks, '구매수': a_purchases, '총매출': a_revenue,
                 'CTR': round(a_clicks/a_visitors*100, 2), 'CVR': round(a_purchases/a_visitors*100, 2),
                 'AOV': int(a_revenue/a_purchases) if a_purchases > 0 else 0,
                 'ARPU': int(a_revenue/a_visitors)},
                {'그룹': 'B', '방문자수': b_visitors, '클릭수': b_clicks, '구매수': b_purchases, '총매출': b_revenue,
                 'CTR': round(b_clicks/b_visitors*100, 2), 'CVR': round(b_purchases/b_visitors*100, 2),
                 'AOV': int(b_revenue/b_purchases) if b_purchases > 0 else 0,
                 'ARPU': int(b_revenue/b_visitors)}
            ])

        if not df_metrics.empty and len(df_metrics) >= 2:
            # Add delta row
            deltas = {}
            for col in df_metrics.columns:
                if col != '그룹':
                    control_val = df_metrics.iloc[0][col]
                    test_val = df_metrics.iloc[1][col]

                    # Handle None/NaN values
                    if pd.isna(control_val) or pd.isna(test_val):
                        deltas[col] = "N/A"
                    elif control_val == 0 or control_val is None:
                        deltas[col] = "N/A"
                    else:
                        try:
                            delta_pct = ((float(test_val) - float(control_val)) / float(control_val)) * 100
                            deltas[col] = f"+{delta_pct:.1f}%" if delta_pct >= 0 else f"{delta_pct:.1f}%"
                        except (TypeError, ValueError):
                            deltas[col] = "N/A"
            deltas['그룹'] = 'Δ (B vs A)'

            # Create comparison dataframe
            import pandas as pd
            df_comparison = pd.concat([df_metrics, pd.DataFrame([deltas])], ignore_index=True)

            st.dataframe(df_comparison, width="stretch", hide_index=True)
            if use_sample_data:
                st.caption("⚠️ 위 데이터는 학습용 샘플입니다. 실제 실험에서는 더 많은 트래픽을 수집하세요.")
            st.caption("💡 CTR = 클릭률, CVR = 전환율, AOV = 평균 주문액, ARPU = 유저당 평균 매출")

        # Raw Data Table with Sample and Download
        st.divider()
        col_raw_title, col_download = st.columns([3, 1])
        with col_raw_title:
            st.markdown("#### 📊 원 데이터 (Raw Data)")
        with col_download:
            # Fetch full event data for download with enriched fields
            # Use different syntax for DuckDB vs PostgreSQL
            if al.is_cloud_mode():
                # PostgreSQL: Use EXTRACT(EPOCH FROM ...) for time difference
                time_diff_expr = "EXTRACT(EPOCH FROM (e.timestamp - LAG(e.timestamp) OVER (PARTITION BY e.user_id ORDER BY e.timestamp)))"
            else:
                # DuckDB: Use DATEDIFF
                time_diff_expr = "DATEDIFF('second', LAG(e.timestamp) OVER (PARTITION BY e.user_id ORDER BY e.timestamp), e.timestamp)"

            raw_data_sql = f"""
            WITH user_journey AS (
                SELECT
                    e.event_id,
                    e.user_id,
                    a.variant,
                    e.event_name,
                    e.timestamp,
                    e.value,
                    a.weight,
                    ROW_NUMBER() OVER (PARTITION BY e.user_id ORDER BY e.timestamp) as event_sequence,
                    LAG(e.event_name) OVER (PARTITION BY e.user_id ORDER BY e.timestamp) as prev_event,
                    LEAD(e.event_name) OVER (PARTITION BY e.user_id ORDER BY e.timestamp) as next_event,
                    {time_diff_expr} as time_since_last_event
                FROM events e
                LEFT JOIN assignments a ON e.user_id = a.user_id AND e.run_id = a.run_id
                WHERE e.run_id = '{current_run_id}'
            )
            SELECT
                event_id,
                user_id,
                variant,
                event_name,
                timestamp,
                value,
                weight,
                event_sequence,
                prev_event,
                next_event,
                time_since_last_event,
                CASE
                    WHEN event_name LIKE 'banner%' THEN 'Awareness'
                    WHEN event_name = 'click_banner' THEN 'Interest'
                    WHEN event_name = 'purchase' THEN 'Conversion'
                    ELSE 'Other'
                END as funnel_stage
            FROM user_journey
            ORDER BY user_id, event_sequence
            """
            df_raw_full = al.run_query(raw_data_sql)

            if not df_raw_full.empty:
                csv_data = df_raw_full.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 CSV 다운로드",
                    data=csv_data,
                    file_name=f"experiment_{current_run_id}_enriched_data.csv",
                    mime="text/csv",
                    use_container_width=True,
                    help="User Journey 분석을 위한 이벤트 시퀀스, 퍼널 단계 포함"
                )

        # Show sample (first 10 rows) or generate educational sample
        if not df_raw_full.empty:
            st.caption(f"총 {len(df_raw_full):,}개 이벤트 (상위 10개 샘플 표시)")
            st.caption("**포함 필드**: event_sequence (이벤트 순서), prev/next_event (이전/다음 이벤트), time_since_last_event (초), funnel_stage (퍼널 단계)")
            st.dataframe(df_raw_full.head(10), width="stretch", hide_index=True)
        else:
            # Educational fallback: Generate sample raw data
            st.info("📚 **[학습 모드]** 실제 이벤트 데이터가 없어 샘플 로그를 표시합니다.")
            import uuid
            from datetime import datetime, timedelta
            sample_events = []
            base_time = datetime.now() - timedelta(minutes=30)
            for i in range(10):
                user_num = i // 3 + 1
                variant = 'A' if user_num % 2 == 1 else 'B'
                event_types = ['page_view', 'banner_A' if variant == 'A' else 'banner_B', 'click_banner', 'purchase']
                event_name = event_types[i % 4]
                sample_events.append({
                    'event_id': str(uuid.uuid4())[:8],
                    'user_id': f'sample_user_{user_num:03d}',
                    'variant': variant,
                    'event_name': event_name,
                    'timestamp': (base_time + timedelta(seconds=i*45)).strftime('%Y-%m-%d %H:%M:%S'),
                    'value': 25000 + (i * 1000) if event_name == 'purchase' else 0,
                    'event_sequence': (i % 3) + 1,
                    'funnel_stage': 'Awareness' if 'banner' in event_name else ('Conversion' if event_name == 'purchase' else 'Other')
                })
            df_sample = pd.DataFrame(sample_events)
            st.caption("**샘플 이벤트 로그** (학습용)")
            st.dataframe(df_sample, width="stretch", hide_index=True)
            st.caption("⚠️ 위 데이터는 학습용 샘플입니다. 실제 실험 후 실 데이터가 표시됩니다.")

        # Show aggregated summary
        st.caption("**집계 요약 (Aggregated Summary)**")
        st.dataframe(df, width="stretch", hide_index=True)
        
        # Report Saving
        st.divider()
        st.markdown("#### 📝 실험 회고록 작성")
        note = st.text_area("배운 점 (Learning Note)", help="이번 실험에서 얻은 인사이트를 기록하세요.")

        # Show current DB mode status
        if st.session_state.get('use_db_coordination', True):
            st.caption("💡 DB 협조 모드 활성화 (사이드바에서 변경 가능)")
        else:
            st.caption("⚠️ 레거시 모드 활성화 (사이드바에서 변경 가능)")

        if st.button("💾 실험 회고록에 저장", type="primary"):
            import json

            # Prepare guardrail results for storage - use session state for reliability
            # Convert numpy types to native Python types for JSON serialization
            stored_guard_results = st.session_state.get('guard_results', [])
            serializable_results = []
            for gr in stored_guard_results:
                serializable_results.append({
                    "metric": str(gr.get("metric", "")),
                    "control": float(gr.get("control", 0)),
                    "test": float(gr.get("test", 0)),
                    "lift": float(gr.get("lift", 0)),
                    "passed": bool(gr.get("passed", True))
                })
            guardrail_results_json = json.dumps(serializable_results) if serializable_results else '[]'

            # Build operations list
            operations = []

            # 1. Insert experiment record
            operations.append((
                """INSERT INTO experiments (
                    target, hypothesis, primary_metric, guardrails,
                    p_value, decision, learning_note, run_id,
                    control_rate, test_rate, lift, guardrail_results,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                [
                    st.session_state.get('target', '-'),
                    st.session_state.get('hypothesis', '-'),
                    st.session_state.get('metric', '-'),
                    ','.join(st.session_state.get('guardrails', [])),
                    res['p_value'], decision, note, current_run_id,
                    res['control_rate'], res['test_rate'], res['lift'],
                    guardrail_results_json
                ]
            ))

            # 2. If adoption was marked, create table and insert
            if st.session_state.get('pending_adoption'):
                adoption_data = st.session_state['pending_adoption']
                # Store lift/p_value in variant_config JSON instead of separate columns
                # This ensures compatibility with existing table schema
                variant_data = adoption_data['variant'].copy() if isinstance(adoption_data['variant'], dict) else {}
                variant_data['lift'] = adoption_data.get('lift')
                variant_data['p_value'] = adoption_data.get('p_value')
                variant_json = json.dumps(variant_data)

                # Create sequence and table if needed (DuckDB uses sequences for auto-increment)
                operations.append((
                    "CREATE SEQUENCE IF NOT EXISTS adoptions_seq",
                    None
                ))
                operations.append((
                    """CREATE TABLE IF NOT EXISTS adoptions (
                        adoption_id INTEGER DEFAULT nextval('adoptions_seq'),
                        experiment_id VARCHAR,
                        variant_config VARCHAR,
                        adopted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )""",
                    None
                ))
                operations.append((
                    "INSERT INTO adoptions (experiment_id, variant_config) VALUES (?, ?)",
                    [current_run_id, variant_json]
                ))
                # Deactivate experiment - adopted variant becomes new baseline
                operations.append(("DELETE FROM active_experiment", None))

            # 3. Clean up run data
            operations.append((f"DELETE FROM assignments WHERE run_id = '{current_run_id}'", None))
            operations.append((f"DELETE FROM events WHERE run_id = '{current_run_id}'", None))

            # Execute with coordination mode setting
            result = safe_write_batch(operations, use_coordination=st.session_state.get('use_db_coordination', True))

            # Accept both 'success' and 'partial_error' (some non-critical ops may fail)
            if result['status'] in ['success', 'partial_error']:
                # Clear caches to ensure UI reflects latest DB state
                st.cache_data.clear()

                if st.session_state.get('pending_adoption'):
                    st.session_state.pop('pending_adoption', None)
                    st.session_state['last_adoption_success'] = True  # Track adoption for UI feedback
                    st.toast("🎉 실험이 채택되어 Target App에 적용되었습니다!")

                if result['status'] == 'partial_error':
                    # Show warning but still proceed
                    st.toast("⚠️ 일부 작업 실패 (중요 데이터는 저장됨)")
                else:
                    st.toast("저장 완료!")

                # Clear experiment-related session state
                st.session_state.pop('current_run_id', None)
                st.session_state.pop('guard_results', None)
                st.session_state.pop('show_adoption_success', None)
                st.session_state['page'] = 'portfolio'
                st.session_state['step'] = 1
                st.rerun()
            else:
                # Show detailed error info
                st.error(f"❌ 저장 실패: {result.get('message', 'Unknown error')}")
                if 'results' in result:
                    failed_ops = [r for r in result['results'] if r.get('status') == 'error']
                    if failed_ops:
                        with st.expander("🔍 실패한 작업 상세"):
                            for op in failed_ops:
                                st.code(f"SQL: {op.get('sql', 'N/A')}\nError: {op.get('message', 'N/A')}")
                st.info("💡 '고급 설정'에서 'DB 협조 모드' 체크박스를 해제하고 다시 시도해보세요.")

# =========================================================
# PAGE: PORTFOLIO
# =========================================================
elif st.session_state['page'] == 'portfolio':
    st.title("📚 실험 회고록 (Experiment Retrospective)")

    # Load all experiments data
    df_history = al.run_query("SELECT * FROM experiments ORDER BY created_at DESC")

    # Sidebar filters
    with st.sidebar:
        st.markdown("### 필터")

        # Get unique targets for filtering
        if not df_history.empty:
            targets = ['전체'] + sorted(df_history['target'].dropna().unique().tolist())
            selected_target = st.selectbox("대상 (Target)", targets)

            # Decision filter
            decisions = ['전체', 'positive', 'negative', 'neutral']
            selected_decision = st.selectbox("결과", decisions)
        else:
            selected_target = '전체'
            selected_decision = '전체'

    # ==========================================
    # Section 1: Adopted Experiments
    # ==========================================
    st.markdown("### ✅ 채택된 실험 (Adopted Experiments)")
    st.caption("플랫폼에 실제로 적용되어 비즈니스에 기여한 실험들")

    try:
        df_adoptions = al.run_query("""
            SELECT
                a.experiment_id,
                a.adopted_at,
                a.variant_config,
                e.hypothesis,
                e.target,
                e.primary_metric,
                e.learning_note,
                e.control_rate,
                e.test_rate,
                e.lift,
                e.p_value,
                e.guardrails,
                e.guardrail_results
            FROM adoptions a
            LEFT JOIN experiments e ON a.experiment_id = e.run_id
            ORDER BY a.adopted_at DESC
        """)

        if not df_adoptions.empty:
            # Group by target
            grouped = df_adoptions.groupby('target')
            for target_name, group in grouped:
                with st.expander(f"📍 {target_name or '미분류'} ({len(group)}건)", expanded=True):
                    for _, row in group.iterrows():
                        with st.container(border=True):
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown(f"**✨ {row.get('hypothesis', '실험 가설')}**")
                                st.caption(f"📊 Metric: {row.get('primary_metric', 'N/A')}")
                            with col2:
                                lift_val = row['lift'] * 100 if row['lift'] else 0
                                st.metric("Lift", f"{lift_val:+.1f}%", delta=f"p={row['p_value']:.4f}" if row['p_value'] else "N/A")

                            # Expandable details
                            with st.expander("상세 보기"):
                                detail_col1, detail_col2 = st.columns(2)
                                with detail_col1:
                                    st.markdown("**📈 성과 지표**")
                                    ctrl_rate = row.get('control_rate', 0) or 0
                                    test_rate = row.get('test_rate', 0) or 0
                                    st.write(f"- Control 전환율: {ctrl_rate:.2f}%")
                                    st.write(f"- Test 전환율: {test_rate:.2f}%")
                                    st.write(f"- p-value: {row.get('p_value', 'N/A')}")
                                with detail_col2:
                                    st.markdown("**🛡️ 가드레일**")
                                    guardrails_str = row.get('guardrails', '')
                                    st.write(f"- 설정: {guardrails_str if guardrails_str else '없음'}")
                                    # Parse guardrail_results JSON
                                    gr_results = row.get('guardrail_results', '')
                                    if gr_results and gr_results != '[]' and gr_results != 'null' and gr_results != 'None':
                                        try:
                                            gr_list = json.loads(gr_results) if isinstance(gr_results, str) else gr_results
                                            if gr_list and isinstance(gr_list, list) and len(gr_list) > 0:
                                                for gr in gr_list:
                                                    status = "✅ Pass" if gr.get('passed', False) else "❌ Fail"
                                                    lift_val = gr.get('lift', 0) * 100
                                                    st.write(f"- {gr.get('metric', 'N/A')}: {status} ({lift_val:+.1f}%)")
                                            else:
                                                if guardrails_str:
                                                    st.write("- 결과: 데이터 부족")
                                                else:
                                                    st.write("- 결과: 가드레일 미설정")
                                        except:
                                            st.write("- 결과: 파싱 오류")
                                    else:
                                        if guardrails_str:
                                            st.write("- 결과: 측정 데이터 없음")
                                        else:
                                            st.write("- 결과: 가드레일 미설정")

                                # Show adopted variant config
                                variant_config = row.get('variant_config', '')
                                if variant_config:
                                    st.markdown("**🎨 채택된 변형 설정**")
                                    try:
                                        config = json.loads(variant_config) if isinstance(variant_config, str) else variant_config
                                        st.json(config)
                                    except:
                                        st.code(variant_config)

                                if row.get('learning_note'):
                                    st.markdown("**📝 학습 내용**")
                                    st.info(row['learning_note'])

                            st.caption(f"🕐 채택일시: {row['adopted_at']}")
        else:
            st.info("아직 채택된 실험이 없습니다. 성공적인 실험을 채택하면 여기에 표시됩니다!")
    except Exception as e:
        error_msg = str(e).lower()
        if 'does not exist' in error_msg or 'relation' in error_msg:
            st.info("아직 채택된 실험이 없습니다.")
        else:
            st.warning(f"⚠️ 채택 정보 조회 오류: {e}")

    st.divider()

    # ==========================================
    # Section 2: All Experiments by Category
    # ==========================================
    st.markdown("### 📋 전체 실험 기록 (All Experiments)")

    if df_history.empty:
        st.info("실험 기록이 없습니다.")
    else:
        # Apply filters
        filtered_df = df_history.copy()
        if selected_target != '전체':
            filtered_df = filtered_df[filtered_df['target'] == selected_target]
        if selected_decision != '전체':
            filtered_df = filtered_df[filtered_df['decision'] == selected_decision]

        if filtered_df.empty:
            st.info("선택한 필터에 해당하는 실험이 없습니다.")
        else:
            # Group by target
            grouped = filtered_df.groupby('target')

            for target_name, group in grouped:
                with st.expander(f"📍 {target_name or '미분류'} ({len(group)}건)", expanded=True):
                    for _, row in group.iterrows():
                        # Determine result badge
                        decision = row.get('decision', '')
                        if decision == 'positive':
                            badge = "🟢 Significant Winner"
                            badge_color = "green"
                        elif decision == 'negative':
                            badge = "🔴 Significant Loser"
                            badge_color = "red"
                        else:
                            badge = "🟡 Inconclusive"
                            badge_color = "orange"

                        with st.container(border=True):
                            col1, col2, col3 = st.columns([3, 1, 1])
                            with col1:
                                st.markdown(f"**{row.get('hypothesis', '실험 가설')}**")
                                st.caption(f"📊 {row.get('primary_metric', 'N/A')} | {str(row.get('created_at', ''))[:10] if row.get('created_at') else 'N/A'}")
                            with col2:
                                lift = row.get('lift', 0) or 0
                                st.metric("Lift", f"{lift*100:+.1f}%" if lift else "N/A")
                            with col3:
                                st.markdown(f"<span style='background-color:{badge_color};color:white;padding:2px 8px;border-radius:4px;font-size:12px;'>{badge.split(' ')[0]} {badge.split(' ')[1] if len(badge.split(' '))>1 else ''}</span>", unsafe_allow_html=True)

                            # Expandable experiment details
                            with st.expander("📄 실험 상세"):
                                st.markdown("**가설 (Hypothesis)**")
                                st.write(row.get('hypothesis', 'N/A'))

                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.markdown("**📈 결과 지표**")
                                    ctrl_rate = row.get('control_rate', 0) or 0
                                    test_rate = row.get('test_rate', 0) or 0
                                    st.write(f"- Control 전환율: {ctrl_rate:.2f}%")
                                    st.write(f"- Test 전환율: {test_rate:.2f}%")
                                    st.write(f"- p-value: {row.get('p_value', 'N/A')}")

                                with col_b:
                                    st.markdown("**🛡️ 가드레일**")
                                    guardrails_str = row.get('guardrails', '')
                                    st.write(f"- 설정: {guardrails_str if guardrails_str else '없음'}")
                                    # Parse guardrail_results JSON
                                    gr_results = row.get('guardrail_results', '')
                                    if gr_results and gr_results != '[]' and gr_results != 'null' and gr_results != 'None':
                                        try:
                                            gr_list = json.loads(gr_results) if isinstance(gr_results, str) else gr_results
                                            if gr_list and isinstance(gr_list, list) and len(gr_list) > 0:
                                                for gr in gr_list:
                                                    status = "✅ Pass" if gr.get('passed', False) else "❌ Fail"
                                                    lift_val = gr.get('lift', 0) * 100
                                                    st.write(f"- {gr.get('metric', 'N/A')}: {status} ({lift_val:+.1f}%)")
                                            else:
                                                if guardrails_str:
                                                    st.write("- 결과: 데이터 부족 (시뮬레이션 데이터 없음)")
                                                else:
                                                    st.write("- 결과: 가드레일 미설정")
                                        except Exception as e:
                                            st.write(f"- 결과: 파싱 오류")
                                    else:
                                        if guardrails_str:
                                            st.write("- 결과: 측정 데이터 없음 (시뮬레이션 미실행)")
                                        else:
                                            st.write("- 결과: 가드레일 미설정")

                                if row.get('learning_note'):
                                    st.markdown("**📝 학습 및 인사이트**")
                                    st.info(row['learning_note'])

                                st.caption(f"Run ID: {row.get('run_id', 'N/A')}")

    # ==========================================
    # Section 3: Summary Statistics (Based on Adoptions, not p-value)
    # ==========================================
    st.divider()
    st.markdown("### 📊 실험 요약 통계")

    if not df_history.empty:
        # Get adopted experiment IDs from adoptions table
        try:
            adopted_ids_df = al.run_query("SELECT DISTINCT experiment_id FROM adoptions")
            adopted_ids = set(adopted_ids_df['experiment_id'].tolist()) if not adopted_ids_df.empty else set()
        except:
            adopted_ids = set()

        # Count adopted experiments (based on adoptions table, not decision field)
        adopted_count = len([rid for rid in df_history['run_id'].tolist() if rid in adopted_ids])
        non_adopted_count = len(df_history) - adopted_count

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("총 실험 수", len(df_history))
        with col2:
            st.metric("채택 (Adopted)", adopted_count)
        with col3:
            st.metric("미채택 (Not Adopted)", non_adopted_count)
        with col4:
            adoption_rate = (adopted_count / len(df_history) * 100) if len(df_history) > 0 else 0
            st.metric("채택률", f"{adoption_rate:.1f}%")
