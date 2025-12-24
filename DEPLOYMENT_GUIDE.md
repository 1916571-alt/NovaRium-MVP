# NovaRium 배포 가이드 (Deployment Guide)

NovaRium을 실제 웹사이트로 배포하는 여러 방법을 안내합니다.

---

## 🎯 배포 옵션 개요

NovaRium은 2개의 애플리케이션으로 구성되어 있습니다:
1. **Streamlit Dashboard** (`src/app.py`) - A/B 테스트 설계 및 분석 대시보드
2. **FastAPI Target App** (`target_app/main.py`) - 실험 대상 웹 애플리케이션

각각 독립적으로 배포하거나, 하나의 서버에 함께 배포할 수 있습니다.

---

## 📦 Option 1: Streamlit Community Cloud (무료, 가장 쉬움)

**장점**: 무료, 설정 간단, Git 연동 자동 배포
**단점**: Target App 별도 배포 필요, 공개 리포지토리만 가능 (또는 유료 플랜)

### 1.1 Streamlit Dashboard 배포

```bash
# 1. GitHub에 코드 푸시 (이미 완료)
git push origin master

# 2. Streamlit Community Cloud 접속
# https://share.streamlit.io/

# 3. "New app" 클릭
# - Repository: 1916571-alt/NovaRium-MVP
# - Branch: master
# - Main file path: src/app.py

# 4. Advanced settings에서 환경 변수 설정 (선택사항)
# - 없어도 작동하지만, DB 경로 등 설정 가능
```

### 1.2 Target App 배포 (Render/Railway)

Target App은 FastAPI이므로 Render.com 또는 Railway.app에 배포:

**Render.com (무료 플랜 제공)**:
```bash
# 1. render.com 회원가입
# 2. "New Web Service" 선택
# 3. GitHub 리포지토리 연결
# 4. 설정:
#    - Name: novarium-target-app
#    - Environment: Python 3
#    - Build Command: pip install -r requirements.txt
#    - Start Command: uvicorn target_app.main:app --host 0.0.0.0 --port $PORT
```

**주의**: 무료 플랜은 비활성 시 슬립 모드로 전환되어 첫 요청이 느릴 수 있습니다.

---

## 🐳 Option 2: Docker + 클라우드 VM (추천, 프로덕션급)

**장점**: 완전한 제어, 안정적, 확장 가능
**단점**: 초기 설정 복잡, 비용 발생

### 2.1 Docker 설정

프로젝트 루트에 `Dockerfile` 생성:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose ports
EXPOSE 8501 8000

# Create startup script
RUN echo '#!/bin/bash\n\
uvicorn target_app.main:app --host 0.0.0.0 --port 8000 &\n\
streamlit run src/app.py --server.port 8501 --server.address 0.0.0.0\n\
' > /app/start.sh && chmod +x /app/start.sh

CMD ["/app/start.sh"]
```

`docker-compose.yml` 생성:

```yaml
version: '3.8'

services:
  novarium:
    build: .
    ports:
      - "8501:8501"  # Streamlit
      - "8000:8000"  # Target App
    volumes:
      - ./novarium_local.db:/app/novarium_local.db
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
```

### 2.2 클라우드 VM 배포

**AWS EC2 / Google Cloud Compute Engine / Azure VM 공통 단계**:

```bash
# 1. VM 인스턴스 생성 (Ubuntu 22.04 LTS 권장)
# - CPU: 2 vCPU
# - RAM: 4GB
# - Storage: 20GB

# 2. SSH 접속 후 Docker 설치
sudo apt update
sudo apt install -y docker.io docker-compose git
sudo usermod -aG docker $USER

# 3. 코드 클론
git clone https://github.com/1916571-alt/NovaRium-MVP.git
cd NovaRium-MVP

# 4. Docker 컨테이너 실행
docker-compose up -d

# 5. 방화벽 규칙 설정
# - 8501 (Streamlit), 8000 (Target App) 포트 개방
```

**도메인 연결**:
```bash
# Nginx 리버스 프록시 설정
sudo apt install nginx

