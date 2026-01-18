"""
Experiment Page - A/B Test Wizard (Steps 1-4)
"""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import subprocess
import sys
import os
import time
import json
import duckdb

from src.core import stats as al
from src.ui import components as ui

# Page and Component Mapping
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

# Metrics database
METRICS_DB = {
    "CTR (클릭률)": {"desc": "노출 대비 클릭한 비율", "formula": "Clicks / Impressions", "type": "Conversion"},
    "CVR (전환율)": {"desc": "방문자 중 실제 구매 비율", "formula": "Orders / Visitors", "type": "Conversion"},
    "AOV (평균 주문액)": {"desc": "구매 고객 1인당 평균 결제 금액", "formula": "Revenue / Orders", "type": "Revenue"},
    "Bounce Rate (이탈률)": {"desc": "첫 페이지만 보고 나가는 비율", "formula": "One-page / Total", "type": "Retention"},
}


def render():
    """Render the experiment wizard page."""
    steps = ["1. Hypothesis", "2. Design", "3. Collection", "4. Analysis"]
    ui.render_step_progress(steps, st.session_state['step'])

    curr = st.session_state['step']

    if curr == 1:
        render_step1_hypothesis()
    elif curr == 2:
        render_step2_design()
    elif curr == 3:
        render_step3_collection()
    elif curr == 4:
        render_step4_analysis()


def render_step1_hypothesis():
    """Step 1: Hypothesis - Define target and variables."""
    st.markdown("<h2>Step 1. 목표 정의 (Define Your Vision)</h2>", unsafe_allow_html=True)
    ui.edu_guide(
        "가설(Hypothesis)",
        "데이터 분석은 막연한 시도가 아닙니다. **'무엇을(X) 바꾸면 어떤 지표(Y)가 좋아질 것이다'**라는 명확한 믿음을 정의하세요."
    )

    col_mock, col_form = st.columns([1.2, 1], gap="large")

    # Determine Current Selection
    default_page = list(PAGE_MAP.keys())[0]
    sel_page = st.session_state.get('builder_page', default_page)
    sel_comp_name = st.session_state.get('builder_comp', list(PAGE_MAP[sel_page]['components'].keys())[0])

    sel_url_path = PAGE_MAP[sel_page]['url']
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

    # 2. Form - Dynamic Builder
    with col_form:
        with st.container(border=True):
            st.markdown("#### 🧬 실험 설계 (Experiment Builder)")
            _render_experiment_builder_tabs(comp_type, sel_comp_name, sel_page)


def _render_experiment_builder_tabs(comp_type, sel_comp_name, sel_page):
    """Render experiment builder tabs (Design & Strategy)."""
    tab_design, tab_strategy = st.tabs(["🎨 디자인 (Design)", "📊 전략 (Strategy)"])

    variant_val = ""

    with tab_design:
        variant_val = _render_design_tab(comp_type, sel_comp_name, sel_page)

    with tab_strategy:
        _render_strategy_tab(comp_type, sel_comp_name, variant_val)


def _render_design_tab(comp_type, sel_comp_name, sel_page):
    """Render the design tab content."""
    st.caption("1. 실험 대상 선택")

    # Page Selection
    st.markdown("**페이지 선택**")
    page_cols = st.columns(len(PAGE_MAP))
    selected_page_idx = list(PAGE_MAP.keys()).index(st.session_state.get('builder_page', list(PAGE_MAP.keys())[0]))

    for idx, (page_name, page_data) in enumerate(PAGE_MAP.items()):
        with page_cols[idx]:
            is_selected = (idx == selected_page_idx)
            if st.button(
                f"{'✓ ' if is_selected else ''}{page_name}",
                key=f"page_btn_{idx}",
                use_container_width=True,
                type="primary" if is_selected else "secondary"
            ):
                st.session_state['builder_page'] = page_name
                st.session_state['builder_comp'] = list(page_data['components'].keys())[0]
                st.rerun()

    target_page = st.session_state.get('builder_page', list(PAGE_MAP.keys())[0])

    st.write("")

    # Component Selection
    st.markdown("**요소 선택**")
    comp_data = PAGE_MAP[target_page]['components']
    comp_names = list(comp_data.keys())

    comp_cols = st.columns(2)
    selected_comp = st.session_state.get('builder_comp', comp_names[0])

    for idx, comp_name in enumerate(comp_names):
        with comp_cols[idx % 2]:
            is_selected = (comp_name == selected_comp)
            if st.button(
                f"{'✓ ' if is_selected else ''}{comp_name}",
                key=f"comp_btn_{idx}",
                use_container_width=True,
                type="primary" if is_selected else "secondary"
            ):
                st.session_state['builder_comp'] = comp_name
                st.rerun()

    target_comp = selected_comp
    current_target = f"{target_page} > {target_comp}"
    st.session_state['target'] = current_target

    st.divider()

    # Variables Simulation
    st.write("")
    st.caption("2. 변인 시뮬레이션")

    # Get updated comp_type for selected component
    comp_type = PAGE_MAP[target_page]['components'].get(target_comp, {"type": "TEXT"})['type']

    variant_summary, config_data = _render_variant_form(comp_type)

    st.session_state['exp_variant_data'] = config_data
    st.success("✅ 디자인 설정 완료! 상단의 **'📊 전략 (Strategy)'** 탭으로 이동하세요.", icon="👉")

    return variant_summary


