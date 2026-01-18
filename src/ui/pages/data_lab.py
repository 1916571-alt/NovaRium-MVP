"""
Data Engineering Lab Page - Data Mart Builder
"""
import streamlit as st
import duckdb
import os
import time

from src.core import stats as al
from src.core import mart_builder as mb


def render():
    """Render the Data Engineering Lab page."""
    st.markdown("## 🛠️ 데이터 엔지니어링 랩 (Data Mart Builder)")
    st.caption("비즈니스 대시보드를 구축하기 위해 먼저 Raw Data를 분석 가능한 'Data Mart'로 가공해야 합니다.")

    col_setup, col_code = st.columns([1, 1.2], gap="large")

    with col_setup:
        _render_schema_design()

    with col_code:
        _render_query_generator()


def _render_schema_design():
    """Render the schema design section."""
    with st.container(border=True):
        st.markdown("### 1. 마트 설계 (Schema Design)")
        st.info("💡 분석가님, 대시보드에서 어떤 지표를 보고 싶으신가요?")

        # Default metrics
        metrics = st.multiselect(
            "포함할 핵심 지표 (Metrics)",
            options=[
                'total_users (DAU)', 'revenue (매출)', 'ctr (클릭률)',
                'cvr (전환율)', 'aov (객단가)', 'arpu (인당 매출)',
                'session_depth (인당 활동량)'
            ],
            default=[
                'total_users (DAU)', 'revenue (매출)', 'ctr (클릭률)',
                'cvr (전환율)', 'aov (객단가)'
            ]
        )

        # Parse selection to clean keys
        clean_metrics = _parse_metrics(metrics)

        # Store in session state for query generator
        st.session_state['clean_metrics'] = clean_metrics

        st.write("")
        if st.button("🚀 데이터 마트 구축 (Build & Run)", type="primary", use_container_width=True):
            _execute_etl(clean_metrics)

        st.divider()
        _render_data_lineage()


def _parse_metrics(metrics):
    """Parse metric selection to clean keys."""
    clean_metrics = []
    metric_map = {
        'revenue': 'revenue',
        'ctr': 'ctr',
        'cvr': 'cvr',
        'aov': 'aov',
        'arpu': 'arpu',
        'session_depth': 'session_depth'
    }

    for key, value in metric_map.items():
        if any(key in m for m in metrics):
            clean_metrics.append(value)

    return clean_metrics


def _execute_etl(clean_metrics):
    """Execute the ETL pipeline."""
    with st.spinner("ETL 파이프라인 가동 중... (Airflow Task #101)"):
        try:
            # 1. Generate SQL
            sql = mb.generate_mart_sql(clean_metrics)

            # 2. Execute directly with DuckDB write connection
            db_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                '..',
                'novarium_local.db'
            )
            with duckdb.connect(db_path) as write_con:
                write_con.execute(sql)

            # 3. Validation
            check_sql = "SELECT COUNT(*) as cnt FROM dm_daily_kpi"
            df_res = al.run_query(check_sql)
            row_count = df_res.iloc[0]['cnt'] if not df_res.empty else 0

            st.success(f"✅ 구축 완료! 총 {row_count:,}개의 일별 데이터가 적재되었습니다.")

            # Move to dashboard
            time.sleep(1)
            st.session_state['page'] = 'monitor'
            st.rerun()

        except Exception as e:
            st.error(f"ETL 실패: {e}")


def _render_data_lineage():
    """Render the data lineage explanation."""
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


def _render_query_generator():
    """Render the SQL query generator section."""
    st.markdown("### 2. SQL 쿼리 생성기 (Query Generator)")
    st.caption("선택하신 설계에 따라 자동으로 생성된 ETL 쿼리입니다. 현업에서는 이 코드가 Airflow에서 매일 새벽에 실행됩니다.")

    # Get clean metrics from session state
    clean_metrics = st.session_state.get('clean_metrics', [])

    # Real-time SQL Generation
    generated_sql = mb.generate_mart_sql(clean_metrics)
    st.code(generated_sql, language="sql")

    st.markdown("""
    > [!NOTE]
    > **왜 SQL을 직접 짜지 않고 생성하나요?**
    > 데이터 엔지니어링에서는 휴먼 에러를 줄이기 위해, 메타데이터(설계)를 기반으로 쿼리를 자동 생성(Templating)하는 방식을 자주 사용합니다.
    """)
