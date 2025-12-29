# NovaRium 배포 가이드 (Deployment Guide)

NovaRium을 로컬 개발 환경과 클라우드에 배포하는 방법을 안내합니다.

---

## 📋 목차

1. [아키텍처 개요](#아키텍처-개요)
2. [로컬 개발 환경 설정](#로컬-개발-환경-설정)
3. [클라우드 배포](#클라우드-배포)
4. [환경 변수 관리](#환경-변수-관리)
5. [데이터베이스 설정](#데이터베이스-설정)
6. [트러블슈팅](#트러블슈팅)

---

## 🏗️ 아키텍처 개요

NovaRium은 2개의 애플리케이션으로 구성됩니다:

```
┌─────────────────────────────────────────────────────────────────┐
│                       NovaRium Architecture                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────┐     ┌──────────────────────┐          │
│  │  Streamlit Dashboard │ ◄──► │  FastAPI Target App  │          │
│  │  (src/app.py)        │     │  (target_app/main.py)│          │
│  │  Port: 8501          │     │  Port: 8000          │          │
│  └──────────┬───────────┘     └──────────┬───────────┘          │
│             │                            │                       │
│             └────────────┬───────────────┘                       │
│                          │                                       │
│                          ▼                                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Database Layer                          │  │
│  │   Local: DuckDB (data/db/*.db)                            │  │
│  │   Cloud: PostgreSQL (Supabase)                            │  │
│  │   Auto-switching based on DB_MODE environment variable    │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 💻 로컬 개발 환경 설정

### 1. 필수 요구사항

- Python 3.11+
- Git

### 2. 프로젝트 클론 및 설정

```bash
# 1. 클론
git clone https://github.com/1916571-alt/NovaRium-MVP.git
cd NovaRium-MVP

# 2. 가상환경 생성
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경 변수 설정
cp .env.example .env
# .env 파일 편집 (기본값 그대로 사용 가능)
```

### 3. 로컬 데이터베이스 초기화

```bash
# DuckDB 데이터베이스 초기화
python -c "from src.data.db import setup_all; setup_all()"

# 또는 마이그레이션 스크립트 실행
python scripts/migrate_v2.py --mode duckdb --fresh
```

### 4. 애플리케이션 실행

```bash
# 터미널 1: FastAPI Target App
uvicorn target_app.main:app --reload --port 8000

# 터미널 2: Streamlit Dashboard
streamlit run src/app.py
```

### 5. 접속 확인

- **Dashboard**: http://localhost:8501
- **Target App**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs

---

## ☁️ 클라우드 배포

### 배포 플랫폼 구성

| 컴포넌트 | 플랫폼 | 이유 |
|---------|--------|------|
| Streamlit Dashboard | Streamlit Cloud | 무료, Git 연동 자동 배포 |
| FastAPI Target App | Render.com | 무료 티어, Docker 지원 |
| Database | Supabase | 무료 PostgreSQL, 관리형 |

### Step 1: Supabase 데이터베이스 설정

1. [Supabase](https://supabase.com) 회원가입
2. 새 프로젝트 생성
3. **Project Settings > Database**에서 연결 정보 확인:
   - Connection string (URI) 복사 → `DATABASE_URL`
4. **Project Settings > API**에서:
   - Project URL 복사 → `SUPABASE_URL`
   - anon/public key 복사 → `SUPABASE_KEY`

5. 스키마 마이그레이션:
```bash
# 환경 변수 설정
export DATABASE_URL="postgresql://postgres:PASSWORD@db.PROJECT.supabase.co:5432/postgres"

# 스키마 생성
python scripts/migrate_v2.py --mode postgres --fresh
```

### Step 2: Render.com (FastAPI) 배포

1. [Render.com](https://render.com) 회원가입
2. **New > Web Service** 선택
3. GitHub 리포지토리 연결
4. 설정:
   - **Name**: `novarium-api`
   - **Environment**: Docker
   - **Region**: Oregon (가장 가까운 지역)
   - **Instance Type**: Free

5. **Environment Variables** 추가:
```
DB_MODE=supabase
DATABASE_URL=postgresql://...
SUPABASE_URL=https://...
SUPABASE_KEY=eyJ...
ENV=production
```

6. Deploy 클릭

### Step 3: Streamlit Cloud 배포

1. [Streamlit Cloud](https://share.streamlit.io) 접속
2. **New app** 클릭
3. 설정:
   - **Repository**: 1916571-alt/NovaRium-MVP
   - **Branch**: master
   - **Main file path**: src/app.py

4. **Advanced settings > Secrets**에 추가:
```toml
DB_MODE = "supabase"
DATABASE_URL = "postgresql://..."
SUPABASE_URL = "https://..."
SUPABASE_KEY = "eyJ..."
TARGET_APP_URL = "https://novarium-api.onrender.com"
ENV = "production"
```

5. Deploy 클릭

### 배포 후 확인

- **Dashboard**: https://novarium-mvp.streamlit.app
- **API**: https://novarium-api.onrender.com
- **API Docs**: https://novarium-api.onrender.com/docs

---

## ⚙️ 환경 변수 관리

### Twelve-Factor App 원칙

NovaRium은 [Twelve-Factor App](https://12factor.net/) 원칙을 따릅니다:
- **Factor III**: 설정은 환경 변수에 저장
- **Factor IV**: 백킹 서비스는 연결된 리소스로 취급
- **Factor X**: 개발/스테이징/프로덕션 환경 일치

### 환경 변수 우선순위

1. **Streamlit secrets** (`st.secrets`) - Streamlit Cloud
2. **OS 환경 변수** (`os.getenv`) - Render, 로컬
3. **기본값** - 코드에 정의된 fallback

### 주요 환경 변수

| 변수 | 설명 | 로컬 | 클라우드 |
|------|------|------|---------|
| `ENV` | 환경 모드 | `local` | `production` |
| `DB_MODE` | DB 타입 | `duckdb` | `supabase` |
| `DATABASE_URL` | PostgreSQL 연결 | - | 필수 |
| `TARGET_APP_URL` | FastAPI URL | `http://localhost:8000` | Render URL |
| `ALLOWED_ORIGINS` | CORS 허용 | `*` | Streamlit URL |

### 파일별 설정

| 파일 | 용도 | Git 추적 |
|------|------|---------|
| `.env.example` | 템플릿 (참조용) | ✅ Yes |
| `.env` | 로컬 실제 값 | ❌ No |
| `.streamlit/secrets.toml.example` | Streamlit 템플릿 | ✅ Yes |
| `.streamlit/secrets.toml` | Streamlit 실제 값 | ❌ No |

---

## 🗄️ 데이터베이스 설정

### 자동 스위칭

`src/data/database.py`가 환경에 따라 자동으로 DB를 선택합니다:

```python
from src.data.database import db

# 환경에 관계없이 동일한 API 사용
df = db.query("SELECT * FROM customers")
db.execute("INSERT INTO events ...")
```

### DuckDB (로컬)

```
data/
├── db/
│   ├── novarium_warehouse.db   # 영구 데이터 (customers, orders)
│   └── novarium_experiment.db  # 실험 데이터 (events, experiments)
└── raw/
    ├── users.csv               # 초기 데이터
    └── orders.csv
```

### PostgreSQL (클라우드)

- Supabase 대시보드에서 테이블 확인 가능
- 동일한 스키마 사용 (DuckDB ↔ PostgreSQL 호환)

### 마이그레이션

```bash
# 로컬 DuckDB 마이그레이션
python scripts/migrate_v2.py --mode duckdb

# 클라우드 PostgreSQL 마이그레이션
python scripts/migrate_v2.py --mode postgres

# 마이그레이션 확인
python scripts/migrate_v2.py --mode duckdb --verify
```

---

## 🗂️ 프로젝트 구조

```
NovaRium-MVP/
├── src/                          # 핵심 애플리케이션 코드
│   ├── app.py                    # Streamlit 진입점
│   ├── core/                     # 비즈니스 로직
│   │   ├── stats.py              # 통계 분석
│   │   ├── simulation.py         # 시뮬레이션
│   │   └── mart_builder.py       # 데이터 마트
│   ├── data/                     # 데이터 계층
│   │   ├── database.py           # DB 추상화 (신규)
│   │   ├── db.py                 # DuckDB 연결
│   │   ├── supabase_db.py        # PostgreSQL 연결
│   │   └── schema.py             # 스키마 정의
│   └── ui/                       # UI 컴포넌트
│
├── target_app/                   # FastAPI 백엔드
│   ├── main.py                   # 진입점
│   ├── templates/                # HTML 템플릿
│   └── static/                   # 정적 파일
│
├── scripts/                      # 유틸리티 스크립트
│   ├── migrate_v2.py             # DB 마이그레이션
│   └── db/                       # DB 관리 스크립트
│
├── data/                         # 로컬 데이터 (Git 제외)
│   ├── db/                       # DuckDB 파일
│   └── raw/                      # CSV 원본 데이터
│
├── docs/                         # 문서
│   └── schema_design.md          # 스키마 설계
│
├── .env.example                  # 환경 변수 템플릿
├── .streamlit/
│   └── secrets.toml.example      # Streamlit 시크릿 템플릿
├── Dockerfile                    # Render 배포용
├── render.yaml                   # Render 설정
└── requirements.txt              # Python 의존성
```

### Git에서 추적되는 파일

| 디렉토리 | 포함 | 제외 |
|---------|------|------|
| `src/` | 모든 소스 코드 | `__pycache__` |
| `target_app/` | 모든 소스 코드 | `__pycache__` |
| `scripts/` | 모든 스크립트 | - |
| `data/` | `.gitkeep` 만 | `*.db`, `*.csv` |
| `docs/` | 모든 문서 | - |
| 루트 | 설정 파일들 | `.env`, 시크릿 |

---

## 🔧 트러블슈팅

### Issue 1: DuckDB 파일 잠금 오류

**증상**: `database is locked` 오류

**해결**:
```bash
# Target App 종료 후 재시작
# 또는 DB 협조 모드 사용 (자동)
```

### Issue 2: Render 무료 플랜 슬립

**증상**: 첫 요청이 매우 느림 (30초+)

**해결**:
- [UptimeRobot](https://uptimerobot.com/)으로 5분마다 ping
- 또는 Render 유료 플랜 사용

### Issue 3: Supabase 연결 실패

**증상**: `connection refused` 또는 `timeout`

**확인사항**:
1. `DATABASE_URL`에 `sslmode=require` 포함 여부
2. Supabase 프로젝트가 활성 상태인지 확인
3. IP 허용 목록 확인 (기본: 모두 허용)

### Issue 4: CORS 오류

**증상**: Streamlit에서 Target App API 호출 실패

**해결**:
```bash
# Render 환경 변수 설정
ALLOWED_ORIGINS=https://novarium-mvp.streamlit.app
```

### Issue 5: 데이터가 보이지 않음

**확인사항**:
1. 마이그레이션 실행 여부: `python scripts/migrate_v2.py --verify`
2. 올바른 DB 모드: `DB_MODE` 환경 변수 확인
3. 테이블 존재 여부: Supabase 대시보드 확인

---

## 📊 비용 비교

| 구성 | 월 비용 (USD) | 난이도 | 안정성 |
|-----|---------------|--------|--------|
| Streamlit Cloud + Render Free + Supabase Free | $0 | ⭐ | ⭐⭐ |
| Streamlit Cloud + Render Starter | ~$7 | ⭐ | ⭐⭐⭐ |
| AWS EC2 t3.small + RDS | ~$25 | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Google Cloud Run | ~$5-10 | ⭐⭐ | ⭐⭐⭐⭐ |

---

## ✅ 배포 체크리스트

### 로컬 개발

- [ ] Python 3.11+ 설치
- [ ] 가상환경 생성 및 활성화
- [ ] 의존성 설치 (`pip install -r requirements.txt`)
- [ ] `.env` 파일 생성 (`.env.example` 복사)
- [ ] DuckDB 초기화
- [ ] 두 앱 모두 실행 확인

### 클라우드 배포

- [ ] Supabase 프로젝트 생성
- [ ] PostgreSQL 스키마 마이그레이션
- [ ] Render.com 서비스 배포
- [ ] Streamlit Cloud 앱 배포
- [ ] 환경 변수 모두 설정
- [ ] CORS 설정 확인
- [ ] Health check 통과 확인

---

**추천 배포 방법 (포트폴리오용)**:
> **Streamlit Cloud (대시보드) + Render.com Free (Target App) + Supabase Free (DB)**

무료이고 설정이 간단하며, 포트폴리오 프로젝트로 충분한 성능을 제공합니다.
