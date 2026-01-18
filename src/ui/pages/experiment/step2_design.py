"""
Step 2: Experiment Design - Traffic split and sample size calculation.
"""
import streamlit as st

from src.core import stats as al
from src.ui import components as ui


def render():
    """Render Step 2: Experiment Design."""
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
        st.metric(
            f"현재 수준 (Baseline)",
            f"{auto_baseline*100:.2f}%",
            help=f"최근 30일간 {selected_metric} 평균입니다."
        )

    with c2:
        st.metric(
            f"목표 상승폭 (MDE)",
            f"+{mde_percent}%",
            help="앞 단계(전략)에서 설정한 최소 목표치입니다."
        )

    with c3:
        st.metric(
            f"총 필요 표본 수",
            f"{total_needed:,}명",
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
