"""
STITCH Design System Factory
============================
NovaRium의 Cosmic Glass 디자인 시스템을 위한 컴포넌트 팩토리

구조:
- StitchConfig: 디자인 토큰 및 설정
- StitchBridge: Python-JS 양방향 통신
- StitchComponents: 재사용 가능한 UI 컴포넌트
- StitchWizard: 실험 마법사 컴포넌트 (Hypothesis, Design, Analysis)

사용법:
    from src.ui.stitch_factory import StitchFactory

    factory = StitchFactory()
    factory.render_sidebar()
    factory.render_hypothesis_wizard(initial_data={...})
"""

import streamlit as st
import streamlit.components.v1 as components
import json
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


# =============================================================================
# STITCH CONFIG - 디자인 토큰 및 설정
# =============================================================================

@dataclass
class StitchConfig:
    """STITCH 디자인 시스템 설정"""

    # Primary Colors
    primary: str = "#5a89f6"
    primary_light: str = "#7aa3ff"
    primary_dark: str = "#4070e0"

    # Background Colors
    bg_dark: str = "#0B0E14"
    bg_surface: str = "#181C25"
    bg_glass: str = "rgba(20, 25, 35, 0.6)"

    # Text Colors
    text_primary: str = "#ffffff"
    text_secondary: str = "#94a3b8"  # slate-400
    text_muted: str = "#64748b"  # slate-500

    # Accent Colors
    success: str = "#22c55e"
    warning: str = "#f59e0b"
    error: str = "#ef4444"
    info: str = "#3b82f6"

    # Border/Glass
    glass_border: str = "rgba(255, 255, 255, 0.08)"
    glass_border_hover: str = "rgba(255, 255, 255, 0.15)"

    # Fonts
    font_display: str = "Plus Jakarta Sans"
    font_body: str = "Noto Sans KR"

    # Shadows
    shadow_glow: str = "0 0 20px rgba(90, 137, 246, 0.4)"
    shadow_glass: str = "0 8px 32px 0 rgba(0, 0, 0, 0.3)"


# =============================================================================
# SHARED CSS & JS - 공통 스타일 및 스크립트
# =============================================================================

STITCH_HEAD_COMMON = """
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<link href="https://fonts.googleapis.com" rel="preconnect"/>
<link crossorigin="" href="https://fonts.gstatic.com" rel="preconnect"/>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&amp;family=Noto+Sans+KR:wght@400;500;600;700&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
"""

STITCH_TAILWIND_CONFIG = """
<script>
tailwind.config = {
    darkMode: "class",
    theme: {
        extend: {
            colors: {
                "primary": "#5a89f6",
                "background-light": "#f5f6f8",
                "background-dark": "#0B0E14",
                "surface-dark": "#181C25",
                "glass-border": "rgba(255, 255, 255, 0.08)",
                "glass-bg": "rgba(20, 25, 35, 0.6)"
            },
            fontFamily: {
                "display": ["Plus Jakarta Sans", "Noto Sans KR", "sans-serif"],
                "body": ["Noto Sans KR", "sans-serif"]
            },
            backgroundImage: {
                'cosmic-gradient': 'radial-gradient(circle at 15% 50%, rgba(90, 137, 246, 0.08), transparent 25%), radial-gradient(circle at 85% 30%, rgba(139, 92, 246, 0.05), transparent 25%)'
            }
        }
    }
}
</script>
"""

STITCH_BASE_STYLES = """
<style>
body { font-family: 'Plus Jakarta Sans', 'Noto Sans KR', sans-serif; margin: 0; padding: 0; }
.stitch-glass-panel { background: rgba(20, 25, 35, 0.6); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.08); }
.stitch-glass-panel-heavy { background: rgba(17, 20, 28, 0.75); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border-right: 1px solid rgba(255, 255, 255, 0.08); }
.stitch-nav-active { background: linear-gradient(90deg, rgba(90, 137, 246, 0.2) 0%, rgba(90, 137, 246, 0.05) 100%); border: 1px solid rgba(90, 137, 246, 0.3); box-shadow: 0 0 15px rgba(90, 137, 246, 0.15); }
.stitch-cosmic-bg { background-color: #0B0E14; background-image: radial-gradient(at 0% 0%, rgba(90, 137, 246, 0.15) 0px, transparent 50%), radial-gradient(at 100% 100%, rgba(124, 58, 237, 0.1) 0px, transparent 50%); }
.stitch-floating-input:focus ~ label, .stitch-floating-input:not(:placeholder-shown) ~ label { transform: translateY(-1.75rem) scale(0.85); color: #5a89f6; }
.stitch-floating-input:focus { box-shadow: 0 0 15px rgba(90, 137, 246, 0.25); }
.stitch-canvas-grid { background-size: 40px 40px; background-image: linear-gradient(to right, rgba(255, 255, 255, 0.03) 1px, transparent 1px), linear-gradient(to bottom, rgba(255, 255, 255, 0.03) 1px, transparent 1px); }
.stitch-btn-primary { background: #5a89f6; color: white; font-weight: 600; padding: 0.75rem 1.5rem; border-radius: 9999px; box-shadow: 0 0 20px rgba(90, 137, 246, 0.4); transition: all 0.2s; }
.stitch-btn-primary:hover { background: #4070e0; box-shadow: 0 0 30px rgba(90, 137, 246, 0.6); transform: translateY(-1px); }
.stitch-save-indicator { opacity: 0; transition: opacity 0.3s; }
.stitch-save-indicator.show { opacity: 1; }
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.2); }
input[type=range]::-webkit-slider-thumb { -webkit-appearance: none; height: 20px; width: 20px; border-radius: 50%; background: #5a89f6; cursor: pointer; box-shadow: 0 0 10px rgba(90, 137, 246, 0.8); margin-top: -8px; }
input[type=range]::-webkit-slider-runnable-track { width: 100%; height: 4px; cursor: pointer; background: rgba(255,255,255,0.1); border-radius: 2px; }
</style>
"""


# =============================================================================
# STITCH BRIDGE - Python-JS 양방향 통신
# =============================================================================

class StitchBridge:
    """STITCH 컴포넌트와 Streamlit 간 양방향 통신 브릿지"""

    @staticmethod
    def get_postmessage_script(component_type: str) -> str:
        """PostMessage 송신 스크립트 생성"""
        return f"""
<script>
// 디바운스 함수
let _stitch_debounce_timer;
function stitchDebounce(func, delay) {{
    clearTimeout(_stitch_debounce_timer);
    _stitch_debounce_timer = setTimeout(func, delay);
}}

// Streamlit으로 데이터 전송
function stitchSendData(data) {{
    data.type = '{component_type}';
    data.timestamp = Date.now();
    window.parent.postMessage(data, '*');

    // 저장 인디케이터 표시
    const indicator = document.getElementById('stitchSaveIndicator');
    if (indicator) {{
        indicator.classList.add('show');
        setTimeout(() => indicator.classList.remove('show'), 2000);
    }}
}}

// 입력 필드 변경 감지 및 자동 전송
function stitchBindInputs(formId, collectFunc) {{
    const form = document.getElementById(formId);
    if (!form) return;

    const inputs = form.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {{
        input.addEventListener('input', () => {{
            stitchDebounce(() => stitchSendData(collectFunc()), 500);
        }});
        input.addEventListener('change', () => {{
            stitchDebounce(() => stitchSendData(collectFunc()), 500);
        }});
    }});
}}
</script>
"""

    @staticmethod
    def get_listener_script() -> str:
        """Streamlit 측 PostMessage 리스너 스크립트 (app.py에 삽입)"""
        return """
<script>
window.addEventListener('message', function(event) {
    if (event.data && event.data.type) {
        const dataStr = JSON.stringify(event.data);
        // sessionStorage에 저장 (Streamlit rerun 시에도 유지)
        sessionStorage.setItem('stitch_' + event.data.type, dataStr);
        console.log('[STITCH] Received:', event.data.type, event.data);
    }
});
</script>
"""


