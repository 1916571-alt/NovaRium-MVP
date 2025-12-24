# NovaRium-MVP 구현 작업 목록

## 0단계: 프로젝트 재정비 및 설계 (Refinement & Design)
- [x] 모던 소프트웨어 엔지니어링 원칙 기반 구현 계획 수립 <!-- id: plan -->
- [x] PRD 한글화 및 요구사항 명확화 (`docs/PRD.md`) <!-- id: prd-ko -->
- [x] 작업 목록(Task) 한글화 및 최신화 (`docs/task.md`) <!-- id: task-ko -->

## 1단계: 코드 구조 리팩토링 (Code Restructuring)
> **목표**: 비대한 `scripts/dashboard.py`를 해체하고, `src/` 패키지 구조로 관심사를 분리합니다.

- [x] `src` 디렉토리 및 하위 패키지(`core`, `ui`, `data`, `utils`) 생성 <!-- id: refactor-init -->
- [x] **Core 로직 분리**:
    - [x] `analytics.py` -> `src/core/stats.py` (통계 및 분석 로직) <!-- id: refactor-stats -->
    - [x] `generating_data.py` -> `src/core/simulation.py` (데이터 생성 및 시뮬레이션) <!-- id: refactor-sim -->
- [x] **Data 계층 분리**:
    - [x] `src/data/db.py` (DuckDB 연결 및 쿼리 관리) <!-- id: refactor-db -->
- [x] **UI 컴포넌트 분리**:
    - [x] `src/ui/components.py` (재사용 가능한 UI 위젯) <!-- id: refactor-ui-comp -->
    - [x] `src/ui/pages/` (각 탭/페이지별 모듈화) <!-- id: refactor-pages -->
- [x] **진입점(Entrypoint) 변경**:
    - [x] `src/app.py` 생성 (새로운 앱 실행 파일, `main.py` 대신 사용) <!-- id: refactor-main -->

## 2단계: 핵심 기능 구현 및 복구 (Core Features Recovery)
> **목표**: 리팩토링된 구조 위에서 기존 기능을 정상 동작하도록 복구하고, TDD로 안정성을 확보합니다.

- [x] **데이터 웨어하우스 연결**: `src/data/db.py`를 통해 DB 초기화 및 연결 테스트 <!-- id: feat-db -->
- [x] **대시보드 메인**: `src/app.py` 구현 (기존 Overview 기능 이관) <!-- id: feat-dashboard -->
- [ ] **A/B 테스트 마법사**:
    - [x] Step 1: 가설 설정 UI (전략 탭 및 시각적 변인 설정) <!-- id: feat-wizard-1 -->
    - [x] Step 2: 파워 분석(Sample Size) 및 트래픽 분배 <!-- id: feat-wizard-2 -->
    - [x] Step 3: 데이터 수집 시뮬레이션 준비 <!-- id: feat-wizard-3 -->
    - [ ] Step 4: 시뮬레이션 실행 및 진행률 표시 <!-- id: feat-wizard-4 -->
    - [ ] Step 5: 결과 분석 및 승/패 판정 <!-- id: feat-wizard-5 -->

## 3단계: 테스트 및 품질 향상 (Testing & Quality)
> **목표**: 자동화된 테스트 환경을 구축하고 코드 신뢰성을 높입니다.

- [x] **테스트 환경 설정**: `pytest` 설정 및 `tests/` 디렉토리 정리 <!-- id: test-setup -->
- [x] **단위 테스트 작성**:
    - [x] `src/core/stats.py` (통계 함수 검증) <!-- id: test-stats -->
    - [ ] `src/core/simulation.py` (데이터 생성 로직 검증) <!-- id: test-sim -->
- [ ] **CI 파이프라인 수정**: 변경된 구조에 맞춰 GitHub Actions 워크플로우 업데이트 <!-- id: ci-update -->

## 4단계: 문서화 및 마무리 (Documentation)
- [x] README.md 한글화 및 실행 가이드 업데이트 <!-- id: doc-readme -->
- [ ] 코드 주석 및 독스트링(Docstring) 보완 <!-- id: doc-code -->
- [ ] 최종 회고 및 모던 소프트웨어 엔지니어링 원칙 준수 여부 점검 <!-- id: retrospective -->
