"""
Dashboard Page - Operations Center / Situation Room
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import time
from datetime import datetime

from src.core import stats as al


def render():
    """Render the dashboard/operations center page."""
    _render_header()

    # Check for historical data
    check_history = al.run_query(
        "SELECT COUNT(*) as cnt FROM assignments WHERE user_id LIKE 'user_hist_%'"
    )
    has_history = not check_history.empty and check_history.iloc[0, 0] > 0

    if not has_history:
        _render_no_data_warning()
    else:
        _render_realtime_pulse()
        st.divider()
        _render_business_intelligence()
        st.divider()
        _render_system_monitor()


def _render_header():
    """Render the dashboard header."""
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


def _render_no_data_warning():
    """Render warning when no historical data exists."""
    st.warning("경고: 과거 데이터가 없습니다. 원활한 상황실 운영을 위해 30일치 데이터를 생성하세요.")
    if st.button("🔄 데이터 초기화 (Reset)", type="primary"):
        st.info("터미널에서 `python scripts/generate_history.py`를 실행하세요.")


def _render_realtime_pulse():
    """Render real-time pulse section."""
    st.markdown("### 🟢 실시간 운영 현황 (Real-time Pulse)")

    # Real-time Queries
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

    # Server Latency Check
    latency_ms, server_status = _check_server_health()

    # Display metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("현재 접속자 (30min)", f"{now_users}명", "Real-time")
    with c2:
        st.metric("오늘 매출 (Values)", f"₩{int(today_rev):,}", f"{today_orders} Orders")
    with c3:
        st.metric("시스템 상태 (Health)", server_status, f"{latency_ms}ms")
    with c4:
        st.metric("데이터 마트 (ETL)", "Sync Active", "Daily Updated")

    # Recent Events Log
    _render_recent_events()


def _check_server_health():
    """Check server health and latency."""
    start_time = time.time()
    latency_ms = 0
    server_status = "Offline"

    try:
        requests.get("http://localhost:8000", timeout=1)
        latency_ms = int((time.time() - start_time) * 1000)
        server_status = "Online"
    except Exception:
        latency_ms = 0
        server_status = "Down"

    return latency_ms, server_status


def _render_recent_events():
    """Render recent events ticker."""
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


def _render_business_intelligence():
    """Render business intelligence section."""
    st.markdown("### 🔵 비즈니스 분석 (Business Intelligence)")

    # Fetch from Data Mart
    sql_mart = "SELECT * FROM dm_daily_kpi ORDER BY report_date ASC"
    df_trend = al.run_query(sql_mart)

    if df_trend.empty:
        st.warning("데이터 마트가 비어있습니다. Data Lab에서 먼저 마트를 구축하세요.")
        return

    # Calculate metrics
    has_rev = 'total_revenue' in df_trend.columns
    has_aov = 'aov' in df_trend.columns
    has_cvr = 'cvr' in df_trend.columns

    avg_rev = df_trend['total_revenue'].mean() if has_rev else 0
    avg_aov = df_trend['aov'].mean() if has_aov else 0

    latest = df_trend.iloc[-1]
    prev = df_trend.iloc[-2] if len(df_trend) > 1 else latest

    # Business Metrics
    _render_business_metrics(has_rev, has_aov, has_cvr, avg_rev, avg_aov, latest, prev)

    # Chart Area
    _render_charts(df_trend, has_rev, has_aov, latest)


def _render_business_metrics(has_rev, has_aov, has_cvr, avg_rev, avg_aov, latest, prev):
    """Render business metrics row."""
    b1, b2, b3, b4 = st.columns(4)

    with b1:
        if has_rev:
            st.metric(
                "일평균 매출 (Revenue)",
                f"₩{int(avg_rev):,}",
                f"{int(latest['total_revenue']-prev['total_revenue']):,}원"
            )
        else:
            st.metric(
                "일평균 매출 (Revenue)", "-", "Not Selected",
                help="Data Lab에서 'Revenue' 지표를 추가하세요."
            )

    with b2:
        if has_aov:
            st.metric(
                "객단가 (AOV)",
                f"₩{int(avg_aov):,}",
                f"{int(latest['aov']-prev['aov']):,}원"
            )
        else:
            st.metric(
                "객단가 (AOV)", "-", "Not Selected",
                help="Data Lab에서 'AOV' 지표를 추가하세요."
            )

    with b3:
        if has_cvr:
            st.metric(
                "구매 전환율 (CVR)",
                f"{latest['cvr']*100:.2f}%",
                f"{(latest['cvr']-prev['cvr'])*100:.2f}%"
            )
        else:
            st.metric(
                "구매 전환율 (CVR)", "-", "Not Selected",
                help="Data Lab에서 'CVR' 지표를 추가하세요."
            )

    with b4:
        st.metric("재구매율 (Retention)", "28.4%", "예측치")


def _render_charts(df_trend, has_rev, has_aov, latest):
    """Render chart tabs."""
    tab_names = []
    if has_rev:
        tab_names.append("💰 매출 트렌드")
    if has_aov:
        tab_names.append("🛒 객단가(AOV)")
    tab_names.append("🔻 퍼널 분석")

    tabs = st.tabs(tab_names)

    idx = 0
    if has_rev:
        with tabs[idx]:
            fig = px.area(
                df_trend, x='report_date', y='total_revenue',
                title='Daily Revenue Trend', template='plotly_dark'
            )
            fig.update_traces(line_color='#8B5CF6', fillcolor="rgba(139, 92, 246, 0.3)")
            st.plotly_chart(fig, use_container_width=True)
        idx += 1

    if has_aov:
        with tabs[idx]:
            fig2 = px.bar(
                df_trend, x='report_date', y='aov',
                title='Average Order Value (AOV)', template='plotly_dark'
            )
            fig2.update_traces(marker_color='#3B82F6')
            st.plotly_chart(fig2, use_container_width=True)
        idx += 1

    with tabs[idx]:
        _render_funnel(df_trend, latest)


def _render_funnel(df_trend, latest):
    """Render conversion funnel."""
    cols_present = df_trend.columns
    v_total = latest['total_users'] if 'total_users' in cols_present else 0
    v_click = latest['click_count'] if 'click_count' in cols_present else 0
    v_order = latest['total_orders'] if 'total_orders' in cols_present else 0

    funnel_data = dict(
        number=[v_total, v_click, v_order],
        stage=["1. 방문 (Total Users)", "2. 클릭 (Active Clicks)", "3. 구매 (Orders)"]
    )
    fig3 = px.funnel(
        funnel_data, x='number', y='stage',
        title=f'Conversion Funnel ({latest["report_date"]})',
        template='plotly_dark'
    )
    st.plotly_chart(fig3, use_container_width=True)


def _render_system_monitor():
    """Render system and crisis monitoring section."""
    st.markdown("### 🟠 시스템 및 위기 감지 (System Integrity)")

    # Fetch mart data for alerts
    sql_mart = "SELECT * FROM dm_daily_kpi ORDER BY report_date ASC"
    df_trend = al.run_query(sql_mart)

    if df_trend.empty:
        st.info("데이터가 없어 위기 감지를 수행할 수 없습니다.")
        return

    latest = df_trend.iloc[-1]
    prev = df_trend.iloc[-2] if len(df_trend) > 1 else latest

    alerts = _detect_alerts(df_trend, latest, prev)

    st.caption(
        "ℹ️ **감지 로직(Detection Logic)**: CTR < 5% (소재 피로), 매출 하락 > 30% (이탈 위험), "
        "CVR < 1% (UX 마찰). 모든 데이터는 실제 DB(`dm_daily_kpi`)에서 실시간으로 연산됩니다."
    )

    if alerts:
        for alert in alerts:
            _render_alert(alert, df_trend)
    else:
        st.success("✅ 모든 시스템 및 비즈니스 지표가 정상 범위(Normal) 내에서 운영 중입니다.")
        st.caption(f"Based on real-time data from `dm_daily_kpi` (Updated: {datetime.now().strftime('%H:%M')})")

    with st.expander("⚙️ 데이터 관리 (Admin)"):
        if st.button("데이터 재생성 (Reset History)"):
            st.warning("터미널에서 generate_history.py를 실행하세요.")


def _detect_alerts(df_trend, latest, prev):
    """Detect business alerts based on metrics."""
    alerts = []

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
        if prev_rev > 0 and (curr_rev / prev_rev) < 0.7:
            drop_rate = (1 - (curr_rev / prev_rev)) * 100
            alerts.append({
                "level": "Warning",
                "title": "매출(Revenue) 이상 하락",
                "desc": f"전일 대비 매출이 **-{drop_rate:.1f}%** 감소했습니다.",
                "cause": "구매 전환율(CVR) 저하 또는 결제 시스템 장애 가능성",
                "action": "결제 프로세스 점검 및 할인율 조정 실험",
                "target": "카테고리 아이콘 (치킨)",
                "metric_key": "total_revenue",
                "threshold": None
            })

    # 3. CVR Alert (UX Friction)
    if 'cvr' in df_trend.columns and latest['cvr'] < 0.01:
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

    return alerts


def _render_alert(alert, df_trend):
    """Render a single alert card."""
    with st.container(border=True):
        c_text, c_btn = st.columns([3.5, 1])

        with c_text:
            st.markdown(f"#### 🚨 {alert['title']}")
            st.markdown(f"**현상**: {alert['desc']}")
            st.info(f"**원인/조치**: {alert['cause']} → {alert['action']}")

        with c_btn:
            st.write("")
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
                fig_alert = px.line(
                    df_trend, x='report_date', y=metric, markers=True,
                    title=f"{alert['title']} - Trend View", template="plotly_dark"
                )
                fig_alert.update_traces(line_color='#ef4444', line_width=3)

                if alert.get('threshold'):
                    fig_alert.add_hline(
                        y=alert['threshold'], line_dash="dash",
                        line_color="yellow", annotation_text="Threshold (위험 기준)"
                    )

                st.plotly_chart(fig_alert, use_container_width=True)
            else:
                st.warning("해당 지표의 상세 데이터를 불러올 수 없습니다.")
