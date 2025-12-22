# NovaRium-MVP 구현 작업 목록

## 0단계: 프로젝트 설정 (Project Setup)
- [x] Git 저장소 초기화 및 .gitignore 설정 <!-- id: git-init -->
- [x] GitHub 퍼블릭 리포지토리 생성 및 업로드 <!-- id: git-push -->

## 1단계: 데이터 생성 (The Generator)
- [ ] Python 환경 설정 및 라이브러리 설치 (`faker`, `pandas`, `duckdb`, `scipy`) <!-- id: 0 -->
- [ ] `generating_data.py` 스크립트 기본 구조 작성 <!-- id: 1 -->
- [ ] 유저 데이터 생성 로직 구현 (`users.csv`) <!-- id: 2 -->
- [ ] 주문 데이터 생성 로직 구현 (`orders.csv`) <!-- id: 3 -->
- [ ] A/B 테스트 로그 생성 로직 구현 (`ab_test_logs.csv`) <!-- id: 4 -->
- [ ] `raw_data/` 폴더에 CSV 파일 생성 확인 <!-- id: 5 -->

## 2단계: 로컬 데이터 웨어하우스 (The Warehouse)
- [ ] CSV 파일을 DuckDB로 로드하는 스크립트 작성 <!-- id: 6 -->
- [ ] `novarium_local.db` 데이터베이스 초기화 <!-- id: 7 -->
- [ ] `users`, `orders`, `ab_test_logs` 테이블에 데이터 적재 <!-- id: 8 -->
- [ ] 데이터 건수 및 스키마 확인 <!-- id: 9 -->

## 3단계: 분석 및 검증 (The Analysis)
- [ ] `analysis.ipynb` 또는 SQL 분석 스크립트 생성 <!-- id: 10 -->
- [ ] 데이터 마트 구성을 위한 SQL 작성 (유저 집계, 첫 주문일 등) <!-- id: 11 -->
- [ ] 코호트 분석 구현 (Retention Rate 계산) <!-- id: 12 -->
- [ ] 세그먼트 분석 구현 (직장인 vs 학생) <!-- id: 13 -->
- [ ] A/B 테스트 성과 분석 (전환율 비교, p-value 계산) <!-- id: 14 -->
- [ ] ROI 계산 (마케팅 비용 대비 매출) <!-- id: 15 -->
- [ ] 최종 분석 인사이트 리포트 작성 <!-- id: 16 -->
