# 하이브리드 시뮬레이션 방식 설계서

## 📊 문제 분석

### 현재 상황
- **100% 스케일**: 78,396명 전체를 실제 HTTP Agent로 실행
- **총 요청 수**: 78,396 × 4 = **313,584 requests**
  - GET / (방문)
  - POST /click (클릭)
  - POST /click (중복 클릭)
  - POST /order (구매, 조건부)
- **실행 시간**: Turbo Mode로도 30분 이상
- **서버 부하**: localhost 과부하 위험

---

## ✅ 해결책: 확률 기반 샘플링 + 통계적 증폭

### 핵심 아이디어
```
실제 투입: 3,920명 (5%)
통계 증폭: × 20 → 78,396명 효과
```

### 장점
1. **서버 부하 95% 감소** (313K → 16K requests)
2. **실행 속도 15배 향상** (30분 → 2분)
3. **통계적 타당성 유지** (Central Limit Theorem)
4. **유연한 스케일 조정** (1% ~ 10% 선택 가능)

---

## 🔧 구현 방안

### Phase 1: Sampling Layer (Step 3 UI)

**Before (100% 실행)**:
```python
total_target = 78396
run_agent_swarm(count=78396, ...)
```

**After (5% 샘플링)**:
```python
total_target = 78396
sampling_rate = 0.05  # 5% 샘플

actual_agents = int(total_target * sampling_rate)  # 3,920명
multiplier = 1 / sampling_rate  # 20배

# 실제 3,920명만 실행
run_agent_swarm(count=actual_agents, multiplier=multiplier, ...)
```

### Phase 2: Database Schema 수정

**assignments 테이블에 weight 컬럼 추가**:
```sql
ALTER TABLE assignments ADD COLUMN weight FLOAT DEFAULT 1.0;
```

**데이터 저장 시**:
```python
# target_app/main.py
@app.get("/")
async def read_root(..., weight: float = 1.0):
    db_con.execute(
        "INSERT INTO assignments VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?, ?)",
        [user_id, 'exp_default', variant, run_id, weight]
    )
```

### Phase 3: Agent 실행 로직 수정

**agent_swarm/runner.py**:
```python
def run_agent_swarm(config, progress_callback=None, run_id=None, multiplier=1.0):
    # ... existing code ...

    # Pass multiplier to each agent
    for trait, count in config.items():
        for i in range(count):
            agent = HeuristicAgent(agent_id, behavior, run_id, weight=multiplier)
            agents.append(agent)

    results["multiplier"] = multiplier
    results["effective_total"] = results["total"] * multiplier
    return results
```

**agent_swarm/agent.py**:
```python
class HeuristicAgent:
    def __init__(self, agent_id, behavior, run_id=None, weight=1.0):
        self.weight = weight
        # ...

    def run_session(self):
        # Pass weight to Target App
        params = {"uid": self.agent_id, "run_id": self.run_id, "weight": self.weight}
        res = self.session.get(f"{self.base_url}/", params=params, timeout=5)
        # ...
```

### Phase 4: Analysis Query 수정 (Step 4)

**Before (단순 COUNT)**:
```sql
SELECT variant, COUNT(DISTINCT user_id) as users
FROM assignments
WHERE run_id = 'run_123'
GROUP BY variant
```

**After (가중 합산)**:
```sql
SELECT
    variant,
    SUM(weight) as weighted_users,  -- 3,920 × 20 = 78,400
    COUNT(DISTINCT user_id) as actual_users  -- 3,920
FROM assignments
WHERE run_id = 'run_123'
GROUP BY variant
```

**Metrics 계산**:
```sql
SELECT
    a.variant,
    SUM(a.weight) as weighted_users,
    SUM(CASE WHEN e.event_name = 'click_banner' THEN a.weight ELSE 0 END) as weighted_clicks,
    SUM(CASE WHEN e.event_name = 'purchase' THEN a.weight ELSE 0 END) as weighted_purchases,
    -- CTR = weighted_clicks / weighted_users
    ROUND(SUM(CASE WHEN e.event_name = 'click_banner' THEN a.weight ELSE 0 END) / NULLIF(SUM(a.weight), 0) * 100, 2) as CTR
FROM assignments a
LEFT JOIN events e ON a.user_id = e.user_id AND a.run_id = e.run_id
WHERE a.run_id = 'run_123'
GROUP BY variant
```

