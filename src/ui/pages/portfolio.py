"""
Portfolio Page - Experiment Retrospective
"""
import streamlit as st

from src.core import stats as al


def render():
    """Render the experiment portfolio/retrospective page."""
    st.title("📚 실험 회고록 (Experiment Retrospective)")

    _render_adopted_experiments()

    st.divider()

    _render_all_experiments()


def _render_adopted_experiments():
    """Render the adopted experiments section."""
    st.markdown("### ✅ 채택된 실험 (Adopted Experiments)")
    st.caption("플랫폼에 실제로 적용된 성공적인 실험들")

    try:
        df_adoptions = al.run_query("""
            SELECT
                a.experiment_id,
                a.adopted_at,
                a.lift,
                a.p_value,
                e.hypothesis,
                e.target,
                e.primary_metric
            FROM adoptions a
            LEFT JOIN experiments e ON a.experiment_id = e.run_id
            ORDER BY a.adopted_at DESC
        """)

        if not df_adoptions.empty:
            for _, row in df_adoptions.iterrows():
                _render_adoption_card(row)
        else:
            st.info("아직 채택된 실험이 없습니다. 성공적인 실험을 채택하면 여기에 표시됩니다!")

    except Exception:
        st.info("아직 채택된 실험이 없습니다.")


def _render_adoption_card(row):
    """Render a single adoption card."""
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"**✨ {row.get('hypothesis', '실험 가설')}**")
            st.caption(f"📍 Target: {row.get('target', 'N/A')} | 📊 Metric: {row.get('primary_metric', 'N/A')}")

        with col2:
            st.metric("Lift", f"+{row['lift']*100:.1f}%", delta=f"p={row['p_value']:.4f}")

        st.caption(f"🕐 채택일시: {row['adopted_at']}")


def _render_all_experiments():
    """Render all experiment history."""
    st.markdown("### 📋 전체 실험 기록 (All Experiments)")

    df_history = al.run_query("SELECT * FROM experiments ORDER BY created_at DESC")

    if df_history.empty:
        st.info("실험 기록이 없습니다.")
        return

    for _, row in df_history.iterrows():
        _render_experiment_card(row)


def _render_experiment_card(row):
    """Render a single experiment history card."""
    with st.container(border=True):
        st.markdown(f"**{row['hypothesis']}**")
        st.caption(f"{row['created_at']} | Result: {row['decision']}")
