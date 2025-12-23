# NovaRium-MVP

**A/B Testing Master Class Simulator** - 누구나 쉽게 배우는 데이터 분석 시뮬레이터

> 이론으로만 배우는 A/B 테스트는 그만. 직접 경험하며 데이터 분석가로 다시 태어나세요.

## 🌟 Features

- **5단계 마스터 클래스**: 가설 설정부터 통계 분석까지 전 과정 실습
- **Agent Swarm 시뮬레이션**: 5가지 성향의 AI 에이전트가 실제 앱을 방문
- **실험 회고록**: 모든 실험을 상세한 성적표로 기록
- **위기 감지 시스템**: 지표 급락 시 자동 경고 및 해결 가이드

## 📚 Documentation

모든 프로젝트 문서는 [`/docs`](./docs) 폴더에서 확인하실 수 있습니다:

- [📖 README](./docs/README.md) - 상세 프로젝트 소개
- [📋 PRD](./docs/PRD.md) - 제품 요구사항 문서
- [📊 Presentation](./docs/presentation.md) - 발표 자료 (Marp)
- [📝 Tutorial](./docs/Tutorial.md) - AI Agent 협업 튜토리얼
- [✅ Task List](./docs/task.md) - 구현 작업 목록
- [💡 Ideation](./docs/Ideation.md) - 프로젝트 아이디어 스케치

## 🚀 Quick Start

### 1. 환경 설정

```bash
# 가상환경 생성 및 활성화
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# 의존성 설치
pip install -r requirements.txt
```

### 2. 서버 실행

```bash
# Target App (포트 8000)
python target_app/main.py

# Dashboard (포트 8501)
streamlit run scripts/dashboard.py
```

### 3. 접속

- **🛒 쇼핑몰 앱**: http://localhost:8000
- **📊 분석 대시보드**: http://localhost:8501

## 🌐 Live Demo

- **Presentation**: https://1916571-alt.github.io/NovaRium-MVP/
- **Repository**: https://github.com/1916571-alt/NovaRium-MVP

## 🛠️ Tech Stack

- **Frontend**: Streamlit (Dashboard), FastAPI (Target App)
- **Database**: DuckDB (Local OLAP)
- **Analysis**: Scipy (Statistical Testing), Plotly (Visualization)
- **Simulation**: Custom Agent Swarm (5 Personas)

## 📁 Project Structure

```
NovaRium-MVP/
├── docs/                  # 📚 모든 문서
├── scripts/               # 🔧 유틸리티 스크립트
│   ├── dashboard.py       # Streamlit 대시보드
│   ├── create_gh_issues.py # GitHub 이슈 생성
│   └── ...
├── agent_swarm/           # 🤖 AI 에이전트 시뮬레이터
├── target_app/            # 🛒 타겟 앱 (FastAPI)
├── raw_data/              # 📊 원본 데이터
└── requirements.txt       # 의존성 목록
```

## 📝 License

MIT License

---

**Made with ❤️ by AI Agent Collaboration**
