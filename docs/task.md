# NovaRium-MVP 구현 작업 목록

## 0단계: 프로젝트 설정 (Project Setup)
- [x] Git 저장소 초기화 및 .gitignore 설정 <!-- id: git-init -->
- [x] GitHub 퍼블릭 리포지토리 생성 및 업로드 <!-- id: git-push -->

## 1단계: 데이터 생성 (The Generator)
- [x] Python 환경 설정 및 라이브러리 설치 (`faker`, `pandas`, `duckdb`, `scipy`) <!-- id: 0 -->
- [x] `generating_data.py` 스크립트 기본 구조 작성 <!-- id: 1 -->
- [x] 유저 데이터 생성 로직 구현 (`users.csv`) <!-- id: 2 -->
- [x] 주문 데이터 생성 로직 구현 (`orders.csv`) <!-- id: 3 -->
- [x] A/B 테스트 로그 생성 로직 구현 (`ab_test_logs.csv`) <!-- id: 4 -->
- [x] `raw_data/` 폴더에 CSV 파일 생성 확인 <!-- id: 5 -->

## 2단계: 로컬 데이터 웨어하우스 (The Warehouse)
- [x] CSV 파일을 DuckDB로 로드하는 스크립트 작성 <!-- id: 6 -->
- [x] `novarium_local.db` 데이터베이스 초기화 <!-- id: 7 -->
- [x] `users`, `orders`, `ab_test_logs` 테이블에 데이터 적재 <!-- id: 8 -->
- [x] 데이터 건수 및 스키마 확인 <!-- id: 9 -->

## 3단계: 대시보드 및 분석 (The Dashboard)
- [x] 라이브러리 설치 (`streamlit`, `plotly`) <!-- id: 10 -->
- [x] `dashboard.py` 프로토타입 생성 (사이드바, 레이아웃) <!-- id: 11 -->
- [x] **Data Explorer** 구현 (테이블 조회 및 필터링) <!-- id: 12 -->
- [x] **SQL Playground** 구현 (양방향 SQL 실행기) <!-- id: 13 -->
- [x] **Overview** 지표 및 차트 구현 (매출 트렌드 등) <!-- id: 14 -->
- [x] **Deep Dive** 분석 시각화 (코호트, A/B 테스트) <!-- id: 15 -->
- [x] 대시보드 최종 실행 테스트 <!-- id: 16 -->

## 4단계: 실전 시뮬레이터 (Simulator & Mock App) [NEW]
- [x] **가상 앱(Mock App) UI** 구현 (홈 화면, 상품 상세 등) <!-- id: 17 -->
- [x] UI 요소별 **실험 생성 트리거** 연동 (버튼 클릭 시 실험 시작) <!-- id: 18 -->
- [x] **실험 설정 마법사** 구현 (주 지표/보조 지표 선택) <!-- id: 19 -->
- [x] 시뮬레이션 엔진 로직 구현 (지표별 데이터 생성 클래스) <!-- id: 20 -->
- [x] 실시간 시각화 대시보드 (Success vs Risk 그래프) <!-- id: 21 -->
- [x] 최종 테스트 및 승리/패배 시나리오 검증 <!-- id: 22 -->

## 5단계: Enterprise SaaS 고도화 (Pro Upgrade) [NEW]
- [x] **Bayesian 엔진** 탑재 (Probability to Win 계산) <!-- id: 23 -->
- [x] **매출 임팩트 계산기** (Revenue Calculator) 구현 <!-- id: 24 -->
- [x] **트래픽 분배 전략** (Allocation Strategy) UI 구현 <!-- id: 25 -->
- [x] 베이지안 확률 분포 시각화 (Density Plot) <!-- id: 26 -->

## 6단계: 교육용 워크플로우 재설계 (Educational Refactor) [NEW]
- [x] **DB 스키마 개편**: `assignments`, `events` 테이블 생성 및 마이그레이션 <!-- id: 27 -->
- [x] **Step 1: 가설/지표**: 기존 UI 교육적 텍스트 보강 <!-- id: 28 -->
- [x] **Step 2: 실험 설계**: `scipy` 기반 Sample Size 계산기 구현 <!-- id: 29 -->
- [x] **Step 3: 샘플링**: Hash 함수 시각화 및 분배 로직 구현 <!-- id: 30 -->
- [x] **Step 4: 로깅 시뮬레이션**: `faker` 연동하여 실제 DB Insert 구현 <!-- id: 31 -->
- [x] **Step 5: 분석 쿼리**: DuckDB 조회 및 P-value 검정 UI 구현 <!-- id: 32 -->

## 7단계: 실험 아카이브 및 포트폴리오 (Archive & Portfolio) [NEW]
- [x] **DB 스키마 추가**: `experiments` 테이블 생성 <!-- id: 33 -->
- [x] **아카이빙 로직**: 실험 종료 시 DB에 결과 저장 (INSERT) <!-- id: 34 -->
- [x] **포트폴리오 페이지**: 과거 실험 내역 리스트/상세 조회 UI 구현 <!-- id: 35 -->
- [x] **UI 폴리싱**: 여백, 폰트, 헤더 등 디자인 디테일 개선 (Presentable하게) <!-- id: 36 -->

## 8단계: 심화 교육 기능 (Advanced Features)
- [x] **Step 1 고도화: 지표 및 가드레일** <!-- id: 37 -->
    - [x] **지표 라이브러리 구축**: CTR, CVR, ROAS 등 핵심 지표와 산식 정의
    - [x] **가드레일(Guardrail) 지표**: 메인 지표(OEC) 외에 부작용을 감지할 보조 지표 선택 기능
    - [x] **지표 가이드 툴팁**: 각 지표의 의미와 사용 사례를 설명하는 툴팁 추가
    - [x] **Step 3 에이전트 튜닝**: 에이전트 유형별(충동/신중 등) 비율 조정 UI 구현
    - [x] **Step 4 분석 고도화**: Primary Metric 동적 반영 및 가드레일 분석 로직 추가

## 9단계: 리팩토링 및 테스트 (Refactoring & Testing) [NEW]
- [x] **모듈 분리**: `dashboard.py`의 로직을 `analytics.py`와 `components.py`로 분리 <!-- id: refactor-1 -->
- [x] **단위 테스트**: `analytics.py`에 대한 Unit Test 작성 (`tests/test_analytics.py`) <!-- id: refactor-2 -->
- [x] **CI/CD 파이프라인**: GitHub Actions를 통한 자동 테스트 설정 (`.github/workflows/ci.yml`) <!-- id: refactor-3 -->
