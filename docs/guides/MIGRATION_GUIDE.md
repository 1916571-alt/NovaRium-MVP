# Database Migration Guide - Run ID Implementation

## 문제 해결 요약 (Problem Summary)

### 이전 문제점 (Previous Issues):
1. **에이전트 카운팅 중복**: 실험을 여러 번 실행하면 이전 실험의 에이전트까지 합산되어 50명을 투입해야 하는데 100명, 150명으로 계속 증가
2. **데이터 격리 부족**: `user_id` 접두사(`agent_`, `sim_`)로만 필터링하여 여러 실험 간 데이터가 섞임
3. **대시보드 데이터 초기화**: 실험 데이터 삭제 시 대시보드의 모든 히스토리 데이터까지 삭제됨
4. **분석 결과 누락**: Analysis 탭에서 주요 메트릭 비교표와 가드레일 결과가 표시되지 않음

### 해결 방법 (Solutions):
1. **`run_id` 컬럼 추가**: 각 실험 실행마다 고유 ID 부여하여 완벽한 데이터 격리
2. **쿼리 필터링 개선**: `user_id LIKE 'agent_%'` → `run_id = '{current_run_id}'`
3. **선택적 삭제**: 실험 종료 시 해당 `run_id` 데이터만 삭제하여 히스토리 보존
4. **상세 분석 추가**: 주요 메트릭 비교표 및 가드레일 자동 계산 구현

---

## 변경 사항 (Changes Made)

### 1. 데이터베이스 스키마 업데이트

#### `assignments` 테이블
```sql
-- 이전 (Before)
CREATE TABLE assignments (
    user_id VARCHAR,
    experiment_id VARCHAR,
    variant VARCHAR,
    assigned_at TIMESTAMP
)

-- 이후 (After)
CREATE TABLE assignments (
    user_id VARCHAR,
    experiment_id VARCHAR,
    variant VARCHAR,
    assigned_at TIMESTAMP,
    run_id VARCHAR          -- 새로 추가
)
```

#### `events` 테이블
```sql
-- 이전 (Before)
CREATE TABLE events (
    event_id VARCHAR,
    user_id VARCHAR,
    event_name VARCHAR,
    timestamp TIMESTAMP
)

-- 이후 (After)
CREATE TABLE events (
    event_id VARCHAR,
    user_id VARCHAR,
    event_name VARCHAR,
    timestamp TIMESTAMP,
    value DOUBLE,           -- 새로 추가 (구매 금액)
    run_id VARCHAR          -- 새로 추가
)
```

#### `experiments` 테이블 (회고록)
```sql
-- 새로운 컬럼 추가
ALTER TABLE experiments ADD COLUMN run_id VARCHAR;
ALTER TABLE experiments ADD COLUMN control_rate FLOAT;
ALTER TABLE experiments ADD COLUMN test_rate FLOAT;
ALTER TABLE experiments ADD COLUMN lift FLOAT;
ALTER TABLE experiments ADD COLUMN guardrail_results VARCHAR;
```

---

### 2. 코드 변경 사항

#### A. Agent 시스템 (`agent_swarm/`)

**`agent.py`**
- `HeuristicAgent.__init__()`: `run_id` 파라미터 추가
- `run_session()`: GET 요청에 `run_id` 쿼리 파라미터 포함
- `/click`, `/order` POST 요청에 `run_id` 폼 데이터 추가

**`runner.py`**
- `run_agent_swarm()`: `run_id` 파라미터 추가, 자동 생성 로직 구현
- CLI 인자: `--run-id` 옵션 추가

#### B. Target App (`target_app/main.py`)

- `log_event()`: `run_id` 파라미터 추가
- `GET /`: `run_id` 쿼리 파라미터 수신 및 저장
- `POST /click`, `/order`: `run_id` 폼 데이터 수신 및 저장
- Assignment 중복 체크: `run_id` 고려

#### C. Streamlit App (`src/app.py`)

**Step 3 (Collection)**:
- 시뮬레이션 시작 시 `current_run_id` 생성 및 세션에 저장
- `runner.py` 호출 시 `--run-id` 인자 전달
- 진행률 쿼리: `WHERE run_id = '{current_run_id}'`
- 실시간 로그 쿼리: `WHERE run_id = '{current_run_id}'`

**Step 4 (Analysis)**:
- 주 메트릭 쿼리: `WHERE a.run_id = '{current_run_id}'`
- **새로운 기능**:
  - 주요 메트릭 비교표 (CTR, CVR, AOV, ARPU)
  - 가드레일 자동 계산 및 표시
  - 실험 저장 시 상세 결과 기록
- 삭제 로직: `DELETE FROM ... WHERE run_id = '{current_run_id}'` (해당 실험만)

#### D. 히스토리 생성 (`scripts/generate_history.py`)

- 히스토리 데이터는 `run_id = NULL`로 저장하여 기준선 역할
- 대시보드 쿼리는 `run_id IS NULL OR ...` 패턴 사용 가능

---

## 마이그레이션 절차 (Migration Steps)

### Option 1: 새로 시작 (권장)

기존 데이터가 중요하지 않은 경우:

```bash
# 1. 기존 DB 삭제
rm novarium_local.db

# 2. 새 스키마로 DB 초기화
python src/data/db.py

# 3. 히스토리 데이터 생성
python scripts/generate_history.py

# 4. Target App 재시작
# (터미널 1)
python target_app/main.py

# 5. Streamlit App 시작
# (터미널 2)
streamlit run src/app.py
```