# /etc/nginx/sites-available/novarium 생성
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    location /target {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }
}

sudo ln -s /etc/nginx/sites-available/novarium /etc/nginx/sites-enabled/
sudo nginx -s reload
```

---

## ☁️ Option 3: Serverless (비용 효율적, 중급)

**Vercel (Streamlit 대체) + AWS Lambda (FastAPI)**

### 3.1 Streamlit 대신 Next.js로 재구성 (고급)
Streamlit은 서버리스에 적합하지 않으므로, 프론트엔드를 Next.js로 재작성 필요.

### 3.2 FastAPI를 AWS Lambda로 배포

```bash
# Mangum 설치 (ASGI → Lambda 어댑터)
pip install mangum

# target_app/main.py 수정
from mangum import Mangum

app = FastAPI()
# ... 기존 코드 ...

# Lambda handler 추가
handler = Mangum(app)
```

AWS SAM 또는 Serverless Framework로 배포:
```yaml
# serverless.yml
service: novarium-target-app

provider:
  name: aws
  runtime: python3.12
  region: ap-northeast-2

functions:
  api:
    handler: target_app.main.handler
    events:
      - http: ANY /
      - http: ANY /{proxy+}
```

```bash
# 배포
serverless deploy
```

---

## 🚀 빠른 시작 (Quick Start for Production)

**가장 빠르고 간단한 방법** (Streamlit Cloud + Render.com):

1. **Streamlit Dashboard**:
   - https://share.streamlit.io/ 접속
   - GitHub 리포지토리 연결
   - 자동 배포 완료

2. **Target App**:
   - https://render.com/ 접속
   - "New Web Service" 생성
   - Start command: `uvicorn target_app.main:app --host 0.0.0.0 --port $PORT`

3. **완료!**
   - Dashboard: https://your-app.streamlit.app
   - Target App: https://novarium-target-app.onrender.com

---

## 📊 비용 비교

| 방법 | 월 비용 (USD) | 난이도 | 안정성 |
|------|---------------|--------|--------|
| Streamlit Cloud Free + Render Free | $0 | ⭐ | ⭐⭐ |
| AWS EC2 t3.small | ~$15 | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Google Cloud Run | ~$5-10 (사용량 기반) | ⭐⭐ | ⭐⭐⭐⭐ |
| AWS Lambda + API Gateway | ~$1-5 (사용량 기반) | ⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## ⚠️ 프로덕션 체크리스트

배포 전 반드시 확인:

- [ ] 데이터베이스 영구 스토리지 설정 (novarium_local.db 백업)
- [ ] 환경 변수로 민감 정보 관리 (DB 경로, API 키 등)
- [ ] HTTPS 적용 (Let's Encrypt 무료 인증서)
- [ ] 방화벽 및 보안 그룹 설정
- [ ] 모니터링 설정 (CloudWatch, Datadog 등)
- [ ] 자동 백업 설정
- [ ] 도메인 네임 설정 (선택사항)

---

## 🔧 트러블슈팅

### Issue 1: DuckDB 파일 잠금 오류
**해결**: 각 앱이 독립적인 DB 연결을 사용하도록 READ ONLY 모드 또는 별도 DB 파일 사용

### Issue 2: 무료 플랜 슬립 모드
**해결**: UptimeRobot (https://uptimerobot.com/) 사용하여 5분마다 ping

### Issue 3: 메모리 부족
**해결**: VM 인스턴스 크기 증가 또는 pandas 대신 polars 사용

---

## 📚 추가 자료

- [Streamlit Deployment Guide](https://docs.streamlit.io/streamlit-community-cloud/get-started)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [AWS EC2 Tutorial](https://aws.amazon.com/ec2/getting-started/)

---

**추천 배포 방법 (포트폴리오용)**:
→ **Streamlit Community Cloud (대시보드) + Render.com Free (Target App)**

무료이고 설정이 간단하며, 포트폴리오 프로젝트로 충분한 성능을 제공합니다.
