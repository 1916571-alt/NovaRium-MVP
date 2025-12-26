# NovaRium-MVP: 로컬 구현 아키텍처

로컬 환경에서 **가장 빠르게 핵심만 구현하여 "데이터 분석가로서의 실무 역량"을 즉시 증명**할 수 있는 MVP(Minimum Viable Product) 단계의 프로젝트 구조입니다.

이 MVP는 화려한 대시보드보다는 **'데이터의 흐름(Pipeline)'과 '실험의 논리(Logic)'**를 보여주는 데 집중합니다.

---

## 핵심 아키텍처 개요

### Split DB Architecture

데이터 안정성을 위해 **2개의 분리된 DB**를 사용합니다:

```
data/
├── db/
│   ├── novarium_warehouse.db    # 영구 데이터 (users, orders)
│   └── novarium_experiment.db   # 실험 데이터 (assignments, events)
└── raw/
    ├── users.csv                # 원본 사용자 데이터
    ├── orders.csv               # 원본 주문 데이터
    └── ab_test_logs.csv         # 초기 로그 데이터
```

### 왜 DB를 분리했나?

1. **실험 리셋 시 기초 데이터 보존**: 새 실험을 시작할 때 assignments/events를 초기화해도 users/orders는 유지
2. **동시 접근 문제 해결**: Target App이 실험 DB를 잠금해도 Warehouse DB는 읽기 가능
3. **데이터 정합성**: 히스토리 데이터와 실시간 실험 데이터의 명확한 분리

---

## 4단계 데이터 파이프라인

### 1단계: 데이터 생성 (The Generator)

- **기술**: Python + Faker
- **산출물**: `data/raw/` 폴더 내의 CSV 파일들
- **실행**: `python src/core/simulation.py`

```python
# 1,000명의 가상 유저와 주문 이력 생성
python src/core/simulation.py
```

### 2단계: 로컬 데이터베이스 구축 (The Warehouse)

- **기술**: DuckDB
- **산출물**: `data/db/novarium_warehouse.db`, `data/db/novarium_experiment.db`
- **실행**: `python src/data/db.py`

```python
# DB 스키마 생성 및 CSV 로드
python src/data/db.py
```

### 3단계: 히스토리 데이터 생성 (The History)

- **기술**: Python + DuckDB
- **산출물**: 30일간의 과거 실험 데이터
- **실행**: `python scripts/data/generate_history.py`

```python
# 30일간 500명/일 규모의 히스토리 데이터 생성
python scripts/data/generate_history.py
```

### 4단계: 분석 및 실험 검증 (The Analysis)

- **기술**: Streamlit + DuckDB + Scipy
- **산출물**: 인터랙티브 대시보드 및 실험 결과
- **실행**: `streamlit run src/app.py`

---

## MVP로 보여줄 핵심 지표 (JD 대응)

| 분석 항목 | 구현 내용 (MVP) | 채용공고 요구 역량 (JD) |
|-----------|----------------|------------------------|
| **코호트 분석** | 가입 주차별 재주문율(Retention) 테이블 작성 | **Retention, Cohort 이해도** |
| **세그먼트 분석** | 5가지 페르소나별 행동 패턴 분석 | **행동 데이터 기반 세그먼트 정의** |
| **A/B 테스트** | 배너 변형에 따른 CTR/CVR 검증 | **실험 설계 및 성과 측정** |
| **지표 산출** | Lift, P-value, 신뢰구간 자동 계산 | **통계적 유의성 검정** |
| **데이터 파이프라인** | Split DB + ETL 자동화 | **데이터 엔지니어링 역량** |

---

## 프로젝트 구조

```
NovaRium-MVP/
├── src/                        # 메인 소스 코드
│   ├── app.py                  # Streamlit 앱 (Entrypoint)
│   ├── core/                   # 핵심 비즈니스 로직
│   │   ├── stats.py            # 통계 검정 엔진
│   │   ├── simulation.py       # 데이터 생성기
│   │   └── mart_builder.py     # 데이터 마트 SQL
│   ├── data/                   # DB 관리
│   │   └── db.py               # Split DB 설정
│   ├── ui/                     # UI 컴포넌트
│   └── utils/                  # 유틸리티
│
├── target_app/                 # FastAPI 타겟 앱
│   ├── main.py
│   ├── templates/
│   └── static/
│
├── agent_swarm/                # 에이전트 시뮬레이션
│   ├── agent.py
│   └── behaviors.py
│
├── data/                       # 데이터 (gitignore)
│   ├── db/                     # DuckDB 파일
│   └── raw/                    # CSV 파일
│
├── scripts/                    # 유틸리티 스크립트
│   ├── data/                   # 데이터 생성
│   ├── db/                     # DB 마이그레이션
│   └── utils/                  # ETL 등
│
├── tests/                      # 테스트 코드
├── docs/                       # 문서
└── requirements.txt
```

---

## 왜 이 MVP가 효과적인가?

1. **실행 가능성**: 내 노트북에서 지금 당장 시작할 수 있습니다.
2. **전문성**: "저는 로컬에서 분석 환경(DuckDB)을 스스로 구축하고 SQL과 통계를 자유자재로 다룹니다"라는 메시지를 줍니다.
3. **확장성**: 이 MVP가 완성되면 나중에 dbt나 클라우드 환경으로 업그레이드하기 매우 쉽습니다.
4. **데이터 안정성**: Split DB 아키텍처로 실험을 반복해도 기초 데이터가 유실되지 않습니다.

---

## Quick Start

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. DB 초기화
python src/data/db.py

# 3. 히스토리 데이터 생성
python scripts/data/generate_history.py

# 4. Target App 실행 (터미널 1)
python target_app/main.py

# 5. Streamlit 대시보드 실행 (터미널 2)
streamlit run src/app.py
```

브라우저에서 `localhost:8501` 접속 후 **"마스터 클래스 (Lab)"** 탭에서 실험을 시작하세요.

---

> **Update (2025-12-26)**
>
> - Split DB Architecture 적용 (Warehouse vs Experiment)
> - 폴더 구조 재정리 (`data/db/`, `data/raw/`)
> - Continuous Experimentation Loop 구현
> - Adoption System 추가
