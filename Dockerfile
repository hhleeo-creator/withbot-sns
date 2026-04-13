# ─── Stage 1: 프론트엔드 빌드 ───
FROM node:18-alpine AS frontend-build
WORKDIR /app/frontend

# Vite 빌드 시 VITE_ 환경변수를 번들에 포함시키기 위해 ARG → ENV 변환
ARG VITE_GOOGLE_CLIENT_ID
ENV VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ─── Stage 2: 백엔드 + 프론트엔드 서빙 ───
FROM python:3.11-slim
WORKDIR /app

# 시스템 패키지 (Pillow, 폰트)
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 백엔드 소스
COPY backend/ .

# 프론트엔드 빌드 결과물 → static/
COPY --from=frontend-build /app/frontend/dist ./static/

# uploads 디렉토리
RUN mkdir -p /app/uploads

# 환경변수 기본값
ENV UPLOAD_DIR=/app/uploads
ENV ENVIRONMENT=production
ENV SECRET_KEY=change-this-in-production
ENV PORT=8080

EXPOSE 8080

# Render는 PORT 환경변수를 동적으로 설정함
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
