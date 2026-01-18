"""
Step 1: Hypothesis - Define target and variables.
"""
import streamlit as st
import streamlit.components.v1 as components

from src.ui import components as ui
from src.ui.pages.experiment.constants import PAGE_MAP, METRICS_DB


def render():
    """Render Step 1: Hypothesis definition."""
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
    selected_page_idx = list(PAGE_MAP.keys()).index(
        st.session_state.get('builder_page', list(PAGE_MAP.keys())[0])
    )

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
        f"**Group B (Test)** <span style='background:#4B5563; padding:2px 6px; "
        f"border-radius:4px; font-size:0.7em'>{comp_type}</span>",
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