def _render_variant_form(comp_type):
    """Render the variant configuration form based on component type."""
    bg_map = {
        "Red (Urgent)": "#EF4444", "Blue (Trust)": "#3B82F6",
        "Black (Dark Mode)": "#111827", "#EF4444 (Red)": "#EF4444",
        "#3B82F6 (Blue)": "#3B82F6", "#10B981 (Green)": "#10B981",
        "#111827 (Black)": "#111827"
    }

    st.markdown(
        f"**Group B (Test)** <span style='background:#4B5563; padding:2px 6px; border-radius:4px; font-size:0.7em'>{comp_type}</span>",
        unsafe_allow_html=True
    )

    config_data = {}
    variant_summary = ""

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
        img_url = "https://cdn-icons-png.flaticon.com/512/3075/3075977.png" if "3D" in config_data['style'] else "https://cdn-icons-png.flaticon.com/512/709/709699.png"
        b_html = f"""<div style='text-align:center;'><img src='{img_url}' style='width:64px; height:64px; drop-shadow:0 10px 10px rgba(0,0,0,0.2);'></div>"""

    elif comp_type == 'TEXT':
        config_data['content'] = st.text_input("내용", "수정된 텍스트")
        config_data['size'] = st.slider("크기 (px)", 12, 32, 18)
        config_data['color'] = st.color_picker("색상", "#EF4444")
        variant_summary = "텍스트 변경"
        b_html = f"""<div style='font-size:{config_data['size']}px; color:{config_data['color']}; font-weight:bold; text-align:center;'>{config_data['content']}</div>"""

    else:
        val = st.text_input("변경 내용", "Layout Change")
        variant_summary = val
        b_html = f"<div style='background:#374151; padding:10px; border-radius:8px; text-align:center; color:#9CA3AF;'>{val}</div>"

    st.caption("👇 미리보기 (Preview)")
    st.markdown(b_html, unsafe_allow_html=True)

    return variant_summary, config_data


def _render_strategy_tab(comp_type, target_comp, variant_summary):
    """Render the strategy tab content."""
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

    # Metrics Settings
    st.markdown("#### 🎯 지표 설정")

    # Auto Recommendation
    rec_metric = "CTR (클릭률)"
    if comp_type == 'BUTTON':
        rec_metric = "CVR (전환율)"
    elif comp_type == 'TEXT' or comp_type == 'ICON':
        rec_metric = "Bounce Rate (이탈률)"

    st.success(f"🤖 AI 추천: **{rec_metric}** (요소 속성 '{comp_type}' 기반)")

    c_m1, c_m2 = st.columns(2, gap="medium")

    with c_m1:
        st.markdown("**핵심 지표 (Primary Metric)**")
        m_sel = st.selectbox(
            "지표 선택", list(METRICS_DB.keys()),
            index=list(METRICS_DB.keys()).index(rec_metric), label_visibility="collapsed"
        )
        st.caption(f"📝 {METRICS_DB[m_sel]['desc']}")

        st.write("")
        st.markdown("**최소 목표 상승폭 (MDE)**")
        min_eff = st.slider(
            "목표", 1, 30, 5, format="+%d%%",
            help=f"실험군(B)의 {m_sel}가 대조군(A)보다 최소 이만큼은 높아야 성공으로 간주합니다.",
            label_visibility="collapsed"
        )

    with c_m2:
        st.markdown("**보조 지표 (Secondary Metrics)**")
        avail_gr = [k for k in METRICS_DB.keys() if k != m_sel]
        g_sel = st.multiselect(
            "지표 선택", avail_gr, default=avail_gr[:1],
            help="주 메트릭 외에 함께 관찰할 지표입니다.",
            label_visibility="collapsed"
        )

        if g_sel:
            st.caption(f"📝 {METRICS_DB[g_sel[0]]['desc']}")
        else:
            st.caption("선택된 보조 지표가 없습니다.")

        st.write("")
        if g_sel:
            st.markdown("**안전 마진 (Safety Margin)**")
            guard_threshold = st.slider(
                "경계선", 1.0, 20.0, 5.0, format="-%.1f%%",
                help="보조 지표가 이 기준 이상 떨어지면 주의가 필요합니다.",
                label_visibility="collapsed"
            )
        else:
            guard_threshold = 5.0

    st.write("")
    if st.button("실험 설계 완료 및 다음 단계 ➡️", type="primary", use_container_width=True):
        if not hypo:
            st.toast("가설을 입력해야 진행할 수 있습니다!", icon="⚠️")
        elif not variant_summary:
            st.toast("Group B의 변경 사항을 입력해주세요!", icon="⚠️")
        else:
            target_page = st.session_state.get('builder_page', list(PAGE_MAP.keys())[0])
            st.session_state['hypothesis'] = hypo
            st.session_state['metric'] = m_sel
            st.session_state['guardrails'] = g_sel
            st.session_state['session_guard_threshold'] = guard_threshold
            st.session_state['min_effect'] = min_eff
            st.session_state['guard_metric'] = g_sel[0] if g_sel else ""

            st.session_state['exp_config'] = {
                "page": target_page,
                "component": target_comp,
                "control": "Default",
                "variant": variant_summary
            }

            st.session_state['step'] = 2
            st.rerun()


