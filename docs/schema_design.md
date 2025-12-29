# NovaRium DB Schema Design v2.0

## 개요

이 문서는 NovaRium MVP의 고도화된 데이터베이스 스키마를 정의합니다.
사용자 인증(OAuth + Email)과 멀티테넌시를 지원하는 확장 가능한 구조입니다.

---

## 1. 엔티티 개념 정리

### 두 가지 "사용자" 개념

| 엔티티 | 설명 | 예시 |
|--------|------|------|
| **auth_users** | NovaRium 플랫폼 사용자 (분석가, 관리자) | 데이터팀 직원, PM |
| **customers** | A/B 테스트 대상 서비스의 고객 | 커피숍 앱 사용자 |

---

## 2. 스키마 다이어그램

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AUTH & USER MANAGEMENT                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────┐       ┌─────────────────────┐                      │
│  │     auth_users      │       │   oauth_accounts    │                      │
│  ├─────────────────────┤       ├─────────────────────┤                      │
│  │ id (PK, UUID)       │──1:N──│ id (PK, UUID)       │                      │
│  │ email (UNIQUE)      │       │ user_id (FK)        │                      │
│  │ password_hash       │       │ provider            │                      │
│  │ name                │       │ provider_user_id    │                      │
│  │ role                │       │ access_token        │                      │
│  │ is_active           │       │ refresh_token       │                      │
│  │ email_verified      │       │ expires_at          │                      │
│  │ created_at          │       │ created_at          │                      │
│  │ updated_at          │       └─────────────────────┘                      │
│  │ last_login_at       │                                                     │
│  └─────────────────────┘                                                     │
│           │                                                                  │
│           │ 1:N                                                              │
│           ▼                                                                  │
│  ┌─────────────────────┐                                                     │
│  │      sessions       │                                                     │
│  ├─────────────────────┤                                                     │
│  │ id (PK, UUID)       │                                                     │
│  │ user_id (FK)        │                                                     │
│  │ token_hash          │                                                     │
│  │ expires_at          │                                                     │
│  │ ip_address          │                                                     │
│  │ user_agent          │                                                     │
│  │ created_at          │                                                     │
│  └─────────────────────┘                                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         WAREHOUSE DB (Business Data)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────┐       ┌─────────────────────┐                      │
│  │     customers       │       │       orders        │                      │
│  │  (기존 users 변경)  │       ├─────────────────────┤                      │
│  ├─────────────────────┤       │ order_id (PK, UUID) │                      │
│  │ customer_id (PK)    │──1:N──│ customer_id (FK)    │                      │
│  │ name                │       │ order_at            │                      │
│  │ gender              │       │ menu_item           │                      │
│  │ age                 │       │ amount              │                      │
│  │ job                 │       │ created_by (FK)     │  ← auth_users 참조   │
│  │ segment             │       └─────────────────────┘                      │
│  │ joined_at           │                                                     │
│  │ created_by (FK)     │  ← auth_users 참조 (누가 이 데이터를 생성했는지)   │
│  └─────────────────────┘                                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                       EXPERIMENT DB (A/B Test Data)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────┐       ┌─────────────────────┐                      │
│  │    experiments      │       │    assignments      │                      │
│  ├─────────────────────┤       ├─────────────────────┤                      │
│  │ exp_id (PK)         │──1:N──│ id (PK)             │                      │
│  │ name                │       │ customer_id (FK)    │                      │
│  │ target              │       │ experiment_id (FK)  │                      │
│  │ hypothesis          │       │ variant             │                      │
│  │ primary_metric      │       │ assigned_at         │                      │
│  │ guardrails          │       │ run_id              │                      │
│  │ sample_size         │       │ weight              │                      │
│  │ start_date          │       └─────────────────────┘                      │
│  │ end_date            │               │                                     │
│  │ traffic_split       │               │ 1:N                                 │
│  │ status              │               ▼                                     │
│  │ created_by (FK)     │       ┌─────────────────────┐                      │
│  │ created_at          │       │       events        │                      │
│  └─────────────────────┘       ├─────────────────────┤                      │
│           │                    │ event_id (PK, UUID) │                      │
│           │ 1:1                │ customer_id         │                      │
│           ▼                    │ event_name          │                      │
│  ┌─────────────────────┐       │ timestamp           │                      │
│  │     adoptions       │       │ value               │                      │
│  ├─────────────────────┤       │ run_id              │                      │
│  │ adoption_id (PK)    │       │ metadata (JSON)     │                      │
│  │ experiment_id (FK)  │       └─────────────────────┘                      │
│  │ winning_variant     │                                                     │
│  │ variant_config      │                                                     │
│  │ adopted_at          │                                                     │
│  │ adopted_by (FK)     │  ← auth_users 참조                                 │
│  └─────────────────────┘                                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 테이블 상세 정의

### 3.1 auth_users (플랫폼 사용자)

