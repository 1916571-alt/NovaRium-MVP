import streamlit as st
import streamlit.components.v1 as components
import json

def render_hypothesis_wizard(height=800, initial_data=None):
    """
    실험 가설 설정 마법사 컴포넌트 (Step 1)
    PostMessage를 통해 Streamlit session_state와 양방향 통신

    Args:
        height: iframe 높이
        initial_data: dict with keys: exp_name, exp_owner, independent_var, target_audience,
                      success_metric, hypothesis_reason, confidence_level
    """
    # 기본값 설정
    data = initial_data or {}
    exp_name = data.get('exp_name', '체크아웃 흐름 최적화 V2')
    exp_owner = data.get('exp_owner', '김연구 박사')
    independent_var = data.get('independent_var', '')
    target_audience = data.get('target_audience', '')
    success_metric = data.get('success_metric', '전환율 (Conversion Rate)')
    hypothesis_reason = data.get('hypothesis_reason', '')
    confidence_level = data.get('confidence_level', 95)

    # JSON으로 초기값 전달
    init_json = json.dumps({
        'exp_name': exp_name,
        'exp_owner': exp_owner,
        'independent_var': independent_var,
        'target_audience': target_audience,
        'success_metric': success_metric,
        'hypothesis_reason': hypothesis_reason,
        'confidence_level': confidence_level
    }, ensure_ascii=False)

    html_content = f"""
<!DOCTYPE html>
<html class="dark" lang="ko">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<link href="https://fonts.googleapis.com" rel="preconnect"/>
<link crossorigin="" href="https://fonts.gstatic.com" rel="preconnect"/>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&amp;family=Noto+Sans+KR:wght@400;500;600;700&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<script>
    tailwind.config = {{
        darkMode: "class",
        theme: {{
            extend: {{
                colors: {{ "primary": "#5586f6", "background-light": "#f5f6f8", "background-dark": "#0a0b14" }},
                fontFamily: {{ "display": ["Space Grotesk", "sans-serif"], "body": ["Noto Sans KR", "sans-serif"] }},
                backgroundImage: {{ 'cosmic-gradient': 'radial-gradient(circle at 50% 0%, rgba(85, 134, 246, 0.15) 0%, rgba(10, 11, 20, 0) 70%)' }}
            }}
        }}
    }}
</script>
<style>
    .stitch-glass-panel {{ background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.08); box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5); }}
    .stitch-floating-input:focus ~ label, .stitch-floating-input:not(:placeholder-shown) ~ label {{ transform: translateY(-1.75rem) scale(0.85); color: #5586f6; }}
    .stitch-floating-input:focus {{ box-shadow: 0 0 15px rgba(85, 134, 246, 0.25); }}
    input[type=range]::-webkit-slider-thumb {{ -webkit-appearance: none; height: 20px; width: 20px; border-radius: 50%; background: #5586f6; cursor: pointer; box-shadow: 0 0 10px rgba(85, 134, 246, 0.8); margin-top: -8px; }}
    input[type=range]::-webkit-slider-runnable-track {{ width: 100%; height: 4px; cursor: pointer; background: rgba(255,255,255,0.1); border-radius: 2px; }}
    .save-indicator {{ opacity: 0; transition: opacity 0.3s; }}
    .save-indicator.show {{ opacity: 1; }}
</style>
</head>
<body class="bg-transparent font-body text-white relative overflow-x-hidden" style="margin:0; padding:0;">
<div class="relative z-10 flex flex-col">
<main class="container mx-auto px-4 py-4 max-w-5xl flex flex-col gap-6">
<div class="flex flex-col gap-2">
    <div class="flex items-center justify-between">
        <h1 class="text-2xl font-display font-bold text-white tracking-tight">가설 설정</h1>
        <span id="saveIndicator" class="save-indicator text-xs text-green-400 flex items-center gap-1">
            <span class="material-symbols-outlined text-sm">check_circle</span> 자동 저장됨
        </span>
    </div>
    <p class="text-gray-400 font-display text-sm">A/B 테스트를 위한 과학적 근거를 정의하세요.</p>
</div>
<div class="stitch-glass-panel rounded-2xl p-8 relative overflow-hidden group"><div class="absolute -top-24 -right-24 w-64 h-64 bg-primary/10 rounded-full blur-[80px] group-hover:bg-primary/15 transition-all duration-700"></div>
<form id="hypothesisForm" class="flex flex-col gap-10 relative z-10">
<div class="grid grid-cols-1 md:grid-cols-2 gap-8">
    <div class="relative pt-2">
        <input class="stitch-floating-input block w-full px-4 py-3 bg-black/30 border border-white/10 rounded-lg text-white appearance-none focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary transition-all peer" id="exp_name" placeholder=" " type="text" value=""/>
        <label class="absolute left-4 top-5 text-gray-400 text-base duration-300 origin-[0] pointer-events-none" for="exp_name">실험 명칭</label>
    </div>
    <div class="relative pt-2">
        <input class="stitch-floating-input block w-full px-4 py-3 bg-black/30 border border-white/10 rounded-lg text-white appearance-none focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary transition-all peer" id="exp_owner" placeholder=" " type="text" value=""/>
        <label class="absolute left-4 top-5 text-gray-400 text-base duration-300 origin-[0] pointer-events-none" for="exp_owner">담당자</label>
    </div>
</div>
<div class="flex flex-col gap-4">
    <div class="flex items-center gap-2">
        <h3 class="text-lg font-bold font-display text-white">가설 정의서</h3>
        <button class="text-gray-400 hover:text-primary transition-colors" title="가설 수립 도움말" type="button"><span class="material-symbols-outlined text-sm">help</span></button>
    </div>
    <div class="bg-black/20 border border-white/10 rounded-xl p-6 md:p-8">
        <div class="flex flex-wrap items-center gap-3 text-lg md:text-xl font-light text-gray-300 leading-loose">
            <span>우리가</span>
            <div class="relative min-w-[200px] flex-1">
                <input id="independent_var" class="w-full bg-white/5 border-b-2 border-primary/50 focus:border-primary text-white px-2 py-1 focus:outline-none transition-colors placeholder-gray-600" placeholder="변수 (예: 버튼 색상)" type="text"/>
            </div>
            <span>을(를) 변경한다면,</span>
            <div class="relative min-w-[180px] flex-1">
                <input id="target_audience" class="w-full bg-white/5 border-b-2 border-primary/50 focus:border-primary text-white px-2 py-1 focus:outline-none transition-colors placeholder-gray-600" placeholder="타겟 고객" type="text"/>
            </div>
            <span>에 대해</span>
            <div class="relative min-w-[200px] flex-1">
                <select id="success_metric" class="w-full bg-black/50 border border-white/10 rounded text-white px-3 py-1.5 focus:outline-none focus:border-primary appearance-none cursor-pointer">
                    <option value="전환율 (Conversion Rate)">전환율 (Conversion Rate)</option>
                    <option value="평균 주문 금액 (AOV)">평균 주문 금액 (AOV)</option>
                    <option value="재방문율 (Retention)">재방문율 (Retention)</option>
                    <option value="클릭률 (CTR)">클릭률 (CTR)</option>
                </select>
            </div>
            <span>이(가) 증가할 것입니다. 그 이유는</span>
            <div class="w-full mt-2">
                <textarea id="hypothesis_reason" class="w-full bg-white/5 border border-white/10 rounded-lg p-3 text-base text-white focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/50 placeholder-gray-600 transition-all resize-none" placeholder="근거를 입력하세요... (예: 어두운 환경에서 밝은 색상이 더 주목을 받기 때문입니다)" rows="2"></textarea>
            </div>
        </div>
    </div>
</div>
<div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
    <div class="flex flex-col gap-4">
        <div class="flex items-center gap-2">
            <h3 class="text-lg font-bold font-display text-white">성공 지표</h3>
            <button class="text-gray-400 hover:text-primary transition-colors" type="button"><span class="material-symbols-outlined text-sm">info</span></button>
        </div>
        <div class="grid grid-cols-2 gap-4">
            <div class="bg-white/5 hover:bg-white/10 border border-white/10 hover:border-primary/50 rounded-xl p-4 transition-all cursor-pointer group/card">
                <div class="flex justify-between items-start mb-2">
                    <span class="material-symbols-outlined text-primary group-hover/card:scale-110 transition-transform">ads_click</span>
                    <span class="text-xs font-bold text-primary bg-primary/10 px-2 py-0.5 rounded uppercase tracking-wider">Primary</span>
                </div>
                <p class="text-sm text-gray-400">주요 KPI</p>
                <p id="primary_metric_display" class="text-white font-bold text-lg">전환율</p>
            </div>
            <div class="bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/30 rounded-xl p-4 transition-all cursor-pointer border-dashed">
                <div class="flex justify-between items-start mb-2">
                    <span class="material-symbols-outlined text-gray-500">add_chart</span>
                </div>
                <p class="text-sm text-gray-500">가드레일 지표</p>
                <p class="text-gray-400 font-medium text-lg">지표 추가</p>
            </div>
        </div>
    </div>
    <div class="flex flex-col gap-4">
        <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
                <h3 class="text-lg font-bold font-display text-white">신뢰 수준 (Confidence Level)</h3>
                <button class="text-gray-400 hover:text-primary transition-colors" type="button"><span class="material-symbols-outlined text-sm">analytics</span></button>
            </div>
            <span id="confidence_display" class="text-primary font-mono font-bold text-xl">95%</span>
        </div>
        <div class="bg-black/20 border border-white/10 rounded-xl p-6 flex flex-col justify-center h-full">
            <input id="confidence_level" class="w-full bg-transparent appearance-none mb-4" max="99" min="80" type="range" value="95"/>
            <div class="flex justify-between text-xs text-gray-500 font-mono">
                <span>80%</span><span>85%</span><span>90%</span><span>95%</span><span>99%</span>
            </div>
            <p class="text-xs text-gray-400 mt-4 leading-relaxed">
                <span class="text-primary font-bold">참고:</span> 신뢰 수준이 높을수록 더 많은 표본과 긴 실험 기간이 필요합니다. 95%가 업계 표준입니다.
            </p>
        </div>
    </div>
</div>
</form></div>
</main></div>

<script>
// 초기 데이터 로드
const initData = {init_json};

// DOM 요소 참조
const elements = {{
    exp_name: document.getElementById('exp_name'),
    exp_owner: document.getElementById('exp_owner'),
    independent_var: document.getElementById('independent_var'),
    target_audience: document.getElementById('target_audience'),
    success_metric: document.getElementById('success_metric'),
    hypothesis_reason: document.getElementById('hypothesis_reason'),
    confidence_level: document.getElementById('confidence_level'),
    confidence_display: document.getElementById('confidence_display'),
    primary_metric_display: document.getElementById('primary_metric_display'),
    saveIndicator: document.getElementById('saveIndicator')
}};

// 초기값 설정
function loadInitialData() {{
    elements.exp_name.value = initData.exp_name || '';
    elements.exp_owner.value = initData.exp_owner || '';
    elements.independent_var.value = initData.independent_var || '';
    elements.target_audience.value = initData.target_audience || '';
    elements.success_metric.value = initData.success_metric || '전환율 (Conversion Rate)';
    elements.hypothesis_reason.value = initData.hypothesis_reason || '';
    elements.confidence_level.value = initData.confidence_level || 95;
    elements.confidence_display.textContent = (initData.confidence_level || 95) + '%';
    updateMetricDisplay();
}}

// 성공 지표 디스플레이 업데이트
function updateMetricDisplay() {{
    const metric = elements.success_metric.value;
    const shortName = metric.split(' (')[0];
    elements.primary_metric_display.textContent = shortName;
}}

// 전체 데이터 수집
function collectFormData() {{
    return {{
        type: 'hypothesis_data',
        exp_name: elements.exp_name.value,
        exp_owner: elements.exp_owner.value,
        independent_var: elements.independent_var.value,
        target_audience: elements.target_audience.value,
        success_metric: elements.success_metric.value,
        hypothesis_reason: elements.hypothesis_reason.value,
        confidence_level: parseInt(elements.confidence_level.value),
        // 가설 문장 자동 생성
        hypothesis: `우리가 ${{elements.independent_var.value}}을(를) 변경한다면, ${{elements.target_audience.value}}에 대해 ${{elements.success_metric.value.split(' (')[0]}}이(가) 증가할 것입니다. 그 이유는 ${{elements.hypothesis_reason.value}}`
    }};
}}

// Streamlit에 데이터 전송
function sendToStreamlit() {{
    const data = collectFormData();
    window.parent.postMessage(data, '*');

    // 저장 표시
    elements.saveIndicator.classList.add('show');
    setTimeout(() => elements.saveIndicator.classList.remove('show'), 2000);
}}

// 디바운스 함수
let debounceTimer;
function debounce(func, delay) {{
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(func, delay);
}}

// 신뢰 수준 슬라이더 업데이트
elements.confidence_level.addEventListener('input', function() {{
    elements.confidence_display.textContent = this.value + '%';
    debounce(sendToStreamlit, 500);
}});

// 성공 지표 변경 시
elements.success_metric.addEventListener('change', function() {{
    updateMetricDisplay();
    debounce(sendToStreamlit, 500);
}});

// 모든 입력 필드에 이벤트 리스너 추가
['exp_name', 'exp_owner', 'independent_var', 'target_audience', 'hypothesis_reason'].forEach(id => {{
    elements[id].addEventListener('input', () => debounce(sendToStreamlit, 500));
}});

// 초기화
loadInitialData();
// 페이지 로드 시 초기 데이터 전송
setTimeout(sendToStreamlit, 100);
</script>
</body></html>
    """
    components.html(html_content, height=height, scrolling=True)