# =============================================================================
# STITCH FACTORY - 메인 팩토리 클래스
# =============================================================================

class StitchFactory:
    """
    STITCH 디자인 시스템 컴포넌트 팩토리

    모든 STITCH UI 컴포넌트를 생성하고 렌더링하는 중앙 클래스
    """

    def __init__(self, config: Optional[StitchConfig] = None):
        self.config = config or StitchConfig()
        self.bridge = StitchBridge()

    def _build_html(self, body_content: str, component_type: str = "generic",
                    extra_styles: str = "", extra_scripts: str = "",
                    body_class: str = "bg-transparent") -> str:
        """HTML 문서 빌더"""
        return f"""<!DOCTYPE html>
<html class="dark" lang="ko">
<head>
{STITCH_HEAD_COMMON}
{STITCH_TAILWIND_CONFIG}
{STITCH_BASE_STYLES}
{extra_styles}
</head>
<body class="{body_class} text-white font-display" style="margin:0; padding:0;">
{body_content}
{self.bridge.get_postmessage_script(component_type)}
{extra_scripts}
</body></html>"""

    # -------------------------------------------------------------------------
    # SIDEBAR COMPONENT
    # -------------------------------------------------------------------------

    def render_sidebar(self, active_page: str = "datalab", height: int = 800) -> None:
        """사이드바 네비게이션 렌더링 (Minified HTML)"""
        # 각 메뉴 아이템의 active 상태 결정
        def get_nav_class(page: str) -> str:
            if page == active_page:
                return "stitch-nav-active group flex items-center gap-3 rounded-full px-4 py-3 transition-all"
            return "group flex items-center gap-3 rounded-full px-4 py-3 text-slate-400 hover:bg-white/5 hover:text-white transition-all"

        def get_icon_class(page: str) -> str:
            if page == active_page:
                return "material-symbols-outlined text-primary group-hover:scale-110 transition-transform"
            return "material-symbols-outlined group-hover:scale-110 transition-transform"

        def get_text_class(page: str) -> str:
            if page == active_page:
                return "text-sm font-semibold text-white"
            return "text-sm font-semibold"

        body_html = f'''<nav class="stitch-glass-panel-heavy flex w-72 flex-col justify-between p-6 h-full">
<div class="flex flex-col gap-8">
<div class="flex items-center gap-4 px-2"><div class="relative flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 shadow-lg shadow-blue-500/20"><span class="material-symbols-outlined text-white" style="font-size:24px">rocket_launch</span><div class="absolute inset-0 rounded-xl ring-1 ring-inset ring-white/20"></div></div><div class="flex flex-col"><h1 class="text-lg font-bold tracking-tight text-white">NovaRium</h1><p class="text-xs font-medium text-slate-400">Analyst Platform</p></div></div>
<div class="flex flex-col gap-2">
<a class="{get_nav_class('datalab')}" href="#" onclick="stitchNav('datalab')"><span class="{get_icon_class('datalab')}" style="font-variation-settings:'FILL' {'1' if active_page=='datalab' else '0'}">science</span><span class="{get_text_class('datalab')}">Data Lab</span></a>
<a class="{get_nav_class('monitor')}" href="#" onclick="stitchNav('monitor')"><span class="{get_icon_class('monitor')}">monitoring</span><span class="{get_text_class('monitor')}">Monitor</span></a>
<a class="{get_nav_class('masterclass')}" href="#" onclick="stitchNav('masterclass')"><span class="{get_icon_class('masterclass')}">school</span><span class="{get_text_class('masterclass')}">Master Class</span></a>
<a class="{get_nav_class('portfolio')}" href="#" onclick="stitchNav('portfolio')"><span class="{get_icon_class('portfolio')}">folder_open</span><span class="{get_text_class('portfolio')}">Portfolio</span></a>
</div>
</div>
<div class="flex flex-col gap-6">
<div class="rounded-2xl bg-gradient-to-br from-indigo-900/30 to-blue-900/30 p-4 border border-white/5"><div class="flex items-center justify-between mb-2"><span class="text-xs font-bold uppercase tracking-wider text-blue-300">System Status</span><div class="h-2 w-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]"></div></div><p class="text-xs text-slate-400">All systems operational.</p></div>
<button class="relative flex w-full cursor-pointer items-center justify-center gap-2 overflow-hidden rounded-full bg-primary px-4 py-3.5 text-sm font-bold text-white shadow-[0_0_20px_rgba(90,137,246,0.4)] transition-transform hover:scale-[1.02] hover:shadow-[0_0_25px_rgba(90,137,246,0.6)]" onclick="stitchNav('new_experiment')"><span class="material-symbols-outlined" style="font-size:20px">add</span><span>New Experiment</span></button>
</div>
</nav>'''

        extra_scripts = """
<script>
function stitchNav(page) {
    stitchSendData({ action: 'navigate', page: page });
}
</script>
"""
        html = self._build_html(body_html, component_type="sidebar_nav",
                                 extra_scripts=extra_scripts,
                                 body_class="bg-transparent h-full")
        components.html(html, height=height, scrolling=False)

    # -------------------------------------------------------------------------
    # HYPOTHESIS WIZARD (Step 1)
    # -------------------------------------------------------------------------

    def render_hypothesis_wizard(self, height: int = 850,
                                  initial_data: Optional[Dict[str, Any]] = None) -> None:
        """실험 가설 설정 마법사 (Step 1) - 완전 구현"""
        data = initial_data or {}
        exp_name = data.get('exp_name', '체크아웃 흐름 최적화 V2')
        exp_owner = data.get('exp_owner', '김연구 박사')
        independent_var = data.get('independent_var', '')
        target_audience = data.get('target_audience', '')
        success_metric = data.get('success_metric', '전환율 (Conversion Rate)')
        hypothesis_reason = data.get('hypothesis_reason', '')
        confidence_level = data.get('confidence_level', 95)

        init_json = json.dumps({
            'exp_name': exp_name, 'exp_owner': exp_owner, 'independent_var': independent_var,
            'target_audience': target_audience, 'success_metric': success_metric,
            'hypothesis_reason': hypothesis_reason, 'confidence_level': confidence_level
        }, ensure_ascii=False)

        body_html = f'''
<div class="relative z-10 flex flex-col">
<main class="container mx-auto px-4 py-4 max-w-5xl flex flex-col gap-6">
<div class="flex flex-col gap-2">
<div class="flex items-center justify-between">
<h1 class="text-2xl font-display font-bold text-white tracking-tight">가설 설정</h1>
<span id="stitchSaveIndicator" class="stitch-save-indicator text-xs text-green-400 flex items-center gap-1"><span class="material-symbols-outlined text-sm">check_circle</span> 자동 저장됨</span>
</div>
<p class="text-slate-400 font-display text-sm">A/B 테스트를 위한 과학적 근거를 정의하세요.</p>
</div>
<div class="stitch-glass-panel rounded-2xl p-8 relative overflow-hidden group">
<div class="absolute -top-24 -right-24 w-64 h-64 bg-primary/10 rounded-full blur-[80px] group-hover:bg-primary/15 transition-all duration-700"></div>
<form id="hypothesisForm" class="flex flex-col gap-10 relative z-10">
<div class="grid grid-cols-1 md:grid-cols-2 gap-8">
<div class="relative pt-2"><input class="stitch-floating-input block w-full px-4 py-3 bg-black/30 border border-white/10 rounded-lg text-white appearance-none focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary transition-all peer" id="exp_name" placeholder=" " type="text" value=""/><label class="absolute left-4 top-5 text-slate-400 text-base duration-300 origin-[0] pointer-events-none" for="exp_name">실험 명칭</label></div>
<div class="relative pt-2"><input class="stitch-floating-input block w-full px-4 py-3 bg-black/30 border border-white/10 rounded-lg text-white appearance-none focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary transition-all peer" id="exp_owner" placeholder=" " type="text" value=""/><label class="absolute left-4 top-5 text-slate-400 text-base duration-300 origin-[0] pointer-events-none" for="exp_owner">담당자</label></div>
</div>
<div class="flex flex-col gap-4">
<div class="flex items-center gap-2"><h3 class="text-lg font-bold font-display text-white">가설 정의서</h3><button class="text-slate-400 hover:text-primary transition-colors" title="가설 수립 도움말" type="button"><span class="material-symbols-outlined text-sm">help</span></button></div>
<div class="bg-black/20 border border-white/10 rounded-xl p-6 md:p-8">
<div class="flex flex-wrap items-center gap-3 text-lg md:text-xl font-light text-slate-300 leading-loose">
<span>우리가</span>
<div class="relative min-w-[200px] flex-1"><input id="independent_var" class="w-full bg-white/5 border-b-2 border-primary/50 focus:border-primary text-white px-2 py-1 focus:outline-none transition-colors placeholder-slate-600" placeholder="변수 (예: 버튼 색상)" type="text"/></div>
<span>을(를) 변경한다면,</span>
<div class="relative min-w-[180px] flex-1"><input id="target_audience" class="w-full bg-white/5 border-b-2 border-primary/50 focus:border-primary text-white px-2 py-1 focus:outline-none transition-colors placeholder-slate-600" placeholder="타겟 고객" type="text"/></div>
<span>에 대해</span>
<div class="relative min-w-[200px] flex-1"><select id="success_metric" class="w-full bg-black/50 border border-white/10 rounded text-white px-3 py-1.5 focus:outline-none focus:border-primary appearance-none cursor-pointer"><option value="전환율 (Conversion Rate)">전환율 (Conversion Rate)</option><option value="평균 주문 금액 (AOV)">평균 주문 금액 (AOV)</option><option value="재방문율 (Retention)">재방문율 (Retention)</option><option value="클릭률 (CTR)">클릭률 (CTR)</option></select></div>
<span>이(가) 증가할 것입니다. 그 이유는</span>
<div class="w-full mt-2"><textarea id="hypothesis_reason" class="w-full bg-white/5 border border-white/10 rounded-lg p-3 text-base text-white focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/50 placeholder-slate-600 transition-all resize-none" placeholder="근거를 입력하세요..." rows="2"></textarea></div>
</div>
</div>
</div>
<div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
<div class="flex flex-col gap-4">
<div class="flex items-center gap-2"><h3 class="text-lg font-bold font-display text-white">성공 지표</h3></div>
<div class="grid grid-cols-2 gap-4">
<div class="bg-white/5 hover:bg-white/10 border border-white/10 hover:border-primary/50 rounded-xl p-4 transition-all cursor-pointer group/card"><div class="flex justify-between items-start mb-2"><span class="material-symbols-outlined text-primary group-hover/card:scale-110 transition-transform">ads_click</span><span class="text-xs font-bold text-primary bg-primary/10 px-2 py-0.5 rounded uppercase tracking-wider">Primary</span></div><p class="text-sm text-slate-400">주요 KPI</p><p id="primary_metric_display" class="text-white font-bold text-lg">전환율</p></div>
<div class="bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/30 rounded-xl p-4 transition-all cursor-pointer border-dashed"><div class="flex justify-between items-start mb-2"><span class="material-symbols-outlined text-slate-500">add_chart</span></div><p class="text-sm text-slate-500">가드레일 지표</p><p class="text-slate-400 font-medium text-lg">지표 추가</p></div>
</div>
</div>
<div class="flex flex-col gap-4">
<div class="flex items-center justify-between"><div class="flex items-center gap-2"><h3 class="text-lg font-bold font-display text-white">신뢰 수준</h3></div><span id="confidence_display" class="text-primary font-mono font-bold text-xl">95%</span></div>
<div class="bg-black/20 border border-white/10 rounded-xl p-6 flex flex-col justify-center h-full"><input id="confidence_level" class="w-full bg-transparent appearance-none mb-4" max="99" min="80" type="range" value="95"/><div class="flex justify-between text-xs text-slate-500 font-mono"><span>80%</span><span>85%</span><span>90%</span><span>95%</span><span>99%</span></div><p class="text-xs text-slate-400 mt-4 leading-relaxed"><span class="text-primary font-bold">참고:</span> 신뢰 수준이 높을수록 더 많은 표본과 긴 실험 기간이 필요합니다.</p></div>
</div>
</div>
</form>
</div>
</main>
</div>'''

        extra_scripts = f'''
<script>
const initData = {init_json};
const els = {{
    exp_name: document.getElementById('exp_name'),
    exp_owner: document.getElementById('exp_owner'),
    independent_var: document.getElementById('independent_var'),
    target_audience: document.getElementById('target_audience'),
    success_metric: document.getElementById('success_metric'),
    hypothesis_reason: document.getElementById('hypothesis_reason'),
    confidence_level: document.getElementById('confidence_level'),
    confidence_display: document.getElementById('confidence_display'),
    primary_metric_display: document.getElementById('primary_metric_display')
}};

function loadInit() {{
    els.exp_name.value = initData.exp_name || '';
    els.exp_owner.value = initData.exp_owner || '';
    els.independent_var.value = initData.independent_var || '';
    els.target_audience.value = initData.target_audience || '';
    els.success_metric.value = initData.success_metric || '전환율 (Conversion Rate)';
    els.hypothesis_reason.value = initData.hypothesis_reason || '';
    els.confidence_level.value = initData.confidence_level || 95;
    els.confidence_display.textContent = (initData.confidence_level || 95) + '%';
    updateMetric();
}}

function updateMetric() {{
    const m = els.success_metric.value.split(' (')[0];
    els.primary_metric_display.textContent = m;
}}

function collectData() {{
    return {{
        exp_name: els.exp_name.value,
        exp_owner: els.exp_owner.value,
        independent_var: els.independent_var.value,
        target_audience: els.target_audience.value,
        success_metric: els.success_metric.value,
        hypothesis_reason: els.hypothesis_reason.value,
        confidence_level: parseInt(els.confidence_level.value),
        hypothesis: `우리가 ${{els.independent_var.value}}을(를) 변경한다면, ${{els.target_audience.value}}에 대해 ${{els.success_metric.value.split(' (')[0]}}이(가) 증가할 것입니다. 그 이유는 ${{els.hypothesis_reason.value}}`
    }};
}}

els.confidence_level.addEventListener('input', function() {{
    els.confidence_display.textContent = this.value + '%';
    stitchDebounce(() => stitchSendData(collectData()), 500);
}});

els.success_metric.addEventListener('change', function() {{
    updateMetric();
    stitchDebounce(() => stitchSendData(collectData()), 500);
}});

['exp_name', 'exp_owner', 'independent_var', 'target_audience', 'hypothesis_reason'].forEach(id => {{
    els[id].addEventListener('input', () => stitchDebounce(() => stitchSendData(collectData()), 500));
}});

loadInit();
setTimeout(() => stitchSendData(collectData()), 100);
</script>'''

        html = self._build_html(body_html, component_type="hypothesis_data",
                                 extra_scripts=extra_scripts, body_class="bg-transparent")
        components.html(html, height=height, scrolling=True)

    # -------------------------------------------------------------------------
    # DESIGN BUILDER (Step 2)
    # -------------------------------------------------------------------------

    def render_design_builder(self, height: int = 900,
                               initial_data: Optional[Dict[str, Any]] = None) -> None:
        """디자인 빌더 (Step 2) - 완전 구현"""
        data = initial_data or {}
        variant_name = data.get('variant_name', 'B: 테스트 변형')
        hypothesis = data.get('hypothesis', '')
        traffic_split = data.get('traffic_split', 50)

        init_json = json.dumps({
            'variant_name': variant_name, 'hypothesis': hypothesis, 'traffic_split': traffic_split
        }, ensure_ascii=False)

        body_html = f'''
<div class="px-4 py-3 flex items-center justify-between">
<div><h1 class="text-2xl font-bold text-white tracking-tight">디자인 빌더</h1><p class="text-slate-400 text-sm">변형을 만들고 실시간으로 미리보기하세요.</p></div>
<span id="stitchSaveIndicator" class="stitch-save-indicator text-xs text-green-400 flex items-center gap-1"><span class="material-symbols-outlined text-sm">check_circle</span> 자동 저장됨</span>
</div>
<main class="flex-1 flex overflow-hidden gap-4 px-4 pb-4 relative z-10">
<aside class="w-80 flex-none flex flex-col stitch-glass-panel rounded-2xl overflow-hidden shadow-glass transition-all duration-300">
<div class="p-5 border-b border-glass-border bg-white/5 flex justify-between items-center"><h3 class="text-sm font-bold text-white uppercase tracking-wider">전략 구성</h3><span class="material-symbols-outlined text-slate-500 text-[18px]">tune</span></div>
<div class="flex-1 overflow-y-auto p-5 space-y-6">
<div class="space-y-2"><label class="text-xs font-semibold text-slate-300 uppercase tracking-wide">변형 이름</label><input id="variant_name" class="w-full bg-[#1b1f27] border border-[#3b4254] rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all" placeholder="예: B: 신뢰 신호" value=""/></div>
<div class="space-y-2"><label class="text-xs font-semibold text-slate-300 uppercase tracking-wide">가설</label><textarea id="design_hypothesis" class="w-full bg-[#1b1f27] border border-[#3b4254] rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all min-h-[100px] resize-none" placeholder="가설을 입력하세요..."></textarea></div>
<div class="space-y-4 pt-2">
<div class="flex justify-between items-center"><label class="text-xs font-semibold text-slate-300 uppercase tracking-wide">트래픽 할당</label><span id="traffic_display" class="text-xs font-mono text-primary bg-primary/10 px-2 py-0.5 rounded border border-primary/20">50% / 50%</span></div>
<div class="relative h-2 bg-[#282d39] rounded-full overflow-hidden"><div id="control_bar" class="absolute left-0 top-0 bottom-0 w-1/2 bg-gradient-to-r from-slate-500 to-slate-400"></div><div id="variant_bar" class="absolute right-0 top-0 bottom-0 w-1/2 bg-gradient-to-r from-primary to-blue-400"></div><input id="traffic_split" type="range" min="10" max="90" value="50" class="absolute inset-0 w-full h-full opacity-0 cursor-col-resize z-10"/></div>
<div class="flex justify-between text-[10px] text-slate-400 font-medium uppercase tracking-wider"><span>대조군 (A)</span><span class="text-primary">실험군 (B)</span></div>
</div>
<div class="space-y-2 pt-2"><label class="text-xs font-semibold text-slate-300 uppercase tracking-wide">타겟 디바이스</label><div class="flex bg-[#1b1f27] p-1 rounded-xl border border-[#3b4254]"><button id="device_desktop" class="flex-1 py-1.5 rounded-lg bg-primary text-white shadow-sm flex items-center justify-center"><span class="material-symbols-outlined text-[18px]">desktop_windows</span></button><button id="device_mobile" class="flex-1 py-1.5 rounded-lg text-slate-400 hover:text-white flex items-center justify-center transition-colors"><span class="material-symbols-outlined text-[18px]">smartphone</span></button></div></div>
</div>
</aside>
<section class="flex-1 relative flex flex-col rounded-2xl overflow-hidden border border-white/5 bg-[#0a0d14] group shadow-inner">
<div class="absolute inset-0 stitch-canvas-grid opacity-20 pointer-events-none"></div>
<div class="absolute top-6 left-1/2 -translate-x-1/2 stitch-glass-panel px-4 py-2 rounded-full flex gap-2 z-20 shadow-lg"><button class="size-9 rounded-full hover:bg-white/10 text-slate-300 hover:text-white flex items-center justify-center transition-colors" title="선택"><span class="material-symbols-outlined text-[20px]">near_me</span></button><button class="size-9 rounded-full bg-primary/20 text-primary border border-primary/20 flex items-center justify-center transition-colors" title="텍스트 편집"><span class="material-symbols-outlined text-[20px]">edit_note</span></button><button class="size-9 rounded-full hover:bg-white/10 text-slate-300 hover:text-white flex items-center justify-center transition-colors" title="이미지 교체"><span class="material-symbols-outlined text-[20px]">image</span></button><div class="w-px h-5 bg-white/10 my-auto mx-1"></div><button class="size-9 rounded-full hover:bg-white/10 text-slate-300 hover:text-white flex items-center justify-center transition-colors" title="실행 취소"><span class="material-symbols-outlined text-[20px]">undo</span></button></div>
<div class="flex-1 overflow-auto flex items-center justify-center p-10 cursor-grab active:cursor-grabbing">
<div class="w-full max-w-[800px] bg-[#0f1218] rounded-xl shadow-2xl overflow-hidden border border-[#2d3342] relative">
<div class="h-8 bg-[#1e232e] flex items-center px-3 border-b border-[#2d3342]"><div class="flex gap-1.5"><div class="size-2.5 rounded-full bg-[#ff5f56]"></div><div class="size-2.5 rounded-full bg-[#ffbd2e]"></div><div class="size-2.5 rounded-full bg-[#27c93f]"></div></div><div class="mx-auto w-1/2 h-5 bg-[#111318] rounded text-[10px] flex items-center justify-center text-slate-500 font-mono">acme-corp.com/landing</div></div>
<div class="relative min-h-[400px] bg-[#0f1218]"><div class="grid grid-cols-2 gap-8 p-12 items-center"><div class="space-y-6 relative group/element"><div class="absolute -inset-4 border-2 border-primary/50 rounded-xl bg-primary/5 pointer-events-none animate-pulse"></div><div class="absolute -top-10 left-0 bg-primary text-white text-[10px] font-bold px-2 py-1 rounded-t-lg rounded-br-lg shadow-sm flex items-center gap-1"><span class="material-symbols-outlined text-[12px]">edit</span>H1 편집 중</div><h1 class="text-4xl font-extrabold text-white leading-tight outline-none" contenteditable="true">새로운 <span class="text-primary">여정</span>을 시작하세요</h1><p class="text-slate-400 text-lg leading-relaxed">차세대 금융 도구를 경험해보세요.</p><div class="flex gap-4 pt-2"><button class="bg-white text-black px-6 py-3 rounded-full font-bold text-sm hover:bg-gray-200">시작하기</button><button class="bg-transparent border border-slate-600 text-white px-6 py-3 rounded-full font-bold text-sm hover:bg-white/5">데모 보기</button></div></div><div class="relative aspect-square rounded-2xl overflow-hidden bg-slate-800 border border-slate-700"><img class="w-full h-full object-cover opacity-80" src="https://picsum.photos/seed/tech/400/400"/><div class="absolute inset-0 bg-primary/20 opacity-0 hover:opacity-100 transition-opacity cursor-pointer flex items-center justify-center border-2 border-primary border-dashed"><span class="bg-black/80 text-white px-3 py-1.5 rounded-full text-xs font-medium backdrop-blur-sm">이미지 교체</span></div></div></div></div>
</div>
</div>
<div class="absolute bottom-6 left-6 flex gap-2"><div class="stitch-glass-panel px-3 py-1.5 rounded-lg flex items-center gap-2 text-xs font-mono text-slate-300"><span class="material-symbols-outlined text-[14px]">aspect_ratio</span>1440x900</div><div class="stitch-glass-panel px-3 py-1.5 rounded-lg flex items-center gap-2 text-xs font-mono text-slate-300"><span class="material-symbols-outlined text-[14px]">zoom_in</span>100%</div></div>
</section>
<aside class="w-80 lg:w-96 flex-none flex flex-col stitch-glass-panel rounded-2xl overflow-hidden shadow-glass">
<div class="p-5 border-b border-glass-border bg-white/5 flex justify-between items-center"><h3 class="text-sm font-bold text-white uppercase tracking-wider">실시간 미리보기</h3></div>
<div class="flex-1 flex flex-col overflow-hidden">
<div class="flex-1 flex flex-col border-b border-white/10 relative"><div class="absolute top-3 left-3 z-10 bg-black/80 text-slate-300 border border-slate-700 px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider">대조군 (A)</div><div class="flex-1 bg-[#0f1218] p-4 overflow-hidden relative grayscale opacity-60"><div class="transform scale-75 origin-top-left w-[133%]"><h1 class="text-3xl font-extrabold text-white mb-2">미래에 오신 것을 환영합니다</h1><p class="text-slate-400 text-sm">모두를 위한 금융 도구.</p></div></div></div>
<div class="flex-1 flex flex-col relative bg-[#111318]"><div class="absolute top-3 left-3 z-10 bg-primary text-white border border-primary/50 px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider shadow-glow">실험군 (B)</div><div class="flex-1 p-4 overflow-hidden relative"><div class="transform scale-75 origin-top-left w-[133%]"><h1 class="text-3xl font-extrabold text-white mb-2">새로운 <span class="text-primary">여정</span>을 시작하세요</h1><p class="text-slate-400 text-sm">차세대 금융 도구를 경험해보세요...</p></div></div></div>
</div>
<div class="p-4 border-t border-glass-border bg-white/5"><div class="flex items-start gap-3 p-3 bg-primary/10 rounded-xl border border-primary/20"><span class="material-symbols-outlined text-primary text-[20px] mt-0.5">auto_awesome</span><div><p class="text-xs font-medium text-white mb-0.5">AI 인사이트</p><p class="text-[11px] text-slate-400 leading-snug">"여정"이라는 단어가 감정적 소구력이 높습니다. 예상 전환율 +5%.</p></div></div></div>
</aside>
</main>'''

        extra_scripts = f'''
<script>
const initData = {init_json};
const els = {{
    variant_name: document.getElementById('variant_name'),
    design_hypothesis: document.getElementById('design_hypothesis'),
    traffic_split: document.getElementById('traffic_split'),
    traffic_display: document.getElementById('traffic_display'),
    control_bar: document.getElementById('control_bar'),
    variant_bar: document.getElementById('variant_bar'),
    device_desktop: document.getElementById('device_desktop'),
    device_mobile: document.getElementById('device_mobile')
}};

let selectedDevice = 'desktop';

function loadInit() {{
    els.variant_name.value = initData.variant_name || '';
    els.design_hypothesis.value = initData.hypothesis || '';
    els.traffic_split.value = initData.traffic_split || 50;
    updateTraffic();
}}

function updateTraffic() {{
    const split = parseInt(els.traffic_split.value);
    els.traffic_display.textContent = `${{100 - split}}% / ${{split}}%`;
    els.control_bar.style.width = `${{100 - split}}%`;
    els.variant_bar.style.width = `${{split}}%`;
}}

function collectData() {{
    return {{
        variant_name: els.variant_name.value,
        hypothesis: els.design_hypothesis.value,
        traffic_split: parseInt(els.traffic_split.value),
        target_device: selectedDevice
    }};
}}

els.traffic_split.addEventListener('input', function() {{
    updateTraffic();
    stitchDebounce(() => stitchSendData(collectData()), 500);
}});

['variant_name', 'design_hypothesis'].forEach(id => {{
    els[id].addEventListener('input', () => stitchDebounce(() => stitchSendData(collectData()), 500));
}});

els.device_desktop.addEventListener('click', () => {{
    selectedDevice = 'desktop';
    els.device_desktop.classList.add('bg-primary', 'text-white', 'shadow-sm');
    els.device_desktop.classList.remove('text-slate-400');
    els.device_mobile.classList.remove('bg-primary', 'text-white', 'shadow-sm');
    els.device_mobile.classList.add('text-slate-400');
    stitchDebounce(() => stitchSendData(collectData()), 500);
}});

els.device_mobile.addEventListener('click', () => {{
    selectedDevice = 'mobile';
    els.device_mobile.classList.add('bg-primary', 'text-white', 'shadow-sm');
    els.device_mobile.classList.remove('text-slate-400');
    els.device_desktop.classList.remove('bg-primary', 'text-white', 'shadow-sm');
    els.device_desktop.classList.add('text-slate-400');
    stitchDebounce(() => stitchSendData(collectData()), 500);
}});

loadInit();
setTimeout(() => stitchSendData(collectData()), 100);
</script>'''

        html = self._build_html(body_html, component_type="design_data",
                                 extra_scripts=extra_scripts,
                                 body_class="bg-transparent w-full flex flex-col overflow-hidden")
        components.html(html, height=height, scrolling=True)

    # -------------------------------------------------------------------------
    # ANALYSIS DASHBOARD (Step 3)
    # -------------------------------------------------------------------------

    def render_analysis_dashboard(self, height: int = 900,
                                   analysis_data: Optional[Dict[str, Any]] = None) -> None:
        """분석 대시보드 (Step 3) - 완전 구현"""
        data = analysis_data or {}

        # 통계 데이터 기본값
        sample_size = data.get('sample_size', 12450)
        lift = data.get('lift', 5.2)
        p_value = data.get('p_value', 0.02)
        power = data.get('power', 88)
        control_rate = data.get('control_rate', 2.10)
        variant_rate = data.get('variant_rate', 2.25)
        confidence_level = data.get('confidence_level', 95)
        is_significant = p_value < 0.05
        recommendation = data.get('recommendation', '실험군 B 배포 권장')

        init_json = json.dumps({
            'sample_size': sample_size, 'lift': lift, 'p_value': p_value,
            'power': power, 'control_rate': control_rate, 'variant_rate': variant_rate,
            'confidence_level': confidence_level, 'is_significant': is_significant,
            'recommendation': recommendation
        }, ensure_ascii=False)

        # 통계적 유의성 스타일
        sig_badge_class = "text-green-400" if is_significant else "text-amber-400"
        sig_icon = "check_circle" if is_significant else "warning"
        sig_text = "통계적 유의성 확보 (< 0.05)" if is_significant else "유의 수준 미달 (≥ 0.05)"

        # 바 차트 높이 계산 (최대 250px 기준)
        max_rate = max(control_rate, variant_rate)
        control_bar_height = int((control_rate / max_rate) * 220)
        variant_bar_height = int((variant_rate / max_rate) * 220)

        body_html = f'''
<div class="flex flex-col h-full">
<header class="flex-none px-6 py-4 border-b border-white/5 flex items-center justify-between">
<div class="flex items-center gap-2 text-sm"><span class="text-slate-400">실험 관리</span><span class="text-slate-600">/</span><span class="text-primary font-medium">분석</span></div>
<span id="stitchSaveIndicator" class="stitch-save-indicator text-xs text-green-400 flex items-center gap-1"><span class="material-symbols-outlined text-sm">check_circle</span> 저장됨</span>
</header>
<main class="flex-1 overflow-y-auto px-6 py-6">
<div class="max-w-6xl mx-auto flex flex-col gap-6">
<div class="flex flex-col gap-2">
<h1 class="text-2xl font-bold text-white tracking-tight">분석 대시보드</h1>
<p class="text-slate-400 text-sm">통계적 결과를 검토하고 의사 결정을 위한 데이터를 해석하세요.</p>
</div>
<div class="rounded-xl overflow-hidden relative border border-primary/30 shadow-[0_0_20px_rgba(90,137,246,0.15)]">
<div class="absolute inset-0 bg-gradient-to-r from-primary/20 to-purple-600/20 backdrop-blur-xl"></div>
<div class="relative p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
<div class="flex items-start gap-4">
<div class="p-3 rounded-full bg-primary/20 text-primary border border-primary/30"><span class="material-symbols-outlined text-2xl">auto_awesome</span></div>
<div class="space-y-1">
<h3 class="text-lg font-bold text-white">유의미한 결과: {recommendation}</h3>
<p class="text-slate-300 text-sm">주요 지표가 <span class="text-green-400 font-bold">+{lift}%</span>의 통계적으로 유의미한 개선을 보였습니다.</p>
</div>
</div>
<button class="px-4 py-2 bg-primary hover:bg-blue-600 text-white font-semibold rounded-lg shadow-lg transition-all flex items-center gap-2" onclick="confirmDecision()">결론 작성<span class="material-symbols-outlined text-lg">arrow_forward</span></button>
</div>
</div>
<div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
<div class="stitch-glass-panel rounded-xl p-4 flex flex-col gap-2 hover:bg-white/10 transition-colors">
<div class="flex justify-between items-center"><p class="text-slate-400 text-xs font-medium">표본 크기</p><span class="material-symbols-outlined text-slate-600 text-lg">groups</span></div>
<p class="text-xl font-bold text-white">{sample_size:,}</p>
</div>
<div class="stitch-glass-panel rounded-xl p-4 flex flex-col gap-2 hover:bg-white/10 transition-colors">
<div class="flex justify-between items-center"><p class="text-slate-400 text-xs font-medium">전환 상승폭</p><span class="material-symbols-outlined text-green-400 text-lg">trending_up</span></div>
<p class="text-xl font-bold text-white">+{lift}%</p>
</div>
<div class="stitch-glass-panel rounded-xl p-4 flex flex-col gap-2 hover:bg-white/10 transition-colors border-green-500/30 bg-green-500/5">
<div class="flex justify-between items-center"><p class="text-slate-400 text-xs font-medium">P-값</p><span class="material-symbols-outlined {sig_badge_class} text-lg">{sig_icon}</span></div>
<p class="text-xl font-bold text-white font-mono">{p_value}</p>
<p class="text-[10px] {sig_badge_class} font-medium">{sig_text}</p>
</div>
<div class="stitch-glass-panel rounded-xl p-4 flex flex-col gap-2 hover:bg-white/10 transition-colors">
<div class="flex justify-between items-center"><p class="text-slate-400 text-xs font-medium">검정력</p><span class="material-symbols-outlined text-purple-400 text-lg">bolt</span></div>
<p class="text-xl font-bold text-white">{power}%</p>
</div>
</div>
<div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
<div class="lg:col-span-2 stitch-glass-panel rounded-xl p-5 flex flex-col">
<div class="flex items-center justify-between mb-4">
<h3 class="text-base font-bold text-white">전환율 비교</h3>
<div class="flex items-center gap-4 text-xs font-medium">
<div class="flex items-center gap-2"><span class="size-2.5 rounded-full bg-slate-600"></span>대조군</div>
<div class="flex items-center gap-2"><span class="size-2.5 rounded-full bg-primary shadow-[0_0_8px_rgba(90,137,246,0.6)]"></span>실험군 B</div>
</div>
</div>
<div class="flex-1 min-h-[220px] flex items-end justify-center gap-16 pb-6 relative border-b border-white/5">
<div class="absolute inset-0 flex flex-col justify-between pointer-events-none">
<div class="border-t border-dashed border-white/5 w-full"></div>
<div class="border-t border-dashed border-white/5 w-full"></div>
<div class="border-t border-dashed border-white/5 w-full"></div>
<div class="border-t border-dashed border-white/5 w-full"></div>
</div>
<div class="flex flex-col items-center gap-2 z-10 group">
<div class="w-14 bg-slate-700/50 rounded-t-lg transition-all hover:bg-slate-600/60" style="height: {control_bar_height}px;">
<div class="opacity-0 group-hover:opacity-100 -mt-6 text-center text-white font-bold text-sm transition-opacity">{control_rate}%</div>
</div>
<span class="text-xs font-medium text-slate-400">대조군</span>
</div>
<div class="flex flex-col items-center gap-2 z-10 group">
<div class="w-14 bg-primary rounded-t-lg shadow-[0_0_20px_rgba(90,137,246,0.3)] transition-all hover:shadow-[0_0_30px_rgba(90,137,246,0.5)]" style="height: {variant_bar_height}px;">
<div class="opacity-0 group-hover:opacity-100 -mt-6 text-center text-white font-bold text-sm transition-opacity">{variant_rate}%</div>
</div>
<span class="text-xs font-bold text-white">실험군 B</span>
</div>
</div>
</div>
<div class="stitch-glass-panel rounded-xl p-5 flex flex-col">
<div class="mb-3">
<h3 class="text-base font-bold text-white">신뢰 구간 ({confidence_level}% CI)</h3>
</div>
<div class="flex-1 flex flex-col justify-center gap-6 py-3">
<div class="space-y-2">
<div class="flex justify-between text-[10px] text-slate-500 px-1"><span>{control_rate - 0.15:.2f}%</span><span>{control_rate + 0.15:.2f}%</span></div>
<div class="relative h-6 flex items-center w-full">
<div class="absolute left-[15%] right-[15%] h-0.5 bg-slate-600 rounded-full"></div>
<div class="absolute left-[15%] h-2.5 w-0.5 bg-slate-600"></div>
<div class="absolute right-[15%] h-2.5 w-0.5 bg-slate-600"></div>
<div class="absolute left-1/2 size-2.5 bg-slate-400 rounded-full border-2 border-surface-dark z-10 -ml-1"></div>
</div>
<p class="text-[10px] font-medium text-slate-500 text-center">대조군</p>
</div>
<div class="space-y-2">
<div class="flex justify-between text-[10px] text-primary/70 px-1"><span>{variant_rate - 0.10:.2f}%</span><span>{variant_rate + 0.10:.2f}%</span></div>
<div class="relative h-6 flex items-center w-full">
<div class="absolute left-[25%] right-[5%] h-0.5 bg-primary rounded-full shadow-[0_0_8px_rgba(90,137,246,0.5)]"></div>
<div class="absolute left-[25%] h-2.5 w-0.5 bg-primary"></div>
<div class="absolute right-[5%] h-2.5 w-0.5 bg-primary"></div>
<div class="absolute left-[60%] size-2.5 bg-white rounded-full border-2 border-primary z-10 -ml-1 shadow-[0_0_10px_white]"></div>
</div>
<p class="text-[10px] font-bold text-white text-center">실험군 B</p>
</div>
</div>
<div class="mt-3 p-2 rounded bg-white/5 text-[10px] text-slate-300 leading-relaxed border border-white/5">
<span class="material-symbols-outlined text-xs align-middle mr-1 text-primary">science</span>
표본 크기가 충분하여 결과가 신뢰할 수 있습니다.
</div>
</div>
</div>
<div class="stitch-glass-panel rounded-xl overflow-hidden">
<div class="px-5 py-3 border-b border-white/10 flex justify-between items-center">
<h3 class="text-base font-bold text-white">상세 지표</h3>
<button class="text-primary text-xs font-medium hover:text-blue-400" onclick="exportCSV()">CSV 내보내기</button>
</div>
<div class="overflow-x-auto">
<table class="w-full text-sm text-left">
<thead class="text-[10px] text-slate-400 uppercase bg-white/5 border-b border-white/5">
<tr><th class="px-5 py-2.5">지표</th><th class="px-5 py-2.5">대조군</th><th class="px-5 py-2.5">실험군</th><th class="px-5 py-2.5">차이</th><th class="px-5 py-2.5">CI</th></tr>
</thead>
<tbody class="divide-y divide-white/5">
<tr class="hover:bg-white/5 transition-colors">
<td class="px-5 py-3 font-medium text-white flex items-center gap-2">전환율<span class="text-[9px] px-1.5 py-0.5 rounded bg-primary/20 text-primary border border-primary/20">Primary</span></td>
<td class="px-5 py-3 text-slate-300">{control_rate}%</td>
<td class="px-5 py-3 font-bold text-white">{variant_rate}%</td>
<td class="px-5 py-3 text-green-400 font-medium">+{lift}%</td>
<td class="px-5 py-3 text-slate-400 font-mono text-xs">[{variant_rate - 0.10:.2f}%, {variant_rate + 0.10:.2f}%]</td>
</tr>
<tr class="hover:bg-white/5 transition-colors">
<td class="px-5 py-3 font-medium text-white">장바구니 담기</td>
<td class="px-5 py-3 text-slate-300">5.40%</td>
<td class="px-5 py-3 text-slate-300">5.65%</td>
<td class="px-5 py-3 text-green-400 font-medium">+4.6%</td>
<td class="px-5 py-3 text-slate-400 font-mono text-xs">[5.50%, 5.80%]</td>
</tr>
<tr class="hover:bg-white/5 transition-colors">
<td class="px-5 py-3 font-medium text-white">평균 세션 시간</td>
<td class="px-5 py-3 text-slate-300">3m 12s</td>
<td class="px-5 py-3 text-slate-300">3m 10s</td>
<td class="px-5 py-3 text-slate-500 font-medium">-1.0%</td>
<td class="px-5 py-3 text-slate-400 font-mono text-xs">[3m 05s, 3m 15s]</td>
</tr>
</tbody>
</table>
</div>
</div>
<form id="analysisForm" class="stitch-glass-panel rounded-xl p-5">
<h3 class="text-base font-bold text-white mb-4">결론 작성</h3>
<div class="space-y-4">
<div class="space-y-2">
<label class="text-xs font-semibold text-slate-300 uppercase tracking-wide">결정</label>
<select id="decision" class="w-full bg-black/30 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-primary appearance-none cursor-pointer">
<option value="deploy_variant">실험군 B 배포</option>
<option value="deploy_control">대조군 유지</option>
<option value="extend_test">실험 연장</option>
<option value="new_test">새 실험 설계</option>
</select>
</div>
<div class="space-y-2">
<label class="text-xs font-semibold text-slate-300 uppercase tracking-wide">결론 요약</label>
<textarea id="conclusion_summary" class="w-full bg-black/30 border border-white/10 rounded-lg px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-primary transition-all min-h-[80px] resize-none" placeholder="결론을 간략히 작성하세요..."></textarea>
</div>
<div class="space-y-2">
<label class="text-xs font-semibold text-slate-300 uppercase tracking-wide">다음 단계</label>
<textarea id="next_steps" class="w-full bg-black/30 border border-white/10 rounded-lg px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-primary transition-all min-h-[60px] resize-none" placeholder="후속 조치를 기록하세요..."></textarea>
</div>
</div>
</form>
</div>
</main>
</div>'''

        extra_scripts = f'''
<script>
const initData = {init_json};
const els = {{
    decision: document.getElementById('decision'),
    conclusion_summary: document.getElementById('conclusion_summary'),
    next_steps: document.getElementById('next_steps')
}};

function collectData() {{
    return {{
        ...initData,
        decision: els.decision.value,
        conclusion_summary: els.conclusion_summary.value,
        next_steps: els.next_steps.value
    }};
}}

function confirmDecision() {{
    stitchSendData({{ ...collectData(), action: 'confirm_decision' }});
}}

function exportCSV() {{
    stitchSendData({{ action: 'export_csv', ...initData }});
}}

['decision', 'conclusion_summary', 'next_steps'].forEach(id => {{
    if (els[id]) {{
        els[id].addEventListener('input', () => stitchDebounce(() => stitchSendData(collectData()), 500));
        els[id].addEventListener('change', () => stitchDebounce(() => stitchSendData(collectData()), 500));
    }}
}});

setTimeout(() => stitchSendData(collectData()), 100);
</script>'''

        html = self._build_html(body_html, component_type="analysis_data",
                                 extra_scripts=extra_scripts,
                                 body_class="bg-transparent h-full")
        components.html(html, height=height, scrolling=True)

    # -------------------------------------------------------------------------
    # UTILITY COMPONENTS
    # -------------------------------------------------------------------------

    def render_toast(self, message: str, toast_type: str = "success",
                     duration: int = 3000, height: int = 80) -> None:
        """토스트 알림 렌더링"""
        type_config = {
            "success": {"icon": "check_circle", "color": "green", "bg": "bg-green-500/10", "border": "border-green-500/30", "text": "text-green-400"},
            "error": {"icon": "error", "color": "red", "bg": "bg-red-500/10", "border": "border-red-500/30", "text": "text-red-400"},
            "warning": {"icon": "warning", "color": "amber", "bg": "bg-amber-500/10", "border": "border-amber-500/30", "text": "text-amber-400"},
            "info": {"icon": "info", "color": "blue", "bg": "bg-primary/10", "border": "border-primary/30", "text": "text-primary"}
        }
        cfg = type_config.get(toast_type, type_config["info"])

        body_html = f'''
<div id="toastContainer" class="fixed top-4 right-4 z-50">
<div id="toast" class="flex items-center gap-3 px-4 py-3 rounded-xl {cfg["bg"]} {cfg["border"]} border backdrop-blur-xl shadow-lg transform translate-x-full opacity-0 transition-all duration-300">
<span class="material-symbols-outlined {cfg["text"]}">{cfg["icon"]}</span>
<p class="text-sm font-medium text-white">{message}</p>
<button onclick="closeToast()" class="ml-2 text-slate-400 hover:text-white transition-colors">
<span class="material-symbols-outlined text-lg">close</span>
</button>
</div>
</div>'''

        extra_scripts = f'''
<script>
const toast = document.getElementById('toast');
setTimeout(() => {{
    toast.classList.remove('translate-x-full', 'opacity-0');
}}, 100);
setTimeout(() => {{
    closeToast();
}}, {duration});
function closeToast() {{
    toast.classList.add('translate-x-full', 'opacity-0');
}}
</script>'''

        html = self._build_html(body_html, component_type="toast",
                                 extra_scripts=extra_scripts, body_class="bg-transparent")
        components.html(html, height=height, scrolling=False)

    def render_loading_state(self, message: str = "로딩 중...",
                              height: int = 200) -> None:
        """로딩 상태 컴포넌트"""
        body_html = f'''
<div class="flex flex-col items-center justify-center h-full gap-4 py-8">
<div class="relative">
<div class="w-12 h-12 border-4 border-white/10 border-t-primary rounded-full animate-spin"></div>
<div class="absolute inset-0 w-12 h-12 border-4 border-transparent border-t-primary/30 rounded-full animate-ping"></div>
</div>
<p class="text-sm text-slate-400 font-medium">{message}</p>
</div>'''

        html = self._build_html(body_html, component_type="loading", body_class="bg-transparent")
        components.html(html, height=height, scrolling=False)

    def render_empty_state(self, title: str, description: str,
                            icon: str = "inbox", action_label: Optional[str] = None,
                            height: int = 300) -> None:
        """빈 상태 컴포넌트"""
        action_html = ""
        if action_label:
            action_html = f'''
<button class="stitch-btn-primary mt-4" onclick="stitchSendData({{action: 'empty_state_action'}})">
{action_label}
</button>'''

        body_html = f'''
<div class="flex flex-col items-center justify-center h-full gap-4 py-8 text-center">
<div class="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center">
<span class="material-symbols-outlined text-3xl text-slate-500">{icon}</span>
</div>
<div class="space-y-2">
<h3 class="text-lg font-bold text-white">{title}</h3>
<p class="text-sm text-slate-400 max-w-xs">{description}</p>
</div>
{action_html}
</div>'''

        html = self._build_html(body_html, component_type="empty_state", body_class="bg-transparent")
        components.html(html, height=height, scrolling=False)

    def render_stat_card(self, title: str, value: str,
                          change: Optional[str] = None,
                          icon: str = "analytics",
                          trend: str = "neutral",
                          height: int = 120) -> None:
        """통계 카드 컴포넌트"""
        trend_config = {
            "up": {"color": "text-green-400", "icon": "trending_up", "bg": "bg-green-500/10"},
            "down": {"color": "text-red-400", "icon": "trending_down", "bg": "bg-red-500/10"},
            "neutral": {"color": "text-slate-400", "icon": "trending_flat", "bg": "bg-white/5"}
        }
        cfg = trend_config.get(trend, trend_config["neutral"])

        change_html = ""
        if change:
            change_html = f'''
<div class="flex items-center gap-1 {cfg["color"]} text-sm">
<span class="material-symbols-outlined text-sm">{cfg["icon"]}</span>
<span class="font-medium">{change}</span>
</div>'''

        body_html = f'''
<div class="stitch-glass-panel rounded-xl p-4 hover:bg-white/10 transition-colors h-full">
<div class="flex justify-between items-start mb-3">
<p class="text-xs font-medium text-slate-400 uppercase tracking-wide">{title}</p>
<div class="p-1.5 rounded-lg {cfg["bg"]}">
<span class="material-symbols-outlined text-lg {cfg["color"]}">{icon}</span>
</div>
</div>
<div class="flex items-end justify-between">
<p class="text-2xl font-bold text-white tracking-tight">{value}</p>
{change_html}
</div>
</div>'''

        html = self._build_html(body_html, component_type="stat_card", body_class="bg-transparent")
        components.html(html, height=height, scrolling=False)

    def render_progress_steps(self, steps: list, current_step: int = 0,
                               height: int = 80) -> None:
        """진행 단계 표시 컴포넌트"""
        steps_html = ""
        for i, step in enumerate(steps):
            if i < current_step:
                # 완료된 단계
                step_class = "bg-green-500 text-white"
                text_class = "text-white"
                icon = "check"
            elif i == current_step:
                # 현재 단계
                step_class = "bg-primary text-white shadow-[0_0_10px_rgba(90,137,246,0.5)]"
                text_class = "text-white font-bold"
                icon = str(i + 1)
            else:
                # 미완료 단계
                step_class = "bg-white/10 text-slate-500"
                text_class = "text-slate-500"
                icon = str(i + 1)

            connector_html = ""
            if i < len(steps) - 1:
                connector_class = "bg-green-500" if i < current_step else "bg-white/10"
                connector_html = f'<div class="w-8 lg:w-16 h-0.5 {connector_class}"></div>'

            if icon == "check":
                icon_html = f'<span class="material-symbols-outlined text-sm">check</span>'
            else:
                icon_html = f'<span class="text-xs font-bold">{icon}</span>'

            steps_html += f'''
<div class="flex items-center gap-2">
<div class="flex items-center justify-center w-6 h-6 rounded-full {step_class}">{icon_html}</div>
<span class="text-xs {text_class} hidden sm:inline">{step}</span>
</div>
{connector_html}'''

        body_html = f'''
<div class="flex items-center justify-center gap-2 py-4">
{steps_html}
</div>'''

        html = self._build_html(body_html, component_type="progress_steps", body_class="bg-transparent")
        components.html(html, height=height, scrolling=False)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