```sql
CREATE TABLE auth_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 기본 정보
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255),  -- NULL if OAuth only
    name VARCHAR(100) NOT NULL,
    avatar_url VARCHAR(500),

    -- 역할 및 상태
    role VARCHAR(20) NOT NULL DEFAULT 'analyst',  -- 'admin', 'analyst', 'viewer'
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,

    -- 메타데이터
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,

    -- 제약 조건
    CONSTRAINT chk_role CHECK (role IN ('admin', 'analyst', 'viewer'))
);

-- 인덱스
CREATE INDEX idx_auth_users_email ON auth_users(email);
CREATE INDEX idx_auth_users_role ON auth_users(role);
```

### 3.2 oauth_accounts (소셜 로그인 연동)

```sql
CREATE TABLE oauth_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,

    -- OAuth Provider 정보
    provider VARCHAR(50) NOT NULL,  -- 'google', 'github', 'kakao', 'naver'
    provider_user_id VARCHAR(255) NOT NULL,
    provider_email VARCHAR(255),

    -- 토큰 정보 (암호화 저장 권장)
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP,

    -- 메타데이터
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 제약 조건: 동일 provider에서 동일 user_id는 하나만
    CONSTRAINT uq_oauth_provider_user UNIQUE (provider, provider_user_id)
);

-- 인덱스
CREATE INDEX idx_oauth_accounts_user_id ON oauth_accounts(user_id);
CREATE INDEX idx_oauth_accounts_provider ON oauth_accounts(provider, provider_user_id);
```

### 3.3 sessions (세션 관리)

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,

    -- 세션 토큰 (해시 저장)
    token_hash VARCHAR(64) NOT NULL UNIQUE,

    -- 세션 메타데이터
    expires_at TIMESTAMP NOT NULL,
    ip_address VARCHAR(45),  -- IPv6 지원
    user_agent TEXT,

    -- 생성 시간
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 만료된 세션 자동 정리를 위한 인덱스
    CONSTRAINT chk_session_expiry CHECK (expires_at > created_at)
);

-- 인덱스
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_token_hash ON sessions(token_hash);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);
```

### 3.4 customers (기존 users → 이름 변경)

```sql
-- 기존 users 테이블을 customers로 rename
-- 시뮬레이션/테스트 대상 고객 데이터

