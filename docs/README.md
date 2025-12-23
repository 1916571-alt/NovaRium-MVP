# 🎓 NovaRium Edu: A/B 테스트 마스터 클래스

> **"책으로만 배우는 A/B 테스트는 그만. 직접 경험하며 배우세요."**

**NovaRium Edu**는 주니어 데이터 분석가와 PM을 위한 **인터랙티브 A/B 테스트 시뮬레이터**입니다.  
가설 설정부터 데이터 수집, 그리고 P-value 계산까지. 실험의 전체 수명주기(Lifecycle)를 직접 시뮬레이션하며 학습할 수 있습니다.

![App Screenshot](https://via.placeholder.com/800x400?text=NovaRium+Edu+Dashboard)

## 🚀 주요 기능 (Features)

### 1. 실전형 5단계 마스터 클래스 (5-Step Wizard)
데이터 분석가가 실제로 일하는 프로세스를 그대로 구현했습니다:
-   **Step 1 (가설 설정)**: 'NovaEats' 앱의 문제를 정의하고, **핵심 지표(OEC)**와 **가드레일 지표**를 설정합니다.
-   **Step 2 (실험 설계)**: 통계적 유의성을 위해 필요한 **필요 표본 수(Sample Size)**를 계산합니다. (Power Analysis)
-   **Step 3 (트래픽 분배)**: 유저 ID가 해시(Hash) 함수를 통해 A/B 그룹으로 나뉘는 과정을 시각적으로 확인합니다.
-   **Step 4 (데이터 수집)**: 가상 유저 1,000명을 주입하고, 실시간으로 DB(`duckdb`)에 로그가 쌓이는 것을 경험합니다.
-   **Step 5 (결과 분석)**: SQL을 직접 실행해 데이터를 집계하고, **P-value**를 통해 실험의 성공/실패를 판단합니다.

### 2. 실험 회고록 (Experiment Retrospective)
-   **단순 저장 그 이상**: 실험마다 `Target`, `Guardrail Indicators`, `Sample Size` 등 상세 설계 정보를 기록합니다.
-   **상세 리포트 (Drill-down)**: 클릭 한 번으로 실험의 전 과정(설계부터 P-value까지)을 한눈에 복기할 수 있는 성적표를 제공합니다.
-   **카테고리 필터링**: '메인 배너', '결제 페이지' 등 관심 영역별로 실험 기록을 필터링하여 성장 과정을 확인하세요.

## 🛠️ 시작하기 (Getting Started)

### 필수 요구사항
-   Python 3.8 이상
-   Pip

### 설치 및 실행

1.  **저장소 복제 (Clone)**:
    ```bash
    git clone https://github.com/1916571-alt/NovaRium-MVP.git
    cd NovaRium-MVP
    ```

2.  **라이브러리 설치**:
    ```bash
    # 가상환경 생성 (권장)
    python -m venv venv
    
    # 의존성 설치
    pip install streamlit duckdb pandas plotly scipy
    ```

3.  **데이터베이스 초기화**:
    ```bash
    python scripts/setup_warehouse.py
    ```

4.  **앱 실행**:
    ```bash
    streamlit run scripts/dashboard.py
    ```

## 📂 프로젝트 구조 (Project Structure)
-   `scripts/dashboard.py`: 메인 애플리케이션 (Streamlit)
-   `scripts/setup_warehouse.py`: DB 초기화 스크립트
-   `novarium_local.db`: 로컬 분석용 데이터베이스 (DuckDB)
-   `raw_data/`: 초기 데이터셋 (users, orders)

## 📅 Patch Notes

### 2025-12-23 Update (Comprehensive)
**"Safety, Realism, and Reliability"**

1.  **🛡️ Guardrail Metrics (가드레일 지표)**
    -   실험의 부작용을 감지하기 위한 안전 장치 도입 (Refund Rate, App Crash Rate).
    -   Step 1에서 Primary(OEC) 지표와 Guardrail 지표를 함께 설정하도록 UX 개선.
    -   Step 4 분석 시, Guardrail 지표가 임계치(Threshold)를 초과하면 **"조기 종료 경고(Early Stopping)"** 발령.

2.  **🤖 Agent Swarm 2.0 (스마트 에이전트)**
    -   **5가지 페르소나**: 충동형(Impulsive), 계산형(Calculator), 윈도우쇼핑(Browser), 목적형(Mission), 신중형(Cautious) 도입.
    -   **동적 분포 조정**: 사용자가 슬라이더를 통해 에이전트 성향 비율을 직접 조정 가능.
    -   **실전 검증**: 에이전트 투입 후 실제 DB 기록 여부를 검증하는 로직 추가.

3.  **📊 Monitoring Dashboard (모니터링 강화)**
    -   **데이터 보존**: 실험 데이터(`sim_*`)와 히스토리 데이터(`user_hist_*`)를 분리하여, 실험 실행 시 모니터링 데이터가 삭제되지 않도록 수정.
    -   **Crisis Alert**: 최근 3일간 CTR 급락 시 경고 발생 및 "실험으로 바로 해결하기" 숏컷 제공.
    -   **30일 트렌드**: KPI 카드가 오늘 하루가 아닌 최근 30일 평균을 보여주도록 개선.

4.  **🔄 Dynamic Metric Integration**
    -   선택한 지표(CTR vs CVR)에 따라 시뮬레이션 이벤트 생성 및 통계 분석 로직이 자동으로 변경됨.

---
**NovaRium Edu** - Built for detailed A/B testing education.