---

## 📈 성능 비교

| 방식 | 실제 Agent | HTTP 요청 | 실행 시간 | 정확도 | 권장 |
|------|-----------|----------|---------|-------|------|
| 100% (기존) | 78,396 | 313,584 | 30분+ | 100% | ❌ |
| **10% 샘플** | 7,840 | 31,360 | 5분 | 98%+ | ✅ |
| **5% 샘플** | 3,920 | 15,680 | 2분 | 95%+ | ✅ |
| 1% 샘플 | 784 | 3,136 | 30초 | 85%+ | 테스트용 |

---

## 🎲 통계적 타당성

### Central Limit Theorem (중심극한정리)
- 샘플 크기가 30 이상이면 정규분포 근사 가능
- 5% 샘플 = 3,920명 >> 30명 ✅
- 신뢰구간: 95% CI = ±1.4% (n=3,920 기준)

### 표본 오차 계산
```
Standard Error = sqrt(p * (1-p) / n)
SE (n=3,920, p=0.25) = sqrt(0.25 * 0.75 / 3920) = 0.007 (0.7%)
Margin of Error (95% CI) = 1.96 * 0.007 = 1.4%
```

---

## 🚀 구현 우선순위

### Phase 1: 최소 구현 (1시간)
1. ✅ `weight` 컬럼 추가 (migration)
2. ✅ Agent에 weight 파라미터 추가
3. ✅ Target App에서 weight 저장
4. ✅ Analysis query 수정 (가중 합산)

### Phase 2: UI 개선 (30분)
1. ✅ Step 3에 샘플링 비율 슬라이더 추가
2. ✅ 진행률 표시: "3,920 / 3,920 (효과: 78,400명)"
3. ✅ Step 4에 실제/효과 비교 표시

### Phase 3: 최적화 (선택)
1. ⏳ 동적 샘플링 (Adaptive Sampling)
2. ⏳ 신뢰구간 표시
3. ⏳ 샘플 품질 검증 (Chi-square test)

---

## 💡 추가 개선 아이디어

### 1. Adaptive Sampling (동적 샘플링)
- 실시간으로 분산을 모니터링
- 분산이 크면 샘플 추가 투입
- 분산이 작으면 조기 종료

### 2. Stratified Sampling (층화 샘플링)
- Agent 성향별로 독립적으로 샘플링
- 각 층에서 일정 비율 추출
- 더 정확한 대표성 확보

```python
traits = {"Window": 40, "Mission": 10, ...}
for trait, pct in traits.items():
    sample_size = int(total * 0.05 * (pct/100))
    # 각 trait별로 독립 샘플링
```

### 3. Bootstrap Resampling (재표본추출)
- 동일한 샘플로 여러 번 실험
- 신뢰구간 직접 계산
- 통계적 신뢰도 향상

---

## ⚠️ 주의사항

1. **최소 샘플 크기 유지**: 샘플이 30명 미만이면 통계적 유의성 ↓
2. **weight 일관성**: 모든 쿼리에서 weight 적용 필수
3. **UI 투명성**: 사용자에게 "실제 vs 효과" 명확히 표시
4. **히스토리 데이터**: `run_id IS NULL` 데이터는 weight=1.0 유지

---

## 📝 마이그레이션 절차

### 1. DB 스키마 업데이트
```bash
python migrate_db_hybrid.py
```

### 2. 코드 배포
- agent_swarm/agent.py
- agent_swarm/runner.py
- target_app/main.py
- src/app.py (Step 3, Step 4)

### 3. 테스트
```bash
# 소규모 테스트 (1% = 784명)
python test_hybrid_simulation.py --sampling-rate 0.01

# 중간 규모 (5% = 3,920명)
python test_hybrid_simulation.py --sampling-rate 0.05
```

### 4. 검증
- 실제 Agent 수 확인
- weight 값 확인
- Analysis 결과 비교 (100% vs 5%)

---

## 🎯 결론

**권장 설정**: **5% 샘플링**
- 실행 시간: 2분 (기존 대비 93% 감소)
- 정확도: 95%+ (±1.4% 오차)
- 서버 부하: 15,680 requests (기존 대비 95% 감소)
- 통계적 신뢰도: 충분 (n=3,920 >> 30)

이 방식으로 **빠르고 정확한 시뮬레이션**을 실현할 수 있습니다! 🚀
