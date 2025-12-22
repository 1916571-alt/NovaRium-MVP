# NovaRium-MVP: AI Agent 협업 튜토리얼

이 문서는 AI Agent와 함께 **NovaRium-MVP** 프로젝트를 구축하는 과정을 기록한 튜토리얼입니다. 실제 사용된 프롬프트와 에이전트의 수행 결과를 중심으로 정리했습니다.

## 1. 프로젝트 기획 (Ideation & PRD)

가장 먼저 프로젝트의 아이디어를 구체화하고 요구사항을 정의했습니다.

### 🗣️ Prompt
> "데이터 분석가로서의 역량을 보여줄 수 있는 로컬 퍼스트 데이터 분석 프로젝트 아이디어를 제안해줘."
> "제안된 아이디어를 바탕으로 PRD(제품 요구사항 문서)를 작성해줘."
> "PRD를 기반으로 구현해야 할 작업 목록을 task.md에 정리해줘."

### 🤖 Agent Action
*   **`Ideation.md`**: 프로젝트 아이디어 스케치 작성.
*   **`PRD.md`**: 상세 기능, 기술 스택, 구현 로드맵 정의.
*   **`task.md`**: 구현 단계별 체크리스트 생성.

---

## 2. 프로젝트 셋업 및 깃허브 호스팅

로컬 프로젝트 폴더를 깃허브 퍼블릭 리포지토리로 호스팅했습니다.

### 🗣️ Prompt
> "이 프로젝트를 github에 호스팅해줘. 퍼블릭 리포지토리로 만들어줘."

### 🤖 Agent Action
1.  **Git 초기화**: `git init` 실행.
2.  **설정 파일 생성**: Python 프로젝트에 맞는 `.gitignore` 자동 생성.
3.  **커밋**: 초기 파일들(`Ideation.md`, `PRD.md`, `task.md`) 커밋.
4.  **리포지토리 생성 및 푸시**:
    ```bash
    gh repo create NovaRium-MVP --public --source=. --push
    ```

### ✅ Result
*   GitHub Repository 생성 완료: [NovaRium-MVP](https://github.com/1916571-alt/NovaRium-MVP)

---

## 3. 태스크 관리 (GitHub Issues 자동 생성)

단순한 텍스트 할 일 목록(`task.md`)을 실제 깃허브 이슈로 변환하여 관리 체계를 구축했습니다.

### 🗣️ Prompt
> "태스크의 항목들을 깃헙 이슈로 등록해줘. 이슈에는 작업 배경, 작업 내용, 인수 조건이 포함 되어야 해."

### 🤖 Agent Action
1.  **구현 계획 수립**: `task.md`와 `PRD.md`를 분석하여 17개의 이슈 세부 내용(배경, 상세, 인수조건)을 매핑.
2.  **자동화 스크립트 작성**: `create_gh_issues.py` 파이썬 스크립트 생성.
    *   GitHub CLI(`gh`)를 사용하여 이슈를 일괄 생성하는 스크립트.
3.  **스크립트 실행**: 스크립트를 실행하여 리포지토리에 이슈 등록.
4.  **정리**: 사용한 임시 스크립트 삭제.

### ✅ Result
*   [GitHub Issues 목록](https://github.com/1916571-alt/NovaRium-MVP/issues)에 17개 태스크가 상세 내용과 함께 등록됨.

---

## 4. 튜토리얼 문서화

현재까지의 작업 과정을 문서화하여 기록으로 남깁니다.

### 🗣️ Prompt
> "지금까지 작업한 것을 프롬프트 중심으로 튜토리얼로 만들어줘. 튜토리얼은 Tutorial.md 파일에 문서화해줘"

### 🤖 Agent Action
*   **`Tutorial.md`**: 본 문서 작성.
