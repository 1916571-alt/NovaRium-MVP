# 빠른 시작 가이드 (Quick Start Guide)

## 현재 상태 요약

✅ **완료된 작업**:
1. 데이터베이스 스키마 업데이트 (`run_id` 컬럼 추가)
2. 히스토리 데이터 생성 (30일치, 14,679명)
3. Agent 시스템 업데이트 (run_id 지원)
4. Target App 업데이트 (run_id 지원)
5. Analysis 탭 개선 (주요 메트릭 비교표, 가드레일 자동 계산)

---

## 시작하기

### 1단계: Target App 시작

**새 터미널 창 열기** (터미널 1):

```bash
cd "c:\Users\신건율\.claude-worktrees\NovaRium-MVP\friendly-buck"
python target_app/main.py
```

**예상 출력**:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

⚠️ **중요**: 이 터미널은 계속 실행 상태로 두어야 합니다!

---

### 2단계: Streamlit App 시작

**새 터미널 창 열기** (터미널 2):

```bash
cd "c:\Users\신건율\.claude-worktrees\NovaRium-MVP\friendly-buck"
streamlit run src/app.py
```

**예상 출력**:
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

브라우저가 자동으로 열립니다.

---

### 3단계: 첫 번째 실험 실행

#### Step 1: Hypothesis (가설 작성)
1. **타겟 선택**: 메인 홈 > 메인 배너
2. **Group B 변경**: "긴급! 50% 할인 (빨간색 배경)"
3. **가설 작성**: "긴급성을 강조하면 클릭률이 증가할 것이다"
4. **주 메트릭**: CTR (클릭률)
5. **가드레일**: CVR (전환율) 선택
6. **다음** 클릭

#### Step 2: Design (실험 설계)
1. **트래픽 비율**: 50% (기본값)
2. **최소 효과 크기**: 10% (기본값)
3. 자동으로 계산된 표본 수 확인
4. **다음** 클릭

#### Step 3: Collection (데이터 수집)
1. **에이전트 성향**: 기본값 사용 (Window 40%, Mission 10%, ...)
2. **시뮬레이션 스케일**: 1% ~ 100% 선택 (테스트는 1%로 시작 권장)
3. **Turbo Mode**: 체크 (빠른 실행)
4. **▶️ Agent Swarm 투입 (Start)** 클릭

**예상 동작**:
```
데이터 수집 중... (25/50) [Loop: 3]

최근 활동:
🕒 00:36:55 | 👤 agent_impulsive_1766558961327 | 📢 purchase
🕒 00:36:55 | 👤 agent_window_1766558961328 | 📢 banner_A
```

**실시간 그룹 분포** 차트가 업데이트되면서 A/B 그룹의 방문자 수가 증가합니다.

⚠️ **중요**: 완료될 때까지 기다리세요! (Turbo Mode로 약 30초~1분 소요)

#### Step 4: Analysis (결과 분석)
자동으로 Step 4로 이동하면:

1. **최종 결과 요약**:
   - Lift (개선율): +XX%
   - P-value: 0.XXXX
   - 통계적 유의성 판정

2. **주요 메트릭 비교표**:
   | 그룹 | 방문자수 | 클릭수 | 구매수 | CTR | CVR | AOV | ARPU |
   |------|---------|--------|--------|-----|-----|-----|------|
   | A    | XX      | XX     | XX     | XX% | XX% | XX  | XX   |
   | B    | XX      | XX     | XX     | XX% | XX% | XX  | XX   |
   | Δ    | XX%     | XX%    | XX%    | XX% | XX% | XX% | XX%  |

3. **가드레일 체크**:
   - ✅ CVR 안정: +X.X%

4. **배운 점 작성** 후 **저장** 클릭

---

### 4단계: 두 번째 실험 (중요!)

**첫 번째 실험과 데이터가 격리되는지 확인**:

1. Step 1부터 다시 시작
2. 다른 가설로 실험 설정
3. Step 3에서 다시 Agent Swarm 투입
4. **확인사항**:
   - 새로운 `run_id`가 생성됨
   - 이전 실험의 50명과 합산되지 않고 **새로운 50명만** 표시
   - Step 4에서 이전 실험 데이터가 보이지 않음

---

## 문제 해결

### 문제 1: "Cannot open file" 에러 (파일 락)

**원인**: DuckDB가 다른 프로세스에서 이미 열려있음

**해결**:
```bash
# 1. 모든 Python 프로세스 종료
taskkill /F /IM python.exe

# 2. Target App 재시작
python target_app/main.py

# 3. 새 터미널에서 Streamlit 재시작
streamlit run src/app.py
```

### 문제 2: Step 4에서 "실험 데이터를 찾을 수 없습니다"

**원인**: Step 3를 거치지 않고 바로 Step 4로 이동

**해결**: Step 1부터 순서대로 진행

**디버깅**: Step 4에 표시되는 "사용 가능한 run_id" 목록에서 수동 선택 가능

### 문제 3: Raw Data에 17,000명 이상 표시

**원인**: 히스토리 데이터(`run_id=NULL`)가 표시되고 있음

**확인**:
```bash
python -c "import duckdb; con = duckdb.connect('novarium_local.db'); print(con.execute('SELECT run_id, COUNT(*) FROM assignments GROUP BY run_id').fetchall()); con.close()"
```

**예상 출력**:
```
[(None, 14679), ('run_1735123456001', 50)]
```

- `None`: 히스토리 데이터 (무시)
- `run_XXX`: 실험 데이터

**해결**: Step 3에서 시뮬레이션이 완료된 후 Step 4로 자동 이동되는지 확인

### 문제 4: Agent Swarm이 시작되지 않음

**확인사항**:
1. Target App이 실행 중인가? (`http://localhost:8000` 접속 확인)
2. 에이전트 성향 합계가 100%인가?

**로그 확인**:
- Step 3의 "최근 활동" 영역에 로그가 표시되는지 확인
- 아무것도 안 나오면 Target App 터미널에서 에러 확인

---

## 데이터베이스 확인

언제든지 현재 데이터베이스 상태를 확인할 수 있습니다:

```bash
python check_db.py
```

**예상 출력**:
```
Assignments with agent_: 50
Events with agent_: 125
Total assignments: 14729

Recent Events:
  00:36:55 | agent_impulsive_XXX | purchase
  00:36:55 | agent_window_XXX | banner_A
```

---

## 다음 단계

1. ✅ 첫 번째 실험 완료
2. ✅ 두 번째 실험 실행하여 데이터 격리 확인
3. ✅ Portfolio 페이지에서 실험 회고록 확인
4. ✅ Monitor 페이지에서 대시보드 확인

---

## 추가 정보

- **상세 마이그레이션 가이드**: [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)
- **데이터베이스 마이그레이션**: `python migrate_db.py` (기존 DB 업그레이드)
- **완전 초기화**: `rm novarium_local.db && python src/data/db.py && python scripts/generate_history.py`

---

## 주의사항

1. **Target App을 먼저 시작**하고 **Streamlit은 나중에** 시작하세요
2. **Step 3 완료 전에 탭을 닫지 마세요** (run_id가 세션에 저장됨)
3. **실험마다 새로운 run_id 생성** 확인
4. **히스토리 데이터(run_id=NULL)는 건드리지 마세요** (대시보드 기준선)