def render_step2_design():
    """Step 2: Experiment Design - Traffic split and sample size."""
    st.markdown("<h2>Step 2. 실험 설계 (Experiment Design)</h2>", unsafe_allow_html=True)
    ui.edu_guide("실험 설계의 3요소", "트래픽 비율 → 목표 설정 → 필요 표본 계산 순서로 진행합니다.")

    st.markdown("#### 1️⃣ 트래픽 비율 설정 (Traffic Allocation)")
    split = st.slider("테스트(B) 그룹 배정 비율", 10, 90, 50, format="%d%%")
    st.caption(f"나머지 {100-split}%는 Control(A) 그룹에 배정됩니다.")

    st.divider()

    st.markdown("#### 2️⃣ 필요 표본 수 계산 (Sample Size)")

    selected_metric = st.session_state.get('metric', 'CTR (클릭률)')

    # Fetch baseline
    auto_baseline = _get_baseline_metric(selected_metric)

    # Get MDE from Step 1
    mde_percent = st.session_state.get('min_effect', 5)
    mde = mde_percent / 100.0

    # Calculate Sample Size
    n_per_group = al.calculate_sample_size(auto_baseline, mde)

    # Account for traffic split
    control_pct = split / 100.0
    test_pct = 1.0 - control_pct

    if split == 50:
        total_needed = n_per_group * 2
    else:
        total_for_control = int(n_per_group / control_pct) if control_pct > 0 else n_per_group * 2
        total_for_test = int(n_per_group / test_pct) if test_pct > 0 else n_per_group * 2
        total_needed = max(total_for_control, total_for_test)

    # Display Metrics
    c1, c2, c3 = st.columns(3, gap="large")

    with c1:
        st.metric(f"현재 수준 (Baseline)", f"{auto_baseline*100:.2f}%", help=f"최근 30일간 {selected_metric} 평균입니다.")

    with c2:
        st.metric(f"목표 상승폭 (MDE)", f"+{mde_percent}%", help="앞 단계(전략)에서 설정한 최소 목표치입니다.")

    with c3:
        st.metric(
            f"총 필요 표본 수", f"{total_needed:,}명",
            delta=f"Control {int(total_needed * control_pct):,} | Test {int(total_needed * test_pct):,}",
            delta_color="off",
            help=f"각 그룹당 최소 {n_per_group:,}명의 샘플이 필요합니다."
        )

    # Formula Explanation
    _render_sample_size_formula(auto_baseline, mde, n_per_group, split, total_needed)

    # Estimation Info
    visit_est = 500
    days_est = int(total_needed / visit_est)
    st.info(f"ℹ️ 일평균 방문자 {visit_est}명 기준, 유의미한 결과를 얻기까지 약 **{days_est}일**이 소요됩니다.")

    st.write("")
    if st.button("다음: 데이터 수집 시작 (Simulation) ➡️", type="primary", use_container_width=True):
        st.session_state['n'] = n_per_group
        st.session_state['total_needed'] = total_needed
        st.session_state['split'] = split
        st.session_state['step'] = 3
        st.rerun()


def _get_baseline_metric(selected_metric):
    """Get baseline metric from historical data."""
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
        df_baseline = al.run_query(sql_baseline, con=None)
        auto_baseline = df_baseline.iloc[0, 0] if not df_baseline.empty and df_baseline.iloc[0, 0] else 0.10
    except Exception as e:
        st.warning(f"Baseline 조회 실패 (기본값 10% 사용): {e}")
        auto_baseline = 0.10

    return auto_baseline