CREATE TABLE customers (
    customer_id UUID PRIMARY KEY,  -- 기존 user_id
    name VARCHAR(100) NOT NULL,
    gender VARCHAR(10),
    age INTEGER,
    job VARCHAR(200),
    segment VARCHAR(50),  -- 'Student', 'Office Worker', etc.
    joined_at TIMESTAMP NOT NULL,

    -- 데이터 소유권 (멀티테넌시 대비)
    created_by UUID REFERENCES auth_users(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 인덱스용 컬럼
    CONSTRAINT chk_age CHECK (age >= 0 AND age <= 150)
);

-- 인덱스
CREATE INDEX idx_customers_segment ON customers(segment);
CREATE INDEX idx_customers_created_by ON customers(created_by);
CREATE INDEX idx_customers_joined_at ON customers(joined_at);
```

### 3.5 orders (주문 테이블)

```sql
CREATE TABLE orders (
    order_id UUID PRIMARY KEY,
    customer_id UUID NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    order_at TIMESTAMP NOT NULL,
    menu_item VARCHAR(100) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,

    -- 데이터 소유권
    created_by UUID REFERENCES auth_users(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 제약 조건
    CONSTRAINT chk_amount CHECK (amount >= 0)
);

-- 인덱스
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_order_at ON orders(order_at);
CREATE INDEX idx_orders_menu_item ON orders(menu_item);
```

### 3.6 experiments (실험 메타데이터) - 개선

```sql
CREATE TABLE experiments (
    exp_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 실험 기본 정보
    name VARCHAR(100) NOT NULL,
    target VARCHAR(255) NOT NULL,
    hypothesis TEXT,
    description TEXT,

    -- 지표 설정
    primary_metric VARCHAR(100) NOT NULL,
    guardrails TEXT,  -- JSON array of guardrail metrics

    -- 실험 설계
    sample_size INTEGER,
    traffic_split FLOAT NOT NULL DEFAULT 0.5,
    start_date DATE,
    end_date DATE,

    -- 결과
    status VARCHAR(20) NOT NULL DEFAULT 'draft',  -- 'draft', 'running', 'completed', 'archived'
    p_value FLOAT,
    control_rate FLOAT,
    test_rate FLOAT,
    lift FLOAT,
    decision VARCHAR(50),  -- 'won', 'lost', 'inconclusive'
    learning_note TEXT,
    guardrail_results TEXT,

    -- 메타데이터
    run_id VARCHAR(255),
    created_by UUID REFERENCES auth_users(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 제약 조건
    CONSTRAINT chk_status CHECK (status IN ('draft', 'running', 'completed', 'archived')),
    CONSTRAINT chk_traffic_split CHECK (traffic_split >= 0 AND traffic_split <= 1)
);

-- 인덱스
CREATE INDEX idx_experiments_status ON experiments(status);
CREATE INDEX idx_experiments_created_by ON experiments(created_by);
CREATE INDEX idx_experiments_run_id ON experiments(run_id);
```

### 3.7 assignments (실험 할당)

```sql
CREATE TABLE assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id VARCHAR(255) NOT NULL,  -- Target App의 user_id (익명 가능)
    experiment_id VARCHAR(255) NOT NULL,
    variant VARCHAR(10) NOT NULL,  -- 'A', 'B', 'C', ...
    assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    run_id VARCHAR(255),
    weight FLOAT NOT NULL DEFAULT 1.0,

    -- 중복 할당 방지
    CONSTRAINT uq_assignment UNIQUE (customer_id, experiment_id, run_id)
);

-- 인덱스
CREATE INDEX idx_assignments_experiment ON assignments(experiment_id);
CREATE INDEX idx_assignments_run_id ON assignments(run_id);
CREATE INDEX idx_assignments_customer ON assignments(customer_id);
CREATE INDEX idx_assignments_variant ON assignments(variant);
```

### 3.8 events (이벤트 로그)

```sql
CREATE TABLE events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id VARCHAR(255) NOT NULL,
    event_name VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    value DOUBLE PRECISION DEFAULT 0,
    run_id VARCHAR(255),

    -- 확장성을 위한 메타데이터
    metadata JSONB,  -- PostgreSQL JSONB for flexible event properties

    -- 파티셔닝 대비
    event_date DATE GENERATED ALWAYS AS (DATE(timestamp)) STORED
);

-- 인덱스
CREATE INDEX idx_events_customer ON events(customer_id);
CREATE INDEX idx_events_name ON events(event_name);
CREATE INDEX idx_events_run_id ON events(run_id);
CREATE INDEX idx_events_timestamp ON events(timestamp);
CREATE INDEX idx_events_date ON events(event_date);
```

### 3.9 adoptions (실험 채택)

```sql
CREATE TABLE adoptions (
    adoption_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id VARCHAR(255) NOT NULL,
    winning_variant VARCHAR(10) NOT NULL,
    variant_config TEXT,  -- JSON config of winning variant
    adopted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    adopted_by UUID REFERENCES auth_users(id),
    notes TEXT
);

-- 인덱스
CREATE INDEX idx_adoptions_experiment ON adoptions(experiment_id);
```

### 3.10 active_experiment (현재 활성 실험)

```sql
CREATE TABLE active_experiment (
    id INTEGER PRIMARY KEY DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    experiment_id UUID REFERENCES experiments(exp_id),
    started_at TIMESTAMP,

    -- 단일 행 보장
    CONSTRAINT single_row CHECK (id = 1)
);
```

---

## 4. 관계 요약

| 관계 | 타입 | 설명 |
|------|------|------|
| auth_users → oauth_accounts | 1:N | 한 사용자가 여러 소셜 계정 연동 |
| auth_users → sessions | 1:N | 한 사용자가 여러 세션 보유 |
| auth_users → experiments | 1:N | 실험 생성자 |
| auth_users → adoptions | 1:N | 채택 결정자 |
| customers → orders | 1:N | 고객별 주문 내역 |
| experiments → assignments | 1:N | 실험별 할당 |
| assignments → events | 1:N (논리적) | customer_id + run_id로 조인 |

---

## 5. 역할 기반 접근 제어 (RBAC)

| Role | 권한 |
|------|------|
| **admin** | 모든 권한 + 사용자 관리 |
| **analyst** | 실험 생성, 수정, 분석, 채택 결정 |
| **viewer** | 읽기 전용 (대시보드 조회) |

---

## 6. Migration 전략

### Phase 1: 스키마 추가 (Non-breaking)
1. `auth_users`, `oauth_accounts`, `sessions` 테이블 생성
2. 기존 테이블에 `created_by` 컬럼 추가 (nullable)

### Phase 2: 데이터 이전
1. `users` 테이블을 `customers`로 rename
2. `user_id` 컬럼을 `customer_id`로 rename
3. 기존 코드의 테이블/컬럼 참조 업데이트

### Phase 3: 인증 통합
1. 로그인 기능 구현
2. 세션 관리 구현
3. `created_by` 필드 활용

---

## 7. DuckDB vs PostgreSQL 호환성

| 기능 | DuckDB | PostgreSQL | 대안 |
|------|--------|------------|------|
| `gen_random_uuid()` | ✅ | ✅ | - |
| `JSONB` | ❌ | ✅ | DuckDB: JSON (VARCHAR) |
| `GENERATED ... STORED` | ❌ | ✅ | DuckDB: 별도 컬럼 + 트리거 |
| `SERIAL` | ❌ | ✅ | DuckDB: SEQUENCE |
| `ON DELETE CASCADE` | ✅ | ✅ | - |

---

## 8. 변경 이력

| 버전 | 날짜 | 변경 사항 |
|------|------|----------|
| 1.0 | 초기 | 기본 테이블 구조 |
| 2.0 | 현재 | 인증 시스템 추가, users→customers 변경 |
