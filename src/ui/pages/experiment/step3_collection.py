"""
Step 3: Data Collection - Run agent swarm simulation.
"""
import streamlit as st
import pandas as pd
import subprocess
import sys
import os
import time
import requests

from src.core import stats as al
from src.core import cache
from src.ui import components as ui


# Target App URL (for experiment synchronization)
def _get_target_url():
    """Get TARGET_APP_URL from Streamlit secrets or environment variable."""
    try:
        if hasattr(st, 'secrets') and 'TARGET_APP_URL' in st.secrets:
            return str(st.secrets['TARGET_APP_URL'])
    except Exception:
        pass
    return os.getenv('TARGET_APP_URL', 'http://localhost:8000')


def _activate_experiment(run_id: str, hypothesis: str = None):
    """Notify Target App that experiment is starting."""
    try:
        target_url = _get_target_url()
        response = requests.post(
            f"{target_url}/admin/activate_experiment",
            json={"run_id": run_id, "hypothesis": hypothesis},
            timeout=5
        )
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                return True
    except Exception as e:
        st.warning(f"Target App 연결 실패: {e}")
    return False


def _deactivate_experiment():
    """Notify Target App that experiment has ended."""
    try:
        target_url = _get_target_url()
        response = requests.post(
            f"{target_url}/admin/deactivate_experiment",
            timeout=5
        )
        if response.status_code == 200:
            return True
    except Exception:
        pass
    return False


def render():
    """Render Step 3: Data Collection."""
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
            st.session_state['p_dist'] = {
                'Window': 40, 'Mission': 10, 'Rational': 20,
                'Impulsive': 20, 'Cautious': 10
            }

        col_sql, col_analyze = st.columns([1, 3])

        with col_sql:
            if st.button("📊 SQL 쿼리 확인", help="세그먼트 분석 SQL 쿼리 보기",
                        key="show_sql_btn", use_container_width=True):
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
                # Use cached query (5-minute TTL)
                dist = cache.get_user_segments()
                st.session_state['p_dist'] = dist
                st.toast("분석 완료! 고객 분포가 적용되었습니다.", icon="✅")
                st.rerun()

        p_dist = st.session_state['p_dist']

        c_p1, c_p2, c_p3, c_p4, c_p5 = st.columns(5)

        p_window = c_p1.number_input(
            "🛍️ 아이쇼핑 (Window)", 0, 100, p_dist.get('Window', 0), step=5,
            help="주문 이력 없음 (탐색만 하는 유저)", key="p_window"
        )
        p_mission = c_p2.number_input(
            "🎯 목적형 (Mission)", 0, 100, p_dist.get('Mission', 0), step=5,
            help="3회 이상 구매 (충성 고객)", key="p_mission"
        )
        p_rational = c_p3.number_input(
            "💡 계산형 (Rational)", 0, 100, p_dist.get('Rational', 0), step=5,
            help="평균 이상 지출 (고액 구매자)", key="p_rational"
        )
        p_impulsive = c_p4.number_input(
            "⚡ 충동형 (Impulsive)", 0, 100, p_dist.get('Impulsive', 0), step=5,
            help="가입 30일 이내 신규 유저", key="p_impulsive"
        )
        p_cautious = c_p5.number_input(
            "🧐 신중형 (Cautious)", 0, 100, p_dist.get('Cautious', 0), step=5,
            help="장기 가입 + 간헐적 구매", key="p_cautious"
        )

        st.session_state['p_dist'] = {
            'Window': p_window, 'Mission': p_mission, 'Rational': p_rational,
            'Impulsive': p_impulsive, 'Cautious': p_cautious
        }

        total_p = sum(st.session_state['p_dist'].values())
        st.progress(min(total_p/100, 1.0))

        if total_p != 100:
            st.warning(f"⚠️ 합계가 100%가 되어야 합니다. (현재: {total_p}%)")
        else:
            st.caption(
                f"✅ 설정 완료: Window {p_window}% | Mission {p_mission}% | "
                f"Rational {p_rational}% | Impulsive {p_impulsive}% | Cautious {p_cautious}%"
            )


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

        st.info(
            f"📊 **투입 규모**: {actual_agents}명 에이전트 → "
            f"효과: {total_target:,}명 (×{weight_multiplier:.1f} 증폭)"
        )
        turbo = st.checkbox("Turbo Mode (무시 지연 제거)", value=True)

        col_start, col_stop = st.columns(2)

        with col_start:
            if st.button("▶️ Agent Swarm 투입 (Start)", type="primary",
                        use_container_width=True, key="start_sim_btn"):
                _run_simulation(actual_agents, weight_multiplier, turbo)

        with col_stop:
            if st.button("⏹️ 중지 (Stop)", type="secondary",
                        use_container_width=True, key="stop_sim_btn"):
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

    # Get hypothesis from session state (set in Step 1)
    hypothesis = st.session_state.get('hypothesis', 'A/B Test')

    # Notify Target App that experiment is starting
    if _activate_experiment(current_run_id, hypothesis):
        st.toast("🔗 Target App에 실험 시작 알림 완료", icon="✅")
    else:
        st.warning("⚠️ Target App 연동 실패 - 독립 모드로 진행")

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
        proc = subprocess.Popen(
            cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
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
            df_count = al.run_query(
                f"SELECT COUNT(*) as cnt FROM assignments WHERE run_id = '{run_filter}'",
                con=None
            )
            curr_count = df_count.iloc[0]['cnt'] if not df_count.empty else 0

            progress = min(curr_count / actual_agents, 1.0) if actual_agents > 0 else 0
            effective_count = int(curr_count * weight_multiplier)
            effective_total_display = int(actual_agents * weight_multiplier)
            progress_bar.progress(
                progress,
                text=f"데이터 수집 중... ({curr_count}/{actual_agents}) → "
                     f"효과: ({effective_count:,}/{effective_total_display:,}) [Loop: {loop_count}]"
            )

            # Show Live Logs
            df_logs = al.run_query(f"""
                SELECT timestamp, user_id, event_name
                FROM events
                WHERE run_id = '{run_filter}'
                ORDER BY timestamp DESC LIMIT 5
            """, con=None)

            if not df_logs.empty:
                df_logs['timestamp'] = pd.to_datetime(df_logs['timestamp'])
                log_text = "  \n".join([
                    f"🕒 {row['timestamp'].strftime('%H:%M:%S')} | "
                    f"👤 {row['user_id']} | 📢 {row['event_name']}"
                    for _, row in df_logs.iterrows()
                ])
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
            # Notify Target App that experiment data collection is complete
            _deactivate_experiment()

            status_container.update(
                label=f"✅ 시뮬레이션 완료! (Exit Code: {exit_code})",
                state="complete", expanded=False
            )
            st.success(f"Loop 실행 횟수: {loop_count}회, 최종 데이터: {last_count}건")
            st.toast("시뮬레이션 완료! 데이터가 수집되었습니다.")
            time.sleep(1)
            st.rerun()

    except Exception as e:
        # Deactivate experiment on error too
        _deactivate_experiment()
        st.error(f"시뮬레이션 중 오류 발생: {e}")
        import traceback
        st.code(traceback.format_exc())
        st.session_state.pop('sim_process', None)