def _render_sample_size_formula(auto_baseline, mde, n_per_group, split, total_needed):
    """Render sample size formula explanation."""
    with st.expander("📐 표본 수 계산 공식 (Sample Size Formula)"):
        st.markdown(f"""
        #### Two-Sample Z-Test for Proportions

        ```
        n = (2 × p̄ × (1-p̄) × (Zα + Zβ)²) / (p₁ - p₂)²
        ```

        **파라미터:**
        - **p₁ (baseline)**: {auto_baseline:.2%} ← 현재 전환율
        - **p₂ (target)**: {auto_baseline * (1 + mde):.2%} ← 목표 전환율 (baseline × (1 + MDE))
        - **p̄ (pooled)**: {(auto_baseline + auto_baseline * (1 + mde)) / 2:.2%} ← (p₁ + p₂) / 2
        - **Zα**: 1.96 ← 95% 신뢰수준 (α=0.05)
        - **Zβ**: 0.84 ← 80% 검정력 (β=0.20)

        **계산 결과:**
        - **그룹당 필요 샘플**: {n_per_group:,}명
        - **트래픽 분배**: Control {split}% / Test {100-split}%
        - **총 방문자 필요**: {total_needed:,}명

        > ℹ️ 불균등 분배 시, 소수 그룹이 충분한 샘플을 얻기 위해 더 많은 총 방문자가 필요합니다.
        """)


def render_step3_collection():
    """Step 3: Data Collection - Run simulation."""
    st.markdown("<h2>Step 3. 데이터 모으기 (Collection)</h2>", unsafe_allow_html=True)
    ui.edu_guide("실시간 시뮬레이션", "Agent System이 가상의 유저가 되어 앱을 방문합니다.")

    # Agent Persona Settings
    _render_persona_settings()

    col_sim, col_chart = st.columns([1, 1], gap="large")

    with col_chart:
        _render_live_chart()

    with col_sim:
        _render_simulation_controls()

    st.write("")
    if st.button("다음: 결과 분석 (Analysis) ➡️", type="primary", use_container_width=True):
        st.session_state['step'] = 4
        st.rerun()


def _render_persona_settings():
    """Render agent persona settings."""
    with st.expander("🤖 에이전트 성향 설정 (Agent Persona)", expanded=True):
        if 'p_dist' not in st.session_state:
            st.session_state['p_dist'] = {'Window': 40, 'Mission': 10, 'Rational': 20, 'Impulsive': 20, 'Cautious': 10}

        col_sql, col_analyze = st.columns([1, 3])

        with col_sql:
            if st.button("📊 SQL 쿼리 확인", help="세그먼트 분석 SQL 쿼리 보기", key="show_sql_btn", use_container_width=True):
                st.session_state['show_segment_sql'] = not st.session_state.get('show_segment_sql', False)

        with col_analyze:
            analyze_clicked = st.button(
                "🔄 기존 고객 분석 및 적용",
                help="DB의 유저/주문 패턴을 분석하여 실제 고객 분포를 반영합니다.",
                key="analyze_btn", use_container_width=True
            )

        st.caption("기존 고객 데이터를 분석하여 에이전트 성향을 자동으로 설정합니다.")

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

        st.session_state['p_dist'] = {
            'Window': p_window, 'Mission': p_mission, 'Rational': p_rational,
            'Impulsive': p_impulsive, 'Cautious': p_cautious
        }

        total_p = sum(st.session_state['p_dist'].values())
        st.progress(min(total_p/100, 1.0))

        if total_p != 100:
            st.warning(f"⚠️ 합계가 100%가 되어야 합니다. (현재: {total_p}%)")
        else:
            st.caption(f"✅ 설정 완료: Window {p_window}% | Mission {p_mission}% | Rational {p_rational}% | Impulsive {p_impulsive}% | Cautious {p_cautious}%")


def _render_live_chart():
    """Render live chart placeholder."""
    with st.container(border=True):
        st.markdown("#### 📊 실시간 그룹 분포")
        chart_placeholder = st.empty()

        if 'last_live_chart' in st.session_state and not st.session_state.get('sim_process'):
            df_last = st.session_state['last_live_chart']
            last_loop = st.session_state.get('last_loop_count', 0)
            with chart_placeholder.container():
                st.bar_chart(df_last, x="variant", y="visitors", color="variant", horizontal=True)
                st.caption(f"✅ 시뮬레이션 완료 (Loop: {last_loop})")
        else:
            with chart_placeholder.container():
                st.info("데이터 대기 중...")


