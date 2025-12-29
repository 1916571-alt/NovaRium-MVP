# NovaRium Edu: End-to-End A/B Testing Simulator for Data Analysts

<div align="center">
  <h3>데이터 분석가를 위한 실전 A/B 테스트 & 데이터 마트 구축 프로젝트</h3>
  <p>이론을 넘어 <b>실험 설계부터 데이터 파이프라인(ETL), 분석, 의사결정</b>까지<br>전 과정을 직접 시뮬레이션하며 구축한 개인 포트폴리오 프로젝트입니다.</p>
</div>

---

## 라이브 데모 (Live Demo)

| 서비스 | URL | 설명 |
|--------|-----|------|
| **Dashboard** | https://novarium-mvp-s9fouprzj5apgznzehprcr.streamlit.app | Streamlit 분석 대시보드 |
| **Target App** | https://novarium-mvp.onrender.com | 실험 대상 가상 쇼핑몰 |

> **참고**: 무료 티어 서버(Streamlit Cloud, Render)를 사용하고 있어 첫 접속 시 Cold Start로 30초 정도 소요될 수 있습니다.

---

## 프로젝트 배경 (Why Project?)

### "실무 경험의 닭과 달걀 문제를 해결하다"
데이터 분석가를 준비하며 가장 큰 어려움은 **'실제 트래픽 기반의 A/B 테스트 경험'**을 쌓기 어렵다는 점이었습니다.
이론만으로는 **실험 설계의 난관(Traffic Split, Sample Size)**, **데이터 정합성 문제**, **지표 설정의 모호함**을 체감하기 어렵다고 판단했습니다.

따라서 직접 **가상 쇼핑몰(Target App)**과 **유저 시뮬레이터(Agent Swarm)**를 구축하고, 그 위에서 분석가가 수행해야 할 전체 라이프사이클을 경험할 수 있는 **통합 시뮬레이션 환경**을 개발했습니다.

## 핵심 역량 및 기능 (Key Capabilities)

이 프로젝트를 통해 다음과 같은 **데이터 분석가 핵심 역량**을 실제 코드로 구현했습니다.

### 1. 실험 설계 및 관리 (Experiment Design & Management)
> *Demonstrated Skill: Experimental Design, Hypothesis Testing, Power Analysis*

- **Visual Experiment Builder**: 코딩 없이 직관적으로 대조군(Control)과 실험군(Test)을 설정하고 미리보기(Preview)를 제공합니다.
- **Robust Metrics Framework**:
    - **OEC (Overall Evaluation Criterion)**: 핵심 지표(Primary)와 목표 상승폭(MDE) 설정.
    - **Guardrails**: 매출 하락 등 부작용을 방지하기 위한 안전 장치(Safety Margin) 설정.
- **Statistical Power Analysis**: `scipy`를 활용해 Alpha(유의수준), Power(검정력), Baseline CTR에 따른 **필요 표본 수(Sample Size)**를 자동 계산합니다.

### 2. 데이터 엔지니어링 및 파이프라인 (Data Engineering)
> *Demonstrated Skill: ETL, SQL, Data Warehouse Modeling*

- **DuckDB 기반 DW 구축**: 로컬 OLAP 데이터베이스인 DuckDB를 활용해 Serverless 데이터 웨어하우스를 구축했습니다.
- **Split DB Architecture**:
    - **Warehouse DB**: 영구 데이터 (users, orders, 30일 히스토리)
    - **Experiment DB**: 실험 데이터 (assignments, events, experiments)
- **Log to Mart 파이프라인**:
    - **Raw Data**: 유저 로그(Events), 주문 정보(Orders) 적재.
    - **Data Mart**: 분석하기 쉬운 형태(`daily_metrics`, `user_stats`)로 가공하는 배치(Batch) 작업 자동화.

### 3. 유저 행동 시뮬레이션 (User Simulation)
> *Demonstrated Skill: Data Generation, Behavioral Analysis*

- **Agent Swarm**: 단순 난수 생성이 아닌, **5가지 페르소나(충동형, 신중형, 체리피커 등)**를 가진 AI 에이전트가 확률 모델에 따라 행동합니다.
- **Dynamic Interaction**: 실험 변인(예: 배너 색상 변경, 할인율 증가)에 따라 에이전트의 클릭률(CTR)과 구매율(CVR)이 동적으로 변화하도록 모델링했습니다.

