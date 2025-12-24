# 📁 폴더 재구성 계획

## 현재 구조 (Current)

```
friendly-buck/
├── agent_swarm/          # Agent simulation
│   ├── agent.py
│   ├── behaviors.py
│   └── runner.py
├── docs/                 # Documentation (scattered)
│   ├── Ideation.md
│   ├── PRD.md
│   ├── presentation.md
│   ├── README.md
│   ├── task.md
│   └── Tutorial.md
├── scripts/              # Utility scripts
│   ├── create_gh_issues.py
│   ├── db_client.py
│   ├── generate_history.py
│   └── run_etl.py
├── src/
│   ├── core/            # Business logic
│   │   ├── mart_builder.py
│   │   ├── simulation.py
│   │   └── stats.py
│   ├── data/            # Database layer
│   │   └── db.py
│   ├── ui/              # UI components
│   │   ├── components.py
│   │   └── pages/
│   └── app.py           # Main Streamlit app
├── target_app/          # Target web app (FastAPI)
│   └── main.py
├── tests/               # Unit tests
│   ├── test_analytics.py
│   └── test_behaviors.py
├── *.md                 # Root-level docs (messy)
│   ├── HYBRID_SIMULATION.md
│   ├── MIGRATION_GUIDE.md
│   ├── QUICK_START.md
│   └── README.md
├── migrate_db.py        # Migration scripts (root)
├── migrate_db_hybrid.py
├── check_db.py
└── test_simulation.py
```

## 문제점 (Issues)

1. **문서 파편화**: README, guides가 root와 docs/ 양쪽에 흩어짐
2. **스크립트 분산**: migration, check_db가 root에 있음 → scripts/로 이동 필요
3. **테스트 파일 혼재**: test_simulation.py가 root에 있음 → tests/로 이동
4. **임시 파일**: folder_structure.txt, task.md 같은 파일들
5. **설정 파일 부재**: config.py가 없어서 하드코딩된 설정 많음

---

## 개선된 구조 (Proposed)

```
friendly-buck/
├── .agent/              # Claude Code agent rules
│   └── rules/
├── agent_swarm/         # Agent simulation (no change)
│   ├── __init__.py
│   ├── agent.py
│   ├── behaviors.py
│   └── runner.py
├── docs/                # 📚 All documentation consolidated
│   ├── guides/          # User guides
│   │   ├── QUICK_START.md (moved from root)
│   │   ├── MIGRATION_GUIDE.md (moved from root)
│   │   └── Tutorial.md
│   ├── design/          # Design docs
│   │   ├── HYBRID_SIMULATION.md (moved from root)
│   │   ├── Ideation.md
│   │   ├── PRD.md
│   │   └── presentation.md
│   ├── development/     # Dev docs
│   │   └── task.md
│   └── README.md        # Docs index
├── scripts/             # 🔧 All utility scripts
│   ├── db/              # Database scripts
│   │   ├── migrate_db.py (moved from root)
│   │   ├── migrate_db_hybrid.py (moved from root)
│   │   ├── check_db.py (moved from root)
│   │   └── db_client.py
│   ├── data/            # Data generation
│   │   └── generate_history.py
│   └── utils/           # Other utilities
│       ├── create_gh_issues.py
│       └── run_etl.py
├── src/
│   ├── config/          # ⚙️ NEW: Configuration
│   │   ├── __init__.py
│   │   ├── settings.py  # App settings (DB path, ports, etc.)
│   │   └── constants.py # Constants (metrics, defaults)
│   ├── core/            # Business logic
│   │   ├── __init__.py
│   │   ├── mart_builder.py
│   │   ├── simulation.py
│   │   └── stats.py
│   ├── data/            # Database layer
│   │   ├── __init__.py
│   │   ├── db.py
│   │   └── queries.py   # NEW: SQL queries separated
│   ├── ui/              # UI components
│   │   ├── __init__.py
│   │   ├── components.py
│   │   └── pages/
│   ├── utils/           # Utilities
│   │   └── __init__.py
│   └── app.py           # Main Streamlit app
├── target_app/          # Target web app (FastAPI)
│   ├── __init__.py
│   ├── main.py
│   ├── config.py        # NEW: FastAPI config
│   └── templates/       # HTML templates
├── tests/               # 🧪 All tests
│   ├── __init__.py
│   ├── test_analytics.py
│   ├── test_behaviors.py
│   └── test_simulation.py (moved from root)
├── .gitignore
├── README.md            # Main README only
├── requirements.txt
└── novarium_local.db    # Database file
```

---

## 이동 계획 (Migration Plan)

### Phase 1: 문서 정리 (Documentation)
```bash
# Create new structure
mkdir -p docs/guides docs/design docs/development

# Move guides
mv QUICK_START.md docs/guides/
mv MIGRATION_GUIDE.md docs/guides/

# Move design docs
mv HYBRID_SIMULATION.md docs/design/

# Update docs/README.md with index
```

### Phase 2: 스크립트 정리 (Scripts)
```bash
# Create new structure
mkdir -p scripts/db scripts/data scripts/utils

# Move DB scripts
mv migrate_db.py scripts/db/
mv migrate_db_hybrid.py scripts/db/
mv check_db.py scripts/db/

# Move data scripts
mv scripts/generate_history.py scripts/data/

# Move utils
mv scripts/create_gh_issues.py scripts/utils/
mv scripts/run_etl.py scripts/utils/
```

### Phase 3: 테스트 정리 (Tests)
```bash
# Move test files
mv test_simulation.py tests/

# Add __init__.py
touch tests/__init__.py
```

### Phase 4: 설정 파일 생성 (Config)
```bash
# Create config structure
mkdir -p src/config

# Create files (will be done programmatically)
touch src/config/__init__.py
touch src/config/settings.py
touch src/config/constants.py
```

### Phase 5: 임시 파일 제거 (Cleanup)
```bash
# Remove temporary files
rm -f folder_structure.txt
rm -f task.md  # (moved to docs/development/)
```

---

## 장점 (Benefits)

1. **명확한 구조**: 파일 위치를 예측 가능
2. **관심사 분리**: 문서/스크립트/코드가 명확히 분리됨
3. **확장성**: 새로운 기능 추가 시 어디에 넣을지 명확
4. **유지보수**: 설정 변경이 config/에서만 이루어짐
5. **전문성**: 프로덕션급 프로젝트 구조

---

## 실행 시점

- **즉시 실행**: 문서와 스크립트 이동 (Phase 1, 2, 3, 5)
- **점진적 실행**: 설정 파일 분리 (Phase 4) - 기존 코드 리팩토링 필요

---

## 주의사항

1. **Import 경로 변경**: 파일 이동 시 import 경로도 업데이트 필요
   - `from check_db import ...` → `from scripts.db.check_db import ...`

2. **문서 링크 업데이트**: README의 링크가 깨질 수 있음
   - `[Quick Start](QUICK_START.md)` → `[Quick Start](docs/guides/QUICK_START.md)`

3. **Git History 유지**: `git mv` 명령어 사용 권장
   ```bash
   git mv QUICK_START.md docs/guides/QUICK_START.md
   ```

4. **상대 경로 검증**: 스크립트 내 상대 경로가 여전히 작동하는지 확인
