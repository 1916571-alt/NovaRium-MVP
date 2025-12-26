# NovaRium MVP 데모 가이드

## 프로젝트 목적

**"데이터 분석가의 실무 역량을 코드로 증명하기 위한 End-to-End A/B 테스팅 시뮬레이터"**

이론으로만 배우던 A/B 테스트의 전체 사이클을 직접 구현하고, **실험 결과가 실제 프로덕션에 반영되는 과정**까지 경험할 수 있는 교육용 플랫폼입니다.

---

## 라이브 데모

| 서비스 | URL | 설명 |
|--------|-----|------|
| **Dashboard** | https://novarium-mvp-s9fouprzj5apgznzehprcr.streamlit.app | Streamlit 기반 분석 대시보드 |
| **Target App** | https://novarium-mvp.onrender.com | 실험 대상 가상 쇼핑몰 (FastAPI) |

> **참고**: 무료 서버(Streamlit Cloud, Render Free Tier)를 사용하고 있어 트래픽이 몰리면 응답이 느려지거나 Cold Start가 발생할 수 있습니다.

---

## 현재 구현된 핵심 기능

### 1. 데이터 마트 생성 (Data Lab)

SQL 기반 ETL 파이프라인을 직접 구축하고 실행합니다.

- 원하는 지표(CTR, CVR, Revenue, AOV 등) 선택
- SQL 쿼리 자동 생성 및 실행
- 데이터 흐름 다이어그램 시각화

### 2. 데이터 신호 기반 실험 진행 (Master Class)

6단계 Wizard 모드로 A/B 테스트 전 과정을 경험합니다.

```
Step 1: 가설 설정 (Hypothesis)
   ↓
Step 2: 실험 설계 (Design) - 배너 문구, 색상 등 수정
   ↓
Step 3: 파워 분석 (Power Analysis) - 필요 샘플 사이즈 계산
   ↓
Step 4: 시뮬레이션 (Simulation) - AI Agent가 유저 행동 재현
   ↓
Step 5: 분석 (Analysis) - P-value, Lift, 신뢰구간 계산
   ↓
Step 6: 의사결정 (Decision) - 채택/기각/롤백
```

### 3. 실시간 프로덕션 반영

**핵심 기능**: 실험에서 승리한 Variant를 채택하면, Target App에 즉시 반영됩니다.

| 액션 | 결과 |
|------|------|
| **채택 (Adopt)** | Target App 배너가 실험 설정(문구, 색상)으로 변경됨 |
| **롤백 (Rollback)** | 원래 배너로 복구 |

### 4. 실험 회고록 (Retrospective)

모든 실험 결과가 DB에 영구 저장되어 포트폴리오로 활용 가능합니다.

- 실험별 가설, 결과, P-value, Lift 기록
- 승리/패배/무효 판정 및 학습 노트
- 언제든 과거 실험 조회 가능

---

## 데모 시나리오 (5분 코스)

### 1. Target App 확인 (1분)

https://novarium-mvp.onrender.com 방문

- 현재 어떤 배너가 표시되는지 확인
- 채택된 실험이 있다면 해당 설정이 반영된 상태

### 2. Dashboard에서 실험 시작 (3분)

https://novarium-mvp-s9fouprzj5apgznzehprcr.streamlit.app 방문

1. **마스터 클래스 (Lab)** 탭 클릭
2. Step 1: 가설 입력 (예: "빨간색 배너가 클릭률을 높일 것이다")
3. Step 2: 배너 문구 수정 (Title, Badge 등)
4. Step 3~4: 파워 분석 후 시뮬레이션 실행
5. Step 5: 결과 확인 (P-value < 0.05면 유의미)
6. Step 6: **채택** 버튼 클릭

### 3. 프로덕션 반영 확인 (1분)

https://novarium-mvp.onrender.com 새로고침

- 배너 문구가 실험에서 설정한 대로 변경되었는지 확인
- 롤백 원하면 Dashboard에서 **롤백** 버튼 클릭

---

## 기술 스택

| Layer | Tech | Purpose |
|-------|------|---------|
| Frontend | Streamlit | 인터랙티브 분석 대시보드 |
| Backend | FastAPI | Target App 서버 |
| Database | Supabase (PostgreSQL) | 클라우드 데이터 저장 |
| Simulation | Agent Swarm | 5가지 페르소나 기반 유저 행동 시뮬레이션 |
| Statistics | Scipy | Z-test, 신뢰구간 계산 |
| Hosting | Streamlit Cloud + Render | 무료 티어 배포 |

---

## 구현하지 않은 것 (MVP 범위 외)

현재 MVP에서는 다음 기능을 의도적으로 제외했습니다:

- **다중 실험 동시 진행**: 현재는 1개 실험만 활성화 가능
- **고급 통계 기법**: Bayesian A/B Testing, Multi-Armed Bandit 등
- **실시간 모니터링**: 실험 중 실시간 대시보드 업데이트
- **세분화된 권한 관리**: 관리자/분석가 역할 분리

이 기능들은 향후 확장 시 추가 예정입니다.

---

## 소스 코드

GitHub: https://github.com/1916571-alt/NovaRium-MVP

```
NovaRium-MVP/
├── src/                 # Streamlit 대시보드
├── target_app/          # FastAPI 타겟 앱
├── agent_swarm/         # AI 에이전트 시뮬레이션
└── docs/                # 문서
```

---

## 문의

프로젝트에 대한 질문이나 피드백은 GitHub Issues를 통해 남겨주세요.

---

> **Last Updated**: 2025-12-26