### 4. 연속 실험 루프 (Continuous Experimentation)
> *Demonstrated Skill: Product Analytics, Decision Making*

- **Adoption System**: 실험 성공 시 winning variant를 즉시 프로덕션에 반영
- **Experiment Retrospective**: 실험 종료 후 결과를 DB에 영구 저장하여 포트폴리오로 활용
- **Learning Loop**: 이전 실험 결과를 바탕으로 다음 실험 설계에 반영

---

## 시스템 아키텍처 (Architecture)

**User Flow**부터 **Data Flow**까지의 전체 흐름입니다.

```mermaid
graph TD
    subgraph "Phase 1: Experiment Design"
        Analyst["Analyst"] -->|Step 1| ExpBuilder["Experiment Builder UI"]
        ExpBuilder -->|Define Variant/Metrics| ConfigDB[("Config")]
    end

    subgraph "Phase 2: Execution (Target App)"
        ConfigDB -->|Apply Variant| TargetApp["NovaEats App (FastAPI)"]
        Simulator["Agent Swarm"] -->|Visit & Action| TargetApp
    end

    subgraph "Phase 3: Data Pipeline"
        TargetApp -->|Generate Logs| ExperimentDB[("Experiment DB")]
        WarehouseDB[("Warehouse DB")] -->|Historical Data| Dashboard
    end

    subgraph "Phase 4: Analysis & Decision"
        ExperimentDB -->|Query| Dashboard["Analytics Dashboard"]
        Dashboard -->|P-value & Lift| Decision{"Decision"}
        Decision -->|Win| Adoption["Adopt Variant"]
        Decision -->|Lose/Inconclusive| NextExp["Design Next Experiment"]
    end
```

## 기술 스택 (Tech Stack)

분석 환경과 동일한 **Python 생태계**를 기반으로 구축했습니다.

| Category | Tech Stack | Usage |
|----------|------------|-------|
| **Analysis** | **DuckDB** | 고성능 로컬 OLAP 분석 및 데이터 저장소 |
| **Logic** | **Statsmodels / Scipy** | T-test, Power Analysis 등 통계 검정 엔진 |
| **Visual** | **Streamlit** | 인터랙티브 대시보드 및 실험 설계 도구 |
| **App** | **FastAPI** | 실험 대상 서비스(Target App) 백엔드 구현 |
| **Viz** | **Plotly** | 시계열 데이터 및 분포 시각화 |
| **Cloud DB** | **Supabase (PostgreSQL)** | 클라우드 환경 데이터 영속성 |
| **Hosting** | **Streamlit Cloud + Render** | 무료 티어 클라우드 배포 |

---

## 클라우드 배포 아키텍처 (Cloud Deployment)

로컬 개발 환경을 클라우드로 확장하여 **실제 프로덕션과 유사한 환경**을 구축했습니다.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Cloud Architecture                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────────┐         ┌──────────────────┐             │
│   │  Streamlit Cloud │         │     Render       │             │
│   │  (Dashboard)     │◄───────►│   (Target App)   │             │
│   │                  │  HTTP   │    FastAPI       │             │
│   └────────┬─────────┘         └────────┬─────────┘             │
│            │                            │                        │
│            │     ┌──────────────────┐   │                        │
│            └────►│    Supabase      │◄──┘                        │
│                  │   (PostgreSQL)   │                            │
│                  │                  │                            │
│                  │  - assignments   │                            │
│                  │  - events        │                            │
│                  │  - experiments   │                            │
│                  │  - adoptions     │                            │
│                  └──────────────────┘                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 서비스 연결 구성

| 서비스 | 역할 | 환경변수 |
|--------|------|----------|
| **Streamlit Cloud** | 분석 대시보드 UI | `DB_MODE=supabase`, `DATABASE_URL`, `TARGET_APP_URL` |
| **Render** | Target App (FastAPI) | `DB_MODE=supabase`, `DATABASE_URL` |
| **Supabase** | PostgreSQL 데이터베이스 | Connection Pooler (Transaction Mode) |

### 환경변수 설정

**Streamlit Cloud** (`.streamlit/secrets.toml` 또는 Dashboard Settings):
```toml
DB_MODE = "supabase"
DATABASE_URL = "postgresql://postgres.xxxx:password@xxxx.pooler.supabase.com:6543/postgres"
TARGET_APP_URL = "https://novarium-mvp.onrender.com"
```