def _render_simulation_controls():
    """Render simulation control panel."""
    with st.container(border=True):
        st.markdown("#### 🚀 시뮬레이션 제어")

        total_target = st.session_state.get('total_needed', st.session_state.get('n', 100) * 2)
        actual_agents = 50
        weight_multiplier = total_target / actual_agents

        st.info(f"📊 **투입 규모**: {actual_agents}명 에이전트 → 효과: {total_target:,}명 (×{weight_multiplier:.1f} 증폭)")
        turbo = st.checkbox("Turbo Mode (무시 지연 제거)", value=True)

        col_start, col_stop = st.columns(2)

        with col_start:
            if st.button("▶️ Agent Swarm 투입 (Start)", type="primary", use_container_width=True, key="start_sim_btn"):
                _run_simulation(actual_agents, weight_multiplier, turbo)

        with col_stop:
            if st.button("⏹️ 중지 (Stop)", type="secondary", use_container_width=True, key="stop_sim_btn"):
                if 'sim_process' in st.session_state:
                    st.session_state['sim_stop_requested'] = True
                    st.warning("중지 요청됨... 프로세스 종료 중")
                else:
                    st.info("실행 중인 시뮬레이션이 없습니다")


def _run_simulation(actual_agents, weight_multiplier, turbo):
    """Run the agent swarm simulation."""
    current_run_id = f"run_{int(time.time() * 1000)}"
    st.session_state['current_run_id'] = current_run_id
    st.session_state['current_weight'] = weight_multiplier

    traits = ["Window", "Mission", "Rational", "Impulsive", "Cautious"]
    weights_str = ",".join([str(st.session_state['p_dist'].get(t, 20)) for t in traits])

    cmd = [
        sys.executable, "agent_swarm/runner.py",
        "--count", str(actual_agents),
        "--weights", weights_str,
        "--run-id", current_run_id,
        "--weight", str(weight_multiplier)
    ]
    if turbo:
        cmd.append("--turbo")

    env = os.environ.copy()
    env['PYTHONPATH'] = os.path.abspath('.')

    progress_bar = st.progress(0, text="준비 중...")
    status_container = st.status("🚀 시뮬레이션 엔진 가동 중...", expanded=True)
    log_area = st.empty()

    try:
        proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        st.session_state['sim_process'] = proc

        time.sleep(0.5)

        start_time = time.time()
        last_count = 0
        loop_count = 0

        status_container.update(label="⚙️ 에이전트 투입 중...", state="running")

        while proc.poll() is None:
            loop_count += 1

            if st.session_state.get('sim_stop_requested', False):
                proc.terminate()
                status_container.update(label="⏹️ 사용자가 중지했습니다", state="error")
                st.session_state['sim_stop_requested'] = False
                st.session_state.pop('sim_process', None)
                break

            # Update Progress
            run_filter = st.session_state.get('current_run_id', 'run_0')
            df_count = al.run_query(f"SELECT COUNT(*) as cnt FROM assignments WHERE run_id = '{run_filter}'", con=None)
            curr_count = df_count.iloc[0]['cnt'] if not df_count.empty else 0

            progress = min(curr_count / actual_agents, 1.0) if actual_agents > 0 else 0
            effective_count = int(curr_count * weight_multiplier)
            effective_total_display = int(actual_agents * weight_multiplier)
            progress_bar.progress(progress, text=f"데이터 수집 중... ({curr_count}/{actual_agents}) → 효과: ({effective_count:,}/{effective_total_display:,}) [Loop: {loop_count}]")

            # Show Live Logs
            df_logs = al.run_query(f"""
                SELECT timestamp, user_id, event_name
                FROM events
                WHERE run_id = '{run_filter}'
                ORDER BY timestamp DESC LIMIT 5
            """, con=None)

            if not df_logs.empty:
                df_logs['timestamp'] = pd.to_datetime(df_logs['timestamp'])
                log_text = "  \n".join([f"🕒 {row['timestamp'].strftime('%H:%M:%S')} | 👤 {row['user_id']} | 📢 {row['event_name']}" for _, row in df_logs.iterrows()])
                log_area.markdown(f"**최근 활동:**  \n{log_text}")
            else:
                log_area.caption("에이전트 활동 대기 중...")

            # Handle timeout
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
            time.sleep(1)
            st.rerun()

    except Exception as e:
        st.error(f"시뮬레이션 중 오류 발생: {e}")
        import traceback
        st.code(traceback.format_exc())
        st.session_state.pop('sim_process', None)


