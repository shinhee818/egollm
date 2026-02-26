FROM python:3.11-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 의존성 파일 먼저 복사 (레이어 캐싱 최적화)
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사 (코드 변경 시에만 재빌드)
COPY app ./app

EXPOSE 8000

# Cloud Run은 PORT 환경변수를 주입하므로 이를 사용 (기본값 8000)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