**Render** (Environment Variables):
```
DB_MODE=supabase
DATABASE_URL=postgresql://postgres.xxxx:password@xxxx.pooler.supabase.com:6543/postgres
```

### 왜 이 구성을 선택했나?

1. **Supabase (PostgreSQL)**: DuckDB는 파일 기반이라 서버 재시작 시 데이터 유실. PostgreSQL로 영속성 확보.
2. **Connection Pooler**: Serverless 환경에서 커넥션 수 제한 문제 해결 (Transaction Mode 사용).
3. **서비스 분리**: Dashboard와 Target App을 분리하여 독립적 스케일링 가능.
4. **무료 티어 활용**: 포트폴리오 목적으로 비용 없이 운영 가능.

## 실행 방법 (How to Run)

누구나 로컬 환경에서 이 분석 시뮬레이터를 실행해볼 수 있습니다.

### 1. 설치 (Installation)

```bash
# Clone Repository
git clone https://github.com/1916571-alt/NovaRium-MVP.git
cd NovaRium-MVP

# Install Dependencies
pip install -r requirements.txt
```

### 2. 초기 데이터 설정 (Initial Data Setup)

```bash
# DB 스키마 및 초기 데이터 생성
python src/data/db.py

# 30일 히스토리 데이터 생성 (선택사항)
python scripts/data/generate_history.py
```

### 3. 실행 (Run Simulator)

```bash
# Target App 실행 (별도 터미널)
python target_app/main.py

# Streamlit 대시보드 실행 (Main Entrypoint)
streamlit run src/app.py
```

브라우저에서 `localhost:8501`이 열리면 **"마스터 클래스 (Lab)"** 탭으로 이동하여 나만의 A/B 테스트를 시작해보세요.

---

## 프로젝트 구조 (Structure)

```
NovaRium-MVP/
├── src/                        # 메인 소스 코드
│   ├── app.py                  # Streamlit 앱 (Entrypoint)
│   ├── core/                   # 핵심 비즈니스 로직
│   │   ├── stats.py            # 통계 검정 및 표본 계산 엔진
│   │   ├── simulation.py       # 유저 행동 시뮬레이터
│   │   └── mart_builder.py     # 데이터 마트 SQL 생성기
│   ├── data/                   # 데이터베이스 관리
│   │   └── db.py               # DB 연결 및 스키마 설정
│   ├── ui/                     # Streamlit UI 컴포넌트
│   └── utils/                  # 유틸리티 함수
│
├── target_app/                 # 실험 대상 웹 앱 (FastAPI)
│   ├── main.py                 # FastAPI 서버
│   ├── templates/              # Jinja2 HTML 템플릿
│   └── static/                 # CSS, JS 등 정적 파일
│
├── agent_swarm/                # AI 에이전트 시뮬레이션
│   ├── agent.py                # 에이전트 클래스
│   └── behaviors.py            # 페르소나별 행동 전략
│
├── data/                       # 데이터 파일 (gitignore)
│   ├── db/                     # DuckDB 파일
│   │   ├── novarium_experiment.db   # 실험 데이터
│   │   └── novarium_warehouse.db    # 영구 데이터
│   └── raw/                    # 원본 CSV 파일
│       ├── users.csv
│       ├── orders.csv
│       └── ab_test_logs.csv
│
├── scripts/                    # 유틸리티 스크립트
│   ├── data/                   # 데이터 생성
│   │   └── generate_history.py # 히스토리 데이터 생성
│   ├── db/                     # DB 마이그레이션
│   └── utils/                  # ETL 등 유틸리티
│
├── tests/                      # 테스트 코드
│   ├── test_analytics.py
│   ├── test_behaviors.py
│   └── test_simulation.py
│
├── docs/                       # 문서
│   └── design/                 # 설계 문서
│       ├── PRD.md
│       └── Ideation.md
│
├── requirements.txt            # Python 의존성
└── README.md                   # 프로젝트 문서
```

---

## 데이터베이스 스키마 (Database Schema)

### Warehouse DB (영구 데이터)
| Table | Description |
|-------|-------------|
| `users` | 사용자 정보 (user_id, joined_at, segment) |
| `orders` | 주문 이력 (order_id, user_id, amount, created_at) |