def render_design_builder(height=900, initial_data=None):
    """
    디자인 빌더/캔버스 컴포넌트 (Step 2)

    Args:
        height: iframe 높이
        initial_data: dict with keys: variant_name, hypothesis, traffic_split
    """
    data = initial_data or {}
    variant_name = data.get('variant_name', 'B: 볼드체 헤드라인 테스트')
    hypothesis = data.get('hypothesis', '')
    traffic_split = data.get('traffic_split', 50)

    init_json = json.dumps({
        'variant_name': variant_name,
        'hypothesis': hypothesis,
        'traffic_split': traffic_split
    }, ensure_ascii=False)

    html_content = f"""
<!DOCTYPE html>
<html class="dark" lang="ko">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<link href="https://fonts.googleapis.com" rel="preconnect"/>
<link crossorigin="" href="https://fonts.gstatic.com" rel="preconnect"/>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&amp;family=Noto+Sans+KR:wght@400;500;600;700&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<script>
    tailwind.config = {{
        darkMode: "class",
        theme: {{
            extend: {{
                colors: {{ "primary": "#5a89f6", "background-light": "#f5f6f8", "background-dark": "#101522", "glass": "rgba(17, 19, 24, 0.7)", "glass-border": "rgba(255, 255, 255, 0.08)" }},
                fontFamily: {{ "display": ["Plus Jakarta Sans", "Noto Sans KR", "sans-serif"] }},
                borderRadius: {{ "DEFAULT": "1rem", "lg": "1.5rem", "xl": "2rem", "2xl": "2.5rem", "full": "9999px" }},
                boxShadow: {{ "glow": "0 0 20px rgba(90, 137, 246, 0.15)", "glass": "0 8px 32px 0 rgba(0, 0, 0, 0.3)" }},
                backgroundImage: {{ "cosmic-gradient": "radial-gradient(circle at 50% 0%, #1e2538 0%, #101522 60%)" }}
            }}
        }}
    }}
</script>
<style>
    ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{ background: rgba(255, 255, 255, 0.1); border-radius: 10px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: rgba(255, 255, 255, 0.2); }}
    .stitch-glass-panel {{ background: rgba(22, 27, 38, 0.6); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.08); }}
    .stitch-canvas-grid {{ background-size: 40px 40px; background-image: linear-gradient(to right, rgba(255, 255, 255, 0.03) 1px, transparent 1px), linear-gradient(to bottom, rgba(255, 255, 255, 0.03) 1px, transparent 1px); }}
    .save-indicator {{ opacity: 0; transition: opacity 0.3s; }}
    .save-indicator.show {{ opacity: 1; }}
</style>
</head>
<body class="bg-transparent text-white font-display w-full flex flex-col overflow-hidden selection:bg-primary/30 selection:text-white" style="margin:0; padding:0;">
<div class="px-4 py-3 flex items-center justify-between">
    <div>
        <h1 class="text-2xl font-bold text-white tracking-tight">디자인 빌더</h1>
        <p class="text-slate-400 text-sm">변형을 만들고 실시간으로 미리보기하세요.</p>
    </div>
    <span id="saveIndicator" class="save-indicator text-xs text-green-400 flex items-center gap-1">
        <span class="material-symbols-outlined text-sm">check_circle</span> 자동 저장됨
    </span>
</div>
<main class="flex-1 flex overflow-hidden gap-4 px-4 pb-4 relative z-10">
<aside class="w-80 flex-none flex flex-col stitch-glass-panel rounded-2xl overflow-hidden shadow-glass transition-all duration-300">
    <div class="p-5 border-b border-glass-border bg-white/5 flex justify-between items-center">
        <h3 class="text-sm font-bold text-white uppercase tracking-wider">전략 구성</h3>
        <span class="material-symbols-outlined text-slate-500 text-[18px]">tune</span>
    </div>
    <div class="flex-1 overflow-y-auto p-5 space-y-6">
        <div class="space-y-2">
            <label class="text-xs font-semibold text-slate-300 uppercase tracking-wide">변형 이름</label>
            <input id="variant_name" class="w-full bg-[#1b1f27] border border-[#3b4254] rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all" placeholder="예: B: 신뢰 신호" value=""/>
        </div>
        <div class="space-y-2">
            <label class="text-xs font-semibold text-slate-300 uppercase tracking-wide">가설</label>
            <textarea id="design_hypothesis" class="w-full bg-[#1b1f27] border border-[#3b4254] rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all min-h-[100px] resize-none" placeholder="가설을 입력하세요..."></textarea>
        </div>
        <div class="space-y-4 pt-2">
            <div class="flex justify-between items-center">
                <label class="text-xs font-semibold text-slate-300 uppercase tracking-wide">트래픽 할당</label>
                <span id="traffic_display" class="text-xs font-mono text-primary bg-primary/10 px-2 py-0.5 rounded border border-primary/20">50% / 50%</span>
            </div>
            <div class="relative h-2 bg-[#282d39] rounded-full overflow-hidden">
                <div id="control_bar" class="absolute left-0 top-0 bottom-0 w-1/2 bg-gradient-to-r from-slate-500 to-slate-400"></div>
                <div id="variant_bar" class="absolute right-0 top-0 bottom-0 w-1/2 bg-gradient-to-r from-primary to-blue-400"></div>
                <input id="traffic_split" type="range" min="10" max="90" value="50" class="absolute inset-0 w-full h-full opacity-0 cursor-col-resize z-10"/>
            </div>
            <div class="flex justify-between text-[10px] text-slate-400 font-medium uppercase tracking-wider">
                <span>대조군 (A)</span>
                <span class="text-primary">실험군 (B)</span>
            </div>
        </div>
        <div class="space-y-2 pt-2">
            <label class="text-xs font-semibold text-slate-300 uppercase tracking-wide">타겟 디바이스</label>
            <div class="flex bg-[#1b1f27] p-1 rounded-xl border border-[#3b4254]">
                <button id="device_desktop" class="flex-1 py-1.5 rounded-lg bg-primary text-white shadow-sm flex items-center justify-center">
                    <span class="material-symbols-outlined text-[18px]">desktop_windows</span>
                </button>
                <button id="device_mobile" class="flex-1 py-1.5 rounded-lg text-slate-400 hover:text-white flex items-center justify-center transition-colors">
                    <span class="material-symbols-outlined text-[18px]">smartphone</span>
                </button>
            </div>
        </div>
    </div>
</aside>
<section class="flex-1 relative flex flex-col rounded-2xl overflow-hidden border border-white/5 bg-[#0a0d14] group shadow-inner">
    <div class="absolute inset-0 stitch-canvas-grid opacity-20 pointer-events-none"></div>
    <div class="absolute top-6 left-1/2 -translate-x-1/2 stitch-glass-panel px-4 py-2 rounded-full flex gap-2 z-20 shadow-lg scale-90 md:scale-100 transition-transform">
        <button class="size-9 rounded-full hover:bg-white/10 text-slate-300 hover:text-white flex items-center justify-center transition-colors" title="선택"><span class="material-symbols-outlined text-[20px]">near_me</span></button>
        <button class="size-9 rounded-full bg-primary/20 text-primary border border-primary/20 flex items-center justify-center transition-colors" title="텍스트 편집"><span class="material-symbols-outlined text-[20px]">edit_note</span></button>
        <button class="size-9 rounded-full hover:bg-white/10 text-slate-300 hover:text-white flex items-center justify-center transition-colors" title="이미지 교체"><span class="material-symbols-outlined text-[20px]">image</span></button>
        <div class="w-px h-5 bg-white/10 my-auto mx-1"></div>
        <button class="size-9 rounded-full hover:bg-white/10 text-slate-300 hover:text-white flex items-center justify-center transition-colors" title="실행 취소"><span class="material-symbols-outlined text-[20px]">undo</span></button>
    </div>
    <div class="flex-1 overflow-auto flex items-center justify-center p-10 cursor-grab active:cursor-grabbing">
        <div class="w-full max-w-[800px] bg-white dark:bg-[#0f1218] rounded-xl shadow-2xl overflow-hidden border border-[#2d3342] relative">
            <div class="h-8 bg-[#1e232e] flex items-center px-3 border-b border-[#2d3342]">
                <div class="flex gap-1.5">
                    <div class="size-2.5 rounded-full bg-[#ff5f56]"></div>
                    <div class="size-2.5 rounded-full bg-[#ffbd2e]"></div>
                    <div class="size-2.5 rounded-full bg-[#27c93f]"></div>
                </div>
                <div class="mx-auto w-1/2 h-5 bg-[#111318] rounded text-[10px] flex items-center justify-center text-slate-500 font-mono">acme-corp.com/landing</div>
            </div>
            <div class="relative min-h-[500px] bg-[#0f1218]">
                <div class="grid grid-cols-2 gap-8 p-12 items-center">
                    <div class="space-y-6 relative group/element">
                        <div class="absolute -inset-4 border-2 border-primary/50 rounded-xl bg-primary/5 pointer-events-none animate-pulse"></div>
                        <div class="absolute -top-10 left-0 bg-primary text-white text-[10px] font-bold px-2 py-1 rounded-t-lg rounded-br-lg shadow-sm flex items-center gap-1">
                            <span class="material-symbols-outlined text-[12px]">edit</span>H1 헤드라인 편집 중
                        </div>
                        <h1 class="text-4xl font-extrabold text-white leading-tight outline-none" contenteditable="true">새로운 <span class="text-primary">여정</span>을 지금 시작하세요</h1>
                        <p class="text-slate-400 text-lg leading-relaxed">현대적인 크리에이터를 위해 설계된 차세대 금융 도구를 경험해보세요.</p>
                        <div class="flex gap-4 pt-2">
                            <button class="bg-white text-black px-6 py-3 rounded-full font-bold text-sm hover:bg-gray-200">시작하기</button>
                            <button class="bg-transparent border border-slate-600 text-white px-6 py-3 rounded-full font-bold text-sm hover:bg-white/5">데모 보기</button>
                        </div>
                    </div>
                    <div class="relative aspect-square rounded-2xl overflow-hidden bg-slate-800 border border-slate-700">
                        <img class="w-full h-full object-cover opacity-80" src="https://picsum.photos/seed/tech/400/400"/>
                        <div class="absolute inset-0 bg-primary/20 opacity-0 hover:opacity-100 transition-opacity cursor-pointer flex items-center justify-center border-2 border-primary border-dashed">
                            <span class="bg-black/80 text-white px-3 py-1.5 rounded-full text-xs font-medium backdrop-blur-sm">이미지 교체</span>
                        </div>
                    </div>
                </div>
                <div class="border-y border-white/5 py-8 bg-white/2">
                    <div class="flex justify-center gap-12 opacity-50 grayscale">
                        <div class="h-6 w-20 bg-slate-600 rounded"></div>
                        <div class="h-6 w-20 bg-slate-600 rounded"></div>
                        <div class="h-6 w-20 bg-slate-600 rounded"></div>
                        <div class="h-6 w-20 bg-slate-600 rounded"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div class="absolute bottom-6 left-6 flex gap-2">
        <div class="stitch-glass-panel px-3 py-1.5 rounded-lg flex items-center gap-2 text-xs font-mono text-slate-300">
            <span class="material-symbols-outlined text-[14px]">aspect_ratio</span>1440x900
        </div>
        <div class="stitch-glass-panel px-3 py-1.5 rounded-lg flex items-center gap-2 text-xs font-mono text-slate-300">
            <span class="material-symbols-outlined text-[14px]">zoom_in</span>100%
        </div>
    </div>
</section>
<aside class="w-80 lg:w-96 flex-none flex flex-col stitch-glass-panel rounded-2xl overflow-hidden shadow-glass">
    <div class="p-5 border-b border-glass-border bg-white/5 flex justify-between items-center">
        <h3 class="text-sm font-bold text-white uppercase tracking-wider">실시간 미리보기</h3>
        <div class="flex gap-1 bg-black/40 p-0.5 rounded-lg border border-white/5">
            <button class="p-1 rounded bg-white/10 text-white"><span class="material-symbols-outlined text-[16px]">splitscreen</span></button>
            <button class="p-1 rounded text-slate-500 hover:text-white"><span class="material-symbols-outlined text-[16px]">tab</span></button>
        </div>
    </div>
    <div class="flex-1 flex flex-col overflow-hidden">
        <div class="flex-1 flex flex-col border-b border-white/10 relative group">
            <div class="absolute top-3 left-3 z-10 bg-black/80 text-slate-300 border border-slate-700 px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider">대조군 (A)</div>
            <div class="flex-1 bg-[#0f1218] p-4 overflow-hidden relative grayscale opacity-60">
                <div class="transform scale-75 origin-top-left w-[133%]">
                    <h1 class="text-3xl font-extrabold text-white mb-2">미래에 오신 것을 환영합니다</h1>
                    <p class="text-slate-400 text-sm">모두를 위한 금융 도구.</p>
                </div>
            </div>
        </div>
        <div class="flex-1 flex flex-col relative bg-[#111318]">
            <div class="absolute top-3 left-3 z-10 bg-primary text-white border border-primary/50 px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider shadow-glow">실험군 (B)</div>
            <div class="flex-1 p-4 overflow-hidden relative">
                <div class="transform scale-75 origin-top-left w-[133%]">
                    <h1 class="text-3xl font-extrabold text-white mb-2">새로운 <span class="text-primary">여정</span>을 지금 시작하세요</h1>
                    <p class="text-slate-400 text-sm">차세대 금융 도구를 경험해보세요...</p>
                </div>
            </div>
        </div>
    </div>
    <div class="p-4 border-t border-glass-border bg-white/5">
        <div class="flex items-start gap-3 p-3 bg-primary/10 rounded-xl border border-primary/20">
            <span class="material-symbols-outlined text-primary text-[20px] mt-0.5">auto_awesome</span>
            <div>
                <p class="text-xs font-medium text-white mb-0.5">AI 인사이트</p>
                <p class="text-[11px] text-slate-400 leading-snug">실험군 B의 "여정"이라는 단어가 "미래"보다 감정적 소구력이 높습니다. 예상 전환율 +5%.</p>
            </div>
        </div>
    </div>
</aside>
</main>

<script>
const initData = {init_json};

const elements = {{
    variant_name: document.getElementById('variant_name'),
    design_hypothesis: document.getElementById('design_hypothesis'),
    traffic_split: document.getElementById('traffic_split'),
    traffic_display: document.getElementById('traffic_display'),
    control_bar: document.getElementById('control_bar'),
    variant_bar: document.getElementById('variant_bar'),
    saveIndicator: document.getElementById('saveIndicator'),
    device_desktop: document.getElementById('device_desktop'),
    device_mobile: document.getElementById('device_mobile')
}};

let selectedDevice = 'desktop';

function loadInitialData() {{
    elements.variant_name.value = initData.variant_name || '';
    elements.design_hypothesis.value = initData.hypothesis || '';
    elements.traffic_split.value = initData.traffic_split || 50;
    updateTrafficDisplay();
}}

function updateTrafficDisplay() {{
    const split = parseInt(elements.traffic_split.value);
    elements.traffic_display.textContent = `${{100 - split}}% / ${{split}}%`;
    elements.control_bar.style.width = `${{100 - split}}%`;
    elements.variant_bar.style.width = `${{split}}%`;
}}

function collectFormData() {{
    return {{
        type: 'design_data',
        variant_name: elements.variant_name.value,
        hypothesis: elements.design_hypothesis.value,
        traffic_split: parseInt(elements.traffic_split.value),
        target_device: selectedDevice
    }};
}}

function sendToStreamlit() {{
    const data = collectFormData();
    window.parent.postMessage(data, '*');

    elements.saveIndicator.classList.add('show');
    setTimeout(() => elements.saveIndicator.classList.remove('show'), 2000);
}}

let debounceTimer;
function debounce(func, delay) {{
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(func, delay);
}}

elements.traffic_split.addEventListener('input', function() {{
    updateTrafficDisplay();
    debounce(sendToStreamlit, 500);
}});

['variant_name', 'design_hypothesis'].forEach(id => {{
    elements[id].addEventListener('input', () => debounce(sendToStreamlit, 500));
}});

elements.device_desktop.addEventListener('click', () => {{
    selectedDevice = 'desktop';
    elements.device_desktop.classList.add('bg-primary', 'text-white', 'shadow-sm');
    elements.device_desktop.classList.remove('text-slate-400');
    elements.device_mobile.classList.remove('bg-primary', 'text-white', 'shadow-sm');
    elements.device_mobile.classList.add('text-slate-400');
    debounce(sendToStreamlit, 500);
}});

elements.device_mobile.addEventListener('click', () => {{
    selectedDevice = 'mobile';
    elements.device_mobile.classList.add('bg-primary', 'text-white', 'shadow-sm');
    elements.device_mobile.classList.remove('text-slate-400');
    elements.device_desktop.classList.remove('bg-primary', 'text-white', 'shadow-sm');
    elements.device_desktop.classList.add('text-slate-400');
    debounce(sendToStreamlit, 500);
}});

loadInitialData();
setTimeout(sendToStreamlit, 100);
</script>
</body></html>
    """
    components.html(html_content, height=height, scrolling=True)

