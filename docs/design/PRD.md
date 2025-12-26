# NovaRium Edu: A/B 테스팅 마스터 클래스 (PRD)

## 1. 프로젝트 개요 (Project Overview)

**NovaRium Edu**는 학생과 주니어 분석가가 A/B 테스트의 전체 워크플로우를 직접 체험하고 학습할 수 있는 **인터랙티브 교육용 시뮬레이터**입니다.

단순한 정적 대시보드가 아니라, 가설 설정부터 실험 설계, 트래픽 분배, 로그 적재, 그리고 통계적 분석에 이르는 전 과정을 "마법사(Wizard)" 모드로 경험하게 합니다.

이 프로젝트는 **'모던 소프트웨어 엔지니어링'** 원칙을 준수하여 개발되며, 사용자와 개발자 모두에게 공학적 사고방식을 함양하는 것을 목표로 합니다.

## 2. 핵심 가치 제안 (Core Value Proposition)

- **실천을 통한 학습 (Learning by Doing)**: 이론으로만 배우던 6단계 실험 과정(가설 -> 설계 -> 샘플링 -> 로깅 -> 분석 -> 채택)을 직접 수행합니다.
- **보이지 않는 것의 시각화 (Visualizing the Invisible)**: 해시(Hash) 알고리즘이 어떻게 사용자를 그룹으로 나누는지, 로그가 데이터베이스에 어떻게 쌓이는지 시각적으로 확인합니다.
- **회고를 통한 성장 (Retrospective Growth)**: 실험이 끝나면 전문적인 "실험 회고록(Experiment Retrospective)"을 자동으로 생성하여 포트폴리오로 활용합니다.
- **공학적 시뮬레이션 (Engineering Simulation)**: 실제 난수 생성 및 통계 라이브러리(`scipy`)를 활용하여 리얼한 데이터를 생성하고 분석합니다.
- **연속 실험 루프 (Continuous Loop)**: 실험 성공 시 즉시 채택(Adoption)하고 다음 실험으로 이어지는 Product Analytics 사이클을 경험합니다.

## 3. 핵심 기능 (Key Features)

### 6단계 마스터 클래스 (Wizard Mode)

1. **가설 및 지표 설정 (Hypothesis & Metrics)**
    - 가상 앱(Mock App, NovaEats)의 문제를 진단하고 가설을 수립합니다.
    - **핵심 지표(Primary/OEC)**와 부작용을 감지할 **가드레일 지표(Guardrail Metrics)**를 선정합니다. (예: 구매율 증가 vs 환불율 증가)

2. **파워 분석 (Power Analysis)**
    - `scipy`를 활용하여 통계적 검정력(Power), 유의 수준(Alpha), 최소 탐지 효과(MDE)에 따른 **필요 표본 크기(Sample Size)**를 계산합니다.

3. **샘플링 및 트래픽 분배 (Sampling)**
    - 결정론적 해시(Deterministic Hash) 함수를 사용하여 트래픽이 고정적이고 재현 가능하게 분배되는 과정을 시각화합니다.

4. **시뮬레이션 및 로깅 (Simulation)**
    - **Agent Swarm** 기술을 활용해 다양한 페르소나(신중형, 충동형 등)를 가진 AI 에이전트들이 가상 앱을 사용하는 행동을 시뮬레이션합니다.
    - 생성된 행동 데이터는 실제 프로덕션 환경처럼 `events`, `assignments` 테이블에 적재됩니다.

5. **분석 및 의사결정 (Analysis)**
    - DuckDB를 이용해 적재된 데이터를 SQL로 집계하고, P-value와 신뢰구간을 계산하여 승리/패배를 판정합니다.

6. **채택 및 회고 (Adoption & Retrospective)**
    - 실험 성공 시 winning variant를 프로덕션에 즉시 반영합니다.
    - 실험 결과를 `experiments` 테이블에 영구 저장하여 포트폴리오로 활용합니다.

### 실험 회고록 (Experiment Portfolio)

- **상세 리포트**: 실험의 맥락(`Target`, `Sample Size`, `Lift`, `P-value`)을 영구 보존합니다.
- **드릴다운 뷰**: 실험 카드를 펼쳐 상세한 "성적표"를 확인하고, 승리한 실험과 패배한 실험을 교훈 삼아 학습합니다.

## 4. 데이터베이스 아키텍처 (Database Architecture)

### Split DB Architecture

데이터 안정성과 실험 유연성을 위해 **2개의 분리된 DB**를 사용합니다:

#### Warehouse DB (`novarium_warehouse.db`)
영구적으로 보존되는 기초 데이터

| Table | Description |
|-------|-------------|
| `users` | 사용자 풀 (user_id, joined_at, segment) |
| `orders` | 과거 구매 이력 (order_id, user_id, amount, created_at) |

#### Experiment DB (`novarium_experiment.db`)
실험별로 리셋 가능한 휘발성 데이터

| Table | Description |
|-------|-------------|
| `assignments` | 실험 그룹 할당 로그 (user_id, experiment_id, variant, run_id, weight) |
| `events` | 사용자 행동 로그 (event_id, user_id, event_name, timestamp, value, run_id) |
| `experiments` | 실험 메타데이터 및 결과 요약 (hypothesis, metrics, p_value, decision, learning_note) |
| `adoptions` | 채택된 실험 기록 (experiment_id, variant_config, adopted_at) |
| `active_experiment` | 현재 활성 실험 상태 |

### 파일 구조

```
data/
├── db/
│   ├── novarium_warehouse.db    # 영구 데이터
│   └── novarium_experiment.db   # 실험 데이터
└── raw/
    ├── users.csv
    ├── orders.csv
    └── ab_test_logs.csv
```

## 5. 기술 스택 (Tech Stack)

| Category | Tech | Purpose |
|----------|------|---------|
| **Frontend** | Streamlit | Python 기반 인터랙티브 UI |
| **Backend** | FastAPI | Target App 서버 |
| **Database** | DuckDB | 로컬 OLAP 분석용 데이터베이스 |
| **Statistics** | Scipy | 정규분포, Z-test 검정 |
| **Visualization** | Plotly | 인터랙티브 차트 |
| **Simulation** | Agent Swarm | 페르소나 기반 유저 행동 시뮬레이션 |

## 6. 개발 가이드라인 (Development Guidelines)

### 테스트 전략 (Testing Strategy)

- **핵심 로직 (Core Logic)**: TDD(테스트 주도 개발) 필수. 모든 비즈니스 로직(통계 계산, 데이터 생성 등)은 단위 테스트로 검증되어야 합니다.
- **UI 테스트**: UI 로직은 수동 검증을 원칙으로 하되, 컴포넌트 단위의 기능은 가능한 테스트합니다.

### 코드 품질 (Code Quality)

- **SOLID 원칙**: 단일 책임 원칙(SRP)을 철저히 준수하여 모듈을 분리합니다.
- **관심사 분리**: UI 코드와 비즈니스 로직, 데이터 접근 계층을 명확히 분리합니다 (`src/ui`, `src/core`, `src/data`).
- **점진적 개선**: 한 번에 완벽한 코드를 짜기보다, 작동하는 코드를 만들고 지속적으로 리팩토링합니다.

### DB 접근 패턴

- **Read**: `run_query(sql, db_type='experiment'|'warehouse')` 함수 사용
- **Write**: `safe_write_execute(sql)` 함수로 Target App과 DB 락 조율
- **Transaction**: 복수 쿼리는 `safe_write_batch(operations)` 사용

---

> **Last Updated**: 2025-12-26
>
> Split DB Architecture, Continuous Experimentation Loop, Adoption System 기능 추가 반영