### Experiment DB (실험 데이터)
| Table | Description |
|-------|-------------|
| `assignments` | 실험 그룹 할당 (user_id, experiment_id, variant, run_id) |
| `events` | 사용자 행동 로그 (event_id, user_id, event_name, value) |
| `experiments` | 실험 메타데이터 및 결과 (hypothesis, metrics, p_value, decision) |
| `adoptions` | 채택된 실험 기록 (experiment_id, variant_config) |

---

## 패치 노트 (Patch Notes)

### v2.0 — Cloud Integration & Auth System (2025-12-30)

> 로컬 프로토타입에서 **프로덕션 레디 클라우드 애플리케이션**으로의 대규모 전환

#### [New] JWT 기반 인증 시스템
**도전 과제**: 여러 사용자가 동시에 플랫폼을 사용하고, 브라우저 새로고침 시에도 로그인 상태가 유지되어야 했습니다.

**해결 방안**:
- `PyJWT` 라이브러리를 활용한 **Stateless JWT 토큰** 인증 구현
- 비밀번호 `bcrypt` 해싱으로 보안 강화
- 회원가입 시 **이메일 형식 검증** 및 **비밀번호 강도 검사** (8자 이상, 영문+숫자)
- `st.query_params`를 활용한 **로그인 상태 영속성** (브라우저 새로고침 대응)
- 7일 만료 토큰으로 사용자 편의성과 보안 균형

#### [New] Supabase 클라우드 마이그레이션
**도전 과제**: 로컬 DuckDB는 서버 재시작 시 데이터 유실, 동시 접근 시 파일 잠금 문제가 발생했습니다.

**해결 방안**:
- **Supabase PostgreSQL**로 완전 이전 (Connection Pooler 적용)
- 고객 1,000명 + 주문 10,000건 데이터 **무결성 검증 완료**
- `scripts/migrate_data_to_supabase.py` 마이그레이션 스크립트 제공
- 환경변수 `DB_MODE`로 로컬(DuckDB) ↔ 클라우드(Supabase) **자동 스위칭**

#### [Improved] Twelve-Factor App 아키텍처
**도전 과제**: 환경별 설정이 코드에 하드코딩되어 있어 배포 시 수동 수정이 필요했습니다.

**해결 방안**:
- `src/data/database.py` **추상화 계층** 도입 (DB 벤더 독립적 인터페이스)
- `.env` 기반 환경 설정 분리 (개발/스테이징/프로덕션)
- `requirements.txt` 의존성 명시적 선언
- 로그 레벨 환경변수 제어 (`LOG_LEVEL`)

#### [Technical] 버그 수정 및 안정화
| 이슈 | 원인 | 해결 |
|------|------|------|
| DuckDB IO Error | 동시 접근 시 파일 잠금 | PostgreSQL 전환 + Connection Pool |
| Windows 인코딩 오류 | CP949 vs UTF-8 충돌 | `encoding='utf-8'` 명시 |
| Streamlit 세션 유실 | 페이지 전환 시 상태 초기화 | `st.session_state` 초기화 로직 개선 |

#### [New] 디자인 시스템 문서화
- **'Cosmic Glass' 테마** 디자인 브리프 작성 (`docs/STITCH_DESIGN_BRIEF.md`)
- 색상 팔레트, 타이포그래피, 컴포넌트 스타일 가이드 정의
- Stitch AI 플랫폼 연동을 위한 기술 컨텍스트 문서화
- UX 개선 포인트 6가지 도출 및 우선순위 정리

---

### 향후 업데이트 계획 (Next Steps)

| 우선순위 | 항목 | 설명 |
|----------|------|------|
| 🔥 P1 | **Cosmic Glass 테마 UI 적용** | Stitch 제안 기반 전면 UI 리뉴얼 |
| 🔥 P1 | 실험 위저드 UX 개선 | 4단계 프로세스 직관성 향상 |
| P2 | 대시보드 드릴다운 기능 | Summary → Detail 탐색 경험 |
| P2 | 소셜 로그인 연동 | Google, GitHub OAuth |
| P3 | 모바일 반응형 최적화 | 차트 및 레이아웃 개선 |

---

### v1.0 — Initial Release (2025-12)
- A/B 테스트 시뮬레이션 코어 기능 구현
- DuckDB 기반 로컬 데이터 웨어하우스
- Agent Swarm 유저 행동 시뮬레이션
- Streamlit 대시보드 + FastAPI Target App

---

<div align="center">
  <p>Developed with care by <b>Geonyul Shin</b></p>
  <p><i>Building Bridges Between Theory and Practice.</i></p>
</div>