def render_analysis_dashboard(height=900):
    """
    분석 대시보드 컴포넌트 (Step 3)
    """
    html_content = """
<!DOCTYPE html>
<html class="dark" lang="ko">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;900&amp;family=Noto+Sans+KR:wght@400;500;600;700&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<script>
    tailwind.config = {
        darkMode: "class",
        theme: {
            extend: {
                colors: { "primary": "#2563f4", "background-light": "#f5f6f8", "background-dark": "#101522" },
                fontFamily: { "display": ["Inter", "Noto Sans KR", "sans-serif"] },
                borderRadius: { "DEFAULT": "0.25rem", "lg": "0.5rem", "xl": "0.75rem", "full": "9999px" },
            }
        }
    }
</script>
<style>
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #101522; }
    ::-webkit-scrollbar-thumb { background: #282d39; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #3b4254; }
    .stitch-glass-panel { background: rgba(16, 21, 34, 0.7); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }
    .stitch-cosmic-bg { background-color: #101522; background-image: radial-gradient(at 0% 0%, rgba(37, 99, 244, 0.15) 0px, transparent 50%), radial-gradient(at 100% 0%, rgba(139, 92, 246, 0.15) 0px, transparent 50%), radial-gradient(at 100% 100%, rgba(37, 99, 244, 0.1) 0px, transparent 50%); background-attachment: fixed; }
</style>
</head>
<body class="font-display text-white bg-transparent flex overflow-hidden" style="margin:0; padding:0;">
<main class="flex-1 overflow-y-auto relative flex flex-col">
<div class="flex-1 px-4 py-4 w-full max-w-7xl mx-auto flex flex-col gap-6">
<div class="flex flex-col gap-4"><div class="flex flex-col gap-2"><h1 class="text-2xl font-bold tracking-tight text-white">분석 결과</h1><p class="text-slate-400 text-sm">통계적 결과를 검토하고 의사 결정을 위한 데이터를 해석하세요.</p></div></div>
<div class="rounded-xl overflow-hidden relative border border-primary/30 shadow-[0_0_20px_rgba(37,99,244,0.15)] group"><div class="absolute inset-0 bg-gradient-to-r from-primary/20 to-purple-600/20 backdrop-blur-xl"></div><div class="relative p-6 lg:p-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6"><div class="flex items-start gap-4"><div class="p-3 rounded-full bg-primary/20 text-primary border border-primary/30 mt-1"><span class="material-symbols-outlined text-2xl">auto_awesome</span></div><div class="space-y-1"><h3 class="text-xl font-bold text-white">유의미한 결과: 실험군 B 배포 권장</h3><p class="text-slate-300 max-w-2xl text-sm leading-relaxed">주요 지표인 <strong>(전환율)</strong>이 98%의 신뢰 수준에서 <span class="text-green-400 font-bold">+5.2%</span>의 통계적으로 유의미한 개선을 보였습니다. 이 결과가 우연일 확률은 매우 낮습니다.</p></div></div><button class="whitespace-nowrap px-5 py-2.5 bg-primary hover:bg-blue-600 text-white font-semibold rounded-lg shadow-lg shadow-primary/25 transition-all flex items-center gap-2">결론 작성하기<span class="material-symbols-outlined text-lg">arrow_forward</span></button></div></div>
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"><div class="stitch-glass-panel rounded-xl p-5 flex flex-col gap-3 group hover:bg-white/10 transition-colors cursor-default"><div class="flex justify-between items-center"><p class="text-slate-400 text-sm font-medium flex items-center gap-1">표본 크기 (Sample Size)<span class="material-symbols-outlined text-slate-500 text-sm cursor-pointer" title="실험에 포함된 총 사용자 수">info</span></p><span class="material-symbols-outlined text-slate-600 group-hover:text-primary transition-colors">groups</span></div><p class="text-2xl font-bold text-white tracking-tight">12,450</p></div><div class="stitch-glass-panel rounded-xl p-5 flex flex-col gap-3 group hover:bg-white/10 transition-colors cursor-default"><div class="flex justify-between items-center"><p class="text-slate-400 text-sm font-medium flex items-center gap-1">전환 상승폭 (Lift)<span class="material-symbols-outlined text-slate-500 text-sm cursor-pointer" title="대조군 대비 실험군의 상대적 차이">info</span></p><span class="material-symbols-outlined text-slate-600 group-hover:text-green-400 transition-colors">trending_up</span></div><div class="flex items-end gap-2"><p class="text-2xl font-bold text-white tracking-tight">+5.2%</p><p class="text-green-400 text-sm font-medium mb-1 flex items-center"><span class="material-symbols-outlined text-sm">arrow_upward</span> 0.15pp</p></div></div><div class="stitch-glass-panel rounded-xl p-5 flex flex-col gap-3 group hover:bg-white/10 transition-colors cursor-default border-green-500/30 bg-green-500/5"><div class="flex justify-between items-center"><p class="text-slate-400 text-sm font-medium flex items-center gap-1">P-값 (P-Value)<span class="material-symbols-outlined text-slate-500 text-sm cursor-pointer" title="귀무가설이 참일 때 이 결과를 관찰할 확률">info</span></p><span class="material-symbols-outlined text-green-400">check_circle</span></div><p class="text-2xl font-bold text-white tracking-tight font-mono">0.02</p><div class="w-full bg-slate-700/50 h-1 rounded-full overflow-hidden"><div class="bg-green-500 h-full w-[98%]"></div></div><p class="text-[10px] text-green-400 font-medium">통계적 유의성 확보 (&lt; 0.05)</p></div><div class="stitch-glass-panel rounded-xl p-5 flex flex-col gap-3 group hover:bg-white/10 transition-colors cursor-default"><div class="flex justify-between items-center"><p class="text-slate-400 text-sm font-medium flex items-center gap-1">검정력 (Power)<span class="material-symbols-outlined text-slate-500 text-sm cursor-pointer" title="효과가 존재할 때 이를 탐지할 확률">info</span></p><span class="material-symbols-outlined text-slate-600 group-hover:text-purple-400 transition-colors">bolt</span></div><p class="text-2xl font-bold text-white tracking-tight">88%</p></div></div>
<div class="grid grid-cols-1 lg:grid-cols-3 gap-6"><div class="lg:col-span-2 stitch-glass-panel rounded-xl p-6 border border-white/10 flex flex-col"><div class="flex items-center justify-between mb-6"><h3 class="text-lg font-bold text-white">전환율 비교 (Conversion Rate)</h3><div class="flex items-center gap-4 text-xs font-medium"><div class="flex items-center gap-2"><span class="size-3 rounded-full bg-slate-600"></span>대조군 (Control)</div><div class="flex items-center gap-2"><span class="size-3 rounded-full bg-primary shadow-[0_0_8px_rgba(37,99,244,0.6)]"></span>실험군 (Variant B)</div></div></div><div class="flex-1 min-h-[300px] flex items-end justify-center gap-16 pb-8 relative border-b border-white/5"><div class="absolute inset-0 flex flex-col justify-between pointer-events-none"><div class="border-t border-dashed border-white/5 w-full h-0"></div><div class="border-t border-dashed border-white/5 w-full h-0"></div><div class="border-t border-dashed border-white/5 w-full h-0"></div><div class="border-t border-dashed border-white/5 w-full h-0"></div><div class="border-t border-dashed border-white/5 w-full h-0"></div></div><div class="flex flex-col items-center gap-3 z-0 w-24 group"><div class="relative w-16 bg-slate-700/50 rounded-t-lg transition-all duration-500 hover:bg-slate-600/60" style="height: 210px;"><div class="absolute -top-8 w-full text-center text-white font-bold text-sm opacity-0 group-hover:opacity-100 transition-opacity">2.10%</div></div><span class="text-sm font-medium text-slate-400">대조군</span></div><div class="flex flex-col items-center gap-3 z-0 w-24 group"><div class="relative w-16 bg-primary rounded-t-lg shadow-[0_0_20px_rgba(37,99,244,0.3)] transition-all duration-500 hover:shadow-[0_0_30px_rgba(37,99,244,0.5)]" style="height: 235px;"><div class="absolute -top-8 w-full text-center text-white font-bold text-sm opacity-0 group-hover:opacity-100 transition-opacity">2.25%</div></div><span class="text-sm font-bold text-white">실험군 B</span></div></div></div><div class="stitch-glass-panel rounded-xl p-6 border border-white/10 flex flex-col"><div class="mb-4"><h3 class="text-lg font-bold text-white">신뢰 구간 (CI)</h3><p class="text-xs text-slate-400 mt-1">95% 신뢰 구간 범위</p></div><div class="flex-1 flex flex-col justify-center gap-8 relative py-4"><div class="absolute inset-0 flex flex-row justify-between pointer-events-none opacity-10"><div class="border-r border-white h-full w-0"></div><div class="border-r border-white h-full w-0"></div><div class="border-r border-white h-full w-0"></div><div class="border-r border-white h-full w-0"></div></div><div class="space-y-2"><div class="flex justify-between text-xs text-slate-500 px-2"><span>1.9%</span><span>2.3%</span></div><div class="relative h-8 flex items-center w-full px-4"><div class="absolute left-[15%] right-[25%] h-0.5 bg-slate-600 rounded-full"></div><div class="absolute left-[15%] h-3 w-0.5 bg-slate-600"></div><div class="absolute right-[25%] h-3 w-0.5 bg-slate-600"></div><div class="absolute left-[55%] size-3 bg-slate-400 rounded-full border-2 border-[#101522] z-10 -ml-1.5"></div></div><p class="text-xs font-medium text-slate-500 text-center">대조군</p></div><div class="space-y-2"><div class="flex justify-between text-xs text-primary/70 px-2"><span>2.1%</span><span>2.4%</span></div><div class="relative h-8 flex items-center w-full px-4"><div class="absolute left-[30%] right-[10%] h-0.5 bg-primary rounded-full shadow-[0_0_8px_rgba(37,99,244,0.5)]"></div><div class="absolute left-[30%] h-3 w-0.5 bg-primary"></div><div class="absolute right-[10%] h-3 w-0.5 bg-primary"></div><div class="absolute left-[70%] size-3 bg-white rounded-full border-2 border-primary z-10 -ml-1.5 shadow-[0_0_10px_white]"></div></div><p class="text-xs font-bold text-white text-center">실험군 B</p></div></div><div class="mt-4 p-3 rounded bg-white/5 text-xs text-slate-300 leading-relaxed border border-white/5"><span class="material-symbols-outlined text-sm align-middle mr-1 text-primary">science</span>구간이 약간 겹치지만, 큰 표본 크기로 인해 차이는 통계적으로 유의미합니다.</div></div></div>
<div class="stitch-glass-panel rounded-xl border border-white/10 overflow-hidden"><div class="px-6 py-4 border-b border-white/10 flex justify-between items-center"><h3 class="text-lg font-bold text-white">상세 지표 분석</h3><button class="text-primary text-sm font-medium hover:text-blue-400">CSV 내보내기</button></div><div class="overflow-x-auto"><table class="w-full text-sm text-left"><thead class="text-xs text-slate-400 uppercase bg-white/5 border-b border-white/5"><tr><th class="px-6 py-3 font-medium">지표</th><th class="px-6 py-3 font-medium">대조군 평균</th><th class="px-6 py-3 font-medium">실험군 평균</th><th class="px-6 py-3 font-medium">차이</th><th class="px-6 py-3 font-medium">95% 신뢰 구간</th></tr></thead><tbody class="divide-y divide-white/5"><tr class="hover:bg-white/5 transition-colors"><td class="px-6 py-4 font-medium text-white flex items-center gap-2">전환율 (Conversion Rate)<span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-primary/20 text-primary border border-primary/20">Primary</span></td><td class="px-6 py-4 text-slate-300">2.10%</td><td class="px-6 py-4 font-bold text-white">2.25%</td><td class="px-6 py-4 text-green-400 font-medium">+5.2%</td><td class="px-6 py-4 text-slate-400 font-mono">[2.15%, 2.35%]</td></tr><tr class="hover:bg-white/5 transition-colors"><td class="px-6 py-4 font-medium text-white">장바구니 담기 비율</td><td class="px-6 py-4 text-slate-300">5.40%</td><td class="px-6 py-4 text-slate-300">5.65%</td><td class="px-6 py-4 text-green-400 font-medium">+4.6%</td><td class="px-6 py-4 text-slate-400 font-mono">[5.50%, 5.80%]</td></tr><tr class="hover:bg-white/5 transition-colors"><td class="px-6 py-4 font-medium text-white">평균 세션 시간</td><td class="px-6 py-4 text-slate-300">3m 12s</td><td class="px-6 py-4 text-slate-300">3m 10s</td><td class="px-6 py-4 text-slate-500 font-medium">-1.0%</td><td class="px-6 py-4 text-slate-400 font-mono">[3m 05s, 3m 15s]</td></tr></tbody></table></div></div>
</div></main></body></html>
    """
    components.html(html_content, height=height, scrolling=True)