def render_step4_analysis():
    """Step 4: Analysis - Calculate statistics and make decisions."""
    st.markdown("<h2>Step 4. 결론 내리기 (Analysis)</h2>", unsafe_allow_html=True)
    ui.edu_guide("P-value 검정", "우연히 이런 결과가 나올 확률을 계산합니다. 0.05(5%) 미만이어야 '통계적으로 유의미'하다고 봅니다.")

    primary_metric = st.session_state.get('metric', 'CTR (클릭률)')
    current_run_id = st.session_state.get('current_run_id', None)

    if not current_run_id:
        _render_no_run_id_warning()
        return

    st.caption(f"🔍 현재 분석 중인 실험: `{current_run_id}`")

    # Get statistics
    df = _get_experiment_stats(primary_metric, current_run_id)

    if len(df) < 2:
        st.warning("📊 분석을 위한 충분한 데이터가 수집되지 않았습니다. (최소 2개의 그룹 필요)")
        st.info(f"현재 run_id '{current_run_id}'에 대한 데이터: {len(df)}개 그룹")
        st.stop()

    # Calculate Statistics
    res = al.calculate_statistics(
        df.iloc[0]['users'], df.iloc[0]['conversions'],
        df.iloc[1]['users'], df.iloc[1]['conversions']
    )

    c_stats, c_plot = st.columns([1, 1.5], gap="medium")

    with c_stats:
        _render_stats_summary(res, current_run_id)

    with c_plot:
        _render_analysis_chart(df, primary_metric, res)
        _render_guardrail_metrics(current_run_id)

    _render_metrics_comparison(primary_metric, current_run_id)
    _render_raw_data(current_run_id)
    _render_retrospective_form(current_run_id, res)


def _render_no_run_id_warning():
    """Render warning when no run_id is found."""
    st.error("⚠️ 실험 데이터를 찾을 수 없습니다!")
    st.info("Step 3 (데이터 모으기)에서 시뮬레이션을 먼저 실행해주세요.")

    available_runs = al.run_query("SELECT DISTINCT run_id FROM assignments WHERE run_id IS NOT NULL ORDER BY run_id DESC LIMIT 5")
    if not available_runs.empty:
        st.write("사용 가능한 실험 run_id:")
        st.dataframe(available_runs)

        selected_run = st.selectbox("수동으로 run_id 선택 (디버깅용):", available_runs['run_id'].tolist())
        if st.button("이 run_id 사용"):
            st.session_state['current_run_id'] = selected_run
            st.rerun()
    st.stop()


def _get_experiment_stats(primary_metric, current_run_id):
    """Get experiment statistics from database."""
    if 'CTR' in primary_metric:
        event_condition = "(e.event_name = 'banner_A' OR e.event_name = 'banner_B')"
    else:
        event_condition = "e.event_name = 'purchase'"

    sql = f"""
    WITH user_events AS (
        SELECT
            a.variant,
            e.user_id,
            a.weight,
            MAX(CASE WHEN {event_condition} THEN 1 ELSE 0 END) as converted
        FROM assignments a
        LEFT JOIN events e ON a.user_id = e.user_id AND a.run_id = e.run_id
        WHERE a.run_id = '{current_run_id}'
        GROUP BY a.variant, e.user_id, a.weight
    )
    SELECT
        variant,
        CAST(ROUND(SUM(weight), 0) AS INTEGER) as users,
        CAST(ROUND(SUM(CASE WHEN converted = 1 THEN weight ELSE 0 END), 0) AS INTEGER) as conversions
    FROM user_events
    GROUP BY variant
    ORDER BY variant
    """

    return al.run_query(sql)


def _render_stats_summary(res, current_run_id):
    """Render statistics summary card."""
    st.markdown("#### 🏁 최종 결과 요약")

    with st.container(border=True):
        st.metric("Lift (개선율)", al.format_delta(res['lift']),
                 delta=f"{al.format_delta(res['lift'])} {'🔥' if res['lift'] > 0 else '❄️'}")

        p_val_str = f"{res['p_value']:.4f}"
        st.write(f"📊 **P-value:** {p_val_str}")

        if res['p_value'] < 0.05:
            st.success("🎊 **통계적으로 유의미함** (p < 0.05)")
            decision = "Significant Winner" if res['lift'] > 0 else "Significant Loser"
        else:
            st.warning("⚖️ **유의미한 차이 없음** (p >= 0.05)")
            decision = "Inconclusive"

        st.session_state['last_res'] = res
        st.session_state['last_decision'] = decision

        st.divider()
        st.markdown("#### 🎯 의사결정 (Decision)")

        col_adopt, col_redesign = st.columns(2)

        with col_adopt:
            if st.button("✅ 채택 (Adopt)", type="primary", use_container_width=True):
                st.session_state['pending_adoption'] = {
                    'variant': st.session_state.get('test_variant', {}),
                    'experiment_id': current_run_id,
                    'lift': res['lift'],
                    'p_value': res['p_value'],
                    'timestamp': pd.Timestamp.now().isoformat()
                }
                st.toast("✅ 채택 표시됨! 회고록 저장 시 Target App에 적용됩니다.")
                st.session_state['show_adoption_success'] = True

        with col_redesign:
            if st.button("🔄 재실험 설계 (Re-design)", type="secondary", use_container_width=True):
                st.session_state['previous_experiment_learning'] = {
                    'run_id': current_run_id,
                    'p_value': res['p_value'],
                    'lift': res['lift'],
                    'decision': decision,
                    'hypothesis': st.session_state.get('hypothesis', ''),
                    'target': st.session_state.get('target', '')
                }
                st.session_state.pop('current_run_id', None)
                st.session_state.pop('sim_complete', None)
                st.session_state['step'] = 1
                st.toast("🔄 새로운 실험을 설계해보세요!")
                st.rerun()

        # Show guidance
        if st.session_state.get('show_adoption_success'):
            st.success("✨ 채택 표시 완료!")
            st.info("⬇️ **중요**: 아래로 스크롤하여 '실험 회고록'을 작성하고 저장 버튼을 눌러야 Target App에 실제로 반영됩니다.")
        else:
            if res['p_value'] < 0.05 and res['lift'] > 0:
                st.info("💡 **권장**: 통계적으로 유의미한 개선입니다. 채택을 고려하세요.")
            elif res['p_value'] < 0.05 and res['lift'] < 0:
                st.warning("⚠️ **주의**: 통계적으로 유의미한 악화입니다. 재실험을 권장합니다.")
            else:
                st.info("💡 **참고**: 유의미한 차이가 없습니다. 실무적 판단 또는 재실험을 고려하세요.")


