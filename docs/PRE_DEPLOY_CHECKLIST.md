# Pre-Deployment Checklist for Schema v2.0

이 문서는 로컬에서 테스트 완료된 v2.0 스키마를 클라우드(PostgreSQL/Supabase)에 배포하기 전 확인해야 할 항목들입니다.

---

## 변경사항 요약

### 테이블 변경
| 변경 전 | 변경 후 | 비고 |
|--------|---------|------|
| `users` | `customers` | 테이블명 변경 |
| `user_id` | `customer_id` | 컬럼명 변경 |

### 새로운 테이블 (Auth)
- `auth_users` - 플랫폼 사용자 (분석가, 관리자)
- `oauth_accounts` - 소셜 로그인 연동
- `sessions` - 세션 토큰 관리

### 새로운 컬럼
| 테이블 | 새 컬럼 |
|--------|---------|
| `experiments` | `name`, `description`, `status`, `created_by`, `updated_at` |
| `adoptions` | `winning_variant`, `adopted_by`, `notes` |

---

## 배포 전 체크리스트

### 1. 로컬 테스트 완료 확인

- [x] DuckDB 마이그레이션 성공 (`python scripts/migrate_v2.py --mode duckdb`)
- [x] `customers` 테이블 생성 (1000 rows)
- [x] `orders` 테이블 `customer_id` 컬럼 사용
- [x] FK 무결성 검증 (orphan records: 0)
- [x] Auth 테이블 3개 생성
- [x] `database.py` 추상화 계층 테스트 통과
- [x] `get_user_segments()` 함수 정상 작동

### 2. 코드 변경 완료 확인

- [x] `src/app.py` - SQL 쿼리 `users` → `customers` 변경
- [x] `src/core/stats.py` - SQL 쿼리 업데이트
- [x] `src/data/db.py` - 테이블명 및 주석 업데이트
- [x] `src/data/database.py` - 추상화 계층 생성

### 3. 클라우드 배포 전 준비

- [ ] **Supabase 데이터 백업**
  ```bash
  # Supabase Dashboard > Database > Backups
  # 또는 pg_dump 사용
  ```

- [ ] **마이그레이션 스크립트 Dry-run 확인**
  ```bash
  python scripts/migrate_v2.py --mode postgres --dry-run
  ```

- [ ] **환경 변수 확인**
  ```bash
  # .env 또는 Render/Streamlit 대시보드에서 확인
  DB_MODE=supabase
  DATABASE_URL=postgresql://...
  ```

### 4. 클라우드 마이그레이션 실행

- [ ] **PostgreSQL 마이그레이션 실행**
  ```bash
  export DATABASE_URL="postgresql://..."
  python scripts/migrate_v2.py --mode postgres
  ```

- [ ] **마이그레이션 검증**
  ```bash
  python scripts/migrate_v2.py --mode postgres --verify
  ```

### 5. 배포 후 확인

- [ ] **Supabase 대시보드에서 테이블 확인**
  - `customers` 테이블 존재
  - `auth_users`, `oauth_accounts`, `sessions` 테이블 존재
  - `experiments` 테이블에 새 컬럼 추가됨

- [ ] **Streamlit Cloud 앱 테스트**
  - 대시보드 로딩 정상
  - 세그먼트 분석 기능 작동
  - 실험 데이터 조회 정상

- [ ] **Render.com FastAPI 앱 테스트**
  - `/health` 엔드포인트 응답
  - `/` 페이지 렌더링

---

## 롤백 계획

만약 마이그레이션 후 문제가 발생하면:

### Option 1: 데이터 복원
```sql
-- Supabase SQL Editor에서 실행
-- customers → users 롤백 (필요시)
ALTER TABLE customers RENAME TO users;
ALTER TABLE users RENAME COLUMN customer_id TO user_id;
```

### Option 2: 백업에서 복원
- Supabase Dashboard > Database > Backups에서 복원

---

## 잠재적 위험 요소

| 위험 | 영향 | 완화 방법 |
|------|------|----------|
| 마이그레이션 중 연결 끊김 | 부분 마이그레이션 | 트랜잭션 사용, 재시도 |
| 기존 데이터 손실 | 복구 불가 | 백업 필수 |
| 코드-DB 불일치 | 앱 오류 | 마이그레이션 후 즉시 배포 |

---

## 마이그레이션 순서 권장

1. **Supabase 백업** (5분)
2. **코드 커밋 & 푸시** (배포 전)
3. **PostgreSQL 마이그레이션 실행** (2분)
4. **Render.com 재배포** (자동 또는 수동)
5. **Streamlit Cloud 재배포** (자동)
6. **기능 테스트** (5분)
7. **완료 확인**

---

## 연락처

문제 발생 시:
- Supabase 상태: https://status.supabase.com/
- Render 상태: https://status.render.com/
- Streamlit 상태: https://status.streamlit.app/

---

**마지막 업데이트**: 2025-12-30
**상태**: 로컬 테스트 완료, 클라우드 배포 대기 중
