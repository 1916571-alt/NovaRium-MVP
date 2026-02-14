# V2 Migration Reuse Map

## 원칙
- A-Z를 다시 설계하되, 검증된 도메인 로직은 적극 재사용한다.
- UI/DB 접근/인프라 경계는 V2 기준으로 재작성한다.

## 1. 즉시 재사용 가능 (High Reuse)
1. 통계 계산 함수
   - Source: `src/core/stats.py`
   - Reuse: `calculate_statistics`, `check_srm`, `bonferroni_correction`, CI 관련 함수
   - Action: 프레임워크 의존(streamlit cache) 제거 후 `packages/domain/stats.py`로 이동

2. 검증/예외 모델
   - Source: `src/core/validators.py`, `src/core/errors.py`
   - Reuse: 입력 검증 규칙, 커스텀 에러 계층
   - Action: API schema와 맞게 파라미터 명세만 조정

3. 에이전트 행동 모델
   - Source: `agent_swarm/behaviors.py`, `agent_swarm/agent.py`
   - Reuse: 페르소나 로직
   - Action: 이벤트명 표준화(`click_cta` 등) 및 API v2 endpoint로 송신 변경

## 2. 부분 재사용 (Refactor Required)
1. 실험 단계 UX 로직
   - Source: `src/ui/pages/experiment/*`
   - Reuse: 단계별 안내 흐름과 학습 문맥
   - Action: Streamlit 의존 제거, Next.js UI로 재구현

2. 데이터 마트 SQL 생성 아이디어
   - Source: `src/core/mart_builder.py`
   - Reuse: KPI mart 생성 아이디어
   - Action: PostgreSQL 기준으로 재작성, canonical event 이름으로 교체

3. 캐시 계층 개념
   - Source: `src/core/cache.py`
   - Reuse: TTL 전략
   - Action: Streamlit cache 대신 Redis/API cache로 이전

## 3. 재사용 금지/폐기 (Do Not Carry)
1. 혼합 DB 경로/직접 파일 락 조정
   - Source: `src/data/db.py` 내 DuckDB coordination
   - Reason: V2는 PostgreSQL + RLS 기반

2. 임시 admin SQL 실행 endpoint
   - Source: `target_app/main.py` `/admin/execute_sql`
   - Reason: 보안 리스크 큼, 학습용 SQL은 sandbox 실행기로 대체

3. 이벤트 명칭 혼재 로직
   - Source: `click_banner`, `banner_A`, `banner_B` 혼합 사용부
   - Reason: 분석 일관성 저해

## 4. V2 이관 우선순위
1. Stats/Validation/Error 모듈 이관
2. Agent 행동 모델 이관 + 이벤트 표준화
3. Funnel/Experiment 분석 함수 이관
4. UI는 새로 작성
5. DB/Infra는 새로 작성

## 5. 코드 이관 체크리스트
1. Streamlit 의존 제거 여부
2. SQL 파라미터 바인딩 적용 여부
3. 이벤트 enum 표준 준수 여부
4. 테넌트 스코프(project_id/workspace_id) 강제 여부
5. 테스트 통과 여부 (unit + integration)

## 6. 첫 번째 이관 대상 파일 (권장)
1. `src/core/errors.py`
2. `src/core/validators.py`
3. `src/core/stats.py` (순수 함수만)
4. `agent_swarm/behaviors.py`
