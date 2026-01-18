"""
Step 4: Analysis - Calculate statistics and make decisions.

Enhanced with advanced statistical analysis:
- SRM (Sample Ratio Mismatch) detection
- Lift confidence intervals
- Segment analysis by persona
- Revenue impact estimation
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import json
import duckdb

from src.core import stats as al
from src.core import cache
from src.ui import components as ui

# Import advanced stats functions
from src.core.stats import (
    check_srm,
    calculate_lift_confidence_interval,
    bonferroni_correction
)


def render():
    """Render Step 4: Analysis and decision making."""
    st.markdown("<h2>Step 4. 결론 내리기 (Analysis)</h2>", unsafe_allow_html=True)
    ui.edu_guide(
        "P-value 검정",
        "우연히 이런 결과가 나올 확률을 계산합니다. 0.05(5%) 미만이어야 '통계적으로 유의미'하다고 봅니다."
    )

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

    # SRM Check - Sample Ratio Mismatch detection
    srm_result = check_srm(df.iloc[0]['users'], df.iloc[1]['users'])
    if srm_result['is_srm']:
        st.error(f"⚠️ **SRM 감지됨!** 샘플 비율 불일치 (p={srm_result['p_value']:.4f})")
        st.warning("무작위 배정에 문제가 있을 수 있습니다. 데이터 품질을 확인하세요.")
        with st.expander("SRM 상세 정보"):
            st.json(srm_result)

    c_stats, c_plot = st.columns([1, 1.5], gap="medium")

    with c_stats:
        _render_stats_summary(res, current_run_id)

    with c_plot:
        _render_analysis_chart(df, primary_metric, res)
        _render_guardrail_metrics(current_run_id)

    # Advanced Analysis Section
    _render_advanced_analysis(df, res, current_run_id)

    _render_metrics_comparison(primary_metric, current_run_id)
    _render_raw_data(current_run_id)
    _render_retrospective_form(current_run_id, res)


def _render_no_run_id_warning():
    """Render warning when no run_id is found."""
    st.error("⚠️ 실험 데이터를 찾을 수 없습니다!")
    st.info("Step 3 (데이터 모으기)에서 시뮬레이션을 먼저 실행해주세요.")

    # Use cached query (5-minute TTL)
    available_runs = cache.get_available_runs()
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
        st.metric(
            "Lift (개선율)", al.format_delta(res['lift']),
            delta=f"{al.format_delta(res['lift'])} {'🔥' if res['lift'] > 0 else '❄️'}"
        )

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
                    guard_results.append({
                        "metric": "CVR (전환율)",
                        "control": control_rate,
                        "test": test_rate,
                        "lift": guard_lift
                    })
                elif "AOV" in guardrail:
                    control_aov = df_guard.iloc[0]['revenue'] / df_guard.iloc[0]['conversions'] if df_guard.iloc[0]['conversions'] > 0 else 0
                    test_aov = df_guard.iloc[1]['revenue'] / df_guard.iloc[1]['conversions'] if df_guard.iloc[1]['conversions'] > 0 else 0
                    guard_lift = (test_aov - control_aov) / control_aov if control_aov > 0 else 0
                    guard_results.append({
                        "metric": "AOV (평균주문액)",
                        "control": control_aov,
                        "test": test_aov,
                        "lift": guard_lift
                    })

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


def _render_advanced_analysis(df, res, current_run_id):
    """Render advanced statistical analysis section."""
    st.divider()
    st.markdown("#### 🔬 심화 분석 (Advanced Analysis)")

    tab_lift, tab_segment, tab_revenue = st.tabs([
        "📊 Lift 신뢰구간",
        "👥 세그먼트 분석",
        "💰 매출 영향 추정"
    ])

    with tab_lift:
        _render_lift_ci(df, res)

    with tab_segment:
        _render_segment_analysis(current_run_id)

    with tab_revenue:
        _render_revenue_impact(df, res, current_run_id)


def _render_lift_ci(df, res):
    """Render Lift Confidence Interval visualization."""
    c_rate = df.iloc[0]['conversions'] / df.iloc[0]['users'] if df.iloc[0]['users'] > 0 else 0
    t_rate = df.iloc[1]['conversions'] / df.iloc[1]['users'] if df.iloc[1]['users'] > 0 else 0

    lift_ci = calculate_lift_confidence_interval(
        c_rate=c_rate, c_n=df.iloc[0]['users'],
        t_rate=t_rate, t_n=df.iloc[1]['users']
    )

    col_ci_chart, col_ci_stats = st.columns([2, 1])

    with col_ci_chart:
        # Create CI visualization
        fig = go.Figure()

        # Add confidence interval bar
        fig.add_trace(go.Scatter(
            x=[lift_ci['lower'] * 100, lift_ci['upper'] * 100],
            y=[1, 1],
            mode='lines',
            line=dict(color='#3b82f6', width=8),
            name='95% CI'
        ))

        # Add point estimate
        fig.add_trace(go.Scatter(
            x=[lift_ci['lift'] * 100],
            y=[1],
            mode='markers',
            marker=dict(color='#ef4444', size=15, symbol='diamond'),
            name='Lift'
        ))

        # Add zero line
        fig.add_vline(x=0, line_dash="dash", line_color="gray")

        # Determine color based on significance
        if lift_ci['is_significant']:
            if lift_ci['lower'] > 0:
                result_text = "✅ 유의미한 개선"
                result_color = "green"
            else:
                result_text = "⚠️ 유의미한 악화"
                result_color = "red"
        else:
            result_text = "⚖️ 유의미하지 않음"
            result_color = "gray"

        fig.update_layout(
            title=f"Lift 95% 신뢰구간: {result_text}",
            xaxis_title="Lift (%)",
            yaxis=dict(visible=False),
            height=150,
            margin=dict(l=20, r=20, t=40, b=20),
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

    with col_ci_stats:
        st.metric("Lift", f"{lift_ci['lift']*100:+.2f}%")
        st.caption(f"95% CI: [{lift_ci['lower']*100:+.2f}%, {lift_ci['upper']*100:+.2f}%]")
        if lift_ci['is_significant']:
            st.success("통계적으로 유의미")
        else:
            st.info("유의미하지 않음")


def _render_segment_analysis(current_run_id):
    """Render segment analysis by user persona/behavior."""
    # Query to get segment breakdown
    segment_sql = f"""
    WITH user_segments AS (
        SELECT
            a.variant,
            a.user_id,
            a.weight,
            CASE
                WHEN e.event_name LIKE 'banner%' AND NOT EXISTS (
                    SELECT 1 FROM events e2
                    WHERE e2.user_id = a.user_id AND e2.run_id = a.run_id AND e2.event_name = 'purchase'
                ) THEN 'Browser'
                WHEN e.event_name = 'purchase' AND e.value > 50000 THEN 'High-Value'
                WHEN e.event_name = 'purchase' THEN 'Converter'
                ELSE 'Visitor'
            END as segment,
            MAX(CASE WHEN e.event_name LIKE 'banner%' THEN 1 ELSE 0 END) as clicked,
            MAX(CASE WHEN e.event_name = 'purchase' THEN 1 ELSE 0 END) as purchased
        FROM assignments a
        LEFT JOIN events e ON a.user_id = e.user_id AND a.run_id = e.run_id
        WHERE a.run_id = '{current_run_id}'
        GROUP BY a.variant, a.user_id, a.weight, segment
    )
    SELECT
        segment as 세그먼트,
        variant as 그룹,
        CAST(ROUND(SUM(weight), 0) AS INTEGER) as 유저수,
        CAST(ROUND(SUM(CASE WHEN clicked = 1 THEN weight ELSE 0 END), 0) AS INTEGER) as 클릭,
        CAST(ROUND(SUM(CASE WHEN purchased = 1 THEN weight ELSE 0 END), 0) AS INTEGER) as 구매,
        ROUND(SUM(CASE WHEN clicked = 1 THEN weight ELSE 0 END) / NULLIF(SUM(weight), 0) * 100, 2) as CTR,
        ROUND(SUM(CASE WHEN purchased = 1 THEN weight ELSE 0 END) / NULLIF(SUM(weight), 0) * 100, 2) as CVR
    FROM user_segments
    GROUP BY segment, variant
    ORDER BY segment, variant
    """

    df_segment = al.run_query(segment_sql)

    if not df_segment.empty:
        # Pivot for comparison
        st.caption("세그먼트별 전환율 비교 (A vs B)")

        # Create comparison chart
        segments = df_segment['세그먼트'].unique()
        fig = go.Figure()

        for variant in ['A', 'B']:
            variant_data = df_segment[df_segment['그룹'] == variant]
            fig.add_trace(go.Bar(
                name=f'Variant {variant}',
                x=variant_data['세그먼트'],
                y=variant_data['CVR'],
                text=[f"{v:.1f}%" for v in variant_data['CVR']],
                textposition='auto'
            ))

        fig.update_layout(
            title="세그먼트별 CVR 비교",
            xaxis_title="세그먼트",
            yaxis_title="CVR (%)",
            barmode='group',
            height=300
        )

        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df_segment, use_container_width=True, hide_index=True)
    else:
        st.info("세그먼트 분석을 위한 데이터가 부족합니다.")


def _render_revenue_impact(df, res, current_run_id):
    """Render revenue impact estimation."""
    # Get revenue data
    revenue_sql = f"""
    SELECT
        a.variant,
        CAST(ROUND(SUM(a.weight), 0) AS INTEGER) as users,
        CAST(ROUND(SUM(CASE WHEN e.event_name = 'purchase' THEN e.value * a.weight ELSE 0 END), 0) AS BIGINT) as revenue,
        CAST(ROUND(SUM(CASE WHEN e.event_name = 'purchase' THEN a.weight ELSE 0 END), 0) AS INTEGER) as purchases
    FROM assignments a
    LEFT JOIN events e ON a.user_id = e.user_id AND a.run_id = e.run_id
    WHERE a.run_id = '{current_run_id}'
    GROUP BY a.variant
    ORDER BY a.variant
    """

    df_revenue = al.run_query(revenue_sql)

    if len(df_revenue) >= 2:
        control_revenue = df_revenue.iloc[0]['revenue'] or 0
        test_revenue = df_revenue.iloc[1]['revenue'] or 0
        control_users = df_revenue.iloc[0]['users'] or 1
        test_users = df_revenue.iloc[1]['users'] or 1

        control_arpu = control_revenue / control_users
        test_arpu = test_revenue / test_users
        arpu_lift = (test_arpu - control_arpu) / control_arpu if control_arpu > 0 else 0

        col_current, col_projected = st.columns(2)

        with col_current:
            st.markdown("##### 📊 현재 실험 결과")
            st.metric("Control ARPU", f"₩{control_arpu:,.0f}")
            st.metric("Test ARPU", f"₩{test_arpu:,.0f}", delta=f"{arpu_lift*100:+.1f}%")
            st.metric("실험 기간 매출 차이", f"₩{test_revenue - control_revenue:+,.0f}")

        with col_projected:
            st.markdown("##### 🚀 연간 영향 추정")

            # User inputs for projection
            monthly_users = st.number_input(
                "월간 예상 방문자 수",
                min_value=1000,
                max_value=10000000,
                value=100000,
                step=10000,
                help="실제 서비스의 월간 방문자 수를 입력하세요"
            )

            if res['p_value'] < 0.05 and arpu_lift != 0:
                annual_impact = monthly_users * 12 * (test_arpu - control_arpu)
                st.metric(
                    "연간 예상 매출 영향",
                    f"₩{annual_impact:+,.0f}",
                    delta="유의미한 변화" if res['p_value'] < 0.05 else "유의미하지 않음"
                )

                if annual_impact > 0:
                    st.success(f"✅ B안 채택 시 연간 약 **₩{annual_impact:,.0f}** 추가 매출 예상")
                else:
                    st.warning(f"⚠️ B안 채택 시 연간 약 **₩{abs(annual_impact):,.0f}** 매출 감소 예상")
            else:
                st.info("유의미한 차이가 없어 매출 영향을 추정할 수 없습니다.")

        # Sensitivity analysis
        with st.expander("📈 민감도 분석 (Sensitivity Analysis)"):
            st.caption("ARPU 변화에 따른 연간 매출 영향")

            scenarios = [
                ("보수적 (-20%)", arpu_lift * 0.8),
                ("기본", arpu_lift),
                ("낙관적 (+20%)", arpu_lift * 1.2)
            ]

            scenario_data = []
            for name, lift in scenarios:
                annual = monthly_users * 12 * control_arpu * lift
                scenario_data.append({
                    "시나리오": name,
                    "Lift": f"{lift*100:+.1f}%",
                    "연간 영향": f"₩{annual:+,.0f}"
                })

            st.dataframe(pd.DataFrame(scenario_data), use_container_width=True, hide_index=True)
    else:
        st.info("매출 영향 분석을 위한 데이터가 부족합니다.")


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