def _render_analysis_chart(df, primary_metric, res):
    """Render the analysis comparison chart."""
    rows = []
    for i, row in df.iterrows():
        rate = row['conversions'] / row['users'] if row['users'] > 0 else 0
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
        if v_data.empty:
            continue

        group_label = f"{v} (Control)" if v == 'A' else f"{v} (Test)"

        fig.add_trace(go.Bar(
            x=[group_label],
            y=v_data['rate'],
            name=group_label,
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

    st.plotly_chart(fig, use_container_width=True)


def _render_guardrail_metrics(current_run_id):
    """Render guardrail metrics section."""
    st.markdown("#### 📊 가드레일 지표 (Guardrail Metrics)")
    guardrails = st.session_state.get('guardrails', [])
    guard_results = []

    if guardrails:
        guard_sql = f"""
        WITH user_metrics AS (
            SELECT
                a.variant,
                e.user_id,
                a.weight,
                MAX(CASE WHEN e.event_name = 'purchase' THEN 1 ELSE 0 END) as purchased,
                SUM(CASE WHEN e.event_name = 'purchase' THEN e.value ELSE 0 END) as revenue
            FROM assignments a
            LEFT JOIN events e ON a.user_id = e.user_id AND a.run_id = e.run_id
            WHERE a.run_id = '{current_run_id}'
            GROUP BY a.variant, e.user_id, a.weight
        )
        SELECT
            variant,
            CAST(ROUND(SUM(weight), 0) AS INTEGER) as users,
            CAST(ROUND(SUM(CASE WHEN purchased = 1 THEN weight ELSE 0 END), 0) AS INTEGER) as conversions,
            CAST(ROUND(SUM(revenue * weight), 0) AS BIGINT) as revenue
        FROM user_metrics
        GROUP BY variant
        ORDER BY variant
        """
        df_guard = al.run_query(guard_sql)

        if len(df_guard) >= 2:
            for guardrail in guardrails:
                if "CVR" in guardrail:
                    control_rate = df_guard.iloc[0]['conversions'] / df_guard.iloc[0]['users'] if df_guard.iloc[0]['users'] > 0 else 0
                    test_rate = df_guard.iloc[1]['conversions'] / df_guard.iloc[1]['users'] if df_guard.iloc[1]['users'] > 0 else 0
                    guard_lift = (test_rate - control_rate) / control_rate if control_rate > 0 else 0
                    guard_results.append({"metric": "CVR (전환율)", "control": control_rate, "test": test_rate, "lift": guard_lift})
                elif "AOV" in guardrail:
                    control_aov = df_guard.iloc[0]['revenue'] / df_guard.iloc[0]['conversions'] if df_guard.iloc[0]['conversions'] > 0 else 0
                    test_aov = df_guard.iloc[1]['revenue'] / df_guard.iloc[1]['conversions'] if df_guard.iloc[1]['conversions'] > 0 else 0
                    guard_lift = (test_aov - control_aov) / control_aov if control_aov > 0 else 0
                    guard_results.append({"metric": "AOV (평균주문액)", "control": control_aov, "test": test_aov, "lift": guard_lift})

        st.session_state['last_guard_results'] = guard_results

        guard_threshold = st.session_state.get('session_guard_threshold', -5.0) / 100

        if guard_results:
            for gr in guard_results:
                col_metric, col_value = st.columns([3, 1])
                with col_metric:
                    st.caption(f"**{gr['metric']}**")
                with col_value:
                    if gr['lift'] < guard_threshold:
                        st.caption(f"🔻 {gr['lift']*100:+.1f}%")
                    else:
                        st.caption(f"✅ {gr['lift']*100:+.1f}%")
        else:
            st.caption("보조 지표 분석 결과가 없습니다.")
    else:
        st.session_state['last_guard_results'] = []
        st.info("설정된 보조 지표가 없습니다.")


def _render_metrics_comparison(primary_metric, current_run_id):
    """Render comprehensive metrics comparison table."""
    st.divider()
    st.markdown("#### 📈 주요 메트릭 비교표 (Key Metrics Comparison)")

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

    if not df_metrics.empty and len(df_metrics) >= 2:
        deltas = {}
        for col in df_metrics.columns:
            if col != '그룹':
                control_val = df_metrics.iloc[0][col]
                test_val = df_metrics.iloc[1][col]

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

        df_comparison = pd.concat([df_metrics, pd.DataFrame([deltas])], ignore_index=True)
        st.dataframe(df_comparison, use_container_width=True, hide_index=True)
        st.caption("💡 CTR = 클릭률, CVR = 전환율, AOV = 평균 주문액, ARPU = 유저당 평균 매출")
    else:
        st.warning("메트릭을 계산하기에 충분한 데이터가 없습니다.")


def _render_raw_data(current_run_id):
    """Render raw data table with download option."""
    st.divider()
    col_raw_title, col_download = st.columns([3, 1])

    with col_raw_title:
        st.markdown("#### 📊 원 데이터 (Raw Data)")

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
            DATEDIFF('second', LAG(e.timestamp) OVER (PARTITION BY e.user_id ORDER BY e.timestamp), e.timestamp) as time_since_last_event
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

    with col_download:
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

    if not df_raw_full.empty:
        st.caption(f"총 {len(df_raw_full):,}개 이벤트 (상위 10개 샘플 표시)")
        st.dataframe(df_raw_full.head(10), use_container_width=True, hide_index=True)
    else:
        st.info("원 데이터가 없습니다.")


def _render_retrospective_form(current_run_id, res):
    """Render the retrospective save form."""
    st.divider()
    st.markdown("#### 📝 실험 회고록 작성")
    note = st.text_area("배운 점 (Learning Note)", help="이번 실험에서 얻은 인사이트를 기록하세요.")

    if st.button("💾 실험 회고록에 저장", type="primary"):
        saved_res = st.session_state.get('last_res')
        saved_decision = st.session_state.get('last_decision')
        saved_guard_results = st.session_state.get('last_guard_results', [])

        if not saved_res:
            st.error("⚠️ 분석 결과를 찾을 수 없습니다.")
            st.info("💡 Step 4 (결론 내리기)로 이동하여 분석을 먼저 실행해주세요.")
            st.stop()

        guardrail_results_json = json.dumps(saved_guard_results) if saved_guard_results else None
        db_path = al.DB_PATH

        with duckdb.connect(db_path) as txn_con:
            txn_con.execute("""
                INSERT INTO experiments (
                    target, hypothesis, primary_metric, guardrails,
                    p_value, decision, learning_note, run_id,
                    control_rate, test_rate, lift, guardrail_results,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, [
                st.session_state.get('target', '-'),
                st.session_state.get('hypothesis', '-'),
                st.session_state.get('metric', '-'),
                ','.join(st.session_state.get('guardrails', [])),
                saved_res['p_value'], saved_decision, note, current_run_id,
                saved_res['control_rate'], saved_res['test_rate'], saved_res['lift'],
                guardrail_results_json
            ])

            if st.session_state.get('pending_adoption'):
                adoption_data = st.session_state['pending_adoption']
                txn_con.execute("""
                    CREATE TABLE IF NOT EXISTS adoptions (
                        experiment_id VARCHAR,
                        variant_config VARCHAR,
                        adopted_at TIMESTAMP,
                        lift FLOAT,
                        p_value FLOAT
                    )
                """)
                variant_json = json.dumps(adoption_data['variant'])
                txn_con.execute("""
                    INSERT INTO adoptions VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?)
                """, [current_run_id, variant_json, adoption_data['lift'], adoption_data['p_value']])

                st.session_state.pop('pending_adoption', None)
                st.toast("🎉 실험이 채택되어 Target App에 적용되었습니다!")

            txn_con.execute(f"DELETE FROM assignments WHERE run_id = '{current_run_id}'")
            txn_con.execute(f"DELETE FROM events WHERE run_id = '{current_run_id}'")

        st.toast("💾 회고록 저장 완료!")
        st.session_state.pop('current_run_id', None)
        st.session_state.pop('last_res', None)
        st.session_state.pop('last_decision', None)
        st.session_state.pop('last_guard_results', None)
        st.session_state['page'] = 'portfolio'
        st.session_state['step'] = 1
        st.rerun()