### Option 2: 기존 DB 마이그레이션

기존 데이터를 유지하려면:

```sql
-- DuckDB CLI 또는 Python에서 실행
-- 1. 새 컬럼 추가
ALTER TABLE assignments ADD COLUMN run_id VARCHAR;
ALTER TABLE events ADD COLUMN value DOUBLE;
ALTER TABLE events ADD COLUMN run_id VARCHAR;

-- 2. 기존 데이터에 NULL 할당 (히스토리로 간주)
UPDATE assignments SET run_id = NULL WHERE run_id IS NULL;
UPDATE events SET run_id = NULL WHERE run_id IS NULL;

-- 3. experiments 테이블 업데이트
ALTER TABLE experiments ADD COLUMN run_id VARCHAR;
ALTER TABLE experiments ADD COLUMN control_rate FLOAT;
ALTER TABLE experiments ADD COLUMN test_rate FLOAT;
ALTER TABLE experiments ADD COLUMN lift FLOAT;
ALTER TABLE experiments ADD COLUMN guardrail_results VARCHAR;
```

---

## 새로운 기능 (New Features)

### 1. 주요 메트릭 비교표 (Key Metrics Comparison)

Analysis 단계에서 자동으로 표시:

| 그룹 | 방문자수 | 클릭수 | 구매수 | 총매출 | CTR | CVR | AOV | ARPU |
|------|---------|--------|--------|--------|-----|-----|-----|------|
| A    | 1,757   | 450    | 25     | 750,000| 25.6| 1.4 | 30,000| 427 |
| B    | 1,753   | 520    | 30     | 900,000| 29.7| 1.7 | 30,000| 513 |
| Δ    | -       | -      | -      | -      | +16.0%| +21.4%| 0.0%| +20.1%|

### 2. 가드레일 자동 계산 (Guardrail Metrics)

Step 1에서 설정한 가드레일 지표를 자동으로 계산:

```
✅ CVR (전환율) 안정: +5.2%
❌ AOV (평균주문액) 하락: -7.3% (임계치: -5.0%)
```

### 3. 실험 격리 (Experiment Isolation)

- 각 실험 실행마다 고유한 `run_id` 부여
- 이전 실험 데이터와 완전히 분리
- 대시보드는 전체 히스토리 유지

---

## 테스트 방법 (Testing)

### 1. 첫 번째 실험
```bash
# Step 1: 가설 작성
# Step 2: 샘플 사이즈 계산 (예: 2,500명)
# Step 3: Agent Swarm 투입 (50명으로 테스트)
# Step 4: 결과 확인 - run_id가 생성되었는지 확인
```

DB 확인:
```sql
SELECT DISTINCT run_id FROM assignments;
-- 결과: run_1234567890001
```

### 2. 두 번째 실험
```bash
# 동일한 프로세스 반복
# Step 3에서 다시 Agent Swarm 투입
```

DB 확인:
```sql
SELECT run_id, COUNT(*) as cnt
FROM assignments
GROUP BY run_id;

-- 결과:
-- run_1234567890001 | 50
-- run_1234567890450 | 50  (새로운 실험)
```

### 3. 데이터 격리 확인
```sql
-- 현재 실험만 조회
SELECT * FROM assignments WHERE run_id = 'run_1234567890450';

-- 히스토리 데이터 조회
SELECT * FROM assignments WHERE run_id IS NULL;
```

---

## 주의사항 (Important Notes)

1. **기존 실험 데이터**: 마이그레이션 후 기존 실험은 `run_id = NULL`로 표시됨
2. **대시보드 호환성**: Monitor 페이지는 `run_id IS NULL` 데이터만 사용 (히스토리)
3. **동시 실험**: 여러 탭에서 동시에 실험 실행 시 각자 다른 `run_id` 생성
4. **Target App 재시작**: 스키마 변경 후 반드시 Target App 재시작 필요

---

## 문제 해결 (Troubleshooting)

### 문제: "table assignments has 4 columns but 5 values were supplied"
**원인**: 스키마가 업데이트되지 않음
**해결**: Target App 재시작 또는 DB 재초기화

### 문제: Analysis에서 데이터가 안 보임
**원인**: `current_run_id`가 세션에 없음
**해결**: Step 3에서 시뮬레이션 다시 실행

### 문제: 에이전트 수가 계속 증가
**원인**: 이전 버전 코드 사용 중
**해결**:
```bash
git pull  # 최신 코드 받기
python src/data/db.py  # DB 재초기화
```

---

## 롤백 방법 (Rollback)

이전 버전으로 돌아가려면:

```bash
# 1. Git 롤백
git checkout <previous-commit-hash>

# 2. DB 재생성
rm novarium_local.db
python src/data/db.py
python scripts/generate_history.py
```

---

## 참고 파일 (Reference Files)

- [src/data/db.py](src/data/db.py:35) - 스키마 정의
- [agent_swarm/agent.py](agent_swarm/agent.py:16) - Agent 클래스
- [agent_swarm/runner.py](agent_swarm/runner.py:10) - Swarm 실행
- [target_app/main.py](target_app/main.py:79) - API 엔드포인트
- [src/app.py](src/app.py:1052) - Analysis 로직
- [scripts/generate_history.py](scripts/generate_history.py:73) - 히스토리 생성