# 전역 팩토리 인스턴스 (편의를 위해)
_default_factory: Optional[StitchFactory] = None

def get_factory() -> StitchFactory:
    """기본 팩토리 인스턴스 반환"""
    global _default_factory
    if _default_factory is None:
        _default_factory = StitchFactory()
    return _default_factory

def render_sidebar(active_page: str = "datalab", height: int = 800):
    """편의 함수: 사이드바 렌더링"""
    get_factory().render_sidebar(active_page, height)

def render_hypothesis_wizard(height: int = 850, initial_data: Optional[Dict] = None):
    """편의 함수: 가설 마법사 렌더링"""
    get_factory().render_hypothesis_wizard(height, initial_data)

def render_design_builder(height: int = 900, initial_data: Optional[Dict] = None):
    """편의 함수: 디자인 빌더 렌더링"""
    get_factory().render_design_builder(height, initial_data)

def render_analysis_dashboard(height: int = 900, analysis_data: Optional[Dict] = None):
    """편의 함수: 분석 대시보드 렌더링"""
    get_factory().render_analysis_dashboard(height, analysis_data)

def render_toast(message: str, toast_type: str = "success", duration: int = 3000, height: int = 80):
    """편의 함수: 토스트 알림 렌더링"""
    get_factory().render_toast(message, toast_type, duration, height)

def render_loading_state(message: str = "로딩 중...", height: int = 200):
    """편의 함수: 로딩 상태 렌더링"""
    get_factory().render_loading_state(message, height)

def render_empty_state(title: str, description: str, icon: str = "inbox",
                       action_label: Optional[str] = None, height: int = 300):
    """편의 함수: 빈 상태 렌더링"""
    get_factory().render_empty_state(title, description, icon, action_label, height)

def render_stat_card(title: str, value: str, change: Optional[str] = None,
                     icon: str = "analytics", trend: str = "neutral", height: int = 120):
    """편의 함수: 통계 카드 렌더링"""
    get_factory().render_stat_card(title, value, change, icon, trend, height)

def render_progress_steps(steps: list, current_step: int = 0, height: int = 80):
    """편의 함수: 진행 단계 렌더링"""
    get_factory().render_progress_steps(steps, current_step, height)
